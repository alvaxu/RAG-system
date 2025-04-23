"""
ChatPDF 简化版本
使用 LangChain 标准组件实现 PDF 文档问答系统
"""
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import create_qa_with_sources_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.prompts import PromptTemplate
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
    chunks = []
    chunk_metadata = []
    
    # 逐页处理PDF
    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        if not page_text:
            continue
            
        # 使用LangChain的文本分割器处理当前页面
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        
        # 分割当前页面的文本
        page_chunks = text_splitter.split_text(page_text)
        
        # 为每个文本块添加元数据
        for chunk in page_chunks:
            chunks.append(chunk)
            chunk_metadata.append({
                "page": page_num,
                "source": pdf_path
            })
    # print(chunks,chunk_metadata)    
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
    prompt = PromptTemplate.from_template(
        """使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。

上下文：
{context}

问题：{input}

回答："""
    )
    
    # 创建文档链
    document_chain = create_stuff_documents_chain(llm, prompt)
    
    # 创建检索链，设置相似度阈值
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 4, "score_threshold": 0.7}  # 只返回相似度大于0.7的文档
    )
    
    qa_chain = create_retrieval_chain(
        retriever=retriever,
        combine_docs_chain=document_chain
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
            
        # 生成回答
        result = qa_chain.invoke({"input": question})
        
        # 输出结果
        print("\n回答：")
        print(result["answer"])
        
        # 检查是否有相关文档且答案不是"不知道"
        if result["context"] and "不知道" not in result["answer"]:
            print("\n来源：")
            for doc in result["context"]:
                print(f"- 页码：{doc.metadata.get('page', '未知')}, 来源：{doc.metadata.get('source', '未知')}")
        else:
            print("\n未找到相关文档。")

if __name__ == "__main__":
    main() 