'''
程序说明：
## 1. 该模块演示了如何使用测试向量数据库进行问答
## 2. 使用模拟的问答系统，不依赖于实际的API密钥
## 3. 展示了基于向量相似度的问答功能
'''

import os
import pickle
import numpy as np
from typing import List, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS


class MockEmbeddings:
    """
    模拟嵌入类，用于测试目的
    """
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        为文本列表生成模拟嵌入向量
        :param texts: 文本列表
        :return: 模拟嵌入向量列表
        """
        # 为每个文本生成128维的随机向量
        return [np.random.rand(128).tolist() for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """
        为查询文本生成模拟嵌入向量
        :param text: 查询文本
        :return: 模拟嵌入向量
        """
        # 生成128维的随机向量
        return np.random.rand(128).tolist()


class MockQuestionAnsweringSystem:
    """
    模拟问答系统类，用于测试目的
    """
    
    def __init__(self, vector_store: FAISS):
        """
        初始化模拟问答系统
        :param vector_store: FAISS向量存储对象
        """
        self.vector_store = vector_store
    
    def answer_question(self, question: str, k: int = 2) -> Dict[str, Any]:
        """
        回答问题
        :param question: 用户问题
        :param k: 检索的相似文档数量
        :return: 包含答案和相关信息的字典
        """
        print(f"正在处理问题: {question}")
        
        # 执行相似度搜索
        docs = self.vector_store.similarity_search(question, k=k)
        print(f"找到 {len(docs)} 个相关文档片段")
        
        # 生成模拟答案
        answer = f"这是针对问题\"{question}\"的模拟答案。基于检索到的{k}个相关文档片段生成。"
        
        # 收集来源信息
        sources = []
        unique_sources = set()
        
        for i, doc in enumerate(docs):
            # 获取文档索引
            doc_index = len(self.vector_store.metadata) - len(docs) + i
            if doc_index in self.vector_store.metadata:
                metadata = self.vector_store.metadata[doc_index]
                source_key = (metadata['document_name'], metadata['page_number'])
                
                if source_key not in unique_sources:
                    unique_sources.add(source_key)
                    sources.append({
                        'document_name': metadata['document_name'],
                        'page_number': metadata['page_number'],
                        'content': doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                    })
        
        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'retrieved_documents': len(docs)
        }


def load_test_vector_store_and_answer_questions(vector_db_path: str = "./vector_db"):
    """
    加载测试向量存储并启动问答交互
    :param vector_db_path: 向量数据库路径
    """
    print(f"正在从 {vector_db_path} 加载向量数据库...")
    
    # 创建模拟嵌入对象
    embeddings = MockEmbeddings()
    
    # 加载FAISS向量数据库
    vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
    print(f"向量数据库已从 {vector_db_path} 加载")
    
    # 加载元数据
    metadata_path = os.path.join(vector_db_path, "metadata.pkl")
    if os.path.exists(metadata_path):
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        vector_store.metadata = metadata
        print("元数据已加载")
    else:
        print("警告: 未找到元数据文件")
    
    # 创建模拟问答系统
    qa_system = MockQuestionAnsweringSystem(vector_store)
    
    print("问答系统已准备就绪！输入 'quit' 退出。")
    
    while True:
        question = input("\n请输入您的问题: ").strip()
        
        if question.lower() == 'quit':
            print("感谢使用问答系统！")
            break
        
        if not question:
            print("请输入有效问题。")
            continue
        
        # 回答问题
        result = qa_system.answer_question(question)
        
        # 显示答案
        print(f"\n问题: {result['question']}")
        print(f"答案: {result['answer']}")
        
        # 显示来源
        print("\n相关信息来源:")
        for i, source in enumerate(result['sources'], 1):
            print(f"{i}. 文档: {source['document_name']}, 页码: {source['page_number']}")
            print(f"   内容: {source['content']}")


if __name__ == "__main__":
    print("测试向量存储和问答系统演示")
    load_test_vector_store_and_answer_questions("./vector_db")