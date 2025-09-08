"""
基于spaCy的查询重写器
用于解决多轮对话中的代词指代问题

严格按照现有系统包导入规范实现
"""

import logging
import re
from typing import List, Dict, Any, Optional

try:
    import spacy
    from spacy.lang.zh import Chinese
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

logger = logging.getLogger(__name__)


class SpaCyQueryRewriter:
    """
    基于spaCy的查询重写器
    
    用于解决多轮对话中的代词指代问题，如：
    - "它的情况如何？" -> "中芯国际的情况如何？"
    - "这张图显示了什么？" -> "图4显示了什么？"
    """
    
    def __init__(self, config_integration=None):
        """
        初始化spaCy查询重写器
        
        Args:
            config_integration: 配置集成管理器实例
        """
        self.config = config_integration
        self.nlp = None
        self.spacy_available = SPACY_AVAILABLE
        
        if self.spacy_available:
            self._initialize_spacy()
            # spaCy可用时，不需要手工代词模式
            self.pronoun_patterns = []
        else:
            logger.warning("spaCy不可用，将使用简化版本")
            # spaCy不可用时，使用手工代词模式
            self.pronoun_patterns = [
                '这家公司', '那家公司', '这个公司', '那个公司',
                '这张图', '那张图', '这家', '那家', 
                '这个', '那个', '这张', '那张',
                '它', '他', '她', '这', '那'
            ]
        
        # 实体类型优先级
        self.entity_priority = ['WORK_OF_ART', 'ORG', 'PERSON', 'PRODUCT', 'GPE', 'MISC']
        
        logger.info("SpaCy查询重写器初始化完成")
    
    def _initialize_spacy(self):
        """初始化spaCy模型"""
        if not SPACY_AVAILABLE:
            logger.warning("spaCy不可用，将使用简化版本")
            return
        
        try:
            # 优先尝试加载中文模型
            self.nlp = spacy.load("zh_core_web_sm")
            logger.info("成功加载中文spaCy模型 (zh_core_web_sm)")
        except OSError:
            try:
                # 如果中文模型不可用，尝试英文模型
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("使用英文spaCy模型 (en_core_web_sm)")
            except OSError:
                # 如果都不可用，使用基础中文模型
                self.nlp = spacy.blank("zh")
                logger.warning("使用基础中文语言模型 (spacy.blank)")
    
    def rewrite_query_with_context(self, query: str, context_memories: List[Dict[str, Any]]) -> str:
        """
        基于历史记忆重写查询
        
        Args:
            query: 用户查询
            context_memories: 历史记忆列表
            
        Returns:
            str: 重写后的查询
        """
        if not context_memories:
            return query
        
        try:
            # 1. 检测代词
            pronouns = self._detect_pronouns(query)
            if not pronouns:
                logger.debug(f"查询中未检测到代词: {query}")
                return query
            
            # 2. 提取实体
            entities = self._extract_entities_from_memories(context_memories)
            if not entities:
                logger.debug("未从历史记忆中提取到实体")
                return query
            
            # 3. 替换代词
            rewritten_query = self._replace_pronouns_with_entities(query, entities)
            
            logger.info(f"查询重写成功: '{query}' -> '{rewritten_query}'")
            return rewritten_query
            
        except Exception as e:
            logger.error(f"查询重写失败: {e}")
            return query
    
    def _simple_rewrite_query(self, query: str, context_memories: List[Dict[str, Any]]) -> str:
        """
        简化版本的查询重写（spaCy不可用时使用）
        
        Args:
            query: 原始查询
            context_memories: 历史记忆列表
            
        Returns:
            str: 重写后的查询
        """
        try:
            # 使用模式匹配检测代词
            pronouns = []
            for pattern in self.pronoun_patterns:
                if pattern in query:
                    pronouns.append(pattern)
            
            if not pronouns:
                return query
            
            # 从历史记忆中提取实体（简单版本）
            entities = []
            for memory in context_memories:
                content = memory.get('content', '')
                # 简单的实体提取：查找公司名、图表名等
                if '中芯国际' in content:
                    entities.append('中芯国际')
                if '图' in content and ('4' in content or '5' in content):
                    entities.append('图4' if '图4' in content else '图5')
                if '表' in content and '1' in content:
                    entities.append('表1')
            
            if not entities:
                return query
            
            # 简单的代词替换
            rewritten_query = query
            for pronoun in pronouns:
                if pronoun in rewritten_query and entities:
                    # 选择最相关的实体
                    best_entity = entities[0]  # 简化：选择第一个实体
                    rewritten_query = rewritten_query.replace(pronoun, best_entity)
                    break
            
            logger.info(f"简化查询重写: '{query}' -> '{rewritten_query}'")
            return rewritten_query
            
        except Exception as e:
            logger.error(f"简化查询重写失败: {e}")
            return query
    
    def _detect_pronouns(self, query: str) -> List[str]:
        """
        检测查询中的代词和指代词
        
        Args:
            query: 用户查询文本
            
        Returns:
            List[str]: 检测到的代词列表
        """
        detected_pronouns = []
        
        if self.nlp and self.spacy_available:
            # 使用spaCy进行智能代词检测
            try:
                doc = self.nlp(query)
                
                # 1. 检测spaCy识别的代词
                for token in doc:
                    if token.pos_ == 'PRON':
                        detected_pronouns.append(token.text)
                
                # 2. 检测指示代词和限定词
                for token in doc:
                    if token.pos_ in ['DET', 'PRON'] and token.text in ['这', '那', '它', '他', '她']:
                        detected_pronouns.append(token.text)
                
                # 3. 检测复合代词（如"这家公司"）
                for i, token in enumerate(doc):
                    if token.text in ['这', '那']:
                        # 检查后续词汇是否形成复合代词
                        if i + 1 < len(doc):
                            next_token = doc[i + 1]
                            if next_token.text in ['家', '个', '张']:
                                compound = token.text + next_token.text
                                if i + 2 < len(doc):
                                    next_next_token = doc[i + 2]
                                    if next_next_token.text in ['公司', '图']:
                                        compound += next_next_token.text
                                detected_pronouns.append(compound)
                
                # 4. 检测spaCy识别的复合限定词（如"这家"）
                for token in doc:
                    if token.text in ['这家', '那家', '这个', '那个', '这张', '那张']:
                        detected_pronouns.append(token.text)
                
            except Exception as e:
                logger.warning(f"spaCy代词检测失败: {e}")
        
        else:
            # spaCy不可用，使用模式匹配检测
            for pattern in self.pronoun_patterns:
                if pattern in query:
                    detected_pronouns.append(pattern)
        
        return list(set(detected_pronouns))
    
    def _extract_entities_from_memories(self, context_memories: List[Dict[str, Any]]) -> List[str]:
        """
        从历史记忆中提取实体
        
        Args:
            context_memories: 历史记忆列表
            
        Returns:
            List[str]: 提取的实体列表，按相关性排序
        """
        entities = []
        
        # 优先从问题中提取实体，然后从答案中提取
        question_texts = []
        answer_texts = []
        
        for mem in context_memories:
            if mem.get('user_query'):
                question_texts.append(mem['user_query'])
            if mem.get('content'):
                answer_texts.append(mem['content'])
        
        # 优先处理问题文本
        priority_text = " ".join(question_texts)
        if not priority_text.strip():
            # 如果没有问题文本，使用答案文本
            priority_text = " ".join(answer_texts)
        
        if not priority_text.strip():
            return entities
        
        if self.nlp:
            try:
                # 使用spaCy进行实体识别
                doc = self.nlp(priority_text)
                
                # 按实体类型分类提取
                entities_by_type = {
                    'ORG': [],      # 机构名
                    'PERSON': [],   # 人名
                    'PRODUCT': [],  # 产品名
                    'WORK_OF_ART': [], # 作品名（如图表）
                    'GPE': [],      # 地名
                    'MISC': []      # 其他
                }
                
                # 提取spaCy识别的实体
                for ent in doc.ents:
                    if ent.label_ in entities_by_type:
                        entities_by_type[ent.label_].append(ent.text)
                    else:
                        entities_by_type['MISC'].append(ent.text)
                
                # 按优先级排序实体
                for entity_type in self.entity_priority:
                    entities.extend(entities_by_type[entity_type])
                    
            except Exception as e:
                logger.warning(f"spaCy实体提取失败: {e}")
        
        # 如果spaCy不可用或失败，使用正则表达式备选方案
        if not entities:
            entities = self._extract_entities_with_regex(priority_text)
        
        # 去重并保持顺序
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen and len(entity.strip()) > 1:
                seen.add(entity)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _extract_entities_with_regex(self, text: str) -> List[str]:
        """
        使用正则表达式提取实体（spaCy不可用时的备选方案）
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 提取的实体列表
        """
        entities = []
        
        # 1. 提取公司/机构实体
        company_patterns = [
            r'([^，。！？\s]{2,20}(?:公司|集团|企业|科技|技术|股份|有限|控股))',
            r'([^，。！？\s]{2,20}(?:国际|中国|美国|日本|韩国))',
            r'([A-Z][a-zA-Z\s]{2,30}(?:Inc|Corp|Ltd|Co|Group))',
        ]
        
        # 2. 提取图片/图表实体
        image_patterns = [
            r'([^，。！？\s]{2,30}(?:图|图表|图片|图像|示意图|流程图|柱状图|饼图|折线图))',
            r'([^，。！？\s]{2,30}(?:图\d+|图表\d+|Figure\s*\d+))',
            r'([^，。！？\s]{2,30}(?:展示|显示|描述|说明).{0,15}(?:图|图表))',
        ]
        
        # 3. 提取人名实体
        name_patterns = [
            r'([^，。！？\s]{2,10}(?:先生|女士|博士|教授|经理|总监|CEO|CTO))',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # 英文姓名
        ]
        
        # 4. 提取产品实体
        product_patterns = [
            r'([^，。！？\s]{2,20}(?:产品|服务|系统|平台|应用|软件|硬件))',
            r'([A-Z][a-zA-Z0-9\s]{2,30})',  # 英文产品名
        ]
        
        all_patterns = company_patterns + image_patterns + name_patterns + product_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return entities
    
    def _replace_pronouns_with_entities(self, query: str, entities: List[str]) -> str:
        """
        将代词替换为最相关的实体
        
        Args:
            query: 原始查询
            entities: 实体列表
            
        Returns:
            str: 替换后的查询
        """
        if not entities:
            return query
        
        rewritten_query = query
        
        # 根据查询类型选择最合适的实体
        best_entity = self._select_best_entity(query, entities)
        if not best_entity:
            best_entity = entities[0]
        
        # 根据spaCy可用性选择代词替换方式
        if self.nlp and self.spacy_available:
            # 使用spaCy智能检测的代词进行替换
            detected_pronouns = self._detect_pronouns(rewritten_query)
            for pronoun in detected_pronouns:
                if pronoun in rewritten_query:
                    if pronoun == "这家公司" and best_entity:
                        # 特殊处理：将"这家公司"替换为"中芯国际公司"而不是"中芯国际家公司"
                        if best_entity.endswith("公司"):
                            rewritten_query = rewritten_query.replace(pronoun, best_entity, 1)
                        else:
                            rewritten_query = rewritten_query.replace(pronoun, best_entity + "公司", 1)
                    else:
                        rewritten_query = rewritten_query.replace(pronoun, best_entity, 1)
        else:
            # 使用模式匹配进行代词替换
            matched_pronouns = []
            for pronoun in self.pronoun_patterns:
                if pronoun in rewritten_query:
                    matched_pronouns.append(pronoun)
            
            # 按长度排序，长的优先处理
            matched_pronouns.sort(key=len, reverse=True)
            
            # 逐个替换所有匹配的代词
            for pronoun in matched_pronouns:
                if pronoun in rewritten_query:  # 再次检查，因为前面的替换可能影响文本
                    if pronoun == "这家公司" and best_entity:
                        # 特殊处理：将"这家公司"替换为"中芯国际公司"而不是"中芯国际家公司"
                        if best_entity.endswith("公司"):
                            rewritten_query = rewritten_query.replace(pronoun, best_entity, 1)
                        else:
                            rewritten_query = rewritten_query.replace(pronoun, best_entity + "公司", 1)
                    else:
                        rewritten_query = rewritten_query.replace(pronoun, best_entity, 1)
        
        return rewritten_query
    
    def _select_best_entity(self, query: str, entities: List[str]) -> str:
        """
        选择最佳实体
        
        Args:
            query: 查询文本
            entities: 实体列表
            
        Returns:
            str: 最佳匹配的实体
        """
        if not entities:
            return None
        
        # 优先使用基于关键词的匹配（更可靠）
        keyword_result = self._keyword_based_entity_selection(query, entities)
        if keyword_result:
            return keyword_result
        
        # 如果spaCy可用，使用语义相似度作为备选
        if self.nlp:
            try:
                query_doc = self.nlp(query)
                best_entity = None
                best_similarity = 0.0
                
                for entity in entities:
                    entity_doc = self.nlp(entity)
                    similarity = query_doc.similarity(entity_doc)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_entity = entity
                
                # 如果相似度太低，返回第一个实体
                if best_similarity < 0.3:
                    return entities[0] if entities else None
                
                return best_entity
            except Exception as e:
                logger.warning(f"spaCy相似度计算失败: {e}")
        
        # 最后选择第一个实体
        return entities[0] if entities else None
    
    def _keyword_based_entity_selection(self, query: str, entities: List[str]) -> str:
        """
        基于关键词的实体选择
        
        Args:
            query: 查询文本
            entities: 实体列表
            
        Returns:
            str: 最佳匹配的实体
        """
        # 根据查询内容选择实体类型
        if "图" in query:
            # 优先选择包含"图"的实体
            image_entities = [e for e in entities if "图" in e]
            if image_entities:
                return image_entities[0]
        elif any(word in query for word in ["公司", "企业", "集团"]):
            # 优先选择公司类实体，按相关性排序
            company_entities = [e for e in entities if any(word in e for word in ["公司", "集团", "企业", "科技", "技术"])]
            if company_entities:
                # 优先选择较短的实体（通常是公司名，而不是长句子）
                short_entities = [e for e in company_entities if len(e) <= 20]
                if short_entities:
                    return short_entities[0]
                # 其次选择包含"国际"的实体（通常是国际公司）
                international_entities = [e for e in company_entities if "国际" in e]
                if international_entities:
                    return international_entities[0]
                # 最后选择其他公司实体
                return company_entities[0]
        
        return entities[0] if entities else None


# 创建全局实例
_query_rewriter = None

def get_query_rewriter(config_integration=None) -> SpaCyQueryRewriter:
    """
    获取查询重写器实例（单例模式）
    
    Args:
        config_integration: 配置集成管理器实例
        
    Returns:
        SpaCyQueryRewriter: 查询重写器实例
    """
    global _query_rewriter
    if _query_rewriter is None:
        _query_rewriter = SpaCyQueryRewriter(config_integration)
    return _query_rewriter
