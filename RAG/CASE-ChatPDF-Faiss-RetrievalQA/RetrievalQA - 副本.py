#!/usr/bin/env python
# coding: utf-8

# In[3]:


"""
ChatPDF 简化版本
使用 LangChain 标准组件实现 PDF 文档问答系统
"""
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Tongyi
from typing import List, Dict, Tuple
from dashscope import TextEmbedding
import numpy as np

# 配置参数
CHUNK_SIZE = 1000  # 分块大小
CHUNK_OVERLAP = 200  # 重叠
EMBEDDING_MODEL = "text-embedding-v1"
LLM_MODEL = "qwen-turbo"
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')

if not DASHSCOPE_API_KEY:
    raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量")

def process_pdf(pdf_path: str) -> Tuple[List[str], List[Dict]]:
    """
    处理PDF文件，返回文本块和元数据
    """
    # 读取PDF
    reader = PdfReader(pdf_path)

    # 收集所有页面的文本和位置信息
    all_text = []
    page_positions = []  # 记录每个字符属于哪一页

    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        if not page_text:
            continue

        # 清理文本
        page_text = page_text.replace("百度文库", "").replace("好好学习，天天向上", "").strip()

        # 记录当前页面的所有字符位置
        for _ in range(len(page_text)):
            page_positions.append(page_num)

        all_text.append(page_text)

    # 合并所有文本
    full_text = "".join(all_text)

    # 使用LangChain的文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],  # 添加中文标点
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False
    )

    # 分割文本
    chunks = text_splitter.split_text(full_text)

    # 为每个文本块创建元数据
    chunk_metadata = []
    for chunk in chunks:
        # 找到这个chunk在原始文本中的位置
        start_pos = full_text.find(chunk)
        if start_pos == -1:
            # 如果找不到精确匹配，使用第一个字符的位置
            start_pos = 0

        # 获取这个chunk的起始页码
        start_page = page_positions[start_pos] if start_pos < len(page_positions) else 1

        # 获取这个chunk的结束页码
        end_pos = start_pos + len(chunk)
        end_page = page_positions[min(end_pos, len(page_positions)-1)] if end_pos < len(page_positions) else start_page

        # 如果chunk跨越了多页，使用起始页码
        chunk_metadata.append({
            "page": start_page,
            "source": pdf_path
        })

    return chunks, chunk_metadata

def create_vector_store(texts: List[str], metadata: List[Dict]):
    """
    创建向量存储
    """
    # 创建embeddings
    embeddings = DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=DASHSCOPE_API_KEY
    )

    # 创建向量存储
    vector_store = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadata
    )
    # print(vector_store)
    return vector_store

def create_qa_chain(vector_store):
    """
    创建问答链
    """
    # 创建LLM
    llm = Tongyi(
        model_name=LLM_MODEL,
        temperature=0.7,
        dashscope_api_key=DASHSCOPE_API_KEY
    )

    # 创建提示模板
    template = (
        """你是一个专业的文档问答助手。请根据提供的上下文来回答问题。
如果上下文中包含问题的答案，请直接回答。
如果上下文中没有相关信息，请明确回答"不知道"。

上下文：
{context}

问题：{question}

请仔细分析上下文，确保答案准确。回答："""
    )

    QA_PROMPT = PromptTemplate(
        input_variables=["context","question"],  # 必须包含这两个变量
        template=template
    )

    # 构建问答链
    qa_chain = RetrievalQA.from_chain_type(
       llm=llm,  # 控制生成稳定性
       chain_type="stuff",
       chain_type_kwargs={
       "prompt": QA_PROMPT,
#       "document_variable_name": "context"  # 必须与模板变量名一致，context 的值是自动从检索器（retriever）获取并注入到 prompt 
        },
       retriever=vector_store.as_retriever(
#            search_kwargs={"k": 5, "score_threshold": 0.65}  # 如果设了score_threshold，就会出现docs返回空值
           search_kwargs={"k": 5}  # 控制检索质量
        ),
       # input_key="query",  # 显式声明输入键名
       # document_variable_name="context",  # 明确指定文档变量名
       return_source_documents=True
    )

    return qa_chain, vector_store

def get_embedding(text):
    """获取文本的嵌入向量"""
    resp = TextEmbedding.call(
        model=EMBEDDING_MODEL,
        input=text
    )
    return np.array(resp.output['embeddings'][0]['embedding'])

def cosine_similarity(a, b):
    """计算两个向量的余弦相似度"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def calculate_similarities(question, docs):
    """计算问题与文档块之间的相似度"""
    question_vec = get_embedding(question)
    similarities = []
    
    for doc in docs:
        doc_vec = get_embedding(doc.page_content)
        similarity = cosine_similarity(question_vec, doc_vec)
        similarities.append((similarity, doc))
    
    return sorted(similarities, key=lambda x: x[0], reverse=True)

# In[4]:


# 处理PDF
# pdf_path = input("请输入PDF文件路径：")
# pdf_path = './上海市数字经济发展.pdf'
pdf_path = './浦发上海浦东发展银行西安分行个金客户经理考核办法.pdf'
texts, metadata = process_pdf(pdf_path)

print(f"\n处理完成，共生成 {len(texts)} 个文本块")

texts, metadata = process_pdf(pdf_path)
# for i in range(len(texts)) :
#     print(f"texts[{i}]\n{texts[i]},\n metadata={metadata[i]}")


# In[5]:


# 创建向量存储
vector_store = create_vector_store(texts, metadata)

# 创建问答链
qa_chain, vector_store = create_qa_chain(vector_store)

# qa_chain


# # In[6]:


# #测试score_threshold参数的作用
# retriever = vector_store.as_retriever(search_kwargs={'k': 5,'score_threshold': 0.65})  # 如果设了score_threshold，就会出现docs返回空值
# docs = retriever.invoke("客户经理被投诉了，投诉一次扣多少分")  # 或 get_relevant_documents()
# docs


# # In[11]:


# #测试score_threshold参数的作用
# retriever = vector_store.as_retriever(search_kwargs={'k': 5})  # 如果设了score_threshold，就会出现docs返回空值
# docs = retriever.invoke("客户经理被投诉了，投诉一次扣多少分")  # 或 get_relevant_documents()
# docs


# In[10]:


# #比较问题和答案文档的相似性
# from dashscope import TextEmbedding
# import numpy as np
# # 1. 获取 DashScope Embeddings
# def get_embedding(text):
#     resp = TextEmbedding.call(
#         model = EMBEDDING_MODEL,
#         input=text
#     )
#     return np.array(resp.output['embeddings'][0]['embedding'])

# # 2. 计算余弦相似度
# def cosine_similarity(a, b):
#     return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# # 实际使用
# query = "客户经理被投诉了，投诉一次扣多少分"
# document = docs

# query_vec = get_embedding(query)
# doc_vec = get_embedding(document)

# similarity = cosine_similarity(query_vec, doc_vec)
# print(f"相似度: {similarity:.4f}")  # 输出示例: 相似度: 0.83


# In[20]:


# 问答循环
print("\n系统已准备就绪，可以开始提问了。输入'退出'结束对话。")


while True:
    question = input("\n请输入问题：")
    if question.lower() == '退出':
        break

    # 获取相关文档
    docs = vector_store.similarity_search(question, k=5)
    
    # 计算相似度
    similarities = calculate_similarities(question, docs)
    
    # 显示相似度
    print("\n=== 相似度分析 ===")
    for sim, doc in similarities:
        print(f"相似度: {sim:.4f}")
        print(f"页码: {doc.metadata.get('page', '未知')}")
        print(f"内容: {doc.page_content[:100]}...\n")
    
    # 生成回答
    answer = qa_chain.invoke({"query": question})
    
    # 输出结果
    print(f"\n=== 问题 ===\n{question}")
    print(f"\n=== 回答 ===\n{answer['result']}")
    
    # 显示来源
    print("\n来源：")
    if answer['source_documents']:
        for doc in answer['source_documents']:
            print(f"- 页码：{doc.metadata.get('page', '未知')}, 来源：{doc.metadata.get('source', '未知')}")
    else:
        print("\n未找到相关文档。")


# In[ ]:




