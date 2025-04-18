"""
向量数据库模块
"""
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from typing import List, Dict, Tuple
from config import EMBEDDING_MODEL, VECTOR_STORE_CONFIG, DASHSCOPE_API_KEY

class VectorStore:
    """
    功能：管理向量数据库
    """
    def __init__(self):
        self.embeddings = DashScopeEmbeddings(
            model=EMBEDDING_MODEL,
            dashscope_api_key=DASHSCOPE_API_KEY
        )
        self.vector_store = None

    def add_vectors(self, texts: List[str], metadata: List[Dict]):
        """
        添加文本和元数据到向量数据库
        """
        self.vector_store = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadata
        )

    def search(self, query: str, k: int = None) -> Tuple[List[float], List[Dict]]:
        """
        搜索相似文本
        """
        if k is None:
            k = VECTOR_STORE_CONFIG["similarity_search_k"]
            
        docs = self.vector_store.similarity_search_with_score(
            query=query,
            k=k
        )
        
        # 提取距离和元数据
        distances = [doc[1] for doc in docs]
        metadatas = [doc[0].metadata for doc in docs]
        
        return distances, metadatas 