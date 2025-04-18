"""
向量化模块
"""
from langchain_community.embeddings import DashScopeEmbeddings
from typing import List
import numpy as np
from config import EMBEDDING_MODEL, DASHSCOPE_API_KEY

class EmbeddingModel:
    """
    功能：使用text-embedding-v1生成文本向量
    参数：
        text: 输入文本
    返回：
        vector: 文本向量
    """
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.embeddings = DashScopeEmbeddings(
            model=model_name,
            dashscope_api_key=DASHSCOPE_API_KEY
        )

    def get_embedding(self, text: str) -> np.ndarray:
        """
        获取单个文本的向量表示
        """
        return np.array(self.embeddings.embed_query(text))

    def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量获取文本向量
        """
        embeddings_list = self.embeddings.embed_documents(texts)
        return [np.array(embedding) for embedding in embeddings_list] 