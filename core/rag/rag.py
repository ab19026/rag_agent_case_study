import sys, os, time
sys.path.append('..')
from util.io import *
from model.util import *
from pymilvus import MilvusClient, DataType, Function, FunctionType, AnnSearchRequest
from tool import *
from network.async_websocket import *
from pymilvus.model.reranker import BGERerankFunction
from core.context import *
from security import *

'''
    基于Milvus的RAG实现
    基于语言、细分类别隔离存储数据到多个库,而不是把所有数据放在一起,这样可以提高搜索准确率
    具备基本检索、混合检索(基于稀疏+稠密向量)以及rerank能力
'''
class Rag():
    def __init__(self, embedding_model_instance_call, rerank_model_instance_list, enhance_query_model_instance_list):
        self.embedding_model_instance_call = embedding_model_instance_call
        self.rerank_model_instance_list = rerank_model_instance_list
        self.enhance_query_model_instance_list = enhance_query_model_instance_list
        self.split_query_prompt = {
            'en' : load_file('../conf/en/prompt/split_rag_query.pmt'),
            'zh' : load_file('../conf/zh/prompt/split_rag_query.pmt'),
        }
        self.enhance_rag_query = {
            'en' : load_file('../conf/en/prompt/enhance_rag_query.pmt'),
            'zh' : load_file('../conf/zh/prompt/enhance_rag_query.pmt'),
        }
        self.rag_conf = parse_json_file('../conf/rag_conf.json')
        self.client = None
        self.table = {}
        self.__create_db()
        self.__load_local_data()
                        
    '''
        离线文档向量化和导入
    '''
    def __load_local_data(self):
        if self.rag_conf['load_data'] is not None:
            for language in self.rag_conf['load_data']:
                for category in self.rag_conf['load_data']['lang'][language]:
                    for filename in os.listdir('../data/%s/%s' % (language, category)):
                        file_path = '../data/%s/%s/%s' % (language, category, filename)
                        #基于递归方式拆分原始文档
                        if '.txt' in file_path:
                            doc = pii_mask(load_file(file_path))
                            chunks = doc_splitter(
                                doc, 
                                self.rag_conf['doc_split']['chunk_size'], 
                                self.rag_conf['doc_split']['chunk_overlap']
                            )
                        if '.pdf' in file_path:
                            chunks += pii_mask(pdf_splitter(
                                file_path, 
                                self.rag_conf['doc_split']['chunk_size'], 
                                self.rag_conf['doc_split']['chunk_overlap']
                            ))
                        #调用embedding模型对拆分后的文档进行embedding
                        model_req = json.dumps({'docs' : chunks})
                        docs_embeddings = binary_decode(json.loads(get_best_model_instance(MODEL_USAGE_EMBEDDING).send(model_req))['binary'])
                        #将原始文档和embedding后的向量插入数据库
                        for i in range(0, len(chunks), 50):
                            batched_entities = [
                                {
                                    'doc_id' : i + j, 
                                    'doc_dense' : docs_embeddings["dense"][j], 
                                    'doc_sparse' : docs_embeddings['sparse'][j], 
                                    'origin_doc' : chunks[i]
                                } for j in rangge(i, i + 50)
                            ]
                            self.__insert_data(language + '_' + categoty, batched_entities)
                        


    '''
        创建RAG数据库
    '''
    def __create_db(self):
        start_time = time.time()
        try:
            self.client = MilvusClient("../data/{%s}.db" % self.rag_conf['db_name'])
            self.table = {}
            for language in self.rag_conf['lang']:
                for category in self.rag_conf['lang'][language]:
                    table_name = language + '_' + categoty
                    self.table[table_name] = create_collection(self.client, table_name)
        except Exception as e:
            err = e
        finally:
            log ({
                    'action_name' : 'create_rag_db',
                    'error' : '%s' % err,
                    'start_time' : start_time,
                    'end_time' : time.time()
                })


    def __insert_data(self, table_name, data):
        start_time = time.time()
        res = None
        try:
            res = self.client.insert(
                collection_name=table_name,
                data=data
            )
        except Exception as e:
            err = e
        finally:
            log ({
                    'action_name' : 'insert_rag_data',
                    'context' : {'result' : res},
                    'error' : '%s' % err,
                    'start_time' : start_time,
                    'end_time' : time.time()
                })

    '''
        RAG检索核心逻辑
    '''
    def retrieve(self, request):
        action_id = uid()
        err = None
        query = None
        # 优化查询(比如把模糊查询拆分成多个精确查询)
        # 由 ../conf/rag.json 配置决定是否启用
        try:
            query = query_enhance(request['query'])
            request['query'] = query[0]
        except Exception as e:
            err = e
        finally:
            if self.rag_conf['retrieve_optimizer'] is not None:
                log ({
                    'action_name' : 'rag_enhance_query',
                    'action_id' : action_id,
                    'source_id' : request['source_id'] if request is not None else 'empty',
                    'context' : {
                        'query' :  request['query'],
                        'enhance_query' : enhance_query,
                    },
                    'trace_id' : request['trace_id'],
                    'error' : '%s' % err,
                    'start_time' : start_time,
                    'end_time' : time.time()
                })
        docs = []
        try:
            if topK is None:
                topK = 3
            rerank_topK = topK = topK * 5
            lang = zh_en_check(query)
            # 调用模型进行embedding
            model_req = json.dumps({'source_id' : action_id, 'docs' : request['query']})
            query_embedding = json.loads(get_best_model_instance(MODEL_USAGE_EMBEDDING).send(model_req))
        except Exception as e:
            err = r
        finally:
            log ({
                'action_name' : 'rag_embedding',
                'action_id' : action_id,
                'source_id' : request['source_id'] if request is not None else 'empty',
                'context' : {
                    'query' :  request['query'],
                    'query_embedding' : docs_embedding,
                },
                'trace_id' : request['trace_id'],
                'error' : '%s' % err,
                'start_time' : start_time,
                'end_time' : time.time()
            })
        try:
            # 基本向量检索 
            if not self.rag_conf['hybrid']:
                res = self.client.search(
                    collection_name=lang + '_' + category,
                    anns_field="doc_dense",
                    data=query_embedding['dense'],
                    limit=topK,
                    search_params={"metric_type": "IP"}
                )
            # 混合检索
            else:
                search_param_dense = {
                    "data": query_embedding['dense'],
                    "anns_field": "doc_dense",
                    "param": {"nprobe": 10},
                    "limit": topK
                }
                search_param_sparse = {
                    "data": query_embedding['sparse'],
                    "anns_field": "doc_sparse",
                    "limit": topK
                }
                res = client.hybrid_search(
                    collection_name=lang + '_' + category,
                    reqs=[
                        AnnSearchRequest(search_param_dense), 
                        AnnSearchRequest(search_param_parse)
                    ],
                    limit=topK
                )
            for hits in res:
                for hit in hits:
                    docs.append(hit)
        except Exception as e:
            err = e
        finally:
            log ({
                'action_name' : 'rag_retrieve',
                'action_id' : action_id,
                'source_id' : request['source_id'] if request is not None else 'empty',
                'context' : {
                    'result' : docs,
                    'hybrid' : self.rag_conf['hybrid']
                },
                'trace_id' : request['trace_id'],
                'error' : '%s' % err,
                'start_time' : start_time,
                'end_time' : time.time()
            })
        # 对检索结果进行rerank
        if self.rag_conf['rerank']:
            try:
                model_req = json.dumps({'docs' : [v['origin_doc'] for v in docs], 'query' : query, 'topK' : self.rag_conf['topK']})
                docs = [v['origin_doc'] for v in docs if v['doc_id'] in set(json.loads(get_best_model_instance(MODEL_USAGE_RERANK).send(model_req)))]
            except Exception as e:
                err = e
            finally:
                log ({
                    'action_name' : 'rag_rerank',
                    'action_id' : action_id,
                    'source_id' : request['source_id'] if request is not None else 'empty',
                    'context' : {
                        'result' : docs,
                    },
                    'trace_id' : request['trace_id'],
                    'error' : '%s' % err,
                    'start_time' : start_time,
                    'end_time' : time.time()
                })
        return [v['origin_doc'] for v in docs]

    '''
        优化查询质量(比如将模糊的查询语句拆分成多个更精确的查询语句)
    '''
    def query_enhance(self, query):
        lang = zh_en_check(query)
        if self.rag_conf['retrieve_optimizer'] is not None:
            for opt in self.rag_conf['retrieve_optimizer']:
                context = self.split_query_prompt[lang] % query if opt == 'SPLIT' else self.enhance_rag_query[lang] % query
                model_req = json.dumps({'context' : context})
                query = json.loads(get_best_model_instance(MODEL_USAGE_QUERY_ENHANCE).send(model_req))
        if not isinstance(query, list):
            query = [query]
        return query

