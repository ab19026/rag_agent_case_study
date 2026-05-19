import sys, json
sys.path.append('..')
from model import *
from context import *
from constant import *
from util.io import *
from rag.rag import *
from model.util import *


'''
    基于Re-Act-Loop架构的Agent
'''
class Agent():
    def __init__(self, rag, memory, lang):
        self.rag = rag
        self.memory = memory
        self.lang = lang
        self.agent_conf = parse_json_file('../conf/agent.json')
        self.first_turn_prompt = load_file('../conf/%s/prompt/first_turn_react.pmt' % lang)
        self.multi_turn_prompt_full = load_file('../conf/%s/prompt/multi_turn_prompt_full.pmt' % lang)
        self.multi_turn_prompt = load_file('../conf/%s/prompt/multi_turn_prompt.pmt' % lang)
        self.multi_turn_prompt_final = load_file('../conf/%s/prompt/multi_turn_prompt_final.pmt' % lang)
        self.question_check_prompt = load_file('../conf/%s/prompt/question_check.pmt' % lang)

    def react_loop(self, request, callback):
        security_post = ''
        content = None
        if 'origin_question' in request:
            content = request['origin_question']
        if 'new_conversation' in request:
            content = request['new_conversation']
        # 安全性和合规性检查
        if content is not None:
            # 如果是基于大模型检查,会把相关合规prompt加在模型请求内容之后
            if self.agent_conf['security_check'] == 'MODEL':
                security_post = self.question_check_prompt
            # 如果基于规则检查问题不合规, 则直接返回
            elif self.agent_conf['security_check'] == 'RULE':
                if not compliance_and_security_check_by_rule(content):
                    return AGENT_REFUSAL[lang]
        if memory.get_overwrite_memory(request['trace_id'], 'round') is not None:
            memory.set_overwrite_memory(request['trace_id'], 'round', memory.get_overwrite_memory(request['trace_id'], 'round') + 1)
        round_num = memory.get_overwrite_memory(message['conv_id'], 'round')
        rag = False
        answer = False
        for loop in range(self.agent_conf['max_react_loop_count']):
            start_time = time.time()
            log_msg = {
                'action_name' : 'agent_process',
                'action_id' : uid(),
                'source_id' : request['source_id'] if request is not None else 'empty',
                'context' : {
                    'round' :  round_num,
                    'iteration' : loop + 1,
                    'rag_query' : None,
                    'rag_result' : None,
                    'model_result' : None
                },
                'trace_id' : request['trace_id'],
                'error' : None,
                'start_time' : start_time,
                'end_time' : None
            }
            try:
                request['source_id'] = log_msg['action_id']
                request['query'] = request['origin_question']
                #第一次迭代,直接查询RAG
                #first iteration, directly query the RAG
                if !memory.exist_memory(request['trace_id']):
                    docs = rag.retrieve(request)
                    self.memory.add_memory(request['trace_id'], "第一次RAG查询:{查询语句:%s, 结果:%s}" % (request['origin_question'], docs))
                    # 调用模型结合rag返回文档生成答案
                    model_req = json.dumps({'context' : self.first_turn_prompt % (request['origin_question'], '\n'.join(doc_list), '\n' + security_post)})
                    current_result = get_best_model_instance(MODEL_USAGE_AGENT).send(model_req)
                    memory.set_overwrite_memory(request['trace_id'], 'last_answer', current_result)
                    self.memory.add_memory(request['trace_id'], "第一次RAG查询给出的答案:%s" % current_result)
                    log_msg['rag_query'] = request['origin_question']
                    log_msg['rag_result'] = docs
                    log_msg['model_result'] = current_result
                    rag = True
                #后续迭代可以自主优化
                else:
                    last_answer = memory.get_overwrite_memory(request['trace_id'], 'last_answer')
                    last_docs = memory.get_overwrite_memory(request['trace_id'], 'last_docs')
                    #multiple turn conversation
                    mem_list = self.memory.get_memory(request['trace_id'])
                    if request['new_conversation'] is not None:
                        log_msg['user_new_conversation'] = request['new_conversation']
                        mem_list = self.memory.add_memory(request['trace_id'], "这是第%s轮对话,用户对上一轮答案不满意,又补充了信息:{%s}" % (round_num, loop+1, message['new_conversation']))
                    if last_docs is not None:
                        model_req = json.dumps({'context' : multi_turn_prompt_full % (last_docs, '\n'.join(mem_list), '\n' + security_post)})
                    else
                        model_req = json.dumps({'context' : self.multi_turn_prompt % ('\n'.join(mem_list), '\n' + security_post)})
                    current_result = get_best_model_instance(MODEL_USAGE_AGENT).send(model_req)
                    log_msg['model_result'] = current_result
                    if 'Query' in current_result:
                        rag = True
                        query = current_result.replace('Query:', '')
                        request['query'] = query
                        docs = rag.retrieve(request)
                        log_msg['rag_query'] = query
                        log_msg['rag_result'] = docs
                        #add previous rag query to memory
                        self.memory.add_memory(request['conv_id'], "这是第%s轮对话的第%s次迭代,你对上次生成的答案:{%s}不满意,所以你又生成了一次RAG查询:{查询语句:%s, 结果:%s}" % (round_num, loop+1, query, docs))
                    elif 'Answer' in current_result:
                        memory.set_overwrite_memory(request['trace_id'], 'last_docs', None)
                        memory.set_overwrite_memory(request['trace_id'], 'last_answer', current_result)
                        self.memory.add_memory(request['trace_id'], "这是第%s轮对话的第%s次迭代,你觉得当前生成的答案:{%s}已经是最优了" % (round_num, loop+1, last_answer))
                        answer = True
                if callback is not None:
                    callback_msg = ''
                    if round_num > 0:
                        callback_msg = '看来用户对之前的答案不满意,现在是第%s轮对话的第%s次迭代,' % (round_num, loop)
                    else:
                        callback_msg = '现在是第%s次迭代,' % loop
                    if rag:
                        callback_msg += '需要进一步检索RAG'
                    if answer:
                        callback_msg += '已经得到当前最优答案'
                    callback(callback_msg, message['conn'])
                if answer:
                    break
            except Exception as e:
                err = e
            finally:
                log_msg['end_time'] = time.time()
                log(log_msg)
        post_msg = ''
        log_msg['context'] = {}
        log_msg['context']['max_round_num'] = round_num
        log_msg['context']['max_iteration_num'] = loop + 1
        if round_num > self.agent_conf['max_round_num']:
            self.memory.clear_memory(message['conv_id'])
            post_msg = '\n【请注意,您目前的对话轮次已经达到上限,如果对当前答案还是不满意,请开启新对话重新描述问题】'
            log_msg['context']['round_max_hit'] = True
        if 'Answer' in current_result:
            log_msg['context']['final_answer'] = current_result
            log_msg['end_time'] = time.time()
            log(log_msg)
            return current_result + post_msg
        #if the ideal answer still not obtained in the final iteration, 
        #then forcibly summarize the existing context and output the answer
        elif loop == self.agent_conf['max_react_loop_count'] - 1 or round_num >= self.agent_conf['max_round_num']:
            log_msg['context']['iteration_max_hit'] = True
            model_req = json.dumps({'context' : self.multi_turn_prompt_final % ('\n'.join(mem_list), security_post)})
            current_result = get_best_model_instance(MODEL_USAGE_AGENT).send(model_req)
            log_msg['context']['final_answer'] = current_result
            log_msg['end_time'] = time.time()
            log(log_msg)
            return current_result + post_msg
        
            



