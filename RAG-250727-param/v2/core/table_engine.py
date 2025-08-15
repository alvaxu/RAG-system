'''
程序说明：
## 1. 表格引擎 - 专门处理表格查询
## 2. 支持表格结构、数据内容、列名匹配
## 3. 智能表格排序和相关性计算
## 4. 向后兼容现有表格查询功能
'''

import logging
import time
from typing import Dict, Any, List, Optional, Union
from .base_engine import BaseEngine, QueryType, QueryResult, EngineConfig, EngineStatus


logger = logging.getLogger(__name__)


class TableEngineConfig(EngineConfig):
    """表格引擎专用配置"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "table_engine"
        self.max_results = 15  # 表格查询结果数量
        self.table_similarity_threshold = 0.15  # 进一步降低表格相似度阈值，提高召回率
        self.structure_weight = 0.20  # 表格结构权重
        self.content_weight = 0.40  # 表格内容权重（提高）
        self.column_weight = 0.20  # 列名权重
        self.keyword_weight = 0.20  # 关键词权重（提高）
        self.enable_structure_search = True  # 启用结构搜索
        self.enable_content_search = True  # 启用内容搜索


class TableEngine(BaseEngine):
    """
    表格引擎
    
    专门处理表格查询，支持多种匹配策略
    """
    
    def __init__(self, config: TableEngineConfig, vector_store=None, document_loader=None, skip_initial_load=False):
        """
        初始化表格引擎
        
        :param config: 表格引擎配置
        :param vector_store: 向量数据库
        :param document_loader: 统一文档加载器
        :param skip_initial_load: 是否跳过初始加载
        """
        super().__init__(config)
        self.vector_store = vector_store
        self.document_loader = document_loader
        self.table_docs = {}  # 缓存的表格文档
        self._docs_loaded = False
        
        # 在设置完vector_store后调用_initialize
        self._initialize()
        
        # 根据参数决定是否加载文档
        if not skip_initial_load:
            if document_loader:
                self._load_from_document_loader()
            else:
                self._load_table_documents()
    
    def _setup_components(self):
        """设置表格引擎组件"""
        if not self.vector_store:
            raise ValueError("向量数据库未提供")
        
        # 加载表格文档
        self._load_table_documents()
    
    def _validate_config(self):
        """验证表格引擎配置"""
        # 支持两种配置类型：TableEngineConfig 和 TableEngineConfigV2
        from ..config.v2_config import TableEngineConfigV2
        
        if not isinstance(self.config, (TableEngineConfig, TableEngineConfigV2)):
            raise ValueError("配置必须是TableEngineConfig或TableEngineConfigV2类型")
        
        # 获取相似度阈值，支持两种配置类型
        threshold = getattr(self.config, 'table_similarity_threshold', 0.65)
        if threshold < 0 or threshold > 1:
            raise ValueError("表格相似度阈值必须在0-1之间")
    
    def _load_from_document_loader(self):
        """从统一文档加载器获取表格文档"""
        if self.document_loader:
            try:
                self.table_docs = self.document_loader.get_documents_by_type('table')
                self._docs_loaded = True
                self.logger.info(f"从统一加载器获取表格文档: {len(self.table_docs)} 个")
            except Exception as e:
                self.logger.error(f"从统一加载器获取表格文档失败: {e}")
                # 降级到传统加载方式
                self._load_table_documents()
        else:
            self.logger.warning("文档加载器未提供，使用传统加载方式")
            self._load_table_documents()
    
    def clear_cache(self):
        """清理表格引擎缓存"""
        try:
            total_docs = len(self.table_docs)
            self.table_docs = {}
            self._docs_loaded = False
            
            self.logger.info(f"表格引擎缓存清理完成，共清理 {total_docs} 个文档")
            return total_docs
            
        except Exception as e:
            self.logger.error(f"清理表格引擎缓存失败: {e}")
            return 0
    
    def _ensure_docs_loaded(self):
        """确保文档已加载（延迟加载）"""
        if not self._docs_loaded:
            if self.document_loader:
                self._load_from_document_loader()
            else:
                self._load_table_documents()
                self._docs_loaded = True
    
    def _load_table_documents(self):
        """加载表格文档到缓存"""
        if not self.vector_store or not hasattr(self.vector_store, 'docstore'):
            self.logger.warning("向量数据库未提供或没有docstore属性")
            return
        
        try:
            # 从向量数据库加载所有表格文档
            for doc_id, doc in self.vector_store.docstore._dict.items():
                chunk_type = doc.metadata.get('chunk_type', '')
                table_id = doc.metadata.get('table_id', '')
                table_type = doc.metadata.get('table_type', '')
                
                # 判断是否为表格文档 - 简化判断逻辑
                is_table = chunk_type == 'table'
                
                if is_table:
                    self.table_docs[doc_id] = doc
                    self.logger.debug(f"加载表格文档: {doc_id}, chunk_type: {chunk_type}, table_id: {table_id}")
            
            self.logger.info(f"成功加载 {len(self.table_docs)} 个表格文档")
            
            # 如果没有找到表格文档，尝试其他方法
            if not self.table_docs:
                self.logger.warning("未找到表格文档，尝试搜索所有文档...")
                self._search_all_documents_for_tables()
                
        except Exception as e:
            self.logger.error(f"加载表格文档失败: {e}")
            self.table_docs = {}
    
    def _search_all_documents_for_tables(self):
        """搜索所有文档中的表格内容"""
        try:
            for doc_id, doc in vector_store.docstore._dict.items():
                # 检查文档内容是否包含表格相关信息
                chunk_type = doc.metadata.get('chunk_type', '')
                if chunk_type == 'table':
                    self.table_docs[doc_id] = doc
                    self.logger.debug(f"通过类型识别表格文档: {doc_id}")
        except Exception as e:
            self.logger.error(f"搜索表格文档失败: {e}")
    
    def process_query(self, query: str, **kwargs) -> QueryResult:
        """
        处理表格查询
        
        :param query: 查询文本
        :param kwargs: 额外参数
        :return: 查询结果
        """
        if not self.is_enabled():
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.TABLE,
                results=[],
                total_count=0,
                processing_time=0.0,
                engine_name=self.name,
                metadata={},
                error_message="表格引擎未启用"
            )
        
        # 确保文档已加载
        self._ensure_docs_loaded()
        
        start_time = time.time()
        
        try:
            # 分析查询意图
            intent = self._analyze_table_intent(query)
            
            # 执行表格搜索
            results = self._search_tables(query, intent, **kwargs)
            
            # 智能排序
            sorted_results = self._rank_table_results(results, query, intent)
            
            processing_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                query=query,
                query_type=QueryType.TABLE,
                results=sorted_results,
                total_count=len(sorted_results),
                processing_time=processing_time,
                engine_name=self.name,
                metadata={'intent': intent, 'total_tables': len(self.table_docs)}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"表格查询失败: {e}")
            
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.TABLE,
                results=[],
                total_count=0,
                processing_time=processing_time,
                engine_name=self.name,
                metadata={},
                error_message=str(e)
            )
    
    def _analyze_table_intent(self, query: str) -> Dict[str, Any]:
        """
        分析表格查询意图 - 增强版
        
        :param query: 查询文本
        :return: 意图分析结果
        """
        intent = {
            'type': 'general',  # general, specific, very_specific
            'keywords': [],
            'table_types': [],
            'data_types': [],
            'confidence': 0.0,
            'business_domain': 'general',  # 新增：业务领域
            'query_complexity': 'simple'   # 新增：查询复杂度
        }
        
        # 提取关键词
        keywords = self._extract_keywords(query)
        intent['keywords'] = keywords
        
        # 检测业务领域（简化版，后续根据实际使用调整）
        domain_keywords = {
            '财务': ['营收', '利润', '成本', '费用', '资产', '现金流'],
            '技术': ['技术', '工艺', '设备', '产能', '利用率'],
            '市场': ['市场', '竞争', '客户', '份额', '趋势']
        }
        
        for domain, terms in domain_keywords.items():
            if any(term in query for term in terms):
                intent['business_domain'] = domain
                break
        
        # 检测表格类型
        table_keywords = {
            '营收': 'financial',
            '利润': 'financial',
            '成本': 'financial',
            '费用': 'financial',
            '季度': 'temporal',
            '年度': 'temporal',
            '月度': 'temporal',
            '增长': 'trend',
            '下降': 'trend',
            '对比': 'comparison',
            '分析': 'analysis',
            '数据': 'data',
            '统计': 'statistics',
            '分布': 'distribution',
            '布局': 'layout',
            '产能': 'capacity',
            '利用率': 'utilization'
        }
        
        for keyword, table_type in table_keywords.items():
            if keyword in query:
                intent['table_types'].append(table_type)
        
        # 检测数据类型
        data_keywords = {
            '数字': 'numeric',
            '百分比': 'percentage',
            '日期': 'date',
            '文本': 'text',
            '金额': 'currency',
            '年份': 'year',
            '季度': 'quarter',
            '月份': 'month'
        }
        
        for keyword, data_type in data_keywords.items():
            if keyword in query:
                intent['data_types'].append(data_type)
        
        # 分析查询复杂度
        complexity_factors = {
            'simple': ['表格', '数据', '什么'],
            'medium': ['如何', '哪些', '情况', '表现'],
            'complex': ['分析', '对比', '趋势', '变化', '原因', '影响']
        }
        
        for complexity, factors in complexity_factors.items():
            if any(factor in query for factor in factors):
                intent['query_complexity'] = complexity
                break
        
        # 根据关键词数量和复杂度判断具体程度
        if len(keywords) >= 4 or intent['query_complexity'] == 'complex':
            intent['type'] = 'very_specific'
            intent['confidence'] = 0.9
        elif len(keywords) >= 2 or intent['query_complexity'] == 'medium':
            intent['type'] = 'specific'
            intent['confidence'] = 0.7
        elif len(keywords) >= 1:
            intent['type'] = 'general'
            intent['confidence'] = 0.5
        
        return intent
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取查询关键词"""
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '吗', '呢', '啊'}
        
        import re
        clean_query = re.sub(r'[^\w\s]', '', query)
        
        words = clean_query.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords
    
    def _search_tables(self, query: str, intent: Dict[str, Any], **kwargs) -> List[Any]:
        """
        搜索表格 - 增强版多策略搜索
        
        :param query: 查询文本
        :param intent: 查询意图
        :return: 匹配的表格列表
        """
        results = []
        
        # 策略1: 精确关键词匹配（最高优先级）
        if intent['keywords']:
            for doc_id, doc in self.table_docs.items():
                score = self._calculate_table_score(doc, query, intent)
                if score >= self.config.table_similarity_threshold:
                    results.append({
                        'doc_id': doc_id,
                        'doc': doc,
                        'score': score,
                        'match_type': 'enhanced_keyword_match'
                    })
        
        # 策略2: 业务领域匹配（中优先级）
        if intent['business_domain'] != 'general':
            domain_results = self._search_by_business_domain(query, intent)
            results.extend(domain_results)
        
        # 策略3: 表格类型匹配（中优先级）
        if intent['table_types']:
            type_results = self._search_by_table_type(query, intent)
            results.extend(type_results)
        
        # 策略4: 向量搜索（低优先级，作为后备）
        if not results and hasattr(self.vector_store, 'similarity_search'):
            try:
                similar_docs = self.vector_store.similarity_search(
                    query, 
                    k=min(20, self.config.max_results * 2)
                )
                
                # 过滤出表格文档
                for doc in similar_docs:
                    if doc.metadata.get('chunk_type') == 'table':
                        score = self._calculate_table_score(doc, query, intent)
                        if score >= self.config.table_similarity_threshold * 0.8:  # 降低阈值
                            results.append({
                                'doc_id': doc.metadata.get('doc_id', 'unknown'),
                                'score': score,
                                'match_type': 'vector_search'
                            })
            except Exception as e:
                self.logger.warning(f"向量搜索失败: {e}")
        
        # 策略5: 智能模糊搜索（最低优先级，作为后备）
        if not results:
            fuzzy_results = self._smart_fuzzy_search(query, intent)
            results.extend(fuzzy_results)
        
        # 去重和排序
        unique_results = self._deduplicate_results(results)
        return unique_results
    
    def _search_by_business_domain(self, query: str, intent: Dict[str, Any]) -> List[Any]:
        """按业务领域搜索表格"""
        results = []
        domain = intent['business_domain']
        
        if domain == '半导体':
            domain_keywords = ['晶圆', '芯片', '制程', '代工', '封装', '设计', '集成电路', 'IC']
        elif domain == '财务':
            domain_keywords = ['营收', '利润', '成本', '费用', '资产', '现金流', '毛利率', '净利率']
        elif domain == '市场':
            domain_keywords = ['市场', '竞争', '客户', '供应链', '份额', '地位', '趋势']
        elif domain == '技术':
            domain_keywords = ['技术', '工艺', '设备', '产能', '利用率', '研发', '创新']
        else:
            return results
        
        for doc_id, doc in self.table_docs.items():
            content = doc.page_content if hasattr(doc, 'page_content') else ''
            if any(keyword in content for keyword in domain_keywords):
                score = self._calculate_table_score(doc, query, intent) * 0.8  # 领域匹配给予0.8倍分数
                if score >= self.config.table_similarity_threshold:
                    results.append({
                        'doc_id': doc_id,
                        'doc': doc,
                        'score': score,
                        'match_type': 'business_domain_match'
                    })
        
        return results
    
    def _search_by_table_type(self, query: str, intent: Dict[str, Any]) -> List[Any]:
        """按表格类型搜索"""
        results = []
        table_types = intent['table_types']
        
        for doc_id, doc in self.table_docs.items():
            content = doc.page_content if hasattr(doc, 'page_content') else ''
            content_lower = content.lower()
            
            # 检查表格类型匹配
            type_matched = False
            for table_type in table_types:
                if table_type == 'financial' and any(term in content_lower for term in ['营收', '利润', '成本', '费用']):
                    type_matched = True
                elif table_type == 'temporal' and any(term in content_lower for term in ['时间', '日期', '年份', '年度']):
                    type_matched = True
                elif table_type == 'trend' and any(term in content_lower for term in ['增长', '下降', '变化', '趋势']):
                    type_matched = True
                elif table_type == 'capacity' and any(term in content_lower for term in ['产能', '利用率', '生产']):
                    type_matched = True
            
            if type_matched:
                score = self._calculate_table_score(doc, query, intent) * 0.7  # 类型匹配给予0.7倍分数
                if score >= self.config.table_similarity_threshold:
                    results.append({
                        'doc_id': doc_id,
                        'doc': doc,
                        'score': score,
                        'match_type': 'table_type_match'
                    })
        
        return results
    
    def _deduplicate_results(self, results: List[Any]) -> List[Any]:
        """去重结果，保留最高分数的版本"""
        unique_results = {}
        
        for result in results:
            doc_id = result['doc_id']
            if doc_id not in unique_results or result['score'] > unique_results[doc_id]['score']:
                unique_results[doc_id] = result
        
        return list(unique_results.values())
    
    def _calculate_table_score(self, doc: Any, query: str, intent: Dict[str, Any]) -> float:
        """
        计算表格匹配分数 - 增强版智能综合评分
        
        :param doc: 文档对象
        :param query: 查询文本
        :param intent: 查询意图
        :return: 匹配分数 (0-1)
        """
        score = 0.0
        
        # 获取表格元数据
        content = doc.page_content if hasattr(doc, 'page_content') else ''
        table_structure = doc.metadata.get('table_structure', '')
        column_names = doc.metadata.get('column_names', [])
        
        # 1. 内容匹配分数（核心指标）- 使用增强版算法
        if content and self.config.enable_content_search:
            content_score = self._calculate_enhanced_text_similarity(query, content)
            score += content_score * self.config.content_weight
        
        # 2. 结构匹配分数 - 增强版
        if table_structure and self.config.enable_structure_search:
            structure_score = self._calculate_enhanced_text_similarity(query, table_structure)
            score += structure_score * self.config.structure_weight
        
        # 3. 列名匹配分数 - 增强版
        if column_names and self.config.enable_content_search:
            column_score = self._calculate_enhanced_column_match(query, column_names)
            score += column_score * self.config.column_weight
        
        # 4. 关键词匹配分数（使用配置的权重）
        if intent['keywords']:
            keyword_score = self._calculate_enhanced_keyword_match(doc, intent['keywords'])
            score += keyword_score * self.config.keyword_weight
        
        # 5. 业务领域匹配分数（简化版，后续根据实际使用调整）
        business_score = self._calculate_business_domain_match(query, content)
        score += business_score * 0.08  # 降低业务领域权重，避免过度优化
        
        # 6. 数值模式匹配分数（新增）
        numeric_score = self._calculate_numeric_pattern_match(query, content)
        score += numeric_score * 0.1  # 数值模式权重
        
        # 7. 文档类型匹配奖励
        if doc.metadata.get('chunk_type') == 'table':
            score += 0.08  # 提高表格文档类型匹配奖励
        
        # 8. 内容质量奖励
        if len(content) > 200:  # 内容更丰富
            score += 0.05
        elif len(content) > 100:
            score += 0.03
        
        # 9. 智能相关性调整
        if content_score < 0.1:  # 内容相似度过低
            score *= 0.5  # 更严格的惩罚
        elif content_score > 0.7:  # 内容相似度很高
            score *= 1.2  # 给予奖励
        
        return min(score, 1.0)
    
    def _calculate_enhanced_text_similarity(self, query: str, text: str) -> float:
        """计算增强版文本相似度 - 专门处理表格结构化内容"""
        if not text or not query:
            return 0.0
        
        # 对于表格内容，使用更智能的匹配策略
        query_lower = query.lower()
        text_lower = text.lower()
        
        # 1. 精确匹配（最高优先级）
        if query_lower in text_lower:
            return 0.95
        
        # 2. 直接关键词匹配（高优先级）
        enhanced_keywords = [
            '营收', '利润', '数据', '表格', '统计', '分析', '对比', '增长', '下降', '分布', 
            '产能', '利用率', '地域', '地区', '区域', '营业收入', '净利润', '归母净利润',
            '销售额', '盈利', '生产', '布局', '市场份额', '毛利率', '净利率', '市盈率',
            '每股收益', '资本开支', '研发费用', '管理费用', '销售费用'
        ]
        direct_matches = sum(1 for keyword in enhanced_keywords if keyword in query_lower and keyword in text_lower)
        if direct_matches > 0:
            return min(0.9, 0.6 + direct_matches * 0.15)  # 直接匹配给予更高分
        
        # 3. 业务术语匹配（中高优先级）
        business_terms = {
            '营收': ['营业收入', '收入', '销售额', '营收分布', '地域营收', '营收情况', '营收变化'],
            '利润': ['净利润', '归母净利润', '利润', '盈利', '利润情况', '利润变化'],
            '产能': ['产能利用率', '产能', '利用率', '生产', '生产能力', '产能爬坡'],
            '地域': ['地域', '地区', '区域', '分布', '布局', '全球布局', '地域分布'],
            '财务': ['财务', '财务数据', '财务指标', '财务表现', '财务分析'],
            '技术': ['技术', '技术发展', '技术路线', '制程', '工艺', '先进制程']
        }
        
        for term, synonyms in business_terms.items():
            if term in query_lower:
                # 检查表格内容是否包含相关术语
                term_matches = sum(1 for synonym in synonyms if synonym in text_lower)
                if term_matches > 0:
                    return min(0.8, 0.5 + term_matches * 0.2)  # 业务术语匹配给予更高分数
        
        # 4. 结构化内容匹配
        if '表格类型' in text_lower or '数据表格' in text_lower:
            # 检查查询是否包含表格相关词汇
            table_keywords = ['表格', '数据', '统计', '记录', '列', '行', '表', '图表']
            if any(keyword in query_lower for keyword in table_keywords):
                return 0.7  # 表格相关查询给予更高分数
        
        # 5. 数值模式匹配
        if any(char.isdigit() for char in query):
            # 查询包含数字，检查表格是否包含数值数据
            if any(char.isdigit() for char in text):
                return 0.6  # 数值数据匹配给予中等分数
        
        # 6. 传统词汇重叠计算（作为后备）
        query_words = set(query_lower.split())
        text_words = set(text_lower.split())
        
        if not query_words or not text_words:
            return 0.0
        
        intersection = query_words.intersection(text_words)
        union = query_words.union(text_words)
        
        if union:
            base_similarity = len(intersection) / len(union)
            # 对于表格内容，适当提高分数
            if '表格' in text_lower or '数据' in text_lower:
                base_similarity *= 1.8  # 提高表格内容权重
            return min(1.0, base_similarity)
        
        return 0.0
    
    def _calculate_enhanced_column_match(self, query: str, column_names: List[str]) -> float:
        """计算增强版列名匹配分数"""
        if not column_names:
            return 0.0
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        total_score = 0.0
        
        # 列名匹配权重配置
        column_weights = {
            'exact_match': 1.0,      # 精确匹配
            'partial_match': 0.8,    # 部分匹配
            'synonym_match': 0.7,    # 同义词匹配
            'category_match': 0.6    # 类别匹配
        }
        
        for column in column_names:
            column_lower = column.lower()
            column_words = set(column_lower.split())
            
            # 1. 精确匹配（最高分）
            if query_lower in column_lower or column_lower in query_lower:
                total_score += column_weights['exact_match']
                continue
            
            # 2. 完全包含匹配
            if query_words.issubset(column_words) or column_words.issubset(query_words):
                total_score += column_weights['partial_match']
                continue
            
            # 3. 部分词汇匹配
            intersection = query_words.intersection(column_words)
            if intersection:
                match_ratio = len(intersection) / max(len(query_words), len(column_words))
                if match_ratio >= 0.5:
                    total_score += column_weights['partial_match'] * match_ratio
                else:
                    total_score += column_weights['partial_match'] * match_ratio * 0.5
            
            # 4. 同义词匹配
            synonym_groups = {
                '营收': ['营业收入', '收入', '销售额', '营收'],
                '利润': ['净利润', '归母净利润', '利润', '盈利'],
                '时间': ['时间', '日期', '年份', '年度', '季度', '月份'],
                '地域': ['地域', '地区', '区域', '国家', '城市'],
                '数据': ['数据', '数值', '数量', '金额', '比例', '百分比']
            }
            
            for group_name, synonyms in synonym_groups.items():
                if any(syn in query_lower for syn in synonyms) and any(syn in column_lower for syn in synonyms):
                    total_score += column_weights['synonym_match']
                    break
            
            # 5. 类别匹配
            category_keywords = {
                '财务': ['营收', '利润', '成本', '费用', '资产', '负债', '现金流'],
                '时间': ['时间', '日期', '年份', '年度', '季度', '月份'],
                '地域': ['地域', '地区', '区域', '国家', '城市'],
                '技术': ['技术', '工艺', '制程', '设备', '产能', '利用率']
            }
            
            for category, keywords in category_keywords.items():
                if any(keyword in query_lower for keyword in keywords) and any(keyword in column_lower for keyword in keywords):
                    total_score += column_weights['category_match']
                    break
        
        # 归一化分数
        max_possible_score = len(column_names) * max(column_weights.values())
        if max_possible_score > 0:
            normalized_score = total_score / max_possible_score
            return min(normalized_score, 1.0)
        
        return 0.0
    
    def _calculate_enhanced_keyword_match(self, doc: Any, keywords: List[str]) -> float:
        """计算增强版关键词匹配分数"""
        if not keywords:
            return 0.0
        
        # 获取所有文本字段
        text_fields = [
            doc.page_content if hasattr(doc, 'page_content') else '',
            doc.metadata.get('table_structure', ''),
            ' '.join(doc.metadata.get('column_names', []))
        ]
        
        total_score = 0.0
        keyword_weights = {}  # 记录每个关键词的权重
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            best_score = 0.0
            
            for field in text_fields:
                field_lower = field.lower()
                
                # 1. 精确匹配（最高分）
                if keyword_lower == field_lower:
                    best_score = max(best_score, 1.0)
                    continue
                
                # 2. 完全包含匹配
                if keyword_lower in field_lower or field_lower in keyword_lower:
                    best_score = max(best_score, 0.9)
                    continue
                
                # 3. 词汇边界匹配
                import re
                pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                if re.search(pattern, field_lower):
                    best_score = max(best_score, 0.8)
                    continue
                
                # 4. 部分匹配
                if keyword_lower in field_lower:
                    # 计算匹配位置和长度的影响
                    pos = field_lower.find(keyword_lower)
                    length_ratio = len(keyword_lower) / len(field_lower)
                    if length_ratio > 0.1:  # 关键词占文本比例较高
                        best_score = max(best_score, 0.7)
                    else:
                        best_score = max(best_score, 0.5)
            
            # 记录关键词权重
            keyword_weights[keyword] = best_score
            total_score += best_score
        
        # 计算加权平均分数
        if keywords:
            weighted_score = total_score / len(keywords)
            
            # 额外奖励：如果多个关键词都匹配得很好
            high_match_count = sum(1 for score in keyword_weights.values() if score >= 0.7)
            if high_match_count >= 2:
                weighted_score *= 1.2  # 多关键词高匹配给予奖励
            
            return min(weighted_score, 1.0)
        
        return 0.0
    
    def _calculate_business_domain_match(self, query: str, content: str) -> float:
        """计算业务领域匹配分数（简化版，后续根据实际使用调整）"""
        if not query or not content:
            return 0.0
        
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 只保留最基础的通用术语，避免过度优化
        basic_terms = {
            '财务': ['营收', '利润', '成本', '费用', '资产', '现金流'],
            '技术': ['技术', '工艺', '设备', '产能', '利用率'],
            '市场': ['市场', '竞争', '客户', '份额', '趋势']
        }
        
        total_score = 0.0
        max_possible_score = 0.0
        
        # 简化的匹配逻辑
        for category, terms in basic_terms.items():
            if any(term in query_lower for term in terms):
                max_possible_score += 1.0
                if any(term in content_lower for term in terms):
                    total_score += 1.0
        
        # 计算匹配分数
        if max_possible_score > 0:
            return total_score / max_possible_score
        
        return 0.0
    
    def _calculate_numeric_pattern_match(self, query: str, content: str) -> float:
        """计算数值模式匹配分数"""
        if not query or not content:
            return 0.0
        
        import re
        
        # 提取查询中的数值模式
        query_numbers = re.findall(r'\d+(?:\.\d+)?', query)
        query_percentages = re.findall(r'\d+(?:\.\d+)?%', query)
        query_years = re.findall(r'20\d{2}', query)  # 年份模式
        
        # 提取内容中的数值模式
        content_numbers = re.findall(r'\d+(?:\.\d+)?', content)
        content_percentages = re.findall(r'\d+(?:\.\d+)?%', content)
        content_years = re.findall(r'20\d{2}', content)
        
        total_score = 0.0
        max_possible_score = 0.0
        
        # 1. 数值匹配
        if query_numbers:
            max_possible_score += 1.0
            if content_numbers:
                # 检查是否有数值重叠
                query_num_set = set(query_numbers)
                content_num_set = set(content_numbers)
                if query_num_set.intersection(content_num_set):
                    total_score += 1.0
                elif len(query_num_set.intersection(content_num_set)) > 0:
                    total_score += 0.5
        
        # 2. 百分比匹配
        if query_percentages:
            max_possible_score += 1.0
            if content_percentages:
                total_score += 1.0
        
        # 3. 年份匹配
        if query_years:
            max_possible_score += 1.0
            if content_years:
                # 检查年份范围匹配
                query_year_set = set(query_years)
                content_year_set = set(content_years)
                if query_year_set.intersection(content_year_set):
                    total_score += 1.0
                elif len(query_year_set.intersection(content_year_set)) > 0:
                    total_score += 0.5
        
        # 4. 数值范围匹配
        if query_numbers and content_numbers:
            try:
                query_nums = [float(n) for n in query_numbers]
                content_nums = [float(n) for n in content_numbers]
                
                if query_nums and content_nums:
                    query_min, query_max = min(query_nums), max(query_nums)
                    content_min, content_max = min(content_nums), max(content_nums)
                    
                    # 检查数值范围是否有重叠
                    if query_max >= content_min and query_min <= content_max:
                        total_score += 0.5
                        max_possible_score += 0.5
            except ValueError:
                pass
        
        # 计算最终分数
        if max_possible_score > 0:
            return total_score / max_possible_score
        
        return 0.0
    
    def _rank_table_results(self, results: List[Any], query: str, intent: Dict[str, Any]) -> List[Any]:
        """
        对表格结果进行智能排序
        
        :param results: 搜索结果
        :param query: 查询文本
        :param intent: 查询意图
        :return: 排序后的结果
        """
        if not results:
            return []
        
        # 按分数排序
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # 限制结果数量
        return sorted_results[:self.config.max_results]
    
    def get_table_by_id(self, table_id: str) -> Optional[Any]:
        """根据ID获取表格"""
        return self.table_docs.get(table_id)
    
    def get_all_tables(self) -> List[Any]:
        """获取所有表格"""
        return list(self.table_docs.values())
    
    def refresh_table_cache(self):
        """刷新表格缓存"""
        self._load_table_documents()
        self.logger.info("表格缓存已刷新")
    
    def get_table_statistics(self) -> Dict[str, Any]:
        """获取表格统计信息"""
        return {
            'total_tables': len(self.table_docs),
            'with_structure': len([d for d in self.table_docs.values() 
                                 if d.metadata.get('table_structure')]),
            'with_columns': len([d for d in self.table_docs.values() 
                               if d.metadata.get('column_names')]),
            'total_cells': sum(len(d.page_content.split('\n')) if hasattr(d, 'page_content') else 0 
                             for d in self.table_docs.values())
        }

    def _smart_fuzzy_search(self, query: str, intent: Dict[str, Any]) -> List[Any]:
        """智能模糊搜索 - 只在真正相关时才启用"""
        results = []
        query_lower = query.lower()
        
        # 分析查询意图，判断是否与中芯国际相关
        smic_keywords = ['中芯国际', '中芯', '晶圆', '芯片', '半导体', '集成电路', 'IC', '代工', '营收', '利润', '产能']
        query_has_smic_context = any(keyword in query_lower for keyword in smic_keywords)
        
        # 如果查询与中芯国际无关，不启用模糊搜索
        if not query_has_smic_context:
            self.logger.debug(f"查询 '{query}' 与中芯国际无关，跳过模糊搜索")
            return results
        
        # 提取查询中的关键概念（只针对中芯国际相关内容）
        key_concepts = ['中芯国际', '晶圆', '芯片', '半导体', '技术', '业务', '市场', '发展', '营收', '利润', '产能', '数据', '统计']
        
        for doc_id, doc in self.table_docs.items():
            content = doc.page_content if hasattr(doc, 'page_content') else ''
            content_lower = content.lower()
            
            # 检查是否包含关键概念
            concept_matches = sum(1 for concept in key_concepts if concept in content_lower)
            if concept_matches > 0:
                # 计算相关性分数，要求至少2个概念匹配
                if concept_matches >= 2:
                    score = min(concept_matches * 0.15, 0.8)  # 降低分数，最高0.8
                    results.append({
                        'doc_id': doc_id,
                        'doc': doc,
                        'score': score,
                        'match_type': 'smart_fuzzy_search'
                    })
        
        return results
