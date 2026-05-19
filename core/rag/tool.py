from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import jieba


'''
    基于递归方式拆分文档
'''
def doc_splitter(doc, chunk_size, chunk_overlap):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500 if chunk_size is None or chunk_size <= 10 else chunk_size,
        chunk_overlap=50,    
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(doc)


'''
    拆分PDF文档
'''
def pdf_spiltter(path, chunk_size, chunk_overlap):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return doc_splitter(text, chunk_size, chunk_overlap)


'''
    简单分词
'''
def split_words(content):
    words = []
    for v in jieba.cut(content, cut_all=False):
        words.append(v)
    return words