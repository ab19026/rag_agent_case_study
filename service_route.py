import sys, random, time, uuid, json
from interface.socket_service_base import *
from util.util import *

'''
    使用websocket实现简单的RPC机制,通过路由将请求转发到合适的实例并得到返回
'''
def ServiceRoute(SocketServiceBase):
    def __init__(self, port):
        self.app_conf = parse_json_file('../conf/app.json')
        self.async_websocket_server = AsyncWebSocketServer(
            self.__handle_request,
            None,
            port
        )
        self.async_websocket_client_arr = []
        for port in self.app_conf['port']['instance']:
            self.async_websocket_client_arr.append(AsyncWebSocketClient(port))

    '''
        负载均衡,选取最佳实例(理论上要根据实例的cpu、内存使用率、延迟、流量等指标加权判断)
        但是为了简单起见,这里就随机挑选一个实例来模拟负载均衡
    '''
    def __load_balancer(self):
        return self.async_websocket_client_arr[random.randint(len(self.async_websocket_client_arr))]

    '''
        请求转发
    '''
    def __handle_request(self, request):
        err = None
        start_time = time.time()
        try:
            trace_id = uid()
            action_id = uid()
            best_async_websocket_client = self.__load_balancer()
            result = best_async_websocket_client.send(json.dumps(
                {
                    'msg' : request['msg'],
                    'trace_id' : trace_id,
                    'source_id' : action_id
                })
            )
            self.async_websocket_server.response(
                result, 
                request['conn']
            )
        except Exception as e:
            err = e
        finally:
            end_time = time.time()
            log(
                {
                    'action_name' : 'service_route',
                    'action_id' : action_id,
                    'source_id' : None,
                    'context' : {
                        'target_uri' : best_async_websocket_client.get_target_uri()
                    },
                    'trace_id' : trace_id,
                    'error' : '%s' % err,
                    'start_time' : start_time,
                    'end_time' : end_time
                }
            )

    def start(self):
        self.async_websocket_server.start()

    def shutdown(self):
        self.async_websocket_server.shutdown()

if __name__ == '__main__':
    args = sys.argv
    port = args[1]
    ServiceRoute(int(port)).start()
