"""
DashScope Reranking引擎 - 基于BGE模型的智能重新排序

## 1. 功能特点
- 使用DashScope API访问BGE reranking模型
- 支持语义相似度重新排序
- 可配置的相似度阈值和权重

## 2. 与其他版本的不同点
- 新增的reranking引擎，替代原有的TF-IDF方案
- 支持DashScope API密钥管理
- 优化的语义理解能力
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import dashscope
from dashscope.rerank import text_rerank

logger = logging.getLogger(__name__)

@dataclass
class RerankingConfig:
    """重新排序配置"""
    model_name: str = "bge-reranker-v2-m3"
    top_k: int = 10
    similarity_threshold: float = 0.7
    weight_semantic: float = 0.8
    weight_keyword: float = 0.2

class DashScopeRerankingEngine:
    """DashScope重新排序引擎"""
    
    def __init__(self, api_key: str, config: Optional[RerankingConfig] = None):
        """
        初始化重新排序引擎
        
        :param api_key: DashScope API密钥
        :param config: 重新排序配置
        """
        self.api_key = api_key
        self.config = config or RerankingConfig()
        
        # 设置API密钥
        dashscope.api_key = self.api_key
        
        logger.info(f"DashScope Reranking引擎初始化完成，使用模型: {self.config.model_name}")
    
    def clear_cache(self):
        """清理重新排序引擎缓存"""
        try:
            # 重新排序引擎主要使用API调用，没有大量内存缓存
            # 这里可以清理一些可能的临时状态
            logger.info("重新排序引擎缓存清理完成")
            return 0
            
        except Exception as e:
            logger.error(f"清理重新排序引擎缓存失败: {e}")
            return 0
    
    def rerank_documents(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对文档进行重新排序
        
        :param query: 查询文本
        :param documents: 待排序的文档列表
        :return: 重新排序后的文档列表
        """
        if not documents:
            logger.warning("没有文档需要重新排序")
            return []
        
        try:
            # 准备文档文本
            documents_text = [doc.get('content', '') for doc in documents]
            
            # 调用DashScope reranking API
            response = text_rerank.TextReRank.call(
                model=self.config.model_name,
                query=query,
                documents=documents_text,
                top_k=min(self.config.top_k, len(documents))
            )
            
            if response.status_code == 200:
                # 处理响应结果
                reranked_docs = self._process_rerank_response(response, documents)
                logger.info(f"重新排序完成，处理了 {len(reranked_docs)} 个文档")
                return reranked_docs
            else:
                logger.error(f"Reranking API调用失败: {response.message}")
                return documents
                
        except Exception as e:
            logger.error(f"重新排序过程中发生错误: {str(e)}")
            return documents
    
    def _process_rerank_response(self, response: Any, original_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理重新排序API响应
        
        :param response: API响应对象
        :param original_docs: 原始文档列表
        :return: 处理后的文档列表
        """
        reranked_docs = []
        
        try:
            # 解析响应结果
            results = response.output.results
            
            for result in results:
                doc_index = result.index
                if 0 <= doc_index < len(original_docs):
                    # 复制原始文档并添加排序信息
                    doc = original_docs[doc_index].copy()
                    doc['rerank_score'] = result.relevance_score
                    doc['rerank_rank'] = len(reranked_docs) + 1
                    reranked_docs.append(doc)
            
            # 按分数降序排列
            reranked_docs.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"处理reranking响应时发生错误: {str(e)}")
            return original_docs
            
        return reranked_docs
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的语义相似度
        
        :param text1: 第一个文本
        :param text2: 第二个文本
        :return: 相似度分数 (0-1)
        """
        try:
            # 使用reranking API计算相似度
            response = text_rerank.TextReRank.call(
                model=self.config.model_name,
                query=text1,
                documents=[text2],
                top_k=1
            )
            
            if response.status_code == 200 and response.output.results:
                return response.output.results[0].relevance_score
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算语义相似度时发生错误: {str(e)}")
            return 0.0
    
    def filter_by_similarity(self, documents: List[Dict[str, Any]], 
                           query: str, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        基于相似度过滤文档
        
        :param documents: 文档列表
        :param query: 查询文本
        :param threshold: 相似度阈值
        :return: 过滤后的文档列表
        """
        threshold = threshold or self.config.similarity_threshold
        filtered_docs = []
        
        for doc in documents:
            content = doc.get('content', '')
            similarity = self.calculate_semantic_similarity(query, content)
            
            if similarity >= threshold:
                doc_copy = doc.copy()
                doc_copy['similarity_score'] = similarity
                filtered_docs.append(doc_copy)
        
        # 按相似度降序排列
        filtered_docs.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        logger.info(f"相似度过滤完成，从 {len(documents)} 个文档中筛选出 {len(filtered_docs)} 个")
        return filtered_docs
    
    def get_engine_status(self) -> Dict[str, Any]:
        """
        获取引擎状态信息
        
        :return: 状态信息字典
        """
        return {
            "engine_type": "DashScope Reranking",
            "model_name": self.config.model_name,
            "api_key_configured": bool(self.api_key),
            "config": {
                "top_k": self.config.top_k,
                "similarity_threshold": self.config.similarity_threshold,
                "weight_semantic": self.config.weight_semantic,
                "weight_keyword": self.config.weight_keyword
            }
        }
