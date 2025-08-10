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
        self.table_similarity_threshold = 0.6  # 表格相似度阈值
        self.structure_weight = 0.3  # 表格结构权重
        self.content_weight = 0.4  # 表格内容权重
        self.column_weight = 0.3  # 列名权重
        self.enable_structure_search = True  # 启用结构搜索
        self.enable_content_search = True  # 启用内容搜索


class TableEngine(BaseEngine):
    """
    表格引擎
    
    专门处理表格查询，支持多种匹配策略
    """
    
    def __init__(self, config: TableEngineConfig, vector_store=None):
        """
        初始化表格引擎
        
        :param config: 表格引擎配置
        :param vector_store: 向量数据库
        """
        super().__init__(config)
        self.vector_store = vector_store
        self.table_docs = {}  # 缓存的表格文档
    
    def _setup_components(self):
        """设置表格引擎组件"""
        if not self.vector_store:
            raise ValueError("向量数据库未提供")
        
        # 加载表格文档
        self._load_table_documents()
    
    def _validate_config(self):
        """验证表格引擎配置"""
        if not isinstance(self.config, TableEngineConfig):
            raise ValueError("配置必须是TableEngineConfig类型")
        
        if self.config.table_similarity_threshold < 0 or self.config.table_similarity_threshold > 1:
            raise ValueError("表格相似度阈值必须在0-1之间")
    
    def _load_table_documents(self):
        """加载表格文档到缓存"""
        if not self.vector_store or not hasattr(self.vector_store, 'docstore'):
            return
        
        try:
            # 从向量数据库加载所有表格文档
            for doc_id, doc in self.vector_store.docstore._dict.items():
                if doc.metadata.get('chunk_type') == 'table':
                    self.table_docs[doc_id] = doc
            
            self.logger.info(f"成功加载 {len(self.table_docs)} 个表格文档")
        except Exception as e:
            self.logger.error(f"加载表格文档失败: {e}")
            self.table_docs = {}
    
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
        分析表格查询意图
        
        :param query: 查询文本
        :return: 意图分析结果
        """
        intent = {
            'type': 'general',  # general, specific, very_specific
            'keywords': [],
            'table_types': [],
            'data_types': [],
            'confidence': 0.0
        }
        
        # 提取关键词
        keywords = self._extract_keywords(query)
        intent['keywords'] = keywords
        
        # 检测表格类型
        table_keywords = {
            '营收': 'financial',
            '利润': 'financial',
            '季度': 'temporal',
            '年度': 'temporal',
            '增长': 'trend',
            '下降': 'trend',
            '对比': 'comparison',
            '分析': 'analysis',
            '数据': 'data',
            '统计': 'statistics'
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
            '金额': 'currency'
        }
        
        for keyword, data_type in data_keywords.items():
            if keyword in query:
                intent['data_types'].append(data_type)
        
        # 根据关键词数量判断具体程度
        if len(keywords) >= 3:
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
        搜索表格
        
        :param query: 查询文本
        :param intent: 查询意图
        :return: 匹配的表格列表
        """
        results = []
        
        # 关键词匹配
        if intent['keywords']:
            for doc_id, doc in self.table_docs.items():
                score = self._calculate_table_score(doc, query, intent)
                if score >= self.config.table_similarity_threshold:
                    results.append({
                        'doc_id': doc_id,
                        'doc': doc,
                        'score': score,
                        'match_type': 'keyword_match'
                    })
        
        # 如果没有找到结果，尝试向量搜索
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
                                'doc': doc,
                                'score': score,
                                'match_type': 'vector_search'
                            })
            except Exception as e:
                self.logger.warning(f"向量搜索失败: {e}")
        
        return results
    
    def _calculate_table_score(self, doc: Any, query: str, intent: Dict[str, Any]) -> float:
        """
        计算表格匹配分数
        
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
        
        # 内容匹配分数
        if content and self.config.enable_content_search:
            content_score = self._calculate_text_similarity(query, content)
            score += content_score * self.config.content_weight
        
        # 结构匹配分数
        if table_structure and self.config.enable_structure_search:
            structure_score = self._calculate_text_similarity(query, table_structure)
            score += structure_score * self.config.structure_weight
        
        # 列名匹配分数
        if column_names and self.config.enable_content_search:
            column_score = self._calculate_column_match(query, column_names)
            score += column_score * self.config.column_weight
        
        # 关键词匹配分数
        if intent['keywords']:
            keyword_score = self._calculate_keyword_match(doc, intent['keywords'])
            score += keyword_score * 0.2  # 关键词权重
        
        return min(score, 1.0)
    
    def _calculate_text_similarity(self, query: str, text: str) -> float:
        """计算文本相似度"""
        if not text or not query:
            return 0.0
        
        # 简单的词汇重叠计算
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words or not text_words:
            return 0.0
        
        intersection = query_words.intersection(text_words)
        union = query_words.union(text_words)
        
        if union:
            return len(intersection) / len(union)
        return 0.0
    
    def _calculate_column_match(self, query: str, column_names: List[str]) -> float:
        """计算列名匹配分数"""
        if not column_names:
            return 0.0
        
        query_words = set(query.lower().split())
        total_score = 0.0
        
        for column in column_names:
            column_words = set(column.lower().split())
            if query_words.intersection(column_words):
                total_score += 1.0
        
        return min(total_score / len(column_names), 1.0)
    
    def _calculate_keyword_match(self, doc: Any, keywords: List[str]) -> float:
        """计算关键词匹配分数"""
        if not keywords:
            return 0.0
        
        # 获取所有文本字段
        text_fields = [
            doc.page_content if hasattr(doc, 'page_content') else '',
            doc.metadata.get('table_structure', ''),
            ' '.join(doc.metadata.get('column_names', []))
        ]
        
        total_score = 0.0
        for keyword in keywords:
            for field in text_fields:
                if keyword in field:
                    total_score += 1.0
                    break
        
        return min(total_score / len(keywords), 1.0)
    
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
