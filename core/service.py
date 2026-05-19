import sys
sys.path.append('..')

import queue, threading, sys, time
from security import 
from network.async_websocket import *
from util.io import 
from concurrent.futures import ThreadPoolExecutor
from agent import 
from memory import
from util.util import *
from model.util import *
from context import *
from interface.socket_service_base import *

'''
    基于事件驱动的agent服务
    基本流程:每个前端请求都会进入队列,之后由事件循环线程从队列里取出请求交给agent去执行
'''
class Service(SocketServiceBase):
    def __init__(self, port):
        self.app_conf = parse_json_file('../conf/app.json')
        self.model_conf = parse_json_file('../conf/model.json')
        self.event_queue = Queue()
        self.async_websocket_server = AsyncWebSocketServer(
            self.process_request, 
            self.app_conf['pre_message'],
            port
        )
        self.memory = memory
        self.agent = Agent(self.app_conf['agent_model_name'], memory)
        self.run = True
        self.thread_pool = ThreadPoolExecutor(max_workers=self.app_conf['max_worker_num'])
        self.async_websocket_server.start()


    '''
        将上有请求放入队列进行事件循环
    '''
    def process_requst(self, request):
        msg_alias = 'new_conversation' if 'trace_id' in request and memory.exist_memory(request['trace_id']) else 'origin_question'
        request[msg_alias] = request['msg']
        request['start_time'] = time.time()
        self.event_queue.put(request)

    '''
        从队列里拿出请求交给agent去执行
    '''
    def start(self):
        self.async_websocket_server.start()
        memory = Memory()
        while self.run:
            if not self.event_queue.empty():
                err = None
                source_id = request['source_id']
                try:
                    request = self.event_queue.get()
                    # 判断当前请求内容语言类型
                    lang = zh_en_check(request['msg'])
                    # 初始化RAG和Agent模块
                    rag = Rag()
                    agent = Agent(rag, memory, lang)
                except Exception as e:
                    err = e
                finally:
                    log(
                        {
                            'action_name' : 'fetch_agent_task',
                            'action_id' : None,
                            'source_id' : source_id,
                            'context' : {
                                'current_queue_len' : len(self.event_queue.queue)
                            },
                            'trace_id' : request['trace_id'],
                            'error' : "%s" % err,
                            'start_time' : request['start_time'],
                            'end_time' : time.time()
                        }
                    )
                action_id = uid()
                request['source_id'] = action_id
                start_time = time.time()
                result = None
                try:
                    # 通过异步回调的方式将Agent执行结果返回给上游
                    def agent_task(request, agent, async_websocket_server, app_conf):
                        response = agent.react_loop(
                            request, 
                            callback=async_websocket_server.response if app_conf['agent_trace'] else None
                        )
                        async_websocket_server.response(response, request['conn'])
                    result = self.thread_pool.submit(
                        agent_task，
                        request,
                        agent,
                        self.async_websocket_server
                    ).result()
                except Exception as e:
                    err = e
                finally:
                    log(
                        {
                            'action_name' : 'execute_agent_task',
                            'action_id' : action_id,
                            'source_id' : source_id,
                            'context' : {
                                'agent_result' : result,
                                'agend_id' : agent.get_id()
                            },
                            'trace_id' : request['trace_id'],
                            'error' : "%s" % err,
                            'start_time' : start_time,
                            'end_time' : time.time()
                        }
                    )
                time.sleep(0.1)


    def shutdown(self):
        self.run = False
        self.async_websocket_server.shutdown()


if __name__ == '__main__':
    args = sys.argv
    port = args[1]
    Service(int(port)).start()




