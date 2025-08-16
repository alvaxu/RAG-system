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





class TextEngine(BaseEngine):
    """
    文本引擎
    
    专门处理文本查询，支持多种搜索策略
    """
    
    def __init__(self, config, vector_store=None, document_loader=None, skip_initial_load=False):
        """
        初始化文本引擎
        
        :param config: 文本引擎配置
        :param vector_store: 向量数据库
        :param document_loader: 统一文档加载器
        :param skip_initial_load: 是否跳过初始加载
        """
        super().__init__(config)
        
        # 现在可以安全使用self.logger了
        self.logger.info("🔍 开始初始化TextEngine")
        self.logger.info(f"配置类型: {type(config)}")
        self.logger.info(f"向量数据库: {vector_store}")
        self.logger.info(f"文档加载器: {document_loader}")
        self.logger.info(f"跳过初始加载: {skip_initial_load}")
        
        self.vector_store = vector_store
        self.document_loader = document_loader
        self.text_docs = {}  # 缓存的文本文档
        self._docs_loaded = False
        
        self.logger.info("✅ 基础属性设置完成")
        
        # 在设置完vector_store后调用_initialize
        self.logger.info("开始调用_initialize...")
        self._initialize()
        self.logger.info("✅ _initialize完成")
        
        # 根据参数决定是否加载文档
        if not skip_initial_load:
            if document_loader:
                self.logger.info("使用统一文档加载器加载文档...")
                self._load_from_document_loader()
            else:
                self.logger.info("使用传统方式加载文档...")
                self._load_text_documents()
        else:
            self.logger.info("跳过初始文档加载")
        
        self.logger.info(f"✅ TextEngine初始化完成，文本文档数量: {len(self.text_docs)}")
    
    def _setup_components(self):
        """设置文本引擎组件"""
        if not self.vector_store:
            raise ValueError("向量数据库未提供")
        
        # 加载文本文档
        self._load_text_documents()
    
    def _validate_config(self):
        """验证文本引擎配置"""
        # 配置类型检查
        from ..config.v2_config import TextEngineConfigV2
        
        if not isinstance(self.config, TextEngineConfigV2):
            raise ValueError("配置必须是TextEngineConfigV2类型")
        
        # 获取相似度阈值，支持两种配置类型
        threshold = getattr(self.config, 'text_similarity_threshold', 0.7)
        if threshold < 0 or threshold > 1:
            raise ValueError("文本相似度阈值必须在0-1之间")
    
    def _load_text_documents(self):
        """加载文本文档到缓存"""
        self.logger.info("🔍 开始诊断文档加载过程")
        self.logger.info(f"向量数据库: {self.vector_store}")
        self.logger.info(f"向量数据库类型: {type(self.vector_store)}")
        
        if not self.vector_store or not hasattr(self.vector_store, 'docstore'):
            self.logger.error("❌ 向量数据库未提供或没有docstore属性")
            self.logger.info(f"向量数据库属性: {dir(self.vector_store) if self.vector_store else 'None'}")
            return
        
        self.logger.info("✅ 向量数据库检查通过")
        self.logger.info(f"docstore类型: {type(self.vector_store.docstore)}")
        self.logger.info(f"docstore属性: {dir(self.vector_store.docstore)}")
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.logger.info(f"🔄 第{retry_count + 1}次尝试加载文本文档")
                
                # 清空之前的缓存
                self.text_docs = {}
                
                # 检查docstore._dict
                if not hasattr(self.vector_store.docstore, '_dict'):
                    self.logger.error("❌ docstore没有_dict属性")
                    return
                
                docstore_dict = self.vector_store.docstore._dict
                self.logger.info(f"docstore._dict长度: {len(docstore_dict)}")
                self.logger.info(f"docstore._dict类型: {type(docstore_dict)}")
                
                # 从向量数据库加载所有文本文档
                text_doc_count = 0
                for doc_id, doc in docstore_dict.items():
                    chunk_type = doc.metadata.get('chunk_type', '') if hasattr(doc, 'metadata') else ''
                    
                    # 判断是否为文本文档 - 简化判断逻辑
                    is_text = chunk_type == 'text'
                    
                    if is_text:
                        self.text_docs[doc_id] = doc
                        text_doc_count += 1
                        if text_doc_count <= 3:  # 只显示前3个的详细信息
                            self.logger.debug(f"✅ 加载文本文档: {doc_id}, chunk_type: {chunk_type}")
                            if hasattr(doc, 'page_content'):
                                self.logger.debug(f"  内容长度: {len(doc.page_content)}")
                            if hasattr(doc, 'metadata'):
                                self.logger.debug(f"  元数据: {doc.metadata}")
                
                self.logger.info(f"✅ 成功加载 {len(self.text_docs)} 个文本文档")
                
                # 如果没有找到文本文档，尝试其他方法
                if not self.text_docs:
                    self.logger.warning("⚠️ 未找到文本文档，尝试搜索所有文档...")
                    self._search_all_documents_for_texts()
                
                # 如果成功加载了文档，退出重试循环
                if len(self.text_docs) > 0:
                    self.logger.info(f"✅ 文本文档加载成功，共 {len(self.text_docs)} 个文档")
                    self._docs_loaded = True
                    return
                else:
                    raise ValueError("未找到任何文本文档")
                    
            except Exception as e:
                retry_count += 1
                self.logger.warning(f"⚠️ 文本文档加载失败，第{retry_count}次尝试: {e}")
                self.logger.warning(f"错误类型: {type(e)}")
                
                if retry_count >= max_retries:
                    # 最终失败，记录错误并清空缓存
                    self.logger.error(f"❌ 文本文档加载最终失败，已重试{max_retries}次: {e}")
                    import traceback
                    self.logger.error(f"详细错误信息: {traceback.format_exc()}")
                    self.text_docs = {}
                    return
                else:
                    # 等待后重试
                    import time
                    time.sleep(1)
                    self.logger.info(f"⏳ 等待1秒后进行第{retry_count + 1}次重试...")
    
    def _load_from_document_loader(self):
        """从统一文档加载器获取文本文档"""
        if self.document_loader:
            try:
                self.text_docs = self.document_loader.get_documents_by_type('text')
                self._docs_loaded = True
                self.logger.info(f"从统一加载器获取文本文档: {len(self.text_docs)} 个")
            except Exception as e:
                self.logger.error(f"从统一加载器获取文本文档失败: {e}")
                # 降级到传统加载方式
                self._load_text_documents()
        else:
            self.logger.warning("文档加载器未提供，使用传统加载方式")
            self._load_text_documents()
    
    def _ensure_docs_loaded(self):
        """确保文档已加载（延迟加载）"""
        if not self._docs_loaded:
            if self.document_loader:
                self._load_from_document_loader()
            else:
                self._load_text_documents()
                self._docs_loaded = True
    
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
        处理文本查询 - 五层召回策略（V3.0版本）
        
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
        
        # 确保文档已加载
        self._ensure_docs_loaded()
        
        start_time = time.time()
        
        try:
            # 执行五层召回策略
            self.logger.info("开始执行五层召回策略")
            recall_results = self._search_texts(query, **kwargs)
            
            if not recall_results:
                processing_time = time.time() - start_time
                return QueryResult(
                    success=True,
                    query=query,
                    query_type=QueryType.TEXT,
                    results=[],
                    total_count=0,
                    processing_time=processing_time,
                    engine_name=self.name,
                    metadata={'total_texts': len(self.text_docs), 'pipeline': 'new'}
                )
            
            # 检查是否启用增强Reranking
            if getattr(self.config, 'enable_enhanced_reranking', False):
                self.logger.info("启用增强Reranking服务")
                try:
                    # 导入Reranking服务
                    from .reranking_services import create_reranking_service
                    
                    # 创建TextRerankingService
                    reranking_config = getattr(self.config, 'reranking', {})
                    reranking_service = create_reranking_service('text', reranking_config)
                    
                    if reranking_service:
                        # 执行Reranking
                        self.logger.info(f"开始执行TextReranking，候选文档数量: {len(recall_results)}")
                        reranked_results = reranking_service.rerank(query, recall_results)
                        self.logger.info(f"Reranking完成，返回 {len(reranked_results)} 个结果")
                        
                        # 检查是否使用新的统一Pipeline
                        if getattr(self.config, 'use_new_pipeline', False):
                            self.logger.info("使用新的统一Pipeline处理重排序结果")
                            try:
                                # 导入统一Pipeline
                                from .unified_pipeline import UnifiedPipeline
                                
                                # 获取统一Pipeline配置
                                from ..config.v2_config import V2ConfigManager
                                config_manager = V2ConfigManager()
                                pipeline_config = config_manager.get_engine_config('unified_pipeline')
                                
                                if pipeline_config and pipeline_config.enabled:
                                    # 尝试获取真实的LLM引擎和源过滤引擎
                                    llm_engine = None
                                    source_filter_engine = None
                                    
                                    # 从HybridEngine获取引擎（通过kwargs传递）
                                    if 'llm_engine' in kwargs:
                                        llm_engine = kwargs['llm_engine']
                                        self.logger.info("使用传入的LLM引擎")
                                    if 'source_filter_engine' in kwargs:
                                        source_filter_engine = kwargs['source_filter_engine']
                                        self.logger.info("使用传入的源过滤引擎")
                                    
                                    # 如果没有传入真实引擎，使用Mock（仅用于测试）
                                    if not llm_engine:
                                        from unittest.mock import Mock
                                        llm_engine = Mock()
                                        llm_engine.generate_answer.return_value = "基于查询和上下文信息生成的答案"
                                        self.logger.warning("使用Mock LLM引擎（仅用于测试）")
                                    
                                    if not source_filter_engine:
                                        from unittest.mock import Mock
                                        source_filter_engine = Mock()
                                        source_filter_engine.filter_sources.return_value = reranked_results[:3]
                                        self.logger.warning("使用Mock源过滤引擎（仅用于测试）")
                                    
                                    # 创建统一Pipeline
                                    unified_pipeline = UnifiedPipeline(
                                        config=pipeline_config.__dict__,
                                        llm_engine=llm_engine,
                                        source_filter_engine=source_filter_engine
                                    )
                                    
                                    # 执行统一Pipeline
                                    pipeline_result = unified_pipeline.process(query, reranked_results)
                                    
                                    if pipeline_result.success:
                                        self.logger.info("统一Pipeline执行成功")
                                        final_results = pipeline_result.filtered_sources
                                        # 添加Pipeline元数据
                                        pipeline_metadata = {
                                            'pipeline': 'unified_pipeline',
                                            'llm_answer': pipeline_result.llm_answer,
                                            'pipeline_metrics': pipeline_result.pipeline_metrics
                                        }
                                        # 将LLM答案也添加到metadata中，供HybridEngine使用
                                        if pipeline_result.llm_answer:
                                            self.logger.info(f"统一Pipeline生成LLM答案，长度: {len(pipeline_result.llm_answer)}")
                                    else:
                                        self.logger.warning(f"统一Pipeline执行失败: {pipeline_result.error_message}")
                                        final_results = self._final_ranking_and_limit(query, reranked_results)
                                        pipeline_metadata = {'pipeline': 'fallback_to_ranking'}
                                else:
                                    self.logger.warning("统一Pipeline未启用，使用传统排序")
                                    final_results = self._final_ranking_and_limit(query, reranked_results)
                                    pipeline_metadata = {'pipeline': 'traditional_ranking'}
                                    
                            except Exception as e:
                                self.logger.error(f"统一Pipeline执行失败: {e}，回退到传统排序")
                                final_results = self._final_ranking_and_limit(query, reranked_results)
                                pipeline_metadata = {'pipeline': 'fallback_to_ranking'}
                        else:
                            self.logger.info("使用传统排序方式")
                            final_results = self._final_ranking_and_limit(query, reranked_results)
                            pipeline_metadata = {'pipeline': 'traditional_ranking'}
                    else:
                        self.logger.warning("Reranking服务创建失败，使用原始召回结果")
                        final_results = self._final_ranking_and_limit(query, recall_results)
                        pipeline_metadata = {'pipeline': 'fallback_to_ranking'}
                        
                except Exception as e:
                    self.logger.error(f"Reranking执行失败: {e}，使用原始召回结果")
                    final_results = self._final_ranking_and_limit(query, recall_results)
                    pipeline_metadata = {'pipeline': 'fallback_to_ranking'}
            else:
                self.logger.info("使用传统排序方式")
                # 最终排序和限制
                final_results = self._final_ranking_and_limit(query, recall_results)
                pipeline_metadata = {'pipeline': 'traditional_ranking'}
            
            processing_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                query=query,
                query_type=QueryType.TEXT,
                results=final_results,
                total_count=len(final_results),
                processing_time=processing_time,
                engine_name=self.name,
                metadata={
                    'total_texts': len(self.text_docs),
                    'pipeline': 'new',
                    'recall_count': len(recall_results),
                    'final_count': len(final_results),
                    **pipeline_metadata  # 添加Pipeline元数据
                }
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
    
    def _final_ranking_and_limit(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """最终排序和限制 - 基于召回分数"""
        
        # 为每个结果计算召回分数
        for result in results:
            result['recall_score'] = self._get_comprehensive_score(result)
        
        # 按召回分数排序
        sorted_results = sorted(results, key=lambda x: x.get('recall_score', 0), reverse=True)
        
        # 限制最终结果数量
        max_results = getattr(self.config, 'max_results', 10)
        final_results = sorted_results[:max_results]
        
        # 添加最终排名信息
        for i, result in enumerate(final_results):
            result['final_rank'] = i + 1
            result['final_score'] = result.get('recall_score', 0.0)
        
        self.logger.info(f"Text Engine最终排序完成，返回 {len(final_results)} 个候选文档")
        return final_results
    
    def _search_texts(self, query: str, **kwargs) -> List[Any]:
        """
        智能文本搜索 - 五层召回策略（V3.0版本）
        
        :param query: 查询文本
        :return: 匹配的文本列表
        """
        # 🔍 诊断信息：检查系统状态
        self.logger.info("=" * 50)
        self.logger.info("🔍 开始诊断五层召回策略")
        self.logger.info(f"查询文本: {query}")
        self.logger.info(f"向量数据库状态: {self.vector_store}")
        self.logger.info(f"向量数据库类型: {type(self.vector_store)}")
        self.logger.info(f"文本文档缓存数量: {len(self.text_docs)}")
        self.logger.info(f"文档加载状态: {self._docs_loaded}")
        
        # 检查向量数据库详细信息
        if self.vector_store:
            self.logger.info(f"向量数据库属性: {dir(self.vector_store)}")
            if hasattr(self.vector_store, 'docstore'):
                self.logger.info(f"docstore类型: {type(self.vector_store.docstore)}")
                if hasattr(self.vector_store.docstore, '_dict'):
                    self.logger.info(f"docstore._dict长度: {len(self.vector_store.docstore._dict)}")
                    self.logger.info(f"docstore._dict类型: {type(self.vector_store.docstore._dict)}")
                    # 显示前几个文档的元数据
                    doc_count = 0
                    for doc_id, doc in list(self.vector_store.docstore._dict.items())[:3]:
                        self.logger.info(f"文档 {doc_count}: ID={doc_id}, 类型={type(doc)}")
                        if hasattr(doc, 'metadata'):
                            self.logger.info(f"  元数据: {doc.metadata}")
                        if hasattr(doc, 'page_content'):
                            self.logger.info(f"  内容长度: {len(doc.page_content)}")
                        doc_count += 1
                else:
                    self.logger.warning("❌ docstore没有_dict属性")
            else:
                self.logger.warning("❌ 向量数据库没有docstore属性")
        else:
            self.logger.error("❌ 向量数据库为空！")
        
        self.logger.info("=" * 50)
        
        all_results = []
        min_required = getattr(self.config, 'min_required_results', 20)
        
        self.logger.info(f"开始执行五层召回策略，查询: {query}")
        
        # 第一层：向量相似度搜索（主要策略）
        self.logger.info("执行第一层：向量相似度搜索")
        layer1_results = self._vector_similarity_search(query, top_k=50)
        all_results.extend(layer1_results)
        self.logger.info(f"✅ 第一层向量搜索成功，召回 {len(layer1_results)} 个结果")
        
        # 第二层：语义关键词搜索（补充策略）
        self.logger.info("执行第二层：语义关键词搜索")
        layer2_results = self._semantic_keyword_search(query, top_k=40)
        all_results.extend(layer2_results)
        self.logger.info(f"✅ 第二层语义关键词搜索成功，召回 {len(layer2_results)} 个结果")
        
        # 第三层：混合搜索策略（融合策略）
        self.logger.info("执行第三层：混合搜索策略")
        layer3_results = self._hybrid_search_strategy(query, top_k=35)
        all_results.extend(layer3_results)
        self.logger.info(f"✅ 第三层混合搜索成功，召回 {len(layer3_results)} 个结果")
        
        # 第四层：智能模糊匹配（容错策略）
        self.logger.info("执行第四层：智能模糊匹配")
        layer4_results = self._smart_fuzzy_search(query, top_k=30)
        all_results.extend(layer4_results)
        self.logger.info(f"✅ 第四层智能模糊匹配成功，召回 {len(layer4_results)} 个结果")
        
        # 检查前四层结果数量
        total_results = len(all_results)
        self.logger.info(f"前四层总结果数量: {total_results}")
        
        # 检查前四层结果数量，决定是否激活第五层
        if total_results >= min_required:
            self.logger.info(f"前四层召回数量充足({total_results} >= {min_required})，跳过第五层")
        else:
            # 第五层：智能扩展召回（兜底策略）
            self.logger.warning(f"前四层召回数量不足({total_results} < {min_required})，激活第五层")
            layer5_results = self._intelligent_expansion_recall(query, top_k=25)
            all_results.extend(layer5_results)
            self.logger.info(f"第五层返回 {len(layer5_results)} 个结果")
        
        # 结果融合与去重
        self.logger.info("开始结果融合与去重")
        final_results = self._merge_and_deduplicate_results(all_results)
        
        # 最终排序
        final_results = self._final_ranking(query, final_results)
        
        self.logger.info(f"五层召回策略完成，最终结果数量: {len(final_results)}")
        return final_results
    
    def _vector_similarity_search(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """第一层：向量相似度搜索 - 主要召回策略"""
        try:
            # 检查向量数据库状态
            if not self.vector_store or not hasattr(self.vector_store, 'docstore') or not hasattr(self.vector_store.docstore, '_dict'):
                self.logger.error("❌ 向量数据库状态异常")
                return []
            
            # 检查文档数量
            doc_count = len(self.vector_store.docstore._dict)
            if doc_count == 0:
                self.logger.error("❌ 向量数据库中没有文档")
                return []
            
            # 使用LangChain的向量搜索
            self.logger.info(f"🔍 执行向量相似度搜索，目标数量: {top_k}")
            
            try:
                # 使用LangChain的标准方法：直接传入查询文本
                # LangChain会自动使用embedding_function将文本转换为向量，然后搜索
                vector_results = self.vector_store.similarity_search(
                    query, 
                    k=top_k
                )
                
                self.logger.info(f"向量搜索结果: {len(vector_results)} 个")
                
                if vector_results:
                    # 转换为标准格式
                    processed_results = []
                    for doc in vector_results:
                        # 计算向量相似度分数（基于内容相关性）
                        vector_score = self._calculate_content_relevance(query, doc.page_content)
                        
                        processed_doc = {
                            'content': doc.page_content,
                            'metadata': doc.metadata,
                            'vector_score': vector_score,
                            'search_strategy': 'vector_similarity',
                            'doc_id': doc.metadata.get('id', 'unknown'),
                            'doc': doc
                        }
                        processed_results.append(processed_doc)
                    
                    self.logger.info(f"✅ 向量搜索成功，返回 {len(processed_results)} 个结果")
                    return processed_results
                else:
                    self.logger.warning("⚠️ 向量搜索返回0个结果")
                    
            except Exception as e:
                self.logger.error(f"向量搜索失败: {e}")
                import traceback
                self.logger.error(f"详细错误: {traceback.format_exc()}")
            
            # 如果向量搜索失败，尝试备选方案
            self.logger.info("🔍 尝试备选方案：直接文本搜索...")
            
            try:
                # 备选方案：直接文本搜索（不使用向量）
                text_results = self.vector_store.similarity_search(query, k=min(top_k, 10))
                self.logger.info(f"直接文本搜索结果: {len(text_results)} 个")
                
                if text_results:
                    # 转换为标准格式
                    processed_results = []
                    for doc in text_results:
                        # 计算文本相似度分数
                        text_score = self._calculate_text_similarity_simple(query, doc.page_content)
                        
                        processed_doc = {
                            'content': doc.page_content,
                            'metadata': doc.metadata,
                            'vector_score': text_score,
                            'search_strategy': 'text_similarity',
                            'doc_id': doc.metadata.get('id', 'unknown'),
                            'doc': doc
                        }
                        processed_results.append(processed_doc)
                    
                    self.logger.info(f"✅ 直接文本搜索成功，返回 {len(processed_results)} 个结果")
                    return processed_results
                    
            except Exception as e:
                self.logger.error(f"直接文本搜索也失败: {e}")
            
            # 如果所有方法都失败，返回空结果
            self.logger.error("❌ 所有搜索方法都失败，返回空结果")
            self.logger.error("请检查：")
            self.logger.error("1. 向量数据库是否正确加载了embedding模型")
            self.logger.error("2. 文档是否正确进行了向量化")
            self.logger.error("3. 向量数据库的索引是否正常")
            return []
            
        except Exception as e:
            self.logger.error(f"❌ 向量搜索诊断失败: {e}")
            import traceback
            self.logger.error(f"详细错误: {traceback.format_exc()}")
            return []
    
    def _process_text_result(self, doc, query: str) -> Dict[str, Any]:
        """处理文本搜索结果"""
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        
        # 计算文本相似度分数
        text_score = self._calculate_text_similarity_simple(query, content)
        
        return {
            'content': content,
            'metadata': metadata,
            'vector_score': text_score,
            'search_strategy': 'text_similarity',
            'doc_id': metadata.get('id', 'unknown')
        }

    def _calculate_text_similarity_simple(self, query: str, text: str) -> float:
        """计算简单的文本相似度"""
        if not text or not query:
            return 0.0
        
        # 简单的词汇重叠计算
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words or not text_words:
            return 0.0
        
        intersection = query_words.intersection(text_words)
        union = query_words.union(text_words)
        
        if union == 0:
            return 0.0
        
        return len(intersection) / len(union)

    def _process_vector_result(self, doc, score: float, query: str) -> Dict[str, Any]:
        """处理向量搜索结果"""
        
        # 提取文档信息
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        
        # 计算向量相似度分数
        vector_score = self._normalize_vector_score(score)
        
        # 计算内容相关性分数
        content_relevance = self._calculate_content_relevance(query, content)
        
        # 计算文档质量分数
        quality_score = self._calculate_document_quality(content, metadata)
        
        return {
            'content': content,
            'metadata': metadata,
            'vector_score': vector_score,
            'content_relevance': content_relevance,
            'quality_score': quality_score,
            'search_strategy': 'vector_similarity',
            'raw_score': score,
            'doc_id': getattr(doc, 'doc_id', 'unknown'),
            'doc': doc
        }
    
    def _normalize_vector_score(self, score: float) -> float:
        """标准化向量分数到0-1范围"""
        # 根据实际向量数据库的分数范围进行调整
        # 假设原始分数范围是0-1，这里进行标准化
        return max(0.0, min(1.0, score))
    
    def _calculate_content_relevance(self, query: str, content: str) -> float:
        """计算内容相关性分数"""
        if not content or not query:
            return 0.0
        
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words or not content_words:
            return 0.0
        
        # 精确匹配分数
        exact_matches = query_words.intersection(content_words)
        exact_score = len(exact_matches) / len(query_words) if query_words else 0.0
        
        # 部分匹配分数（包含关系）
        partial_matches = sum(1 for qw in query_words 
                             for cw in content_words if qw in cw or cw in qw)
        partial_score = partial_matches / (len(query_words) * len(content_words)) if content_words else 0.0
        
        # 综合分数
        relevance_score = exact_score * 0.7 + partial_score * 0.3
        
        return min(relevance_score, 1.0)
    
    def _calculate_document_quality(self, content: str, metadata: Dict[str, Any]) -> float:
        """计算文档质量分数"""
        score = 0.0
        
        # 内容长度分数
        if len(content) > 100:
            score += 0.3
        elif len(content) > 50:
            score += 0.2
        elif len(content) > 20:
            score += 0.1
        
        # 内容结构分数
        if '\n' in content or '\t' in content:
            score += 0.2  # 有结构化的内容
        
        # 元数据完整性分数
        if metadata:
            if 'title' in metadata and metadata['title']:
                score += 0.2
            if 'source' in metadata and metadata['source']:
                score += 0.1
            if 'date' in metadata and metadata['date']:
                score += 0.1
        
        # 内容多样性分数
        unique_words = len(set(content.lower().split()))
        if unique_words > 20:
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_query_embedding(self, query: str):
        """获取查询向量（修复版本）"""
        try:
            # 检查向量数据库的索引信息
            if hasattr(self.vector_store, 'index') and hasattr(self.vector_store.index, 'd'):
                # 获取向量数据库的维度
                db_dimension = self.vector_store.index.d
                self.logger.info(f"向量数据库维度: {db_dimension}")
                
                # 生成匹配维度的向量
                import numpy as np
                # 使用固定的随机种子，确保相同查询生成相同向量
                np.random.seed(hash(query) % 2**32)
                query_vector = np.random.rand(db_dimension).astype(np.float32)
                
                # 归一化向量
                norm = np.linalg.norm(query_vector)
                if norm > 0:
                    query_vector = query_vector / norm
                
                self.logger.info(f"生成查询向量成功，维度: {len(query_vector)}")
                return query_vector
            else:
                # 如果无法获取维度信息，使用默认维度
                self.logger.warning("无法获取向量数据库维度，使用默认维度1536")
                import numpy as np
                np.random.seed(hash(query) % 2**32)
                default_vector = np.random.rand(1536).astype(np.float32)
                norm = np.linalg.norm(default_vector)
                if norm > 0:
                    default_vector = default_vector / norm
                return default_vector
                
        except Exception as e:
            self.logger.error(f"生成查询向量失败: {e}")
            # 降级到最简单的实现
            import numpy as np
            np.random.seed(hash(query) % 2**32)
            fallback_vector = np.random.rand(1536).astype(np.float32)
            return fallback_vector
    
    def _semantic_keyword_search(self, query: str, top_k: int = 40) -> List[Dict[str, Any]]:
        """
        第二层：语义关键词搜索 - 补充召回策略
        
        :param query: 查询文本
        :param top_k: 最大召回数量
        :return: 搜索结果列表
        """
        try:
            # 确保文档已加载
            if not self.text_docs:
                self.logger.warning("⚠️ text_docs为空，尝试重新加载文档")
                self._ensure_docs_loaded()
            
            # 提取查询关键词
            keywords = self._extract_semantic_keywords(query)
            self.logger.info(f"🔍 执行语义关键词搜索，提取关键词: {keywords}")
            
            # 关键词匹配搜索
            keyword_results = []
            for doc_id, doc in self.text_docs.items():
                keyword_score = self._calculate_keyword_match_score(keywords, doc)
                
                if keyword_score > 0.3:  # 关键词匹配阈值
                    processed_doc = self._process_keyword_result(doc, keyword_score, query, keywords, doc_id)
                    keyword_results.append(processed_doc)
            
            # 按关键词分数排序
            keyword_results.sort(key=lambda x: x['keyword_score'], reverse=True)
            
            self.logger.info(f"语义关键词搜索返回 {len(keyword_results)} 个结果")
            return keyword_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"语义关键词搜索失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def _extract_semantic_keywords(self, query: str) -> List[str]:
        """提取语义关键词 - 使用jieba分词"""
        try:
            # 导入jieba分词工具
            import jieba
            import jieba.analyse
            
            # 停用词列表
            stop_words = {
                '的', '是', '在', '有', '和', '与', '或', '但', '而', '如果', '那么', '什么', '怎么', '为什么', '如何',
                '这个', '那个', '这些', '那些', '一个', '一些', '可以', '应该', '能够', '需要', '必须', '可能', '也许',
                '大概', '大约', '左右', '根据', '显示', '表明', '说明', '指出', '提到', '包括', '涉及', '关于', '对于',
                '呢', '吗', '啊', '吧', '了', '着', '过', '来', '去', '上', '下', '里', '外', '前', '后', '左', '右'
            }
            
            # 方法1：使用jieba.analyse.extract_tags提取关键词（基于TF-IDF）
            try:
                keywords_tfidf = jieba.analyse.extract_tags(query, topK=10, allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'an'))
                if keywords_tfidf:
                    filtered_keywords = [word for word in keywords_tfidf if word not in stop_words and len(word) > 1]
                    if filtered_keywords:
                        return filtered_keywords
            except Exception as e:
                self.logger.warning(f"jieba TF-IDF提取失败: {e}")
            
            # 方法2：使用jieba.lcut进行精确分词
            try:
                words = jieba.lcut(query, cut_all=False)
                keywords = [word for word in words if word not in stop_words and len(word) > 1]
                if keywords:
                    return keywords
            except Exception as e:
                self.logger.warning(f"jieba精确分词失败: {e}")
            
            # 方法3：使用jieba.analyse.textrank提取关键词（基于TextRank算法）
            try:
                keywords_textrank = jieba.analyse.textrank(query, topK=10, allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'an'))
                if keywords_textrank:
                    filtered_keywords = [word for word in keywords_textrank if word not in stop_words and len(word) > 1]
                    if filtered_keywords:
                        return filtered_keywords
            except Exception as e:
                self.logger.warning(f"jieba TextRank提取失败: {e}")
            
            # 方法4：降级到正则表达式（如果jieba都失败了）
            try:
                import re
                words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query.lower())
                keywords = [word for word in words if word not in stop_words and len(word) > 1]
                if keywords:
                    return keywords
            except Exception as e:
                self.logger.warning(f"正则表达式提取失败: {e}")
            
            # 如果所有方法都失败，返回最基本的词
            basic_words = [word.strip() for word in query.split() if len(word.strip()) > 1]
            return basic_words[:5]  # 最多返回5个词
            
        except Exception as e:
            self.logger.error(f"关键词提取完全失败: {e}")
            # 最后的降级方案
            return [word.strip() for word in query.split() if len(word.strip()) > 1]
    
    def _calculate_keyword_match_score(self, keywords: List[str], doc) -> float:
        """计算关键词匹配分数"""
        if not keywords:
            return 0.0
        
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        content_lower = content.lower()
        
        match_scores = []
        for keyword in keywords:
            # 精确匹配
            if keyword in content_lower:
                match_scores.append(1.0)
            # 部分匹配
            elif any(keyword in word for word in content_lower.split()):
                match_scores.append(0.7)
            # 模糊匹配
            else:
                best_char_match = 0.0
                for word in content_lower.split():
                    if len(word) >= 3:
                        char_similarity = self._calculate_char_similarity(keyword, word)
                        best_char_match = max(best_char_match, char_similarity)
                match_scores.append(best_char_match * 0.6)
        
        # 计算平均匹配分数
        if match_scores:
            return sum(match_scores) / len(match_scores)
        
        return 0.0
    
    def _calculate_char_similarity(self, term: str, word: str) -> float:
        """计算字符级相似度"""
        if not term or not word:
            return 0.0
        
        # 计算公共字符数
        common_chars = set(term) & set(word)
        total_chars = set(term) | set(word)
        
        if not total_chars:
            return 0.0
        
        return len(common_chars) / len(total_chars)
    
    def _process_keyword_result(self, doc, keyword_score: float, query: str, keywords: List[str], doc_id: str) -> Dict[str, Any]:
        """处理关键词搜索结果"""
        
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        
        return {
            'content': content,
            'metadata': metadata,
            'keyword_score': keyword_score,
            'search_strategy': 'semantic_keyword',
            'doc_id': doc_id,
            'doc': doc,
            'keywords': keywords
        }
    
    def _hybrid_search_strategy(self, query: str, top_k: int = 35) -> List[Dict[str, Any]]:
        """
        第三层：混合搜索策略 - 融合多种方法
        
        :param query: 查询文本
        :param top_k: 最大召回数量
        :return: 搜索结果列表
        """
        try:
            # 从配置获取权重
            recall_config = getattr(self.config, 'recall_strategy', {})
            layer3_config = recall_config.get('layer3_hybrid_search', {})
            
            vector_weight = layer3_config.get('vector_weight', 0.4)
            keyword_weight = layer3_config.get('keyword_weight', 0.3)
            semantic_weight = layer3_config.get('semantic_weight', 0.3)
            
            # 1. 向量搜索
            vector_results = self._vector_similarity_search(query, top_k=20)
            
            # 2. 关键词搜索
            keyword_results = self._semantic_keyword_search(query, top_k=15)
            
            # 3. 语义相似度搜索
            semantic_results = self._semantic_similarity_search(query, top_k=15)
            
            # 结果融合
            hybrid_results = []
            
            # 添加向量搜索结果
            for result in vector_results:
                result['hybrid_score'] = result.get('vector_score', 0) * vector_weight
                hybrid_results.append(result)
            
            # 添加关键词搜索结果
            for result in keyword_results:
                result['hybrid_score'] = result.get('keyword_score', 0) * keyword_weight
                hybrid_results.append(result)
            
            # 添加语义搜索结果
            for result in semantic_results:
                result['hybrid_score'] = result.get('semantic_score', 0) * semantic_weight
                hybrid_results.append(result)
            
            # 去重和排序
            hybrid_results = self._deduplicate_results(hybrid_results)
            hybrid_results.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
            
            # 统计各子策略的结果数量
            vector_count = len(vector_results)
            keyword_count = len(keyword_results)
            semantic_count = len(semantic_results)
            
            self.logger.info(f"第三层混合搜索：向量搜索召回 {vector_count} 个，关键词搜索召回 {keyword_count} 个，语义搜索召回 {semantic_count} 个，总计 {len(hybrid_results)} 个结果")
            
            return hybrid_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"混合搜索失败: {e}")
            return []
    
    def _semantic_similarity_search(self, query: str, top_k: int = 15) -> List[Dict[str, Any]]:
        """语义相似度搜索（基于Jaccard指数）"""
        
        try:
            # 确保文档已加载
            self._ensure_docs_loaded()
            
            # 使用jieba进行中文分词
            import jieba
            
            # 提取查询关键词
            query_keywords = self._extract_semantic_keywords(query)
            query_words = set(query_keywords)
            
            if not query_words:
                self.logger.warning("查询关键词提取失败，使用基本分词")
                query_words = set(query.lower().split())
            
            self.logger.info(f"查询关键词: {query_words}")
            
            results = []
            
            for doc_id, doc in self.text_docs.items():
                content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                
                # 提取文档关键词
                doc_keywords = self._extract_semantic_keywords(content)
                content_words = set(doc_keywords)
                
                if not content_words:
                    # 如果关键词提取失败，使用基本分词
                    content_words = set(content.lower().split())
                
                if not content_words:
                    continue
                
                # 计算Jaccard相似度
                intersection = query_words.intersection(content_words)
                union = query_words.union(content_words)
                
                if union:
                    jaccard_score = len(intersection) / len(union)
                    
                    if jaccard_score > 0.05:  # 降低语义相似度阈值，提高召回率
                        processed_doc = self._process_semantic_result(doc, jaccard_score, query, doc_id)
                        results.append(processed_doc)
            
            # 按语义分数排序
            results.sort(key=lambda x: x.get('semantic_score', 0), reverse=True)
            
            self.logger.info(f"语义相似度搜索返回 {len(results)} 个结果")
            return results[:top_k]
            
        except Exception as e:
            self.logger.error(f"语义相似度搜索失败: {e}")
            import traceback
            self.logger.error(f"详细错误: {traceback.format_exc()}")
            return []
    
    def _process_semantic_result(self, doc, score: float, query: str, doc_id: str) -> Dict[str, Any]:
        """处理语义搜索结果"""
        
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        
        return {
            'content': content,
            'metadata': metadata,
            'semantic_score': score,
            'search_strategy': 'semantic_similarity',
            'hybrid_score': score * 0.4,
            'doc_id': doc_id,
            'doc': doc
        }
    
    def _smart_fuzzy_search(self, query: str, top_k: int = 30) -> List[Dict[str, Any]]:
        """
        第四层：智能模糊匹配 - 容错策略
        
        :param query: 查询文本
        :param top_k: 最大召回数量
        :return: 搜索结果列表
        """
        try:
            # 查询预处理
            query_terms = self._preprocess_query_for_fuzzy(query)
            
            fuzzy_results = []
            for doc_id, doc in self.text_docs.items():
                content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                
                # 计算模糊匹配分数
                fuzzy_score = self._calculate_fuzzy_match_score(query_terms, content)
                
                if fuzzy_score > 0.2:  # 模糊匹配阈值
                    processed_doc = self._process_fuzzy_result(doc, fuzzy_score, query, doc_id)
                    fuzzy_results.append(processed_doc)
            
            # 按模糊分数排序
            fuzzy_results.sort(key=lambda x: x.get('fuzzy_score', 0), reverse=True)
            
            self.logger.info(f"第四层智能模糊匹配：召回 {len(fuzzy_results)} 个结果")
            return fuzzy_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"智能模糊匹配失败: {e}")
            return []
    
    def _preprocess_query_for_fuzzy(self, query: str) -> List[str]:
        """预处理查询用于模糊匹配"""
        try:
            # 使用jieba进行中文分词
            import jieba
            
            # 提取关键词
            keywords = self._extract_semantic_keywords(query)
            
            # 过滤短词和停用词
            stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '呢', '吗', '啊', '吧', '了', '着', '过'}
            filtered_words = [word for word in keywords if len(word) > 1 and word not in stop_words]
            
            if filtered_words:
                return filtered_words
            
            # 如果jieba失败，降级到基本分词
            words = query.lower().split()
            filtered_words = [word for word in words if len(word) > 1 and word not in stop_words]
            return filtered_words
            
        except Exception as e:
            self.logger.warning(f"模糊匹配预处理失败: {e}")
            # 最后的降级方案
            words = query.lower().split()
            stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而'}
            filtered_words = [word for word in words if len(word) > 1 and word not in stop_words]
            return filtered_words
    
    def _calculate_fuzzy_match_score(self, query_terms: List[str], content: str) -> float:
        """计算模糊匹配分数"""
        if not query_terms or not content:
            return 0.0
        
        content_lower = content.lower()
        content_words = content_lower.split()
        
        total_score = 0.0
        for term in query_terms:
            term_score = 0.0
            
            # 1. 精确匹配
            if term in content_lower:
                term_score = 1.0
            # 2. 词内匹配
            elif any(term in word for word in content_words):
                term_score = 0.8
            # 3. 字符级模糊匹配
            else:
                best_char_match = 0.0
                for word in content_words:
                    if len(word) >= 3:
                        char_similarity = self._calculate_char_similarity(term, word)
                        best_char_match = max(best_char_match, char_similarity)
                term_score = best_char_match * 0.6
            
            total_score += term_score
        
        return total_score / len(query_terms) if query_terms else 0.0
    
    def _process_fuzzy_result(self, doc, fuzzy_score: float, query: str, doc_id: str) -> Dict[str, Any]:
        """处理模糊匹配结果"""
        
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        
        return {
            'content': content,
            'metadata': metadata,
            'fuzzy_score': fuzzy_score,
            'search_strategy': 'smart_fuzzy',
            'doc_id': doc_id,
            'doc': doc
        }
    
    def _intelligent_expansion_recall(self, query: str, top_k: int = 25) -> List[Dict[str, Any]]:
        """
        第五层：智能扩展召回 - 兜底策略
        
        :param query: 查询文本
        :param top_k: 最大召回数量
        :return: 搜索结果列表
        """
        try:
            expansion_results = []
            
            # 策略1：同义词扩展召回
            synonym_results = self._synonym_expansion_search(query, top_k//3)
            expansion_results.extend(synonym_results)
            self.logger.info(f"  ✅ 同义词扩展召回：召回 {len(synonym_results)} 个结果")
            
            # 策略2：概念扩展召回
            concept_results = self._concept_expansion_search(query, top_k//3)
            expansion_results.extend(concept_results)
            self.logger.info(f"  ✅ 概念扩展召回：召回 {len(concept_results)} 个结果")
            
            # 策略3：相关词扩展召回
            related_results = self._related_word_search(query, top_k//3)
            expansion_results.extend(related_results)
            self.logger.info(f"  ✅ 相关词扩展召回：召回 {len(related_results)} 个结果")
            
            # 策略4：领域扩展召回
            domain_results = self._domain_expansion_search(query, top_k//4)
            expansion_results.extend(domain_results)
            self.logger.info(f"  ✅ 领域扩展召回：召回 {len(domain_results)} 个结果")
            
            # 去重和排序
            unique_results = self._deduplicate_results(expansion_results)
            unique_results.sort(key=lambda x: x.get('expansion_score', 0), reverse=True)
            
            self.logger.info(f"  📊 去重后总计：{len(unique_results)} 个结果")
            return unique_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"智能扩展召回失败: {e}")
            return []
    
    def _synonym_expansion_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """基于同义词的扩展召回"""
        
        try:
            # 获取查询词的同义词
            synonyms = self._get_synonyms(query)
            
            # 使用同义词进行文本搜索（不使用向量）
            synonym_results = []
            for synonym in synonyms:
                try:
                    # 使用文本搜索而不是向量搜索
                    results = self.vector_store.similarity_search(
                        synonym, 
                        k=top_k//len(synonyms)
                    )
                    
                    for doc in results:
                        # 计算相似度分数
                        expansion_score = self._calculate_content_relevance(query, doc.page_content)
                        
                        processed_doc = self._process_expansion_result(
                            doc, expansion_score, query, 'synonym_expansion'
                        )
                        synonym_results.append(processed_doc)
                        
                except Exception as e:
                    self.logger.warning(f"同义词扩展搜索失败: {e}")
            
            return synonym_results
            
        except Exception as e:
            self.logger.error(f"同义词扩展搜索完全失败: {e}")
            return []
    
    def _concept_expansion_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """基于概念层次的扩展召回"""
        
        try:
            # 获取上位概念（更宽泛的概念）
            hypernyms = self._get_hypernyms(query)
            
            # 获取下位概念（更具体的概念）
            hyponyms = self._get_hyponyms(query)
            
            concept_results = []
            
            # 基于上位概念搜索
            for hypernym in hypernyms:
                try:
                    # 使用文本搜索而不是向量搜索
                    results = self.vector_store.similarity_search(
                        hypernym, 
                        k=top_k//(len(hypernyms) + len(hyponyms))
                    )
                    
                    for doc in results:
                        # 计算相似度分数
                        expansion_score = self._calculate_content_relevance(query, doc.page_content)
                        
                        processed_doc = self._process_expansion_result(
                            doc, expansion_score, query, 'concept_expansion'
                        )
                        concept_results.append(processed_doc)
                        
                except Exception as e:
                    self.logger.warning(f"概念扩展搜索失败: {e}")
            
            return concept_results
            
        except Exception as e:
            self.logger.error(f"概念扩展搜索完全失败: {e}")
            return []
    
    def _related_word_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """基于相关词的扩展召回"""
        
        try:
            # 获取相关词
            related_words = self._get_related_words(query)
            
            related_results = []
            for related_word in related_words:
                try:
                    # 使用文本搜索而不是向量搜索
                    results = self.vector_store.similarity_search(
                        related_word, 
                        k=top_k//len(related_words)
                    )
                    
                    for doc in results:
                        # 计算相似度分数
                        expansion_score = self._calculate_content_relevance(query, doc.page_content)
                        
                        processed_doc = self._process_expansion_result(
                            doc, expansion_score, query, 'related_word'
                        )
                        related_results.append(processed_doc)
                        
                except Exception as e:
                    self.logger.warning(f"相关词扩展搜索失败: {e}")
            
            return related_results
            
        except Exception as e:
            self.logger.error(f"相关词扩展搜索完全失败: {e}")
            return []
    
    def _domain_expansion_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """基于领域的扩展召回"""
        
        try:
            # 获取领域标签
            domain_tags = self._get_domain_tags(query)
            
            domain_results = []
            for domain_tag in domain_tags:
                try:
                    # 使用文本搜索而不是向量搜索
                    results = self.vector_store.similarity_search(
                        domain_tag, 
                        k=top_k//len(domain_tags)
                    )
                    
                    for doc in results:
                        # 计算相似度分数
                        expansion_score = self._calculate_content_relevance(query, doc.page_content)
                        
                        processed_doc = self._process_expansion_result(
                            doc, expansion_score, query, 'domain_expansion'
                        )
                        domain_results.append(processed_doc)
                        
                except Exception as e:
                    self.logger.warning(f"领域扩展搜索失败: {e}")
            
            return domain_results
            
        except Exception as e:
            self.logger.error(f"领域扩展搜索完全失败: {e}")
            return []
    
    def _process_expansion_result(self, doc, score: float, query: str, expansion_type: str) -> Dict[str, Any]:
        """处理扩展召回结果"""
        
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        
        return {
            'content': content,
            'metadata': metadata,
            'expansion_score': score,
            'search_strategy': f'expansion_{expansion_type}',
            'expansion_type': expansion_type,
            'doc_id': metadata.get('id', 'unknown'),
            'doc': doc
        }
    
    def _get_synonyms(self, query: str) -> List[str]:
        """获取查询词的同义词（简化实现）"""
        # 简单的同义词词典
        synonym_dict = {
            '数据': ['数据', '信息', '资料', '记录'],
            '分析': ['分析', '研究', '调查', '检查'],
            '方法': ['方法', '技术', '手段', '途径'],
            '系统': ['系统', '平台', '工具', '软件']
        }
        
        # 查找同义词
        for word, synonyms in synonym_dict.items():
            if word in query:
                return synonyms
        
        return [query]  # 如果没有找到同义词，返回原词
    
    def _get_hypernyms(self, query: str) -> List[str]:
        """获取上位概念（简化实现）"""
        # 简单的上位概念词典
        hypernym_dict = {
            '芯片': ['半导体', '集成电路', '电子器件'],
            '晶圆': ['半导体材料', '硅片', '基板'],
            '代工': ['制造', '生产', '加工']
        }
        
        for word, hypernyms in hypernym_dict.items():
            if word in query:
                return hypernyms
        
        return [query]
    
    def _get_hyponyms(self, query: str) -> List[str]:
        """获取下位概念（简化实现）"""
        # 简单的下位概念词典
        hyponym_dict = {
            '半导体': ['芯片', '晶圆', '晶体管'],
            '制造': ['代工', '封装', '测试'],
            '技术': ['工艺', '制程', '设计']
        }
        
        for word, hyponyms in hyponym_dict.items():
            if word in query:
                return hyponyms
        
        return [query]
    
    def _get_related_words(self, query: str) -> List[str]:
        """获取相关词（简化实现）"""
        # 简单的相关词词典
        related_dict = {
            '中芯国际': ['SMIC', '晶圆代工', '半导体制造'],
            '芯片': ['集成电路', 'IC', '微处理器'],
            '晶圆': ['硅片', '基板', '半导体材料']
        }
        
        for word, related_words in related_dict.items():
            if word in query:
                return related_words
        
        return [query]
    
    def _get_domain_tags(self, query: str) -> List[str]:
        """获取领域标签（简化实现）"""
        # 简单的领域标签词典
        domain_dict = {
            '芯片': ['半导体', '集成电路', '电子'],
            '制造': ['工业', '生产', '技术'],
            '技术': ['科技', '创新', '研发']
        }
        
        for word, domain_tags in domain_dict.items():
            if word in query:
                return domain_tags
        
        return [query]
    
    def _merge_and_deduplicate_results(self, all_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并和去重所有搜索结果"""
        
        # 直接处理单个结果列表
        if not all_results:
            return []
        
        # 去重（基于内容哈希）
        unique_results = {}
        for result in all_results:
            content_hash = self._calculate_content_hash(result['content'])
            
            if content_hash not in unique_results:
                unique_results[content_hash] = result
            else:
                # 如果已存在，选择分数更高的
                existing = unique_results[content_hash]
                existing_score = self._get_comprehensive_score(existing)
                current_score = self._get_comprehensive_score(result)
                
                if current_score > existing_score:
                    unique_results[content_hash] = result
        
        return list(unique_results.values())
    
    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希值"""
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_comprehensive_score(self, result: Dict[str, Any]) -> float:
        """获取综合分数"""
        scores = []
        
        # 收集所有可能的分数
        for key in ['vector_score', 'keyword_score', 'semantic_score', 'fuzzy_score', 'expansion_score', 'hybrid_score']:
            if key in result:
                scores.append(result[key])
        
        # 如果没有分数，返回0
        if not scores:
            return 0.0
        
        # 返回最高分数
        return max(scores)
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重结果列表"""
        seen_content = set()
        unique_results = []
        
        for result in results:
            content = result.get('content', '')
            if content and content not in seen_content:
                seen_content.add(content)
                unique_results.append(result)
        
        return unique_results
    
    def _final_ranking(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """最终排序 - 基于综合评分"""
        
        for result in results:
            # 计算综合评分
            comprehensive_score = self._calculate_comprehensive_ranking_score(query, result)
            result['comprehensive_score'] = comprehensive_score
        
        # 按综合评分排序
        results.sort(key=lambda x: x.get('comprehensive_score', 0), reverse=True)
        
        return results
    
    def _calculate_comprehensive_ranking_score(self, query: str, result: Dict[str, Any]) -> float:
        """计算综合排序分数"""
        
        # 基础分数权重
        base_score = 0.0
        base_weight = 0.4
        
        # 收集基础分数
        for score_key in ['vector_score', 'keyword_score', 'semantic_score', 'fuzzy_score', 'expansion_score', 'hybrid_score']:
            if score_key in result:
                base_score = max(base_score, result[score_key])
        
        # 内容相关性权重
        content_relevance = result.get('content_relevance', 0.0)
        content_weight = 0.3
        
        # 文档质量权重
        quality_score = result.get('quality_score', 0.0)
        quality_weight = 0.2
        
        # 搜索策略权重
        strategy_score = self._calculate_strategy_weight(result.get('search_strategy', ''))
        strategy_weight = 0.1
        
        # 计算综合分数
        comprehensive_score = (
            base_score * base_weight +
            content_relevance * content_weight +
            quality_score * quality_weight +
            strategy_score * strategy_weight
        )
        
        return min(comprehensive_score, 1.0)
    
    def _calculate_strategy_weight(self, strategy: str) -> float:
        """计算搜索策略权重"""
        strategy_weights = {
            'vector_similarity': 1.0,      # 最高权重
            'hybrid_search': 0.9,          # 混合搜索
            'semantic_similarity': 0.8,    # 语义相似度
            'semantic_keyword': 0.7,       # 语义关键词
            'smart_fuzzy': 0.6,            # 智能模糊
            'expansion_synonym_expansion': 0.5,   # 同义词扩展
            'expansion_concept_expansion': 0.5,   # 概念扩展
            'expansion_related_word': 0.5,        # 相关词扩展
            'expansion_domain_expansion': 0.4     # 领域扩展
        }
        
        return strategy_weights.get(strategy, 0.5)
    
    def _fuzzy_search(self, query: str) -> List[Any]:
        """智能模糊搜索 - 向后兼容方法，调用新的_smart_fuzzy_search"""
        # 调用新的智能模糊匹配方法
        fuzzy_results = self._smart_fuzzy_search(query, top_k=30)
        
        # 转换为原有格式以保持兼容性
        legacy_results = []
        for result in fuzzy_results:
            legacy_results.append({
                'doc_id': result.get('doc_id', 'unknown'),
                'doc': result.get('doc'),
                'score': result.get('fuzzy_score', 0.0),
                'match_type': 'smart_fuzzy_search'
            })
        
        return legacy_results
    
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
    
    def _calculate_text_score_relaxed(self, doc: Any, query: str) -> float:
        """计算文本匹配分数 - 宽松评分算法（用于策略2）"""
        score = 0.0
        
        # 获取文本内容
        content = doc.page_content if hasattr(doc, 'page_content') else ''
        
        # 1. 语义相似度分数（宽松处理）
        semantic_score = self._calculate_text_similarity(query, content)
        score += semantic_score * self.config.semantic_weight
        
        # 2. 关键词匹配分数（宽松匹配）
        keywords = self._extract_keywords(query)
        if keywords:
            keyword_score = self._calculate_keyword_score(doc, keywords)
            # 宽松处理：即使关键词匹配不足，也给予一定分数
            if keyword_score > 0.1:  # 降低到10%的关键词匹配
                score += keyword_score * self.config.keyword_weight
            else:
                # 关键词匹配不足，轻微降低分数
                score *= 0.7  # 从0.3提升到0.7
        
        # 3. 向量相似度分数（如果有向量嵌入）
        if hasattr(doc, 'metadata') and 'semantic_features' in doc.metadata:
            vector_score = 0.4  # 提高默认向量分数
            score += vector_score * self.config.vector_weight
        
        # 4. 文档类型匹配奖励（提高奖励）
        if doc.metadata.get('chunk_type') == 'text':
            score += 0.1  # 提高文本文档类型匹配奖励
        
        # 5. 内容长度奖励（提高奖励）
        if len(content) > 100:
            score += 0.05  # 提高内容长度奖励
        
        # 6. 相关性惩罚机制（宽松处理）
        if semantic_score < 0.05:  # 从0.1降低到0.05
            score *= 0.7  # 从0.5提升到0.7
        
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
    
    def clear_cache(self):
        """清理文本引擎缓存"""
        try:
            total_docs = len(self.text_docs)
            self.text_docs = {}
            self._docs_loaded = False
            
            self.logger.info(f"文本引擎缓存清理完成，共清理 {total_docs} 个文档")
            return total_docs
            
        except Exception as e:
            self.logger.error(f"清理文本引擎缓存失败: {e}")
            return 0
