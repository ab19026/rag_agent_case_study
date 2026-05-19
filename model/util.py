import sys, random, time, uuid, json
sys.path.append('..')
from openai import OpenAI
from util.io import *
from transformers import AutoTokenizer, AutoModelForCausalLM

model_conf = parse_json_file('../conf/model.json')


async_websocket_client_arr = {}

'''
    初始化当前类型模型的所有客户端实例
'''
def init_model_instance_list(model_usage):
    global async_websocket_client_arr
    if model_usage not in async_websocket_client_arr:
        async_websocket_client_arr[model_usage] = [AsyncWebSocketClient(port) for port in model_conf[model_usage]['port']['instance']] for model_usage in model_conf

'''
    基于负载均衡从当前模型类型所有实例中选择最优实例
    为了简单起见此处使用随机选取
'''
def get_best_model_instance(model_usage):
    global async_websocket_client_arr
    init_model_instance_list(model_usage)
    return async_websocket_client_arr[random.randint(len(model_instance_list))]


'''
    通过外部api调用模型
'''
def model_by_api(name, host, key, content):
    client = OpenAI(api_key=key, base_url=host)
    response = client.chat.completions.create(
        model="name",
        messages=[
            {"role": "user", "content": content},
        ],
        stream=False,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )
    return response.choices[0].message.content


'''
    调用本地模型
'''
def model_by_local(model, content, max_output_token_num):
    messages = [
        {"role": "user", "content": content},
    ]
    inputs = model['tokenizer'].apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model['model'].device)
    outputs = model['model'].generate(**inputs, max_new_tokens=max_output_token_num)
    result = model['tokenizer'].decode(outputs[0][inputs["input_ids"].shape[-1]:])