'''
程序说明：
## 1. 智能过滤引擎实现
## 2. 综合内容、语义、上下文、用户意图的过滤策略
## 3. 支持多维度相关性计算
## 4. 集成到QA系统中
'''

import re
import logging
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher
from collections import Counter

logger = logging.getLogger(__name__)


class SmartFilterEngine:
    """
    智能过滤引擎
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化智能过滤引擎
        :param config: 配置字典
        """
        self.enable_smart_filtering = config.get('enable_smart_filtering', True)
        self.semantic_similarity_threshold = config.get('semantic_similarity_threshold', 0.6)
        self.content_relevance_threshold = config.get('content_relevance_threshold', 0.5)
        self.max_filtered_results = config.get('max_filtered_results', 3)
        
        logger.info(f"智能过滤引擎初始化完成: enabled={self.enable_smart_filtering}")
    
    def smart_filter(self, query: str, documents: List[Dict[str, Any]], 
                    llm_answer: str = None, user_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        智能过滤文档
        :param query: 用户查询
        :param documents: 原始文档列表
        :param llm_answer: LLM回答（可选）
        :param user_context: 用户上下文（可选）
        :return: 过滤后的文档列表
        """
        if not self.enable_smart_filtering or not documents:
            return documents
        
        try:
            logger.info(f"开始智能过滤，原始文档数量: {len(documents)}")
            
            # 计算每个文档的综合分数
            scored_documents = []
            
            for doc in documents:
                # 1. 内容相关性分数
                content_score = self._calculate_content_relevance(query, doc)
                
                # 2. 语义相似度分数
                semantic_score = self._calculate_semantic_similarity(query, doc)
                
                # 3. 上下文相关性分数
                context_score = self._calculate_context_relevance(query, doc, user_context)
                
                # 4. 用户意图匹配分数
                intent_score = self._calculate_intent_relevance(query, doc, llm_answer)
                
                # 5. 综合分数计算
                final_score = self._calculate_final_score(
                    content_score, semantic_score, context_score, intent_score
                )
                
                # 更新文档分数
                doc['smart_filter_scores'] = {
                    'content_score': content_score,
                    'semantic_score': semantic_score,
                    'context_score': context_score,
                    'intent_score': intent_score,
                    'final_score': final_score
                }
                
                scored_documents.append(doc)
            
            # 按综合分数排序
            sorted_documents = sorted(
                scored_documents, 
                key=lambda x: x['smart_filter_scores']['final_score'], 
                reverse=True
            )
            
            # 应用阈值过滤
            filtered_documents = [
                doc for doc in sorted_documents
                if doc['smart_filter_scores']['final_score'] >= self.content_relevance_threshold
            ]
            
            # 限制结果数量
            final_documents = filtered_documents[:self.max_filtered_results]
            
            logger.info(f"智能过滤完成，过滤后文档数量: {len(final_documents)}")
            return final_documents
            
        except Exception as e:
            logger.error(f"智能过滤失败: {e}")
            return documents
    
    def _calculate_content_relevance(self, query: str, document: Dict[str, Any]) -> float:
        """
        计算内容相关性分数
        :param query: 查询
        :param document: 文档
        :return: 内容相关性分数
        """
        try:
            content = document.get('content', '')
            
            if not query or not content:
                return 0.0
            
            # 1. 关键词匹配
            query_keywords = self._extract_keywords(query)
            content_keywords = self._extract_keywords(content)
            
            keyword_overlap = len(set(query_keywords) & set(content_keywords))
            keyword_score = keyword_overlap / max(len(query_keywords), 1)
            
            # 2. 短语匹配
            phrase_score = self._calculate_phrase_similarity(query, content)
            
            # 3. 实体匹配
            entity_score = self._calculate_entity_similarity(query, content)
            
            # 综合内容分数
            content_score = (keyword_score * 0.4 + phrase_score * 0.4 + entity_score * 0.2)
            
            return content_score
            
        except Exception as e:
            logger.error(f"内容相关性计算失败: {e}")
            return 0.0
    
    def _calculate_semantic_similarity(self, query: str, document: Dict[str, Any]) -> float:
        """
        计算语义相似度分数
        :param query: 查询
        :param document: 文档
        :return: 语义相似度分数
        """
        try:
            content = document.get('content', '')
            
            if not query or not content:
                return 0.0
            
            # 使用序列匹配器计算相似度
            similarity = SequenceMatcher(None, query, content).ratio()
            
            # 应用阈值
            if similarity < self.semantic_similarity_threshold:
                similarity = 0.0
            
            return similarity
            
        except Exception as e:
            logger.error(f"语义相似度计算失败: {e}")
            return 0.0
    
    def _calculate_context_relevance(self, query: str, document: Dict[str, Any], 
                                   user_context: Dict[str, Any] = None) -> float:
        """
        计算上下文相关性分数
        :param query: 查询
        :param document: 文档
        :param user_context: 用户上下文
        :return: 上下文相关性分数
        """
        try:
            if not user_context:
                return 0.5  # 默认中等分数
            
            context_score = 0.0
            context_factors = 0
            
            # 1. 时间上下文
            if 'time_context' in user_context:
                time_score = self._calculate_time_relevance(document, user_context['time_context'])
                context_score += time_score
                context_factors += 1
            
            # 2. 主题上下文
            if 'topic_context' in user_context:
                topic_score = self._calculate_topic_relevance(document, user_context['topic_context'])
                context_score += topic_score
                context_factors += 1
            
            # 3. 用户偏好上下文
            if 'user_preferences' in user_context:
                preference_score = self._calculate_preference_relevance(document, user_context['user_preferences'])
                context_score += preference_score
                context_factors += 1
            
            # 计算平均分数
            if context_factors > 0:
                return context_score / context_factors
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"上下文相关性计算失败: {e}")
            return 0.5
    
    def _calculate_intent_relevance(self, query: str, document: Dict[str, Any], 
                                  llm_answer: str = None) -> float:
        """
        计算用户意图匹配分数
        :param query: 查询
        :param document: 文档
        :param llm_answer: LLM回答
        :return: 意图匹配分数
        """
        try:
            intent_score = 0.0
            intent_factors = 0
            
            # 1. 查询意图分析
            query_intent = self._analyze_query_intent(query)
            doc_intent = self._analyze_document_intent(document)
            
            if query_intent and doc_intent:
                intent_match = self._calculate_intent_match(query_intent, doc_intent)
                intent_score += intent_match
                intent_factors += 1
            
            # 2. LLM回答意图分析（如果可用）
            if llm_answer:
                answer_intent = self._analyze_answer_intent(llm_answer)
                if answer_intent and doc_intent:
                    answer_match = self._calculate_intent_match(answer_intent, doc_intent)
                    intent_score += answer_match
                    intent_factors += 1
            
            # 计算平均分数
            if intent_factors > 0:
                return intent_score / intent_factors
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"意图相关性计算失败: {e}")
            return 0.5
    
    def _calculate_final_score(self, content_score: float, semantic_score: float,
                              context_score: float, intent_score: float) -> float:
        """
        计算综合分数
        :param content_score: 内容分数
        :param semantic_score: 语义分数
        :param context_score: 上下文分数
        :param intent_score: 意图分数
        :return: 综合分数
        """
        # 权重配置
        weights = {
            'content': 0.35,
            'semantic': 0.30,
            'context': 0.20,
            'intent': 0.15
        }
        
        final_score = (
            content_score * weights['content'] +
            semantic_score * weights['semantic'] +
            context_score * weights['context'] +
            intent_score * weights['intent']
        )
        
        return final_score
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        :param text: 输入文本
        :return: 关键词列表
        """
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
    
    def _calculate_phrase_similarity(self, query: str, content: str) -> float:
        """
        计算短语相似度
        :param query: 查询
        :param content: 内容
        :return: 短语相似度分数
        """
        try:
            # 提取短语（2-4个词的组合）
            query_phrases = self._extract_phrases(query)
            content_phrases = self._extract_phrases(content)
            
            if not query_phrases or not content_phrases:
                return 0.0
            
            # 计算短语重叠
            query_phrase_set = set(query_phrases)
            content_phrase_set = set(content_phrases)
            
            intersection = query_phrase_set & content_phrase_set
            
            if not intersection:
                return 0.0
            
            # 计算重叠率
            overlap_ratio = len(intersection) / len(query_phrase_set)
            
            return overlap_ratio
            
        except Exception as e:
            logger.error(f"短语相似度计算失败: {e}")
            return 0.0
    
    def _extract_phrases(self, text: str) -> List[str]:
        """
        提取短语
        :param text: 输入文本
        :return: 短语列表
        """
        words = self._extract_keywords(text)
        phrases = []
        
        # 生成2-4个词的短语
        for i in range(len(words) - 1):
            for j in range(2, min(5, len(words) - i + 1)):
                phrase = ' '.join(words[i:i+j])
                phrases.append(phrase)
        
        return phrases
    
    def _calculate_entity_similarity(self, query: str, content: str) -> float:
        """
        计算实体相似度
        :param query: 查询
        :param content: 内容
        :return: 实体相似度分数
        """
        try:
            # 提取实体（公司名、产品名、数字等）
            query_entities = self._extract_entities(query)
            content_entities = self._extract_entities(content)
            
            if not query_entities or not content_entities:
                return 0.0
            
            # 计算实体匹配
            query_entity_set = set(query_entities)
            content_entity_set = set(content_entities)
            
            intersection = query_entity_set & content_entity_set
            
            if not intersection:
                return 0.0
            
            # 计算匹配率
            match_ratio = len(intersection) / len(query_entity_set)
            
            return match_ratio
            
        except Exception as e:
            logger.error(f"实体相似度计算失败: {e}")
            return 0.0
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        提取实体
        :param text: 输入文本
        :return: 实体列表
        """
        entities = []
        
        # 提取公司名（包含"公司"、"集团"、"股份"等）
        company_pattern = r'[\u4e00-\u9fff]+(?:公司|集团|股份|有限|科技|电子|半导体)'
        companies = re.findall(company_pattern, text)
        entities.extend(companies)
        
        # 提取数字
        number_pattern = r'\d+(?:\.\d+)?(?:%|万|亿|元)?'
        numbers = re.findall(number_pattern, text)
        entities.extend(numbers)
        
        # 提取英文缩写
        abbreviation_pattern = r'[A-Z]{2,}'
        abbreviations = re.findall(abbreviation_pattern, text)
        entities.extend(abbreviations)
        
        return entities
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        分析查询意图
        :param query: 查询
        :return: 意图分析结果
        """
        intent = {
            'type': 'general',
            'keywords': [],
            'entities': [],
            'time_related': False,
            'comparison': False
        }
        
        # 分析意图类型
        if any(word in query for word in ['比较', '对比', '差异']):
            intent['type'] = 'comparison'
            intent['comparison'] = True
        
        if any(word in query for word in ['2024', '2025', '去年', '今年', '明年']):
            intent['time_related'] = True
        
        # 提取关键词和实体
        intent['keywords'] = self._extract_keywords(query)
        intent['entities'] = self._extract_entities(query)
        
        return intent
    
    def _analyze_document_intent(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析文档意图
        :param document: 文档
        :return: 意图分析结果
        """
        content = document.get('content', '')
        
        intent = {
            'type': 'general',
            'keywords': [],
            'entities': [],
            'time_related': False,
            'comparison': False
        }
        
        # 分析文档内容
        intent['keywords'] = self._extract_keywords(content)
        intent['entities'] = self._extract_entities(content)
        
        if any(word in content for word in ['比较', '对比', '差异']):
            intent['comparison'] = True
        
        if any(word in content for word in ['2024', '2025', '去年', '今年', '明年']):
            intent['time_related'] = True
        
        return intent
    
    def _analyze_answer_intent(self, answer: str) -> Dict[str, Any]:
        """
        分析回答意图
        :param answer: LLM回答
        :return: 意图分析结果
        """
        return self._analyze_query_intent(answer)  # 复用查询意图分析
    
    def _calculate_intent_match(self, query_intent: Dict[str, Any], 
                              doc_intent: Dict[str, Any]) -> float:
        """
        计算意图匹配度
        :param query_intent: 查询意图
        :param doc_intent: 文档意图
        :return: 意图匹配分数
        """
        try:
            match_score = 0.0
            match_factors = 0
            
            # 1. 关键词匹配
            query_keywords = set(query_intent.get('keywords', []))
            doc_keywords = set(doc_intent.get('keywords', []))
            
            if query_keywords and doc_keywords:
                keyword_overlap = len(query_keywords & doc_keywords)
                keyword_score = keyword_overlap / len(query_keywords)
                match_score += keyword_score
                match_factors += 1
            
            # 2. 实体匹配
            query_entities = set(query_intent.get('entities', []))
            doc_entities = set(doc_intent.get('entities', []))
            
            if query_entities and doc_entities:
                entity_overlap = len(query_entities & doc_entities)
                entity_score = entity_overlap / len(query_entities)
                match_score += entity_score
                match_factors += 1
            
            # 3. 时间相关性匹配
            if query_intent.get('time_related') and doc_intent.get('time_related'):
                match_score += 1.0
                match_factors += 1
            
            # 4. 比较意图匹配
            if query_intent.get('comparison') and doc_intent.get('comparison'):
                match_score += 1.0
                match_factors += 1
            
            # 计算平均分数
            if match_factors > 0:
                return match_score / match_factors
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"意图匹配计算失败: {e}")
            return 0.5
    
    def _calculate_time_relevance(self, document: Dict[str, Any], time_context: str) -> float:
        """
        计算时间相关性
        :param document: 文档
        :param time_context: 时间上下文
        :return: 时间相关性分数
        """
        # 简单实现：检查文档内容是否包含时间上下文
        content = document.get('content', '')
        if time_context in content:
            return 1.0
        return 0.0
    
    def _calculate_topic_relevance(self, document: Dict[str, Any], topic_context: str) -> float:
        """
        计算主题相关性
        :param document: 文档
        :param topic_context: 主题上下文
        :return: 主题相关性分数
        """
        # 简单实现：检查文档内容是否包含主题关键词
        content = document.get('content', '')
        topic_keywords = self._extract_keywords(topic_context)
        
        if not topic_keywords:
            return 0.5
        
        content_keywords = self._extract_keywords(content)
        overlap = len(set(topic_keywords) & set(content_keywords))
        
        return overlap / len(topic_keywords)
    
    def _calculate_preference_relevance(self, document: Dict[str, Any], 
                                      user_preferences: Dict[str, Any]) -> float:
        """
        计算用户偏好相关性
        :param document: 文档
        :param user_preferences: 用户偏好
        :return: 偏好相关性分数
        """
        # 简单实现：基于用户偏好计算相关性
        content = document.get('content', '')
        preference_score = 0.5  # 默认中等分数
        
        # 这里可以根据具体的用户偏好进行更复杂的计算
        # 例如：用户偏好技术分析 -> 检查文档是否包含技术指标
        
        return preference_score
    
    def get_filtering_stats(self) -> Dict[str, Any]:
        """
        获取过滤统计信息
        :return: 统计信息
        """
        return {
            'enable_smart_filtering': self.enable_smart_filtering,
            'semantic_similarity_threshold': self.semantic_similarity_threshold,
            'content_relevance_threshold': self.content_relevance_threshold,
            'max_filtered_results': self.max_filtered_results
        } 