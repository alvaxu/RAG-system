"""
ChatPDF 简化版本
使用 LangChain 标准组件实现 PDF 文档问答系统
"""
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_community.llms import Tongyi
from typing import List, Dict, Tuple

# 配置参数
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
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
    text = ""
    metadata = []
    
    # 提取文本和页码信息
    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        if page_text:
            text += f"\n{page_text}"
            metadata.append({
                "page": page_num,
                "source": pdf_path
            })
    
    # 使用LangChain的文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    # 分割文本
    chunks = text_splitter.split_text(text)
    
    return chunks, metadata

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
    
    # 创建问答链
    qa_chain = load_qa_chain(
        llm=llm,
        chain_type="stuff"
    )
    
    return qa_chain, vector_store

def main():
    # 处理PDF
    pdf_path = input("请输入PDF文件路径：")
    texts, metadata = process_pdf(pdf_path)
    
    # 创建向量存储
    vector_store = create_vector_store(texts, metadata)
    
    # 创建问答链
    qa_chain, vector_store = create_qa_chain(vector_store)
    
    # 问答循环
    print("\n系统已准备就绪，可以开始提问了。输入'退出'结束对话。")
    while True:
        question = input("\n请输入问题：")
        if question.lower() == '退出':
            break
            
        # 获取相关文档
        docs = vector_store.similarity_search(question)
        
        # 生成回答
        result = qa_chain.run(input_documents=docs, question=question)
        
        # 输出结果
        print("\n回答：")
        print(result)
        print("\n来源：")
        for doc in docs:
            print(f"- 页码：{doc.metadata.get('page', '未知')}, 来源：{doc.metadata.get('source', '未知')}")

if __name__ == "__main__":
    main() 