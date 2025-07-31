'''
程序说明：
## 1. 该模块实现了简化版的向量存储功能，用于测试目的
## 2. 不依赖于实际的API密钥，使用模拟的嵌入向量
## 3. 验证FAISS向量数据库的创建和保存功能
'''

import os
import pickle
import numpy as np
from pathlib import Path
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from V100_document_loader_chunker import DocumentChunk, process_documents


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


def create_test_vector_store(md_dir: str = "md", save_path: str = "./vector_db") -> FAISS:
    """
    从文档创建测试向量存储的主函数
    :param md_dir: markdown文件目录路径
    :param save_path: 保存向量数据库的路径
    :return: FAISS向量存储对象
    """
    # 处理文档分块
    print("正在处理文档分块...")
    chunks = process_documents(md_dir)
    print(f"共处理 {len(chunks)} 个文档分块")
    
    # 提取文档分块的内容
    texts = [chunk.content for chunk in chunks]
    
    # 创建模拟嵌入对象
    embeddings = MockEmbeddings()
    
    # 从文本创建向量存储
    print("正在创建向量存储...")
    vector_store = FAISS.from_texts(texts, embeddings)
    
    # 存储额外的元数据（文档名、页码等）
    metadata = {}
    for i, chunk in enumerate(chunks):
        metadata[i] = {
            'document_name': chunk.document_name,
            'page_number': chunk.page_number,
            'chunk_index': chunk.chunk_index
        }
    vector_store.metadata = metadata
    
    print(f"向量存储创建完成，共包含 {len(texts)} 个文本块")
    
    # 如果提供了保存路径，则保存向量数据库
    if save_path:
        # 确保目录存在
        os.makedirs(save_path, exist_ok=True)
        
        # 保存FAISS向量数据库
        vector_store.save_local(save_path)
        print(f"向量数据库已保存到: {save_path}")
        
        # 保存元数据到同一目录
        with open(os.path.join(save_path, "metadata.pkl"), "wb") as f:
            pickle.dump(metadata, f)
        print(f"元数据已保存到: {os.path.join(save_path, 'metadata.pkl')}")
    
    return vector_store


if __name__ == "__main__":
    print("开始创建测试向量数据库...")
    
    # 从文档创建向量存储
    vector_store = create_test_vector_store("md", "./vector_db")
    
    print("测试向量数据库创建完成！")