'''
程序说明：
## 1. 文本引擎 - 专门处理文本查询
## 2. 支持关键词、语义、向量相似度搜索
## 3. 智能文本排序和相关性计算
## 4. 向后兼容现有文本查询功能
'''

import logging
import time
from typing import Dict, Any, List, Optional, Union
from .base_engine import BaseEngine, QueryType, QueryResult, EngineConfig, EngineStatus


logger = logging.getLogger(__name__)


class TextEngineConfig(EngineConfig):
    """文本引擎专用配置"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "text_engine"
        self.max_results = 10  # 文本查询结果数量
        self.text_similarity_threshold = 0.7  # 文本相似度阈值
        self.keyword_weight = 0.3  # 关键词权重
        self.semantic_weight = 0.4  # 语义权重
        self.vector_weight = 0.3  # 向量权重
        self.enable_semantic_search = True  # 启用语义搜索
        self.enable_vector_search = True  # 启用向量搜索


class TextEngine(BaseEngine):
    """
    文本引擎
    
    专门处理文本查询，支持多种搜索策略
    """
    
    def __init__(self, config: TextEngineConfig, vector_store=None):
        """
        初始化文本引擎
        
        :param config: 文本引擎配置
        :param vector_store: 向量数据库
        """
        super().__init__(config)
        self.vector_store = vector_store
        self.text_docs = {}  # 缓存的文本文档
    
    def _setup_components(self):
        """设置文本引擎组件"""
        if not self.vector_store:
            raise ValueError("向量数据库未提供")
        
        # 加载文本文档
        self._load_text_documents()
    
    def _validate_config(self):
        """验证文本引擎配置"""
        if not isinstance(self.config, TextEngineConfig):
            raise ValueError("配置必须是TextEngineConfig类型")
        
        if self.config.text_similarity_threshold < 0 or self.config.text_similarity_threshold > 1:
            raise ValueError("文本相似度阈值必须在0-1之间")
    
    def _load_text_documents(self):
        """加载文本文档到缓存"""
        if not self.vector_store or not hasattr(self.vector_store, 'docstore'):
            return
        
        try:
            # 从向量数据库加载所有文本文档
            for doc_id, doc in self.vector_store.docstore._dict.items():
                if doc.metadata.get('chunk_type') == 'text':
                    self.text_docs[doc_id] = doc
            
            self.logger.info(f"成功加载 {len(self.text_docs)} 个文本文档")
        except Exception as e:
            self.logger.error(f"加载文本文档失败: {e}")
            self.text_docs = {}
    
    def process_query(self, query: str, **kwargs) -> QueryResult:
        """
        处理文本查询
        
        :param query: 查询文本
        :param kwargs: 额外参数
        :return: 查询结果
        """
        if not self.is_enabled():
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.TEXT,
                results=[],
                total_count=0,
                processing_time=0.0,
                engine_name=self.name,
                metadata={},
                error_message="文本引擎未启用"
            )
        
        start_time = time.time()
        
        try:
            # 执行文本搜索
            results = self._search_texts(query, **kwargs)
            
            # 智能排序
            sorted_results = self._rank_text_results(results, query)
            
            processing_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                query=query,
                query_type=QueryType.TEXT,
                results=sorted_results,
                total_count=len(sorted_results),
                processing_time=processing_time,
                engine_name=self.name,
                metadata={'total_texts': len(self.text_docs)}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"文本查询失败: {e}")
            
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.TEXT,
                results=[],
                total_count=0,
                processing_time=processing_time,
                engine_name=self.name,
                metadata={},
                error_message=str(e)
            )
    
    def _search_texts(self, query: str, **kwargs) -> List[Any]:
        """
        搜索文本
        
        :param query: 查询文本
        :return: 匹配的文本列表
        """
        results = []
        
        # 向量相似度搜索
        if self.config.enable_vector_search and hasattr(self.vector_store, 'similarity_search'):
            try:
                similar_docs = self.vector_store.similarity_search(
                    query, 
                    k=min(20, self.config.max_results * 2)
                )
                
                # 过滤出文本文档并计算分数
                for doc in similar_docs:
                    if doc.metadata.get('chunk_type') == 'text':
                        score = self._calculate_text_score(doc, query)
                        if score >= self.config.text_similarity_threshold:
                            results.append({
                                'doc_id': doc.metadata.get('doc_id', 'unknown'),
                                'doc': doc,
                                'score': score,
                                'match_type': 'vector_search'
                            })
            except Exception as e:
                self.logger.warning(f"向量搜索失败: {e}")
        
        # 关键词搜索
        keyword_results = self._keyword_search(query)
        results.extend(keyword_results)
        
        # 去重
        seen_ids = set()
        unique_results = []
        for result in results:
            if result['doc_id'] not in seen_ids:
                seen_ids.add(result['doc_id'])
                unique_results.append(result)
        
        return unique_results
    
    def _keyword_search(self, query: str) -> List[Any]:
        """关键词搜索"""
        results = []
        keywords = self._extract_keywords(query)
        
        if not keywords:
            return results
        
        for doc_id, doc in self.text_docs.items():
            score = self._calculate_keyword_score(doc, keywords)
            if score >= self.config.text_similarity_threshold:
                results.append({
                    'doc_id': doc_id,
                    'doc': doc,
                    'score': score,
                    'match_type': 'keyword_search'
                })
        
        return results
    
    def _calculate_text_score(self, doc: Any, query: str) -> float:
        """计算文本匹配分数"""
        score = 0.0
        
        # 获取文本内容
        content = doc.page_content if hasattr(doc, 'page_content') else ''
        
        # 计算相似度
        similarity = self._calculate_text_similarity(query, content)
        score += similarity * self.config.semantic_weight
        
        return min(score, 1.0)
    
    def _calculate_keyword_score(self, doc: Any, keywords: List[str]) -> float:
        """计算关键词匹配分数"""
        if not keywords:
            return 0.0
        
        content = doc.page_content if hasattr(doc, 'page_content') else ''
        
        total_score = 0.0
        for keyword in keywords:
            if keyword in content:
                total_score += 1.0
        
        return min(total_score / len(keywords), 1.0)
    
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
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取查询关键词"""
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '吗', '呢', '啊'}
        
        import re
        clean_query = re.sub(r'[^\w\s]', '', query)
        
        words = clean_query.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords
    
    def _rank_text_results(self, results: List[Any], query: str) -> List[Any]:
        """对文本结果进行智能排序"""
        if not results:
            return []
        
        # 按分数排序
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # 限制结果数量
        return sorted_results[:self.config.max_results]
    
    def get_text_by_id(self, text_id: str) -> Optional[Any]:
        """根据ID获取文本"""
        return self.text_docs.get(text_id)
    
    def get_all_texts(self) -> List[Any]:
        """获取所有文本"""
        return list(self.text_docs.values())
    
    def refresh_text_cache(self):
        """刷新文本缓存"""
        self._load_text_documents()
        self.logger.info("文本缓存已刷新")
    
    def get_text_statistics(self) -> Dict[str, Any]:
        """获取文本统计信息"""
        return {
            'total_texts': len(self.text_docs),
            'total_chars': sum(len(doc.page_content) if hasattr(doc, 'page_content') else 0 
                             for doc in self.text_docs.values())
        }
