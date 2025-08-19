"""
源过滤引擎 - 基于LLM回答内容的智能源过滤

## 1. 功能特点
- 基于LLM生成答案的智能源过滤
- 动态相关性判断和阈值调整
- 支持多种过滤策略和算法
- 可配置的过滤参数和规则

## 2. 与其他版本的不同点
- 新增的源过滤引擎，替代原有的简单源过滤
- 基于AI内容的智能相关性判断
- 动态阈值调整和自适应过滤
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class SourceFilterConfig:
    """源过滤配置"""
    enable_filtering: bool = True
    relevance_threshold: float = 0.6
    content_overlap_threshold: float = 0.3
    keyword_match_weight: float = 0.4
    semantic_similarity_weight: float = 0.4
    content_quality_weight: float = 0.2
    enable_dynamic_threshold: bool = True
    min_sources_to_keep: int = 1
    max_sources_to_keep: int = 10
    enable_source_ranking: bool = True

class SourceFilterEngine:
    """源过滤引擎"""
    
    def __init__(self, config: Optional[SourceFilterConfig] = None):
        """
        初始化源过滤引擎
        
        :param config: 源过滤配置
        """
        self.config = config or SourceFilterConfig()
        
        logger.info(f"源过滤引擎初始化完成")
    
    # def filter_sources(self, llm_answer: str, sources: List[Dict[str, Any]], 
    #                   query: str = "") -> List[Dict[str, Any]]:
    #     """
    #     基于LLM回答内容过滤源
        
    #     :param llm_answer: LLM生成的答案
    #     :param sources: 源列表
    #     :param query: 原始查询（可选）
    #     :return: 过滤后的源列表
    #     """
    #     if not self.config.enable_filtering:
    #         logger.info("源过滤功能已禁用，返回原始源")
    #         return sources
        
    #     if not sources:
    #         logger.warning("没有源需要过滤")
    #         return []
        
    #     if not llm_answer:
    #         logger.warning("LLM答案为空，返回原始源")
    #         return sources
        
    #     try:
    #         logger.info(f"开始源过滤，原始源数量: {len(sources)}")
            
    #         # 1. 提取LLM答案中的关键信息
    #         answer_keywords = self._extract_answer_keywords(llm_answer)
    #         answer_entities = self._extract_answer_entities(llm_answer)
            
    #         # 2. 计算每个源的相关性分数
    #         scored_sources = []
    #         for source in sources:
    #             relevance_score = self._calculate_source_relevance(
    #                 source, answer_keywords, answer_entities, llm_answer, query
    #             )
                
    #             source_copy = source.copy()
    #             source_copy['relevance_score'] = relevance_score
    #             scored_sources.append(source_copy)
            
    #         # 3. 动态阈值调整
    #         if self.config.enable_dynamic_threshold:
    #             adjusted_threshold = self._adjust_threshold_dynamically(
    #                 scored_sources, llm_answer
    #             )
    #             logger.info(f"动态调整阈值: {self.config.relevance_threshold} -> {adjusted_threshold}")
    #         else:
    #             adjusted_threshold = self.config.relevance_threshold
            
    #         # 4. 过滤源
    #         filtered_sources = []
    #         for source in scored_sources:
    #             if source['relevance_score'] >= adjusted_threshold:
    #                 filtered_sources.append(source)
            
    #         # 5. 确保保留最小数量的源
    #         if len(filtered_sources) < self.config.min_sources_to_keep:
    #             logger.info(f"过滤后源数量不足，补充到最小数量: {self.config.min_sources_to_keep}")
    #             filtered_sources = self._ensure_minimum_sources(
    #                 scored_sources, self.config.min_sources_to_keep
    #             )
            
    #         # 6. 限制最大源数量
    #         if len(filtered_sources) > self.config.max_sources_to_keep:
    #             logger.info(f"过滤后源数量过多，限制到最大数量: {self.config.max_sources_to_keep}")
    #             filtered_sources = filtered_sources[:self.config.max_sources_to_keep]
            
    #         # 7. 源排序
    #         if self.config.enable_source_ranking:
    #             filtered_sources.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
    #         logger.info(f"源过滤完成，最终保留: {len(filtered_sources)} 个源")
    #         return filtered_sources
            
    #     except Exception as e:
    #         logger.error(f"源过滤过程中发生错误: {str(e)}")
    #         return sources
    
   
    def filter_sources(self, llm_answer: str, sources: List[Dict[str, Any]], 
                    query: str = "", query_type: str = None) -> List[Dict[str, Any]]:
        """
        基于LLM回答内容和查询类型过滤源
        
        :param llm_answer: LLM生成的答案
        :param sources: 源列表
        :param query: 原始查询（可选）
        :param query_type: 查询类型（text/image/table/hybrid/smart）
        :return: 过滤后的源列表
        """
        if not self.config.enable_filtering:
            logger.info("源过滤功能已禁用，返回原始源")
            return sources
        
        if not sources:
            logger.warning("没有源需要过滤")
            return []
        
        if not llm_answer:
            logger.warning("LLM答案为空，返回原始源")
            return sources
        
        try:
            logger.info(f"开始源过滤，原始源数量: {len(sources)}")
            logger.info(f"查询类型: {query_type}")
            
            # 根据查询类型选择过滤策略
            if query_type:
                # 明确的查询类型，使用对应的过滤策略
                if query_type.lower() in ['image', 'img']:
                    logger.info("检测到图片查询类型，使用图片过滤策略")
                    return self._filter_image_sources(llm_answer, sources, query)
                elif query_type.lower() in ['table', 'tbl']:
                    logger.info("检测到表格查询类型，使用表格过滤策略")
                    return self._filter_table_sources(llm_answer, sources, query)
                elif query_type.lower() in ['text', 'txt']:
                    logger.info("检测到文本查询类型，使用文本过滤策略")
                    return self._filter_text_sources(llm_answer, sources, query)
                elif query_type.lower() in ['hybrid']:
                    logger.info("检测到混合查询类型，使用混合过滤策略")
                    return self._filter_hybrid_sources(llm_answer, sources, query)
                elif query_type.lower() in ['smart']:
                    logger.info("检测到智能查询类型，使用智能检测策略")
                    return self._filter_sources_with_detection(llm_answer, sources, query)
                else:
                    logger.info(f"未知查询类型: {query_type}，使用默认文本过滤策略")
                    return self._filter_text_sources(llm_answer, sources, query)
            else:
                # 没有明确查询类型，使用智能检测（保持向后兼容）
                logger.info("未指定查询类型，使用智能检测")
                return self._filter_sources_with_detection(llm_answer, sources, query)
                
        except Exception as e:
            logger.error(f"源过滤过程中发生错误: {str(e)}")
            return sources
    
    def _filter_text_sources(self, llm_answer: str, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        文本查询专用过滤策略
        
        :param llm_answer: LLM生成的答案
        :param sources: 源列表
        :param query: 原始查询
        :return: 过滤后的源列表
        """
        logger.info("使用文本查询过滤策略")
        
        # 1. 提取LLM答案中的关键信息
        answer_keywords = self._extract_answer_keywords(llm_answer)
        answer_entities = self._extract_answer_entities(llm_answer)
        
        # 2. 计算每个源的相关性分数
        scored_sources = []
        for source in sources:
            relevance_score = self._calculate_source_relevance(
                source, answer_keywords, answer_entities, llm_answer, query
            )
            
            # 确保保留所有原始信息，特别是metadata
            source_copy = source.copy()
            source_copy['relevance_score'] = relevance_score
            
            # 确保metadata信息完整
            if 'metadata' not in source_copy and hasattr(source, 'metadata'):
                source_copy['metadata'] = source.metadata
            
            # 如果source本身有document_name等字段，确保保留
            if hasattr(source, 'document_name') and 'document_name' not in source_copy:
                source_copy['document_name'] = source.document_name
            if hasattr(source, 'page_number') and 'page_number' not in source_copy:
                source_copy['page_number'] = source.page_number
            if hasattr(source, 'page_content') and 'page_content' not in source_copy:
                source_copy['page_content'] = source.page_content
            
            scored_sources.append(source_copy)
        
        # 3. 动态阈值调整
        if self.config.enable_dynamic_threshold:
            adjusted_threshold = self._adjust_threshold_dynamically(
                scored_sources, llm_answer
            )
            logger.info(f"动态调整阈值: {self.config.relevance_threshold} -> {adjusted_threshold}")
        else:
            adjusted_threshold = self.config.relevance_threshold
        
        # 4. 过滤源
        filtered_sources = []
        for source in scored_sources:
            if source['relevance_score'] >= adjusted_threshold:
                filtered_sources.append(source)
        
        # 5. 确保保留最小数量的源
        if len(filtered_sources) < self.config.min_sources_to_keep:
            logger.info(f"过滤后源数量不足，补充到最小数量: {self.config.min_sources_to_keep}")
            filtered_sources = self._ensure_minimum_sources(
                scored_sources, self.config.min_sources_to_keep
            )
        
        # 6. 限制最大源数量
        if len(filtered_sources) > self.config.max_sources_to_keep:
            logger.info(f"过滤后源数量过多，限制到最大数量: {self.config.max_sources_to_keep}")
            filtered_sources = filtered_sources[:self.config.max_sources_to_keep]
        
        # 7. 源排序
        if self.config.enable_source_ranking:
            filtered_sources.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        logger.info(f"文本查询源过滤完成，最终保留: {len(filtered_sources)} 个源")
        return filtered_sources
    
    def _filter_image_sources(self, llm_answer: str, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        图片查询专用过滤策略
        
        :param llm_answer: LLM生成的答案
        :param sources: 源列表
        :param query: 原始查询
        :return: 过滤后的源列表
        """
        logger.info("使用图片查询过滤策略")
        
        # 图片查询时，只过滤掉完全不相关的源
        filtered_sources = []
        for source in sources:
            relevance_score = self._calculate_source_relevance(
                source, [], [], llm_answer, query
            )
            
            # 确保保留所有原始信息，特别是metadata
            source_copy = source.copy()
            source_copy['relevance_score'] = relevance_score
            
            # 确保metadata信息完整
            if 'metadata' not in source_copy and hasattr(source, 'metadata'):
                source_copy['metadata'] = source.metadata
            
            # 如果source本身有document_name等字段，确保保留
            if hasattr(source, 'document_name') and 'document_name' not in source_copy:
                source_copy['document_name'] = source.document_name
            if hasattr(source, 'page_number') and 'page_number' not in source_copy:
                source_copy['page_number'] = source.page_number
            if hasattr(source, 'page_content') and 'page_content' not in source_copy:
                source_copy['page_content'] = source.page_content
            
            # 图片查询使用更低的阈值
            if relevance_score >= 0.05:  # 大幅降低阈值
                filtered_sources.append(source_copy)
            else:
                logger.debug(f"过滤掉低相关性图片源: {source_copy.get('title', 'N/A')} (分数: {relevance_score:.3f})")
        
        # 如果过滤后数量不足，从原始源中补充
        if len(filtered_sources) < self.config.min_sources_to_keep:
            remaining_sources = [s for s in sources if s not in filtered_sources]
            needed_sources = self.config.min_sources_to_keep - len(filtered_sources)
            filtered_sources.extend(remaining_sources[:needed_sources])
            logger.info(f"图片查询补充源数量: {needed_sources}")
        
        # 限制最大源数量
        if len(filtered_sources) > self.config.max_sources_to_keep:
            filtered_sources = filtered_sources[:self.config.max_sources_to_keep]
        
        logger.info(f"图片查询源过滤完成，最终保留: {len(filtered_sources)} 个源")
        return filtered_sources
    
    def _filter_table_sources(self, llm_answer: str, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        表格查询专用过滤策略
        
        :param llm_answer: LLM生成的答案
        :param sources: 源列表
        :param query: 原始查询
        :return: 过滤后的源列表
        """
        logger.info("使用表格查询过滤策略")
        
        # 表格查询使用中等阈值，平衡精度和召回
        filtered_sources = []
        for source in sources:
            relevance_score = self._calculate_source_relevance(
                source, [], [], llm_answer, query
            )
            
            # 确保保留所有原始信息，特别是metadata
            source_copy = source.copy()
            source_copy['relevance_score'] = relevance_score
            
            # 确保metadata信息完整
            if 'metadata' not in source_copy and hasattr(source, 'metadata'):
                source_copy['metadata'] = source.metadata
            
            # 如果source本身有document_name等字段，确保保留
            if hasattr(source, 'document_name') and 'document_name' not in source_copy:
                source_copy['document_name'] = source.document_name
            if hasattr(source, 'page_number') and 'page_number' not in source_copy:
                source_copy['page_number'] = source.page_number
            if hasattr(source, 'page_content') and 'page_content' not in source_copy:
                source_copy['page_content'] = source.page_content
            
            # 表格查询使用中等阈值
            if relevance_score >= 0.15:  # 中等阈值
                filtered_sources.append(source_copy)
            else:
                logger.debug(f"过滤掉低相关性表格源: {source_copy.get('title', 'N/A')} (分数: {relevance_score:.3f})")
        
        # 如果过滤后数量不足，从原始源中补充
        if len(filtered_sources) < self.config.min_sources_to_keep:
            remaining_sources = [s for s in sources if s not in filtered_sources]
            needed_sources = self.config.min_sources_to_keep - len(filtered_sources)
            filtered_sources.extend(remaining_sources[:needed_sources])
            logger.info(f"表格查询补充源数量: {needed_sources}")
        
        # 限制最大源数量
        if len(filtered_sources) > self.config.max_sources_to_keep:
            filtered_sources = filtered_sources[:self.config.max_sources_to_keep]
        
        logger.info(f"表格查询源过滤完成，最终保留: {len(filtered_sources)} 个源")
        return filtered_sources
    
    def _filter_hybrid_sources(self, llm_answer: str, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        混合查询专用过滤策略
        
        :param llm_answer: LLM生成的答案
        :param sources: 源列表
        :param query: 原始查询
        :return: 过滤后的源列表
        """
        logger.info("使用混合查询过滤策略")
        
        # 混合查询使用平衡策略，确保各类型源都有代表性
        filtered_sources = []
        
        # 按类型分组源
        text_sources = []
        image_sources = []
        table_sources = []
        
        for source in sources:
            chunk_type = source.get('chunk_type', 'text')
            if chunk_type in ['image', 'image_text']:
                image_sources.append(source)
            elif chunk_type == 'table':
                table_sources.append(source)
            else:
                text_sources.append(source)
        
        logger.info(f"源分类统计: 文本={len(text_sources)}, 图片={len(image_sources)}, 表格={len(table_sources)}")
        
        # 为每种类型分配配额
        max_per_type = min(self.config.max_sources_to_keep // 3, 5)  # 每种类型最多5个
        
        # 处理文本源
        text_filtered = self._filter_text_sources(llm_answer, text_sources, query)
        filtered_sources.extend(text_filtered[:max_per_type])
        
        # 处理图片源
        image_filtered = self._filter_image_sources(llm_answer, image_sources, query)
        filtered_sources.extend(image_filtered[:max_per_type])
        
        # 处理表格源
        table_filtered = self._filter_table_sources(llm_answer, table_sources, query)
        filtered_sources.extend(table_filtered[:max_per_type])
        
        # 限制总数量
        if len(filtered_sources) > self.config.max_sources_to_keep:
            filtered_sources = filtered_sources[:self.config.max_sources_to_keep]
        
        logger.info(f"混合查询源过滤完成，最终保留: {len(filtered_sources)} 个源")
        return filtered_sources
    
    def _filter_sources_with_detection(self, llm_answer: str, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        智能检测查询类型的过滤策略（向后兼容）
        
        :param llm_answer: LLM生成的答案
        :param sources: 源列表
        :param query: 原始查询
        :return: 过滤后的源列表
        """
        logger.info("使用智能检测查询类型")
        
        # 检测图片源占比
        image_sources_count = sum(1 for source in sources 
                                if (source.get('chunk_type') == 'image' or 
                                    source.get('chunk_type') == 'image_text' or
                                    (hasattr(source, 'metadata') and 
                                     source.metadata and 
                                     source.metadata.get('chunk_type') == 'image')))
        
        total_sources = len(sources)
        image_ratio = image_sources_count / total_sources if total_sources > 0 else 0
        
        # 根据检测结果选择策略
        if image_ratio > 0.5:
            logger.info(f"智能检测到图片查询（图片源占比: {image_ratio:.2%}），使用图片过滤策略")
            return self._filter_image_sources(llm_answer, sources, query)
        else:
            logger.info(f"智能检测到文本查询（图片源占比: {image_ratio:.2%}），使用文本过滤策略")
            return self._filter_text_sources(llm_answer, sources, query)
    
   
    def _extract_answer_keywords(self, answer: str) -> List[str]:
        """
        从LLM答案中提取关键词
        
        :param answer: LLM答案
        :return: 关键词列表
        """
        if not answer:
            return []
        
        # 简单的关键词提取逻辑
        # 移除标点符号和常见停用词
        cleaned_answer = re.sub(r'[，。！？；：""''（）【】]', ' ', answer)
        words = cleaned_answer.split()
        
        # 过滤短词和停用词
        keywords = []
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个'}
        
        for word in words:
            word = word.strip()
            if len(word) > 1 and word not in stopwords:
                keywords.append(word)
        
        return keywords[:20]  # 限制关键词数量
    
    def _extract_answer_entities(self, answer: str) -> List[str]:
        """
        从LLM答案中提取实体
        
        :param answer: LLM答案
        :return: 实体列表
        """
        if not answer:
            return []
        
        # 简单的实体提取逻辑
        # 查找引号内的内容、数字、英文单词等
        entities = []
        
        # 引号内的内容
        quoted_content = re.findall(r'[""]([^""]+)[""]', answer)
        entities.extend(quoted_content)
        
        # 数字
        numbers = re.findall(r'\d+(?:\.\d+)?', answer)
        entities.extend(numbers)
        
        # 英文单词（可能是专有名词）
        english_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', answer)
        entities.extend(english_words)
        
        return entities[:10]  # 限制实体数量
    
    def _calculate_source_relevance(self, source: Dict[str, Any], answer_keywords: List[str], 
                                  answer_entities: List[str], llm_answer: str, 
                                  query: str = "") -> float:
        """
        计算源的相关性分数
        
        :param source: 源信息
        :param answer_keywords: 答案关键词
        :param answer_entities: 答案实体
        :param llm_answer: LLM答案
        :param query: 原始查询
        :return: 相关性分数 (0-1)
        """
        if not source:
            return 0.0
        
        # 获取源内容
        source_content = source.get('content', '')
        source_metadata = source.get('metadata', {})
        
        if not source_content:
            return 0.0
        
        # 1. 关键词匹配分数
        keyword_score = self._calculate_keyword_match_score(
            answer_keywords, source_content
        )
        
        # 2. 实体匹配分数
        entity_score = self._calculate_entity_match_score(
            answer_entities, source_content
        )
        
        # 3. 内容重叠分数
        overlap_score = self._calculate_content_overlap_score(
            llm_answer, source_content
        )
        
        # 4. 元数据相关性分数
        metadata_score = self._calculate_metadata_relevance_score(
            source_metadata, query, llm_answer
        )
        
        # 5. 计算综合分数
        comprehensive_score = (
            keyword_score * self.config.keyword_match_weight +
            entity_score * self.config.keyword_match_weight * 0.5 +  # 实体权重稍低
            overlap_score * self.config.semantic_similarity_weight +
            metadata_score * self.config.content_quality_weight
        )
        
        return min(comprehensive_score, 1.0)
    
    def _calculate_keyword_match_score(self, keywords: List[str], content: str) -> float:
        """
        计算关键词匹配分数
        
        :param keywords: 关键词列表
        :param content: 内容文本
        :return: 匹配分数 (0-1)
        """
        if not keywords or not content:
            return 0.0
        
        content_lower = content.lower()
        matched_keywords = 0
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                matched_keywords += 1
        
        # 计算匹配率
        match_rate = matched_keywords / len(keywords)
        
        # 考虑关键词密度
        total_words = len(content.split())
        keyword_density = matched_keywords / max(total_words, 1)
        
        # 综合分数
        score = match_rate * 0.7 + keyword_density * 0.3
        
        return min(score, 1.0)
    
    def _calculate_entity_match_score(self, entities: List[str], content: str) -> float:
        """
        计算实体匹配分数
        
        :param entities: 实体列表
        :param content: 内容文本
        :return: 匹配分数 (0-1)
        """
        if not entities or not content:
            return 0.0
        
        content_lower = content.lower()
        matched_entities = 0
        
        for entity in entities:
            if entity.lower() in content_lower:
                matched_entities += 1
        
        # 实体匹配通常更重要，给予更高权重
        match_rate = matched_entities / len(entities)
        
        return min(match_rate, 1.0)
    
    def _calculate_content_overlap_score(self, answer: str, content: str) -> float:
        """
        计算内容重叠分数
        
        :param answer: LLM答案
        :param content: 源内容
        :return: 重叠分数 (0-1)
        """
        if not answer or not content:
            return 0.0
        
        # 简单的文本重叠计算
        answer_words = set(answer.lower().split())
        content_words = set(content.lower().split())
        
        if not answer_words or not content_words:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = len(answer_words.intersection(content_words))
        union = len(answer_words.union(content_words))
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # 如果重叠度太高，可能是过度匹配，适当降低分数
        if jaccard_similarity > 0.8:
            jaccard_similarity *= 0.8
        
        return min(jaccard_similarity, 1.0)
    
    def _calculate_metadata_relevance_score(self, metadata: Dict[str, Any], 
                                          query: str, llm_answer: str) -> float:
        """
        计算元数据相关性分数
        
        :param metadata: 源元数据
        :param query: 原始查询
        :param llm_answer: LLM答案
        :return: 相关性分数 (0-1)
        """
        if not metadata:
            return 0.5  # 默认中等分数
        
        score = 0.5  # 基础分数
        
        # 检查文档类型
        chunk_type = metadata.get('chunk_type', '')
        if chunk_type in ['text', 'table', 'image']:
            score += 0.1
        
        # 检查文档来源
        source_name = metadata.get('source_name', '')
        if source_name and source_name != '未知文档':
            score += 0.1
        
        # 检查页码信息
        if metadata.get('page_number'):
            score += 0.05
        
        # 检查时间信息
        if metadata.get('timestamp'):
            score += 0.05
        
        return min(score, 1.0)
    
    def _adjust_threshold_dynamically(self, scored_sources: List[Dict[str, Any]], 
                                    llm_answer: str) -> float:
        """
        动态调整过滤阈值
        
        :param scored_sources: 已评分的源列表
        :param llm_answer: LLM答案
        :return: 调整后的阈值
        """
        if not scored_sources:
            return self.config.relevance_threshold
        
        # 获取所有相关性分数
        scores = [source.get('relevance_score', 0) for source in scored_sources]
        scores = [s for s in scores if s > 0]  # 过滤零分
        
        if not scores:
            return self.config.relevance_threshold
        
        # 计算统计信息
        mean_score = sum(scores) / len(scores)
        max_score = max(scores)
        
        # 基于答案长度和分数分布调整阈值
        answer_length = len(llm_answer)
        
        if answer_length < 100:  # 短答案，降低阈值
            adjusted_threshold = mean_score * 0.8
        elif answer_length > 500:  # 长答案，提高阈值
            adjusted_threshold = mean_score * 1.2
        else:  # 中等长度，使用均值
            adjusted_threshold = mean_score
        
        # 确保阈值在合理范围内
        adjusted_threshold = max(0.3, min(0.9, adjusted_threshold))
        
        return adjusted_threshold
    
    def _ensure_minimum_sources(self, scored_sources: List[Dict[str, Any]], 
                              min_count: int) -> List[Dict[str, Any]]:
        """
        确保保留最小数量的源
        
        :param scored_sources: 已评分的源列表
        :param min_count: 最小数量
        :return: 调整后的源列表
        """
        if len(scored_sources) <= min_count:
            return scored_sources
        
        # 按分数排序
        sorted_sources = sorted(scored_sources, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # 返回前min_count个源
        return sorted_sources[:min_count]
    
    def get_engine_status(self) -> Dict[str, Any]:
        """
        获取引擎状态信息
        
        :return: 状态信息字典
        """
        return {
            "engine_type": "Source Filter",
            "enable_filtering": self.config.enable_filtering,
            "config": {
                "relevance_threshold": self.config.relevance_threshold,
                "content_overlap_threshold": self.config.content_overlap_threshold,
                "keyword_match_weight": self.config.keyword_match_weight,
                "semantic_similarity_weight": self.config.semantic_similarity_weight,
                "content_quality_weight": self.config.content_quality_weight,
                "enable_dynamic_threshold": self.config.enable_dynamic_threshold,
                "min_sources_to_keep": self.config.min_sources_to_keep,
                "max_sources_to_keep": self.config.max_sources_to_keep,
                "enable_source_ranking": self.config.enable_source_ranking
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
