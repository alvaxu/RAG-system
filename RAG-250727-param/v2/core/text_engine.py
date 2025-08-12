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
        self.text_similarity_threshold = 0.3  # 提高相似度阈值，确保相关性
        self.keyword_weight = 0.5  # 关键词权重
        self.semantic_weight = 0.3  # 语义权重
        self.vector_weight = 0.2  # 向量权重
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
        
        # 在设置完vector_store后调用_initialize
        self._initialize()
        
        # 加载文本文档
        self._load_text_documents()
    
    def _setup_components(self):
        """设置文本引擎组件"""
        if not self.vector_store:
            raise ValueError("向量数据库未提供")
        
        # 加载文本文档
        self._load_text_documents()
    
    def _validate_config(self):
        """验证文本引擎配置"""
        # 支持两种配置类型：TextEngineConfig 和 TextEngineConfigV2
        from ..config.v2_config import TextEngineConfigV2
        
        if not isinstance(self.config, (TextEngineConfig, TextEngineConfigV2)):
            raise ValueError("配置必须是TextEngineConfig或TextEngineConfigV2类型")
        
        # 获取相似度阈值，支持两种配置类型
        threshold = getattr(self.config, 'text_similarity_threshold', 0.7)
        if threshold < 0 or threshold > 1:
            raise ValueError("文本相似度阈值必须在0-1之间")
    
    def _load_text_documents(self):
        """加载文本文档到缓存"""
        if not self.vector_store or not hasattr(self.vector_store, 'docstore'):
            self.logger.warning("向量数据库未提供或没有docstore属性")
            return
        
        try:
            # 从向量数据库加载所有文本文档
            for doc_id, doc in self.vector_store.docstore._dict.items():
                chunk_type = doc.metadata.get('chunk_type', '')
                
                # 判断是否为文本文档 - 简化判断逻辑
                is_text = chunk_type == 'text'
                
                if is_text:
                    self.text_docs[doc_id] = doc
                    self.logger.debug(f"加载文本文档: {doc_id}, chunk_type: {chunk_type}")
            
            self.logger.info(f"成功加载 {len(self.text_docs)} 个文本文档")
            
            # 如果没有找到文本文档，尝试其他方法
            if not self.text_docs:
                self.logger.warning("未找到文本文档，尝试搜索所有文档...")
                self._search_all_documents_for_texts()
                
        except Exception as e:
            self.logger.error(f"加载文本文档失败: {e}")
            self.text_docs = {}
    
    def _search_all_documents_for_texts(self):
        """搜索所有文档中的文本内容"""
        try:
            for doc_id, doc in self.vector_store.docstore._dict.items():
                # 检查文档内容是否包含文本信息
                chunk_type = doc.metadata.get('chunk_type', '')
                if chunk_type == 'text' or chunk_type == '':
                    self.text_docs[doc_id] = doc
                    self.logger.debug(f"通过类型识别文本文档: {doc_id}")
        except Exception as e:
            self.logger.error(f"搜索文本文档失败: {e}")
    
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
        智能文本搜索 - V2.0增强版（严格类型过滤）
        
        :param query: 查询文本
        :return: 匹配的文本列表
        """
        results = []
        
        # 策略1: 优先使用已加载的文本文档进行搜索
        if self.text_docs:
            try:
                # 对文本文档进行向量相似度搜索
                for doc_id, doc in self.text_docs.items():
                    score = self._calculate_text_score(doc, query)
                    if score >= self.config.text_similarity_threshold:
                        results.append({
                            'doc_id': doc_id,
                            'doc': doc,
                            'score': score,
                            'match_type': 'text_doc_search'
                        })
                
                self.logger.debug(f"文本文档搜索找到 {len(results)} 个结果")
            except Exception as e:
                self.logger.warning(f"文本文档搜索失败: {e}")
        
        # 策略2: 如果文本文档搜索没有结果，尝试向量存储搜索（但严格过滤类型）
        if not results and hasattr(self.vector_store, 'similarity_search'):
            try:
                # 使用向量存储的相似度搜索，但严格过滤文档类型
                similar_docs = self.vector_store.similarity_search(
                    query, 
                    k=min(50, self.config.max_results * 5)  # 增加搜索范围
                )
                
                # 严格过滤：只处理文本文档
                for doc in similar_docs:
                    chunk_type = doc.metadata.get('chunk_type', '')
                    
                    # 只处理文本文档，排除图片和表格
                    if chunk_type == 'text':
                        score = self._calculate_text_score(doc, query)
                        if score >= self.config.text_similarity_threshold:
                            results.append({
                                'doc_id': doc.metadata.get('doc_id', doc.metadata.get('id', 'unknown')),
                                'doc': doc,
                                'score': score,
                                'match_type': 'vector_search_filtered'
                            })
                
                self.logger.debug(f"向量搜索（类型过滤后）找到 {len(results)} 个结果")
            except Exception as e:
                self.logger.warning(f"向量搜索失败: {e}")
        
        # 策略3: 如果仍然没有结果，尝试关键词搜索
        if not results:
            keyword_results = self._keyword_search(query)
            results.extend(keyword_results)
            self.logger.debug(f"关键词搜索找到 {len(keyword_results)} 个结果")
        
        # 策略4: 如果还是没有结果，尝试模糊匹配（但只针对文本文档）
        if not results:
            fuzzy_results = self._fuzzy_search(query)
            results.extend(fuzzy_results)
            self.logger.debug(f"模糊搜索找到 {len(fuzzy_results)} 个结果")
        
        # 策略5: 如果还是没有结果，降低阈值重新搜索（但保持类型过滤）
        if not results and self.config.text_similarity_threshold > 0.05:
            self.logger.debug("降低阈值重新搜索（保持类型过滤）...")
            original_threshold = self.config.text_similarity_threshold
            self.config.text_similarity_threshold = 0.05
            
            # 重新执行向量搜索，但严格过滤类型
            if hasattr(self.vector_store, 'similarity_search'):
                try:
                    similar_docs = self.vector_store.similarity_search(query, k=30)
                    for doc in similar_docs:
                        chunk_type = doc.metadata.get('chunk_type', '')
                        if chunk_type == 'text':  # 只处理文本文档
                            score = self._calculate_text_score(doc, query)
                            if score >= self.config.text_similarity_threshold:
                                results.append({
                                    'doc_id': doc.metadata.get('doc_id', doc.metadata.get('id', 'unknown')),
                                    'doc': doc,
                                    'score': score,
                                    'match_type': 'low_threshold_search_filtered'
                                })
                except Exception as e:
                    self.logger.warning(f"低阈值搜索失败: {e}")
            
            # 恢复原始阈值
            self.config.text_similarity_threshold = original_threshold
        
        # 去重和排序
        seen_ids = set()
        unique_results = []
        for result in results:
            doc_id = result.get('doc_id', 'unknown')
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_results.append(result)
        
        # 按分数排序
        unique_results.sort(key=lambda x: x['score'], reverse=True)
        
        self.logger.debug(f"最终去重后得到 {len(unique_results)} 个结果")
        return unique_results
    
    def _fuzzy_search(self, query: str) -> List[Any]:
        """智能模糊搜索 - 只在真正相关时才启用"""
        results = []
        query_lower = query.lower()
        
        # 分析查询意图，判断是否与中芯国际相关
        smic_keywords = ['中芯国际', '中芯', '晶圆', '芯片', '半导体', '集成电路', 'IC', '代工']
        query_has_smic_context = any(keyword in query_lower for keyword in smic_keywords)
        
        # 如果查询与中芯国际无关，不启用模糊搜索
        if not query_has_smic_context:
            self.logger.debug(f"查询 '{query}' 与中芯国际无关，跳过模糊搜索")
            return results
        
        # 提取查询中的关键概念（只针对中芯国际相关内容）
        key_concepts = ['中芯国际', '晶圆', '芯片', '半导体', '技术', '业务', '市场', '发展', '营收', '利润']
        
        for doc_id, doc in self.text_docs.items():
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
        """计算文本匹配分数 - 智能综合评分（严格相关性判断）"""
        score = 0.0
        
        # 获取文本内容
        content = doc.page_content if hasattr(doc, 'page_content') else ''
        
        # 1. 语义相似度分数（核心指标）
        semantic_score = self._calculate_text_similarity(query, content)
        score += semantic_score * self.config.semantic_weight
        
        # 2. 关键词匹配分数（严格匹配）
        keywords = self._extract_keywords(query)
        if keywords:
            keyword_score = self._calculate_keyword_score(doc, keywords)
            # 关键词匹配必须达到一定阈值才给分
            if keyword_score > 0.3:  # 至少30%的关键词匹配
                score += keyword_score * self.config.keyword_weight
            else:
                # 关键词匹配不足，大幅降低分数
                score *= 0.3
        
        # 3. 向量相似度分数（如果有向量嵌入）
        if hasattr(doc, 'metadata') and 'semantic_features' in doc.metadata:
            vector_score = 0.3  # 降低默认向量分数
            score += vector_score * self.config.vector_weight
        
        # 4. 文档类型匹配奖励（降低奖励）
        if doc.metadata.get('chunk_type') == 'text':
            score += 0.05  # 降低文本文档类型匹配奖励
        
        # 5. 内容长度奖励（降低奖励）
        if len(content) > 100:
            score += 0.02  # 降低内容长度奖励
        
        # 6. 相关性惩罚机制
        if semantic_score < 0.1:  # 语义相似度过低
            score *= 0.5  # 大幅降低分数
        
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
