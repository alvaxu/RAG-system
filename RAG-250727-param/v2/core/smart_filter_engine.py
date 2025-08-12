"""
智能过滤引擎 - 基于语义相似度和关键词匹配的智能过滤

## 1. 功能特点
- 多维度过滤策略（语义相似度、关键词匹配、内容质量）
- 可配置的过滤阈值和权重
- 智能的过滤算法和优化
- 支持批量处理和实时过滤

## 2. 与其他版本的不同点
- 新增的智能过滤引擎，替代原有的简单阈值过滤
- 支持多种过滤策略的组合
- 动态阈值调整和自适应过滤
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import jieba
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class FilterConfig:
    """过滤配置"""
    enable_filtering: bool = True
    similarity_threshold: float = 0.6
    keyword_weight: float = 0.3
    semantic_weight: float = 0.5
    content_quality_weight: float = 0.2
    min_content_length: int = 10
    max_content_length: int = 10000
    enable_keyword_extraction: bool = True
    enable_content_quality_check: bool = True
    enable_adaptive_threshold: bool = True

class SmartFilterEngine:
    """智能过滤引擎"""
    
    def __init__(self, config: Optional[FilterConfig] = None):
        """
        初始化智能过滤引擎
        
        :param config: 过滤配置
        """
        self.config = config or FilterConfig()
        
        # 初始化jieba分词器
        try:
            jieba.initialize()
            logger.info("jieba分词器初始化成功")
        except Exception as e:
            logger.warning(f"jieba分词器初始化失败: {str(e)}")
        
        logger.info(f"智能过滤引擎初始化完成")
    
    def filter_documents(self, query: str, documents: List[Dict[str, Any]], 
                        similarity_scores: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """
        智能过滤文档
        
        :param query: 查询文本
        :param documents: 待过滤的文档列表
        :param similarity_scores: 预计算的相似度分数
        :return: 过滤后的文档列表
        """
        if not self.config.enable_filtering:
            logger.info("过滤功能已禁用，返回原始文档")
            return documents
        
        if not documents:
            logger.warning("没有文档需要过滤")
            return []
        
        try:
            logger.info(f"开始智能过滤，原始文档数量: {len(documents)}")
            
            # 1. 内容质量过滤
            quality_filtered = self._filter_by_content_quality(documents)
            logger.info(f"内容质量过滤后剩余: {len(quality_filtered)} 个文档")
            
            # 2. 关键词匹配过滤
            keyword_filtered = self._filter_by_keyword_match(query, quality_filtered)
            logger.info(f"关键词匹配过滤后剩余: {len(keyword_filtered)} 个文档")
            
            # 3. 语义相似度过滤
            if similarity_scores:
                semantic_filtered = self._filter_by_semantic_similarity(
                    query, keyword_filtered, similarity_scores
                )
            else:
                semantic_filtered = keyword_filtered
            
            logger.info(f"语义相似度过滤后剩余: {len(semantic_filtered)} 个文档")
            
            # 4. 综合评分和排序
            final_filtered = self._calculate_comprehensive_scores(
                query, semantic_filtered, similarity_scores
            )
            
            logger.info(f"智能过滤完成，最终保留: {len(final_filtered)} 个文档")
            return final_filtered
            
        except Exception as e:
            logger.error(f"智能过滤过程中发生错误: {str(e)}")
            return documents
    
    def _filter_by_content_quality(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        基于内容质量过滤文档
        
        :param documents: 文档列表
        :return: 过滤后的文档列表
        """
        if not self.config.enable_content_quality_check:
            return documents
        
        filtered_docs = []
        
        for doc in documents:
            content = doc.get('content', '')
            if not content:
                continue
            
            # 检查内容长度
            if len(content) < self.config.min_content_length:
                continue
            
            if len(content) > self.config.max_content_length:
                continue
            
            # 检查内容质量（简单启发式规则）
            quality_score = self._calculate_content_quality_score(content)
            if quality_score > 0.3:  # 质量阈值
                doc_copy = doc.copy()
                doc_copy['quality_score'] = quality_score
                filtered_docs.append(doc_copy)
        
        return filtered_docs
    
    def _calculate_content_quality_score(self, content: str) -> float:
        """
        计算内容质量分数
        
        :param content: 内容文本
        :return: 质量分数 (0-1)
        """
        if not content:
            return 0.0
        
        score = 0.0
        
        # 1. 长度分数
        length_score = min(len(content) / 1000, 1.0)  # 标准化长度分数
        score += length_score * 0.2
        
        # 2. 结构分数
        if '\n' in content:  # 有换行，可能结构更好
            score += 0.1
        
        # 3. 标点符号分数
        punctuation_count = len(re.findall(r'[，。！？；：""''（）【】]', content))
        if punctuation_count > 0:
            score += min(punctuation_count / len(content) * 10, 0.3)
        
        # 4. 数字和字母混合分数
        has_digits = bool(re.search(r'\d', content))
        has_letters = bool(re.search(r'[a-zA-Z]', content))
        if has_digits and has_letters:
            score += 0.1
        
        return min(score, 1.0)
    
    def _filter_by_keyword_match(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        基于关键词匹配过滤文档
        
        :param query: 查询文本
        :param documents: 文档列表
        :return: 过滤后的文档列表
        """
        if not self.config.enable_keyword_extraction:
            return documents
        
        # 提取查询关键词
        query_keywords = self._extract_keywords(query)
        if not query_keywords:
            return documents
        
        filtered_docs = []
        
        for doc in documents:
            content = doc.get('content', '')
            if not content:
                continue
            
            # 计算关键词匹配分数
            keyword_score = self._calculate_keyword_match_score(query_keywords, content)
            
            if keyword_score > 0.1:  # 关键词匹配阈值
                doc_copy = doc.copy()
                doc_copy['keyword_score'] = keyword_score
                filtered_docs.append(doc_copy)
        
        return filtered_docs
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取文本关键词
        
        :param text: 输入文本
        :return: 关键词列表
        """
        try:
            # 使用jieba分词
            words = jieba.lcut(text)
            
            # 过滤停用词和短词
            keywords = []
            for word in words:
                word = word.strip()
                if len(word) > 1 and not self._is_stopword(word):
                    keywords.append(word)
            
            return keywords
            
        except Exception as e:
            logger.error(f"关键词提取失败: {str(e)}")
            # 回退到简单分词
            return [word.strip() for word in text.split() if len(word.strip()) > 1]
    
    def _is_stopword(self, word: str) -> bool:
        """
        判断是否为停用词
        
        :param word: 词语
        :return: 是否为停用词
        """
        # 简单的停用词列表
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '什么', '怎么', '为什么', '可以', '应该', '需要', '能够'
        }
        return word in stopwords
    
    def _calculate_keyword_match_score(self, query_keywords: List[str], content: str) -> float:
        """
        计算关键词匹配分数
        
        :param query_keywords: 查询关键词
        :param content: 文档内容
        :return: 匹配分数 (0-1)
        """
        if not query_keywords or not content:
            return 0.0
        
        content_lower = content.lower()
        matched_keywords = 0
        
        for keyword in query_keywords:
            if keyword.lower() in content_lower:
                matched_keywords += 1
        
        # 计算匹配率
        match_rate = matched_keywords / len(query_keywords)
        
        # 考虑关键词密度
        total_keywords = len(content.split())
        keyword_density = matched_keywords / max(total_keywords, 1)
        
        # 综合分数
        score = match_rate * 0.7 + keyword_density * 0.3
        
        return min(score, 1.0)
    
    def _filter_by_semantic_similarity(self, query: str, documents: List[Dict[str, Any]], 
                                     similarity_scores: List[float]) -> List[Dict[str, Any]]:
        """
        基于语义相似度过滤文档
        
        :param query: 查询文本
        :param documents: 文档列表
        :param similarity_scores: 相似度分数列表
        :return: 过滤后的文档列表
        """
        if len(documents) != len(similarity_scores):
            logger.warning("文档数量与相似度分数不匹配，跳过语义过滤")
            return documents
        
        filtered_docs = []
        
        for i, doc in enumerate(documents):
            similarity_score = similarity_scores[i]
            
            if similarity_score >= self.config.similarity_threshold:
                doc_copy = doc.copy()
                doc_copy['semantic_score'] = similarity_score
                filtered_docs.append(doc_copy)
        
        return filtered_docs
    
    def _calculate_comprehensive_scores(self, query: str, documents: List[Dict[str, Any]], 
                                      similarity_scores: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """
        计算综合评分并排序
        
        :param query: 查询文本
        :param documents: 文档列表
        :param similarity_scores: 相似度分数列表
        :return: 排序后的文档列表
        """
        scored_docs = []
        
        for i, doc in enumerate(documents):
            doc_copy = doc.copy()
            
            # 获取各项分数
            quality_score = doc.get('quality_score', 0.5)
            keyword_score = doc.get('keyword_score', 0.0)
            semantic_score = doc.get('semantic_score', 0.0)
            
            # 如果没有语义分数，尝试从similarity_scores获取
            if semantic_score == 0.0 and similarity_scores and i < len(similarity_scores):
                semantic_score = similarity_scores[i]
                doc_copy['semantic_score'] = semantic_score
            
            # 计算综合分数
            comprehensive_score = (
                quality_score * self.config.content_quality_weight +
                keyword_score * self.config.keyword_weight +
                semantic_score * self.config.semantic_weight
            )
            
            doc_copy['comprehensive_score'] = comprehensive_score
            scored_docs.append(doc_copy)
        
        # 按综合分数降序排序
        scored_docs.sort(key=lambda x: x.get('comprehensive_score', 0), reverse=True)
        
        return scored_docs
    
    def get_engine_status(self) -> Dict[str, Any]:
        """
        获取引擎状态信息
        
        :return: 状态信息字典
        """
        return {
            "engine_type": "Smart Filter",
            "enable_filtering": self.config.enable_filtering,
            "config": {
                "similarity_threshold": self.config.similarity_threshold,
                "keyword_weight": self.config.keyword_weight,
                "semantic_weight": self.config.semantic_weight,
                "content_quality_weight": self.config.content_quality_weight,
                "min_content_length": self.config.min_content_length,
                "max_content_length": self.config.max_content_length,
                "enable_keyword_extraction": self.config.enable_keyword_extraction,
                "enable_content_quality_check": self.config.enable_content_quality_check,
                "enable_adaptive_threshold": self.config.enable_adaptive_threshold
            }
        }
    
    def update_config(self, **kwargs) -> bool:
        """
        更新配置参数
        
        :param kwargs: 要更新的配置参数
        :return: 是否更新成功
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    logger.info(f"配置参数 {key} 更新为: {value}")
                else:
                    logger.warning(f"未知的配置参数: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
