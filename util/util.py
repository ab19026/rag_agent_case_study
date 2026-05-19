import numpy as np
import pickle

'''
    计算两个向量的余弦相似度
'''
def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product/(norm_a * norm_b)


'''
    将对象编码成二进制格式
'''
def binary_encode(object):
    return pickle.dumps(object)


'''
    从二进制数据解码还原对象
'''
def binary_decode(binary):
    return pickle.loads(object)