import sys, json
sys.path.append('..')

from model import PIIMasker
from rag.tool import *
from util.util import *
from context import *
from util.io import *
from model.util import *
import pickle

masker = PIIMasker()

# 加载已有的风险规则语料的embedding
with open('../conf/risk_rules.pkl', 'rb') as f:
    risk_rules = pickle.load(f)

'''
    过滤文档的敏感性内容
'''
def pii_mask(content):
    return masker.mask_pii(content)


'''
    基于规则检查内容合规性
'''
def compliance_and_security_check_by_rule(content):
    lang = zh_en_check(content)
    words = split_words(content)
    # 对当前内容进行embedding
    model_req = json.dumps({'docs' : words})
    embedding = json.loads(get_best_model_instance(MODEL_USAGE_EMBEDDING).send(model_req))['dense']
    # 计算待检查内容每个关键词和风险关键词的语义相似度,大于0.7认为是有合规风险的
    for emb in embedding:
        for v in risk_rules[lang]:
            if cosine_similarity(emb, v['embedding']) > 0.7:
                return False
    return True

