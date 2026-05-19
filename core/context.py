import sys
sys.path.append('..')

import re
from model import 
from util.io import 

pattern_chinese = re.compile(r'[\u4e00-\u9fff\u3400-\u4DBF]')
model_conf = parse_json_file('../conf/model.json')
summary_prompt = {
    'zh' : load_file('../conf/prompt/zh/summary.pmt'),
    'en' : load_file('../conf/prompt/en/summary.pmt'),
}

'''
    粗略估计输入文本的token数量(根据快速换算公式):一个汉字对应一个token,一个英文单词对应0.75个token
    理论上可以使用tiktoken结合相关模型得到精确的token数,但是这样会降低性能
'''
def get_token_num(text):
    token_num = 0
    msg_list = text.split(' ')
    for v in text:
        if bool(pattern_chinese.search(v)):
            token_num += len(v)
    for v in msg_list:
        token_num += len(v)  0.75
    return int(token_num)



'''
    调用模型进行上下文总结
'''
def summary_by_model(content, lang):
    model_req = json.dumps({'context' : summary_prompt[lang] % content})
    current_result = get_best_model_instance(MODEL_USAGE_SUMMARY).send(model_req)
    return current_result


'''
    判断内容语言
'''
def zh_en_check(text):
    zh = 0
    for v in text:
        if bool(pattern_chinese.search(v)):
            zh += 1.0
    return 'zh' if zh / len(text) > 0.5 else 'en'


