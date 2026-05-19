import sys, json
sys.path.append('..')

from model import PIIMasker
from rag.tool import *
from util.util import *
from context import *
from util.io import *
from model.util import *

masker = PIIMasker()

rule_content = {
    'zh' : load_file('../conf/risk_rules_zh.txt'),
    'en' : load_file('../conf/risk_rules_en.txt')
}


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
    # 计算待检查内容每个关键词和风险关键词的语义相似度
    for line in rule_content[lang].split('\n'):
        for word in words:
            sim_score = 

'''
    基于大模型检查内容合规性
'''
