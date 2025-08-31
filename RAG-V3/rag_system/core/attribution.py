"""
溯源功能模块

实现智能溯源功能，支持正向和反向溯源
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AttributionService:
    """溯源服务 - 实现智能溯源功能"""
    
    def __init__(self):
        self.attribution_mode = "reverse"  # 默认反向溯源
        self.max_sources = 10
        self.relevance_threshold = 0.7
        
        logger.info("溯源服务初始化完成")
    
    def get_sources(self, query_text: str, llm_answer: str, attribution_mode: str = "reverse", candidates: List[Dict] = None) -> List[Dict]:
        """
        获取溯源信息
        
        Args:
            query_text: 查询文本
            llm_answer: LLM生成的答案
            attribution_mode: 溯源模式 ("forward" 或 "reverse")
            candidates: 候选结果列表
            
        Returns:
            List[Dict]: 溯源信息列表
        """
        try:
            logger.info(f"开始溯源信息提取，模式: {attribution_mode}")
            
            if attribution_mode == "forward":
                sources = self._forward_attribution(query_text, candidates)
            else:
                sources = self._reverse_attribution(query_text, llm_answer, candidates)
            
            # 过滤和排序溯源信息
            filtered_sources = self._filter_sources(sources)
            sorted_sources = self._sort_sources(filtered_sources)
            
            logger.info(f"溯源信息提取完成，获得 {len(sorted_sources)} 个来源")
            return sorted_sources
            
        except Exception as e:
            logger.error(f"溯源信息提取失败: {str(e)}")
            return []
    
    def _forward_attribution(self, query_text: str, candidates: List[Dict]) -> List[Dict]:
        """正向溯源 - 基于输入文档"""
        try:
            logger.info("执行正向溯源")
            
            if not candidates:
                return []
            
            sources = []
            for candidate in candidates:
                source_info = self._extract_source_info(candidate)
                if source_info:
                    sources.append(source_info)
            
            return sources
            
        except Exception as e:
            logger.error(f"正向溯源失败: {str(e)}")
            return []
    
    def _reverse_attribution(self, query_text: str, llm_answer: str, candidates: List[Dict]) -> List[Dict]:
        """反向溯源 - 基于LLM答案"""
        try:
            logger.info("执行反向溯源")
            
            if not candidates:
                return []
            
            sources = []
            
            # 1. 基于答案内容进行关键词匹配
            answer_keywords = self._extract_keywords(llm_answer)
            
            # 2. 在候选结果中查找匹配的来源
            for candidate in candidates:
                relevance_score = self._calculate_relevance(candidate, answer_keywords, query_text)
                
                if relevance_score >= self.relevance_threshold:
                    source_info = self._extract_source_info(candidate)
                    if source_info:
                        source_info["relevance_score"] = relevance_score
                        sources.append(source_info)
            
            return sources
            
        except Exception as e:
            logger.error(f"反向溯源失败: {str(e)}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取文本关键词"""
        try:
            # 这里应该使用更复杂的关键词提取算法
            # 暂时使用简单的分词
            import re
            words = re.findall(r'\w+', text.lower())
            
            # 过滤停用词（简化版）
            stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '如果', '那么', '因为', '所以'}
            keywords = [word for word in words if word not in stop_words and len(word) > 1]
            
            return keywords[:20]  # 限制关键词数量
            
        except Exception as e:
            logger.error(f"关键词提取失败: {str(e)}")
            return []
    
    def _calculate_relevance(self, candidate: Dict, answer_keywords: List[str], query_text: str) -> float:
        """计算候选结果与答案的相关性"""
        try:
            relevance_score = 0.0
            
            # 1. 关键词匹配分数
            candidate_text = candidate.get("content", "")
            candidate_keywords = self._extract_keywords(candidate_text)
            
            keyword_matches = 0
            for keyword in answer_keywords:
                if keyword in candidate_keywords:
                    keyword_matches += 1
            
            keyword_score = keyword_matches / max(len(answer_keywords), 1)
            
            # 2. 语义相似度分数（使用原有的相似度分数）
            semantic_score = candidate.get("similarity_score", 0.0)
            
            # 3. 综合分数
            relevance_score = (keyword_score * 0.6) + (semantic_score * 0.4)
            
            return min(relevance_score, 1.0)
            
        except Exception as e:
            logger.error(f"相关性计算失败: {str(e)}")
            return 0.0
    
    def _extract_source_info(self, candidate: Dict) -> Optional[Dict]:
        """提取来源信息"""
        try:
            metadata = candidate.get("metadata", {})
            
            source_info = {
                "chunk_id": candidate.get("chunk_id", ""),
                "chunk_type": metadata.get("chunk_type", "unknown"),
                "document_name": metadata.get("document_name", "未知文档"),
                "page_number": metadata.get("page_number", 0),
                "content_preview": candidate.get("content", "")[:200] + "...",
                "similarity_score": candidate.get("similarity_score", 0.0),
                "source_type": metadata.get("source_type", "unknown"),
                "metadata": metadata
            }
            
            return source_info
            
        except Exception as e:
            logger.error(f"来源信息提取失败: {str(e)}")
            return None
    
    def _filter_sources(self, sources: List[Dict]) -> List[Dict]:
        """过滤溯源信息"""
        try:
            filtered_sources = []
            
            for source in sources:
                relevance_score = source.get("relevance_score", 0.0)
                
                if relevance_score >= self.relevance_threshold:
                    filtered_sources.append(source)
                else:
                    logger.debug(f"过滤低相关性来源: {source.get('chunk_id', '')}, 分数: {relevance_score}")
            
            return filtered_sources
            
        except Exception as e:
            logger.error(f"溯源信息过滤失败: {str(e)}")
            return sources
    
    def _sort_sources(self, sources: List[Dict]) -> List[Dict]:
        """排序溯源信息"""
        try:
            # 按相关性分数排序
            sorted_sources = sorted(sources, key=lambda x: x.get("relevance_score", 0.0), reverse=True)
            
            # 限制返回数量
            return sorted_sources[:self.max_sources]
            
        except Exception as e:
            logger.error(f"溯源信息排序失败: {str(e)}")
            return sources
    
    def update_config(self, **kwargs):
        """更新配置参数"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"溯源服务配置更新: {key} = {value}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "attribution_mode": self.attribution_mode,
            "max_sources": self.max_sources,
            "relevance_threshold": self.relevance_threshold
        }
