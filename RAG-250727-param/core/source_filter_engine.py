'''
程序说明：
## 1. 源过滤引擎实现
## 2. 基于LLM回答内容过滤检索源
## 3. 支持关键词匹配、图片ID匹配、相似度过滤
## 4. 集成到QA系统中
'''

import re
import logging
from typing import List, Dict, Any, Set
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SourceFilterEngine:
    """
    源过滤引擎
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化源过滤引擎
        :param config: 配置字典
        """
        self.enable_sources_filtering = config.get('enable_sources_filtering', True)
        self.min_relevance_score = config.get('min_relevance_score', 0.6)
        self.enable_keyword_matching = config.get('enable_keyword_matching', True)
        self.enable_image_id_matching = config.get('enable_image_id_matching', True)
        self.enable_similarity_filtering = config.get('enable_similarity_filtering', True)
        
        logger.info(f"源过滤引擎初始化完成: enabled={self.enable_sources_filtering}")
    
    def filter_sources(self, llm_answer: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        基于LLM回答过滤检索源
        :param llm_answer: LLM的回答内容
        :param sources: 原始检索源列表
        :return: 过滤后的源列表
        """
        if not self.enable_sources_filtering or not sources:
            return sources
        
        try:
            logger.info(f"开始源过滤，原始源数量: {len(sources)}")
            
            filtered_sources = []
            
            for source in sources:
                relevance_score = self._calculate_source_relevance(llm_answer, source)
                source['relevance_score'] = relevance_score
                
                # 根据相关性分数决定是否保留
                if relevance_score >= self.min_relevance_score:
                    filtered_sources.append(source)
            
            logger.info(f"源过滤完成，过滤后源数量: {len(filtered_sources)}")
            return filtered_sources
            
        except Exception as e:
            logger.error(f"源过滤失败: {e}")
            return sources
    
    def _calculate_source_relevance(self, llm_answer: str, source: Dict[str, Any]) -> float:
        """
        计算源与LLM回答的相关性分数
        :param llm_answer: LLM回答
        :param source: 检索源
        :return: 相关性分数 (0-1)
        """
        scores = []
        
        # 1. 关键词匹配分数
        if self.enable_keyword_matching:
            keyword_score = self._calculate_keyword_relevance(llm_answer, source)
            scores.append(keyword_score)
        
        # 2. 图片ID匹配分数
        if self.enable_image_id_matching:
            image_score = self._calculate_image_relevance(llm_answer, source)
            scores.append(image_score)
        
        # 3. 相似度过滤分数
        if self.enable_similarity_filtering:
            similarity_score = self._calculate_similarity_relevance(llm_answer, source)
            scores.append(similarity_score)
        
        # 如果没有启用任何过滤方法，返回默认分数
        if not scores:
            return 0.5
        
        # 返回平均分数
        return sum(scores) / len(scores)
    
    def _calculate_keyword_relevance(self, llm_answer: str, source: Dict[str, Any]) -> float:
        """
        计算关键词匹配相关性
        :param llm_answer: LLM回答
        :param source: 检索源
        :return: 关键词匹配分数
        """
        try:
            # 确保llm_answer是字符串
            if not isinstance(llm_answer, str):
                llm_answer = str(llm_answer)
            
            # 提取LLM回答中的关键词
            answer_keywords = self._extract_keywords(llm_answer)
            
            # 提取源内容中的关键词
            source_content = source.get('content', '')
            if not isinstance(source_content, str):
                source_content = str(source_content)
            source_keywords = self._extract_keywords(source_content)
            
            if not answer_keywords or not source_keywords:
                return 0.0
            
            # 计算关键词重叠度
            answer_keyword_set = set(answer_keywords)
            source_keyword_set = set(source_keywords)
            
            intersection = answer_keyword_set & source_keyword_set
            union = answer_keyword_set | source_keyword_set
            
            if not union:
                return 0.0
            
            # Jaccard相似度
            jaccard_similarity = len(intersection) / len(union)
            
            # 关键词频率加权
            frequency_score = 0.0
            for keyword in intersection:
                answer_freq = answer_keywords.count(keyword)
                source_freq = source_keywords.count(keyword)
                frequency_score += min(answer_freq, source_freq)
            
            # 归一化频率分数
            max_possible_freq = len(answer_keywords) * 2
            normalized_freq_score = min(frequency_score / max_possible_freq, 1.0)
            
            # 综合分数
            final_score = (jaccard_similarity * 0.7 + normalized_freq_score * 0.3)
            
            return final_score
            
        except Exception as e:
            logger.error(f"关键词相关性计算失败: {e}")
            return 0.0
    
    def _calculate_image_relevance(self, llm_answer: str, source: Dict[str, Any]) -> float:
        """
        计算图片ID匹配相关性
        :param llm_answer: LLM回答
        :param source: 检索源
        :return: 图片匹配分数
        """
        try:
            # 提取LLM回答中提到的图片ID
            mentioned_image_ids = self._extract_image_ids(llm_answer)
            
            # 提取源中的图片ID
            source_image_ids = self._extract_image_ids_from_source(source)
            
            if not mentioned_image_ids or not source_image_ids:
                return 0.0
            
            # 计算图片ID匹配度
            mentioned_set = set(mentioned_image_ids)
            source_set = set(source_image_ids)
            
            intersection = mentioned_set & source_set
            
            if not intersection:
                return 0.0
            
            # 匹配分数
            match_ratio = len(intersection) / len(mentioned_set)
            
            return match_ratio
            
        except Exception as e:
            logger.error(f"图片相关性计算失败: {e}")
            return 0.0
    
    def _calculate_similarity_relevance(self, llm_answer: str, source: Dict[str, Any]) -> float:
        """
        计算相似度相关性
        :param llm_answer: LLM回答
        :param source: 检索源
        :return: 相似度分数
        """
        try:
            source_content = source.get('content', '')
            if not isinstance(source_content, str):
                source_content = str(source_content)
            
            if not llm_answer or not source_content:
                return 0.0
            
            # 使用序列匹配器计算相似度
            similarity = SequenceMatcher(None, llm_answer, source_content).ratio()
            
            return similarity
            
        except Exception as e:
            logger.error(f"相似度相关性计算失败: {e}")
            return 0.0
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取文本关键词
        :param text: 输入文本
        :return: 关键词列表
        """
        # 确保text是字符串
        if not isinstance(text, str):
            text = str(text)
        
        # 停用词列表
        stop_words = {
            '的', '是', '在', '有', '和', '与', '或', '但', '而', '如果', '因为', '所以',
            '什么', '怎么', '为什么', '如何', '这个', '那个', '这些', '那些', '一个', '一些',
            '可以', '应该', '能够', '需要', '必须', '可能', '也许', '大概', '大约', '左右',
            '根据', '显示', '表明', '说明', '指出', '提到', '包括', '涉及', '关于', '对于'
        }
        
        # 提取中文词汇和英文词汇
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        
        # 过滤停用词和短词
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords
    
    def _extract_image_ids(self, text: str) -> List[str]:
        """
        从文本中提取图片ID
        :param text: 输入文本
        :return: 图片ID列表
        """
        # 匹配图片ID模式（假设图片ID是32位十六进制字符串）
        image_id_pattern = r'[a-f0-9]{32}'
        image_ids = re.findall(image_id_pattern, text.lower())
        
        return image_ids
    
    def _extract_image_ids_from_source(self, source: Dict[str, Any]) -> List[str]:
        """
        从源中提取图片ID
        :param source: 检索源
        :return: 图片ID列表
        """
        image_ids = []
        
        # 从源内容中提取
        content = source.get('content', '')
        if not isinstance(content, str):
            content = str(content)
        image_ids.extend(self._extract_image_ids(content))
        
        # 从元数据中提取
        metadata = source.get('metadata', {})
        if 'image_ids' in metadata:
            image_ids.extend(metadata['image_ids'])
        
        # 去重
        return list(set(image_ids))
    
    def get_filtering_stats(self) -> Dict[str, Any]:
        """
        获取过滤统计信息
        :return: 统计信息
        """
        return {
            'enable_sources_filtering': self.enable_sources_filtering,
            'min_relevance_score': self.min_relevance_score,
            'enable_keyword_matching': self.enable_keyword_matching,
            'enable_image_id_matching': self.enable_image_id_matching,
            'enable_similarity_filtering': self.enable_similarity_filtering
        } 