import sys, os, time, json
sys.path.append('..')
from util.io import *
from ragas import evaluate
from ragas.metrics import faithfulness, context_precision, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from datasets import Dataset
from constant import *
from network.async_websocket import *
from model.util import *
import numpy as np


def Evaluate():
    def __init__(self):
        pass

    def generate_score(self):
        pass

'''
    评估Agent生成质量
    1.合法问答评估语料文件,文件每一行对应一个问题的评估集合,格式为:
    {
        // 用户原始问题
        'query' : 'xxx',
        // agent生成的回答
        'agent_answer' : 'xxx',
        // 该问题的真实答案
        'truth_answer' : 'xxx',
        // RAG检索到的和这个问题相关的topK文档片段
        'rag_retrieve_docs' : [{'id' : '...', 'doc' : '...'}],
        // 和这个问题相关的所有文档片段
        'all_related_docs' : [{'id' : '...', 'doc' : '...'}]
    }
    2.非法问答评估语料文件,每一行包含一个无关问题和agent返回的答案
    {'query' : 'xxx', 'answer' : 'xxx'}
'''
def EffectiveEvaluate(Evaluate):
    def __init__(self, lang):
        self.app_conf = parse_json_file('../conf/app.json')
        self.lang = lang
        self.compliance_prompt = parse_json_file('../conf/prompt/%s/compliance.pmt' % lang)
        self.style_consistency_prompt = parse_json_file('../conf/prompt/%s/style_consistency.pmt' % lang)
        self.model_conf = parse_json_file('../conf/model_conf.json')
        self.evaluate_valid = parse_json_file('../data/evaluate/%s/evaluate_valid.txt' % lang)
        self.evaluate_invalid = parse_json_file('../data/evaluate/%s/evaluate_invalid.txt' % lang)
        # 由于agent使用的模型是性能较好的deepseekV4,继续用它作为评估模型也是可以的
        self.eval_llm = ChatOpenAI(
            model=self.model_conf ['agent']['name'],
            openai_api_key=self.model_conf['agent']['api']['key'],
            openai_api_base=self.model_conf['agent']['api']['host'],
            temperature=self.model_conf['agent']['temperature']
        )
        self.evaluate_model_instance_list = get_model_instance_list('agent')

    '''
        综合评估 
    '''
    def generate_score(self):
        # 计算正常指标
        acc = 0.0
        recall = 0.0
        faithfulness = 0.0
        compliance = 0.0
        style_consistency = 0.0
        for line in self.evaluate_source:
            acc += __accuracy(line)
            recall += __recall(line)
            faithfulness += __faithfulness(line)
            compliance += __compliance(line)
            style_consistency += __style_consistency(line)
        acc /= len(self.evaluate_source)
        recall /= len(self.evaluate_source)
        faithfulness /= len(self.evaluate_source)
        compliance /= len(self.evaluate_source)
        style_consistency /= len(self.evaluate_source)
        # 计算拒绝率
        hit = 0.0
        for line in self.evaluate_invalid:
            if line['answer'] in [AGENT_REFUSAL_ZH, AGENT_REFUSAL_EN]:
                hit += 1.0
        resusal_score = hit / len(self.evaluate_invalid)
        return {
            'acc' : acc,
            'recall' : recall,
            'faithfulness' : faithfulness,
            'compliance' : compliance,
            'style_consistency' : style_consistency
        }

    '''
        计算文档topK准确率
    '''
    def __accuracy(self, line):
        truth_ids = set([v['id'] for v in line['all_related_docs']])
        hit = 0.0
        for v in line['rag_retrieve_docs']:
            if v['id'] in truth_ids:
                hit += 1.0
        return hit / len(rag_retrieve_docs)

    '''
        计算文档topK召回率
    '''
    def __recall(self, line)
        truth_ids = set([v['id'] for v in line['all_related_docs']])
        hit = 0.0
        for v in line['rag_retrieve_docs']:
            if v['id'] in truth_ids:
                hit += 1.0
        return hit / len(truth_ids)

    '''
        计算agent生成答案的忠诚度
    '''
    def __faithfulness(self, line):
        dataset = Dataset.from_dict(
            {
                'question': [line['query']],
                'answer': [line['answer']],
                'contexts': [
                    [v] for v in line['rag_retrieve_docs']
                ],
                'ground_truth': [line['truth_answer']]
            }
        )
        score = evaluate(
            dataset,
            metrics=[faithfulness],
            llm=LangchainLLMWrapper(eval_llm),
        ).to_pandas()[['faithfulness']][0]
        return score

    '''
        计算回答合规性
    '''
    def __compliance(self, line):
        model_req = json.dumps({'context' : self.compliance_prompt % (line['agent_answer'], line['all_related_docs'])})
        result = get_best_model_instance(MODEL_USAGE_COMPLIANCE).send(model_req)
        return json.loads(result)['score']

    '''
        计算回答的风格一致性
    '''
    def __style_consistency(self, line):
        model_req = json.dumps({'context' : self.style_consistency_prompt % (line['truth_answer'], line['agent_answer'], line['all_related_docs'])})
        result = get_best_model_instance(MODEL_USAGE_STYLE_CONSISTENCY).send(model_req)
        return json.loads(result)['score']


'''
    评估Agent工程质量(耗时、token消耗、对话轮次等)
    主要根据日志计算相关指标
'''
def EngineeringEvaluate(Evaluate):
    def __init__(self):
        self.log = parse_json_file(self.app_conf['log_path'])
        self.step = ['total', 'agent_queue', 'agent_total', 'agent_call_model', 'rag_total', 'rag_enhance_query', 'rag_query_basic', 'rag_query_hybrid', 'rag_rerank', 'rag_embedding']


    def generate_score(self):
        time_result = {}
        context_result = {}
        for line in self.log:
            line = json.loads(log)
            trace_id = line['trace_id']
            if trace_id not in time_result:
                time_result[trace_id] = {
                    'service_route' : [],
                    'fetch_agent_task' : [],
                    'execute_agent_task' : [],
                    'agent_process_call_model' : [],
                    'rag_enhance_query' : [],
                    'rag_embedding' : [],
                    'rag_retrieve_basic' : [],
                    'rag_retrieve_hybrid' : [],
                    'rag_rerank' : []
                }
            if line['action_name'] == 'model_infer':
                if line['context']['model_name'] == 'agent':
                    time_result[trace_id]['agent_process_call_model'].append(line['end_time'] - line['start_time'])
            elif line['action_name'] == 'rag_retrieve':
                if line['context']['hybrid']:
                    time_result[trace_id]['rag_retrieve_hybrid'].append(line['end_time'] - line['start_time'])
                else:
                    time_result[trace_id]['rag_retrieve_basic'].append(line['end_time'] - line['start_time'])
            else:
                time_result[trace_id][line['action_name']].append(line['end_time'] - line['start_time'])
            if trace_id not in context_result:
                context_result[trace_id] = {
                    'agent_max_iteration' : [],
                    'model_token_num' : []
                }
            if line['action_name'] == 'model_infer':
                if line['context']['model_name'] == 'agent':
                    context_result[trace_id]['model_token_num'].append(line['context']['token_num'])
            if line['action_name'] == 'agent_process':
                context_result[trace_id]['agent_max_loop'].append(line['context']['max_iteration_num'])
        return {
            'avg_latency' : self.__avg_latency(time_result),
            'max_latency' : self.__max_latency(time_result),
            'max_iteration' : self.__conversation_loop(context_result),
            'token_consumption' : self.__token_consumption(context_result)
        }

    def __avg_latency(self, time_result):
        result = {}
        for trace_id in time_result:
            for item in time_result[trace_id]:
                result[item + '_avg_latency'] += np.mean(time_result[trace_id][item])
        for item in result:
            result[item] /= len(time_result)
        return result

    def __max_latency(self):
        result = {}
        for trace_id in time_result:
            for item in time_result[trace_id]:
                if item + '_max_latency' not in result:
                    result[item + '_max_latency'] = []
                result[item + '_max_latency'] += time_result[trace_id][item]
        for item in result:
            result[item] = sorted(result[item])[-1]
        return result

    def __token_consumption(self, context_result):
        token_num = 0.0
        for trace_id in context_result:
            token_num += sum(context_result[trace_id]['model_token_num'])
        return token_num / len(context_result)

    def __conversation_loop(self, context_result):
        max_iteration = 0.0
        for trace_id in context_result:
            max_iteration += sum(context_result[trace_id]['agent_max_loop'])
        return max_iteration / len(context_result)


if __name__ == '__main__':
    args = sys.argv
    if args[1] == 'EFFECTIVE':
        print(EffectiveEvaluate().generate_score())
    elif args[1] == 'ENGINEERING':
        print(EngineeringEvaluate().generate_score())