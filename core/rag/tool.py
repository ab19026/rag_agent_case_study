from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import jieba


'''
    基于递归方式拆分文档
'''
def doc_splitter(doc, chunk_size, chunk_overlap):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=10 if chunk_size is None or chunk_size <= 10 else chunk_size,
        chunk_overlap=5 if chunk_overlap is None or chunk_overlap <= 5 else chunk_overlap,    
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(doc)


'''
    导入PDF文档
'''
def pdf_spiltter(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


'''
    简单分词
'''
def split_words(content):
    words = []
    for v in jieba.cut(content, cut_all=False):
        words.append(v)
    return words