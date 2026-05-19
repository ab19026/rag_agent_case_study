import sys, os
sys.path.append('..')
from util.io import *
from transformers import AutoTokenizer, AutoModelForCausalLM
import json
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from pymilvus.model.reranker import BGERerankFunction
from util.util import *
from interface.socket_service_base import *
import pickle

'''
    单模型实例,启动后将以websocket server形式对外提供推理服务
'''
class ModelInstance(SocketServiceBase):
    def __init__(self, model_name, port):
        self.model_name = model_name
        self.model_conf = parse_json_file('../conf/model_conf.json')
        self.port = port
        self.async_websocket_server = AsyncWebSocketServer(
            self.infer, 
            None,
            port
        )
        #用于RAG的同时支持稠密和稀疏向量的embedding模型
        if model_name == 'embedding':
            self.model = BGEM3EmbeddingFunction(
                model_name=model_name,
                device='cpu',
                use_fp16=False
            )
        #用于RAG的rerank模型
        elif model_name == 'rerank':
            self.model = BGERerankFunction(
                model_name=model_name,
                device="cpu"
            )
        #如果是通用需求(agent对话、优化等)
        #可以调用本地模型或者通过API调用外部大模型服务
        elif model_name == 'agent':
            if self.model_conf['local']:
                self.model_name += '_local'
                tokenizer = AutoTokenizer.from_pretrained(self.model_conf['name'])
                model = AutoModelForCausalLM.from_pretrained(self.model_conf['name'])
                self.model = {'tokenizer' : tokenizer, 'model' : model}
            elif self.model_conf['api'] is not None and self.model_conf['api']['key'] is not None and self.model_conf['api']['host'] is not None:
                self.model_name += '_api'

    def infer(self, raw_request):
        start_time = time.time()
        error = None
        request = None
        try:
            request = json.loads(raw_request['msg'])
            if self.model_name == 'embedding':
                result = self.model.encode_documents(request['docs'])
                result = json.dumps({'binary' : binary_encode(result)})
            elif self.model_name == 'rerank':
                index_arr = []
                for v in self.model(query=request['query'], documents=request['docs'].split('\n'), top_k=request['topK']):
                    index_arr.append(v.index)
                result = json.dumps(index_arr)
            elif self.model_name == 'agent_local':
                messages = [
                    {"role": "user", "content": request['context']},
                ]
                inputs = tokenizer.apply_chat_template(
                    messages,
                    add_generation_prompt=True,
                    tokenize=True,
                    return_dict=True,
                    return_tensors="pt",
                ).to(model.device)
                outputs = model.generate(**inputs, max_new_tokens=100)
                result = json.dumps({'result' : tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:])})
            elif self.model_name == 'agent_api':
                result = None
            self.async_websocket_server.response(
                'FINAL:' + result, 
                raw_request['conn']
            )
        except Exception as e:
            error = e
        finally:
            log(
                {
                    'action_name' : 'model_infer',
                    'action_id' : uid(),
                    'source_id' : request['source_id'] if request is not None else 'empty',
                    'context' : {
                        'model_name' : self.model_name,
                        'instance_port' : self.port,
                        'token_num' : get_token_num(result)
                    },
                    'trace_id' : request['trace_id'],
                    'error' : "%s" % err,
                    'start_time' : start_time,
                    'end_time' : time.time()
                }
            )

    def start(self):
        self.async_websocket_server.start()

    def shutdown(self):
        self.async_websocket_server.shutdown()


if __name__ == '__main__':
    args = sys.argv
    port = args[1]
    ModelInstance(args[1], int(args[2])).start()