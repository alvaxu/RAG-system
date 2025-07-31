'''
程序说明：
## 1. 重排序引擎实现
## 2. 支持语义相似度、关键词匹配、混合排序
## 3. 可配置权重和排序方法
## 4. 集成到QA系统中
'''

import re
import logging
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class RerankingEngine:
    """
    重排序引擎
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化重排序引擎
        :param config: 配置字典
        """
        self.enable_reranking = config.get('enable_reranking', True)
        self.reranking_method = config.get('reranking_method', 'hybrid')
        self.semantic_weight = config.get('semantic_weight', 0.7)
        self.keyword_weight = config.get('keyword_weight', 0.3)
        self.min_similarity_threshold = config.get('min_similarity_threshold', 0.6)
        
        # 初始化TF-IDF向量化器
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            analyzer='char'  # 使用字符级别的分析，更适合中文
        )
        
        logger.info(f"重排序引擎初始化完成: method={self.reranking_method}")
    
    def rerank_results(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对检索结果进行重排序
        :param query: 查询问题
        :param documents: 原始检索结果
        :return: 重排序后的结果
        """
        if not self.enable_reranking or not documents:
            return documents
        
        try:
            logger.info(f"开始重排序，方法: {self.reranking_method}")
            
            if self.reranking_method == 'semantic':
                return self._semantic_rerank(query, documents)
            elif self.reranking_method == 'keyword':
                return self._keyword_rerank(query, documents)
            elif self.reranking_method == 'hybrid':
                return self._hybrid_rerank(query, documents)
            else:
                logger.warning(f"未知的重排序方法: {self.reranking_method}")
                return documents
                
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return documents
    
    def _semantic_rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        语义相似度重排序
        :param query: 查询问题
        :param documents: 文档列表
        :return: 重排序后的文档列表
        """
        try:
            # 提取文档内容
            doc_texts = [doc.get('content', '') for doc in documents]
            
            # 计算TF-IDF向量
            all_texts = [query] + doc_texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
            
            # 计算查询与文档的相似度
            query_vector = tfidf_matrix[0:1]
            doc_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(query_vector, doc_vectors).flatten()
            
            # 更新文档的相似度分数
            for i, doc in enumerate(documents):
                doc['semantic_score'] = float(similarities[i])
                doc['rerank_score'] = doc['semantic_score']
            
            # 按相似度排序
            reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
            
            logger.info(f"语义重排序完成，最高分数: {max(similarities):.3f}")
            return reranked_docs
            
        except Exception as e:
            logger.error(f"语义重排序失败: {e}")
            return documents
    
    def _keyword_rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        关键词匹配重排序
        :param query: 查询问题
        :param documents: 文档列表
        :return: 重排序后的文档列表
        """
        try:
            # 提取查询关键词
            query_keywords = self._extract_keywords(query)
            
            for doc in documents:
                doc_content = doc.get('content', '')
                keyword_score = self._calculate_keyword_score(query_keywords, doc_content)
                doc['keyword_score'] = keyword_score
                doc['rerank_score'] = keyword_score
            
            # 按关键词分数排序
            reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
            
            logger.info(f"关键词重排序完成，最高分数: {max([d['keyword_score'] for d in documents]):.3f}")
            return reranked_docs
            
        except Exception as e:
            logger.error(f"关键词重排序失败: {e}")
            return documents
    
    def _hybrid_rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        混合重排序（语义+关键词）
        :param query: 查询问题
        :param documents: 文档列表
        :return: 重排序后的文档列表
        """
        try:
            # 先进行语义重排序
            semantic_docs = self._semantic_rerank(query, documents)
            
            # 提取查询关键词
            query_keywords = self._extract_keywords(query)
            
            # 计算混合分数
            for doc in semantic_docs:
                doc_content = doc.get('content', '')
                keyword_score = self._calculate_keyword_score(query_keywords, doc_content)
                doc['keyword_score'] = keyword_score
                
                # 混合分数 = 语义权重 * 语义分数 + 关键词权重 * 关键词分数
                semantic_score = doc.get('semantic_score', 0.0)
                doc['rerank_score'] = (
                    self.semantic_weight * semantic_score + 
                    self.keyword_weight * keyword_score
                )
            
            # 按混合分数排序
            reranked_docs = sorted(semantic_docs, key=lambda x: x['rerank_score'], reverse=True)
            
            # 过滤低分数文档
            filtered_docs = [
                doc for doc in reranked_docs 
                if doc['rerank_score'] >= self.min_similarity_threshold
            ]
            
            logger.info(f"混合重排序完成，文档数: {len(documents)} -> {len(filtered_docs)}")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"混合重排序失败: {e}")
            return documents
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取文本关键词
        :param text: 输入文本
        :return: 关键词列表
        """
        # 简单的关键词提取：去除停用词，保留重要词汇
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '如果', '因为', '所以', '什么', '怎么', '为什么', '如何', '什么', '主要', '业务', '什么'}
        
        # 提取中文词汇和英文词汇
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        
        # 过滤停用词和短词
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 确保至少返回一些关键词
        if not keywords:
            # 如果没有提取到关键词，返回一些基本词汇
            basic_words = re.findall(r'[\u4e00-\u9fff]+', text)
            keywords = [word for word in basic_words if len(word) > 1][:3]
        
        return keywords
    
    def _calculate_keyword_score(self, query_keywords: List[str], doc_content: str) -> float:
        """
        计算关键词匹配分数
        :param query_keywords: 查询关键词
        :param doc_content: 文档内容
        :return: 关键词匹配分数
        """
        if not query_keywords or not doc_content:
            return 0.0
        
        # 计算关键词在文档中的出现情况
        doc_lower = doc_content.lower()
        total_matches = 0
        matched_keywords = 0
        
        for keyword in query_keywords:
            # 计算关键词出现次数
            matches = doc_lower.count(keyword.lower())
            total_matches += matches
            if matches > 0:
                matched_keywords += 1
        
        # 计算匹配率
        keyword_match_rate = matched_keywords / len(query_keywords) if query_keywords else 0
        
        # 计算频率分数
        frequency_score = min(total_matches / (len(query_keywords) * 5), 1.0) if query_keywords else 0
        
        # 综合分数 = 匹配率 * 0.7 + 频率分数 * 0.3
        score = keyword_match_rate * 0.7 + frequency_score * 0.3
        
        return score
    
    def get_reranking_stats(self) -> Dict[str, Any]:
        """
        获取重排序统计信息
        :return: 统计信息
        """
        return {
            'enable_reranking': self.enable_reranking,
            'reranking_method': self.reranking_method,
            'semantic_weight': self.semantic_weight,
            'keyword_weight': self.keyword_weight,
            'min_similarity_threshold': self.min_similarity_threshold
        } 