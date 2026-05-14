import sys, random, time, uuid, json
sys.path.append('..')
from util.io import *

model_conf = parse_json_file('../conf/model.json')

'''
    初始化当前类型模型的所有实例
'''
def get_model_instance_list(model_usage):
    async_websocket_client_arr = {
        model_usage : [AsyncWebSocketClient(port) for port in model_conf[model_usage]['port']['instance']] for model_usage in model_conf
    }
    return async_websocket_client_arr


'''
    基于负载均衡从当前模型类型所有实例中选择最优实例
    为了简单起见此处使用随机选取
'''
def get_best_model_instance(model_instance_list, model_usage):
    return model_instance_list[random.randint(len(model_instance_list))]
