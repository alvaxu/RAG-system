#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 图片引擎核心实现 - V2.0版本
## 2. 实现五层召回策略：向量搜索、关键词匹配、混合召回、模糊匹配、查询扩展
## 3. 集成向量搜索和关键词搜索
## 4. 支持图片描述和元数据匹配
## 5. 为后续ImageRerankingService和统一Pipeline集成做准备
"""

import logging
import time
import re
from typing import List, Dict, Any, Optional, Set
from ..core.base_engine import BaseEngine
from ..core.base_engine import EngineConfig
from ..core.base_engine import QueryResult, QueryType

logger = logging.getLogger(__name__)


class ImageEngine(BaseEngine):
    """
    图片引擎 - V2.0版本
    
    专门处理图片查询，实现五层召回策略
    """
    
    def __init__(self, config, vector_store=None, document_loader=None, skip_initial_load=False):
        """
        初始化图片引擎
        
        :param config: 图片引擎配置
        :param vector_store: 向量数据库
        :param document_loader: 文档加载器
        :param skip_initial_load: 是否跳过初始文档加载
        """
        super().__init__(config)
        self.vector_store = vector_store
        self.document_loader = document_loader
        self.image_docs = []  # 图片文档缓存
        self._docs_loaded = False
        
        if not skip_initial_load:
            self._load_documents()
    
    def _load_documents(self):
        """加载图片文档"""
        if self._docs_loaded:
            return
            
        try:
            if self.document_loader:
                # 使用统一文档加载器
                # 获取image和image_text两种类型的文档
                image_docs = self.document_loader.get_documents_by_type('image')
                image_text_docs = self.document_loader.get_documents_by_type('image_text')
                
                # 合并两种类型的文档
                self.image_docs = []
                
                # 添加image类型的文档
                if image_docs:
                    if isinstance(image_docs, dict):
                        self.image_docs.extend(image_docs.values())
                    else:
                        self.image_docs.extend(image_docs)
                    logger.info(f"加载image文档: {len(image_docs)} 个")
                
                # 添加image_text类型的文档
                if image_text_docs:
                    if isinstance(image_text_docs, dict):
                        self.image_docs.extend(image_text_docs.values())
                    else:
                        self.image_docs.extend(image_text_docs)
                    logger.info(f"加载image_text文档: {len(image_text_docs)} 个")
                
                logger.info(f"图片引擎总共加载了 {len(self.image_docs)} 个图片相关文档")
                
            elif self.vector_store:
                # 从向量数据库加载
                self.image_docs = self.vector_store.get_image_documents()
                logger.info(f"从向量数据库加载了 {len(self.image_docs)} 个图片文档")
            else:
                logger.warning("未提供文档加载器或向量数据库，图片引擎将无法工作")
                return
                
            self._docs_loaded = True
            
        except Exception as e:
            logger.error(f"加载图片文档失败: {e}")
            self._docs_loaded = False
    
    def _load_from_document_loader(self):
        """从统一文档加载器获取图片文档"""
        if self.document_loader:
            try:
                # 获取image和image_text两种类型的文档
                image_docs = self.document_loader.get_documents_by_type('image')
                image_text_docs = self.document_loader.get_documents_by_type('image_text')
                
                # 合并两种类型的文档
                self.image_docs = []
                
                # 添加image类型的文档
                if image_docs:
                    if isinstance(image_docs, dict):
                        self.image_docs.extend(image_docs.values())
                    else:
                        self.image_docs.extend(image_docs)
                    logger.info(f"从统一加载器获取image文档: {len(image_docs)} 个")
                
                # 添加image_text类型的文档
                if image_text_docs:
                    if isinstance(image_text_docs, dict):
                        self.image_docs.extend(image_text_docs.values())
                    else:
                        self.image_docs.extend(image_text_docs)
                    logger.info(f"从统一加载器获取image_text文档: {len(image_text_docs)} 个")
                
                self._docs_loaded = True
                logger.info(f"从统一加载器总共获取图片相关文档: {len(self.image_docs)} 个")
                
            except Exception as e:
                logger.error(f"从统一加载器获取图片文档失败: {e}")
                # 降级到传统加载方式
                self._load_from_vector_store()
        else:
            logger.warning("文档加载器未提供，使用传统加载方式")
            self._load_from_vector_store()
    
    def _load_from_vector_store(self):
        """从向量数据库加载图片文档"""
        if not self.vector_store or not hasattr(self.vector_store, 'docstore'):
            logger.error("❌ 向量数据库未提供或没有docstore属性")
            return
        
        try:
            logger.info("✅ 向量数据库检查通过")
            logger.info(f"docstore类型: {type(self.vector_store.docstore)}")
            
            # 清空之前的缓存
            self.image_docs = []
            
            # 检查docstore._dict
            if not hasattr(self.vector_store.docstore, '_dict'):
                logger.error("❌ docstore没有_dict属性")
                return
            
            docstore_dict = self.vector_store.docstore._dict
            logger.info(f"docstore._dict长度: {len(docstore_dict)}")
            
            # 从向量数据库加载所有图片文档
            image_doc_count = 0
            for doc_id, doc in docstore_dict.items():
                chunk_type = doc.metadata.get('chunk_type', '') if hasattr(doc, 'metadata') else ''
                
                # 判断是否为图片文档
                is_image = chunk_type in ['image', 'image_text']
                
                if is_image:
                    self.image_docs.append(doc)
                    image_doc_count += 1
                    if image_doc_count <= 3:  # 只显示前3个的详细信息
                        logger.debug(f"✅ 加载图片文档: {doc_id}, chunk_type: {chunk_type}")
                        if hasattr(doc, 'metadata'):
                            logger.debug(f"  元数据: {doc.metadata}")
            
            logger.info(f"✅ 成功加载 {len(self.image_docs)} 个图片文档")
            self._docs_loaded = True
            
        except Exception as e:
            logger.error(f"从向量数据库加载图片文档失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            self.image_docs = []
    
    def _ensure_docs_loaded(self):
        """确保文档已加载（延迟加载）"""
        if not self._docs_loaded:
            if self.document_loader:
                self._load_from_document_loader()
            else:
                self._load_from_vector_store()
                self._docs_loaded = True
    
    def _validate_config(self):
        """验证图片引擎配置"""
        # 配置类型检查
        from ..config.v2_config import ImageEngineConfigV2
        
        if not isinstance(self.config, ImageEngineConfigV2):
            raise ValueError("配置必须是ImageEngineConfigV2类型")
        
        # 获取相似度阈值，支持两种配置类型
        threshold = getattr(self.config, 'image_similarity_threshold', 0.7)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            raise ValueError("图片相似度阈值必须在0-1之间")
    
    def _setup_components(self):
        """设置引擎组件 - 实现抽象方法"""
        # 检查文档是否已加载，如果没有则加载
        if not self._docs_loaded and self.document_loader:
            try:
                self._load_documents()
                logger.info(f"图片引擎在_setup_components中加载了 {len(self.image_docs)} 个文档")
            except Exception as e:
                logger.error(f"图片引擎在_setup_components中加载文档失败: {e}")
                raise
    
    def process_query(self, query: str, **kwargs) -> QueryResult:
        """
        处理图片查询 - 使用五层召回策略 + ImageRerankingService + 统一Pipeline
        
        :param query: 查询文本
        :param kwargs: 其他参数
        :return: 搜索结果
        """
        # 确保文档已加载（延迟加载）
        self._ensure_docs_loaded()
        
        if not self.image_docs:
            logger.warning("图片引擎没有可用的文档")
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.IMAGE,
                results=[],
                total_count=0,
                processing_time=0.0,
                engine_name=self.name,
                metadata={},
                error_message="图片引擎没有可用的文档"
            )
        
        start_time = time.time()
        
        try:
            # 执行五层召回策略
            recall_results = self._search_images_with_five_layer_recall(query)
            
            # 检查是否启用增强Reranking
            if getattr(self.config, 'enable_enhanced_reranking', False):
                logger.info("启用增强Reranking服务")
                try:
                    # 导入Reranking服务
                    from .reranking_services import create_reranking_service
                    
                    # 创建ImageRerankingService
                    reranking_config = getattr(self.config, 'reranking', {})
                    reranking_service = create_reranking_service('image', reranking_config)
                    
                    if reranking_service:
                        # 执行Reranking
                        logger.info(f"开始执行ImageReranking，候选文档数量: {len(recall_results)}")
                        reranked_results = reranking_service.rerank(query, recall_results)
                        logger.info(f"Reranking完成，返回 {len(reranked_results)} 个结果")
                        
                        # 检查是否使用新的统一Pipeline
                        if getattr(self.config, 'use_new_pipeline', False):
                            logger.info("使用新的统一Pipeline处理重排序结果")
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
                                        logger.info("使用传入的LLM引擎")
                                    if 'source_filter_engine' in kwargs:
                                        source_filter_engine = kwargs['source_filter_engine']
                                        logger.info("使用传入的源过滤引擎")
                                    
                                    # 如果没有传入真实引擎，使用Mock（仅用于测试）
                                    if not llm_engine:
                                        from unittest.mock import Mock
                                        llm_engine = Mock()
                                        llm_engine.generate_answer.return_value = "基于查询和图片信息生成的答案"
                                        logger.warning("使用Mock LLM引擎（仅用于测试）")
                                    
                                    if not source_filter_engine:
                                        from unittest.mock import Mock
                                        source_filter_engine = Mock()
                                        source_filter_engine.filter_sources.return_value = reranked_results[:3]
                                        logger.warning("使用Mock源过滤引擎（仅用于测试）")
                                    
                                    # 创建统一Pipeline
                                    unified_pipeline = UnifiedPipeline(
                                        config=pipeline_config.__dict__,
                                        llm_engine=llm_engine,
                                        source_filter_engine=source_filter_engine
                                    )
                                    
                                    # 执行统一Pipeline
                                    pipeline_result = unified_pipeline.process(query, reranked_results)
                                    
                                    if pipeline_result.success:
                                        logger.info("统一Pipeline执行成功")
                                        final_results = pipeline_result.filtered_sources
                                        # 添加Pipeline元数据
                                        pipeline_metadata = {
                                            'pipeline': 'unified_pipeline',
                                            'llm_answer': pipeline_result.llm_answer,
                                            'pipeline_metrics': pipeline_result.pipeline_metrics
                                        }
                                        # 将LLM答案也添加到metadata中，供HybridEngine使用
                                        if pipeline_result.llm_answer:
                                            logger.info(f"统一Pipeline生成LLM答案，长度: {len(pipeline_result.llm_answer)}")
                                    else:
                                        logger.warning(f"统一Pipeline执行失败: {pipeline_result.error_message}")
                                        final_results = self._final_ranking_and_limit(query, reranked_results)
                                        pipeline_metadata = {'pipeline': 'fallback_to_ranking'}
                                else:
                                    logger.warning("统一Pipeline未启用，使用传统排序")
                                    final_results = self._final_ranking_and_limit(query, reranked_results)
                                    pipeline_metadata = {'pipeline': 'traditional_ranking'}
                                    
                            except Exception as e:
                                logger.error(f"统一Pipeline执行失败: {e}，回退到传统排序")
                                final_results = self._final_ranking_and_limit(query, reranked_results)
                                pipeline_metadata = {'pipeline': 'fallback_to_ranking'}
                        else:
                            logger.info("使用传统排序方式")
                            final_results = self._final_ranking_and_limit(query, reranked_results)
                            pipeline_metadata = {'pipeline': 'traditional_ranking'}
                    else:
                        logger.warning("ImageRerankingService创建失败，使用原始结果")
                        final_results = recall_results
                        pipeline_metadata = {'pipeline': 'no_reranking'}
                except Exception as e:
                    logger.error(f"ImageReranking执行失败: {e}，使用原始结果")
                    final_results = recall_results
                    pipeline_metadata = {'pipeline': 'reranking_failed'}
            else:
                logger.info("增强Reranking未启用，使用原始结果")
                final_results = recall_results
                pipeline_metadata = {'pipeline': 'no_reranking'}
            
            processing_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                query=query,
                query_type=QueryType.IMAGE,
                results=final_results,
                total_count=len(final_results),
                processing_time=processing_time,
                engine_name=self.name,
                metadata={
                    'total_images': len(self.image_docs), 
                    'pipeline': 'five_layer_recall_with_reranking',
                    'pipeline_metadata': pipeline_metadata
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"图片查询失败: {e}")
            
            return QueryResult(
                success=False,
                query=query,
                query_type=QueryType.IMAGE,
                results=[],
                total_count=0,
                processing_time=processing_time,
                engine_name=self.name,
                metadata={},
                error_message=str(e)
            )
    
    def _search_images_with_five_layer_recall(self, query: str) -> List[Dict[str, Any]]:
        """
        执行五层召回策略的图片搜索
        
        :param query: 查询文本
        :return: 搜索结果列表
        """
        logger.info(f"开始执行五层召回策略，查询: {query}")
        
        # 获取配置参数
        max_results = getattr(self.config, 'max_results', 10)
        max_recall_results = getattr(self.config, 'max_recall_results', 150)
        
        all_candidates = []
        
        try:
            # 第一层：向量相似度搜索
            logger.info("第一层：向量相似度搜索")
            vector_results = self._vector_search(query, max_recall_results // 3)
            all_candidates.extend(vector_results)
            logger.info(f"第一层召回结果数量: {len(vector_results)}")
            
            # 第二层：语义关键词匹配
            logger.info("第二层：语义关键词匹配")
            keyword_results = self._keyword_search(query, max_recall_results // 3)
            all_candidates.extend(keyword_results)
            logger.info(f"第二层召回结果数量: {len(keyword_results)}")
            
            # 第三层：混合召回策略
            logger.info("第三层：混合召回策略")
            # 传入第一层结果，避免重复调用
            hybrid_results = self._hybrid_search(query, max_recall_results // 3, vector_candidates=vector_results)
            all_candidates.extend(hybrid_results)
            logger.info(f"第三层召回结果数量: {len(hybrid_results)}")
            
            # 第四层：智能模糊匹配
            logger.info("第四层：智能模糊匹配")
            fuzzy_results = self._fuzzy_search(query, max_recall_results // 6)
            all_candidates.extend(fuzzy_results)
            logger.info(f"第四层召回结果数量: {len(fuzzy_results)}")
            
            # 第五层：查询扩展召回
            logger.info("第五层：查询扩展召回")
            expansion_results = self._expansion_search(query, max_recall_results // 6)
            all_candidates.extend(expansion_results)
            logger.info(f"第五层召回结果数量: {len(expansion_results)}")
            
            logger.info(f"五层召回总结果数量: {len(all_candidates)}")
            
            # 去重和排序
            final_results = self._deduplicate_and_sort_results(all_candidates)
            
            # 限制结果数量
            return final_results[:max_results]
            
        except Exception as e:
            logger.error(f"五层召回搜索失败: {e}")
            return []
    
    def _vector_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第一层：向量相似度搜索 - 双重向量搜索策略
        
        利用两种不同的embedding模型实现图片召回：
        1. 查询文本 → text-embedding-v1 → 与image_text chunks比较（语义相似度）
        2. 查询文本 → text-embedding-v1 → 与image chunks比较（视觉特征相似度）
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        
        if not self.vector_store or not getattr(self.config, 'enable_vector_search', True):
            logger.info("向量搜索未启用或向量数据库不可用")
            return results
        
        try:
            threshold = getattr(self.config, 'image_similarity_threshold', 0.05)
            logger.info(f"第一层向量搜索 - 查询: {query}, 阈值: {threshold}, 最大结果数: {max_results}")
            
            # 策略1：搜索image_text chunks（语义相似度）
            # 查询文本通过text-embedding-v1转换为向量，与enhanced_description的向量比较
            logger.info("策略1：搜索image_text chunks（语义相似度）")
            image_text_results = self.vector_store.similarity_search(
                query, 
                k=max_results,  # 获取结果用于筛选
                filter={'chunk_type': 'image_text'}  # 搜索图片描述文本
            )
            
            logger.info(f"image_text搜索返回原始结果数量: {len(image_text_results)}")
            
            # 处理image_text搜索结果
            for doc in image_text_results:
                if not hasattr(doc, 'metadata'):
                    continue
                
                # 获取相似度分数
                score = getattr(doc, 'score', 0.5)
                
                # 应用阈值过滤
                if score >= threshold:
                    # 通过related_image_id找到对应的image chunk
                    related_image_id = doc.metadata.get('related_image_id')
                    if related_image_id:
                        # 查找对应的image chunk
                        image_doc = self._find_image_chunk_by_id(related_image_id)
                        if image_doc:
                            results.append({
                                'doc': image_doc,  # 返回image chunk，不是image_text chunk
                                'score': score * 1.2,  # 语义相似度权重更高
                                'source': 'vector_search',
                                'layer': 1,
                                'search_method': 'semantic_similarity',
                                'semantic_score': score,
                                'related_image_text_id': doc.metadata.get('image_id'),
                                'enhanced_description': doc.metadata.get('enhanced_description', '')
                            })
            
            logger.info(f"策略1通过阈值检查的结果数量: {len(results)}")
            
            # 策略2：搜索image chunks（视觉特征相似度）
            # 查询文本通过text-embedding-v1转换为向量，与图片的multimodal-embedding-v1向量比较
            logger.info("策略2：搜索image chunks（视觉特征相似度）")
            image_results = self.vector_store.similarity_search(
                query, 
                k=max_results,  # 获取结果用于筛选
                filter={'chunk_type': 'image'}  # 搜索图片视觉特征
            )
            
            logger.info(f"image搜索返回原始结果数量: {len(image_results)}")
            
            # 处理image搜索结果
            for doc in image_results:
                if not hasattr(doc, 'metadata'):
                    continue
                
                # 获取相似度分数
                score = getattr(doc, 'score', 0.5)
                
                # 应用阈值过滤
                if score >= threshold:
                    # 检查是否已经在结果中（避免重复）
                    doc_id = self._get_doc_id(doc)
                    if not any(r['doc'] == doc for r in results):
                        results.append({
                            'doc': doc,
                            'score': score * 0.8,  # 视觉特征相似度权重稍低
                            'source': 'vector_search',
                            'layer': 1,
                            'search_method': 'visual_similarity',
                            'visual_score': score
                        })
            
            logger.info(f"策略2通过阈值检查的结果数量: {len([r for r in results if r['search_method'] == 'visual_similarity'])}")
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            final_results = results[:max_results]
            
            logger.info(f"第一层向量搜索完成，总结果数量: {len(final_results)}")
            logger.info(f"语义相似度结果: {len([r for r in final_results if r['search_method'] == 'semantic_similarity'])}")
            logger.info(f"视觉相似度结果: {len([r for r in final_results if r['search_method'] == 'visual_similarity'])}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            logger.info("向量搜索失败，降级到关键词搜索作为第一层召回")
            
            # 降级策略：使用关键词搜索作为第一层召回
            try:
                keyword_fallback = self._keyword_search(query, max_results)
                logger.info(f"第一层降级关键词搜索返回 {len(keyword_fallback)} 个结果")
                
                # 为降级结果添加标识
                for result in keyword_fallback:
                    result['source'] = 'vector_search_fallback'
                    result['layer'] = 1
                    result['search_method'] = 'keyword_fallback'
                    result['fallback_reason'] = str(e)
                
                return keyword_fallback
            except Exception as fallback_error:
                logger.error(f"第一层降级关键词搜索也失败: {fallback_error}")
                return []
    
    def _keyword_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第二层：语义关键词匹配
        
        在图片元数据的文本字段中进行关键词匹配，
        包括enhanced_description、img_caption、image_type等
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        
        if not getattr(self.config, 'enable_keyword_search', True):
            logger.info("关键词搜索未启用")
            return results
        
        try:
            # 使用jieba分词提取查询关键词，参考TextEngine的实现
            query_keywords = self._extract_semantic_keywords_from_query(query)
            query_words = set(query_keywords)
            logger.info(f"第二层关键词搜索 - 查询词: {query_words}")
            
            for doc in self.image_docs:
                if not hasattr(doc, 'metadata') or not doc.metadata:
                    continue
                
                score = 0.0
                metadata = doc.metadata
                
                # 图片标题匹配 (权重最高)
                if 'img_caption' in metadata and metadata['img_caption']:
                    caption_text = ' '.join(metadata['img_caption']).lower()
                    caption_score = self._calculate_text_match_score(query_words, caption_text, 0.8)
                    score += caption_score
                    if caption_score > 0:
                        logger.debug(f"标题匹配得分: {caption_score}, 标题: {metadata['img_caption']}")
                
                # 增强描述匹配 (权重次之)
                if 'enhanced_description' in metadata and metadata['enhanced_description']:
                    enhanced_text = metadata['enhanced_description'].lower()
                    enhanced_score = self._calculate_text_match_score(query_words, enhanced_text, 0.7)
                    score += enhanced_score
                    if enhanced_score > 0:
                        logger.debug(f"增强描述匹配得分: {enhanced_score}")
                
                # 图片类型匹配
                if 'image_type' in metadata and metadata['image_type']:
                    image_type = metadata['image_type'].lower()
                    type_score = self._calculate_text_match_score(query_words, image_type, 0.6)
                    score += type_score
                    if type_score > 0:
                        logger.debug(f"图片类型匹配得分: {type_score}, 类型: {metadata['image_type']}")
                
                # 文档名称匹配
                if 'document_name' in metadata and metadata['document_name']:
                    doc_name = metadata['document_name'].lower()
                    doc_name_score = self._calculate_text_match_score(query_words, doc_name, 0.5)
                    score += doc_name_score
                    if doc_name_score > 0:
                        logger.debug(f"文档名称匹配得分: {doc_name_score}")
                
                # 其他元数据匹配
                for key in ['title', 'description', 'content']:
                    if key in metadata and metadata[key]:
                        text = str(metadata[key]).lower()
                        other_score = self._calculate_text_match_score(query_words, text, 0.4)
                        score += other_score
                
                if score > 0:
                    results.append({
                        'doc': doc,
                        'score': score,
                        'source': 'keyword_search',
                        'layer': 2,
                        'search_method': 'metadata_text_matching'
                    })
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"第二层关键词搜索完成，找到 {len(results)} 个匹配结果")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return []
    
    def _hybrid_search(self, query: str, max_results: int, vector_candidates: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        第三层：混合召回策略
        
        结合向量搜索和关键词搜索的结果，
        通过加权融合提升召回质量
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :param vector_candidates: 第一层的向量搜索结果（避免重复调用）
        :return: 搜索结果列表
        """
        results = []
        
        try:
            logger.info(f"第三层混合召回 - 开始融合向量搜索和关键词搜索结果")
            
            # 使用传入的向量搜索结果，避免重复调用第一层
            if vector_candidates is None:
                logger.info("未传入向量搜索结果，重新调用第一层搜索")
                vector_candidates = self._vector_search(query, max_results // 2)
            else:
                logger.info(f"使用传入的向量搜索结果，数量: {len(vector_candidates)}")
            
            keyword_candidates = self._keyword_search(query, max_results // 2)
            
            logger.info(f"向量搜索候选: {len(vector_candidates)}, 关键词搜索候选: {len(keyword_candidates)}")
            
            # 融合策略：加权平均 + 多样性保证
            all_candidates = {}
            
            # 处理向量搜索结果 (权重0.7)
            for candidate in vector_candidates:
                doc_id = self._get_doc_id(candidate['doc'])
                if doc_id not in all_candidates:
                    all_candidates[doc_id] = candidate.copy()
                    all_candidates[doc_id]['hybrid_score'] = candidate['score'] * 0.7  # 向量搜索权重
                    all_candidates[doc_id]['vector_score'] = candidate['score']
                    all_candidates[doc_id]['keyword_score'] = 0.0
                else:
                    # 如果已存在，更新向量分数
                    all_candidates[doc_id]['vector_score'] = candidate['score']
                    all_candidates[doc_id]['hybrid_score'] = max(
                        all_candidates[doc_id]['hybrid_score'],
                        candidate['score'] * 0.7
                    )
            
            # 处理关键词搜索结果 (权重0.8)
            for candidate in keyword_candidates:
                doc_id = self._get_doc_id(candidate['doc'])
                if doc_id not in all_candidates:
                    all_candidates[doc_id] = candidate.copy()
                    all_candidates[doc_id]['hybrid_score'] = candidate['score'] * 0.8  # 关键词搜索权重
                    all_candidates[doc_id]['keyword_score'] = candidate['score']
                    all_candidates[doc_id]['vector_score'] = 0.0
                else:
                    # 如果已存在，更新关键词分数并重新计算混合分数
                    all_candidates[doc_id]['keyword_score'] = candidate['score']
                    # 混合分数 = 向量分数*0.7 + 关键词分数*0.8
                    all_candidates[doc_id]['hybrid_score'] = (
                        all_candidates[doc_id]['vector_score'] * 0.7 + 
                        candidate['score'] * 0.8
                    )
            
            # 转换为列表并按混合分数排序
            results = list(all_candidates.values())
            results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            # 添加混合搜索标识
            for result in results:
                result['source'] = 'hybrid_search'
                result['layer'] = 3
                result['search_method'] = 'vector_keyword_fusion'
                # 记录融合详情
                result['fusion_details'] = {
                    'vector_weight': 0.7,
                    'keyword_weight': 0.8,
                    'vector_score': result.get('vector_score', 0.0),
                    'keyword_score': result.get('keyword_score', 0.0)
                }
            
            logger.info(f"第三层混合召回完成，融合后结果数量: {len(results)}")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return []
    
    def _fuzzy_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第四层：智能模糊匹配
        
        在图片元数据中进行模糊匹配，处理拼写错误、同义词等，
        提升召回率
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        
        try:
            # 使用jieba分词提取查询关键词，参考TextEngine的实现
            query_keywords = self._extract_semantic_keywords_from_query(query)
            query_words = query_keywords
            logger.info(f"第四层模糊匹配 - 查询词: {query_words}")
            
            for doc in self.image_docs:
                if not hasattr(doc, 'metadata') or not doc.metadata:
                    continue
                
                score = 0.0
                metadata = doc.metadata
                
                # 遍历所有文本字段进行模糊匹配
                for key, text in metadata.items():
                    if isinstance(text, str) and text:
                        text_lower = text.lower()
                        
                        # 1. 完全包含匹配 (权重最高)
                        if query.lower() in text_lower:
                             score += 0.6
                             logger.debug(f"完全包含匹配: {query.lower()} in {text_lower[:50]}...")
                        
                        # 2. 单词级匹配（使用jieba分词结果）
                        text_keywords = self._extract_semantic_keywords_from_text(text_lower, set())
                        text_words_set = set(text_keywords)
                        common_words = set(query_words) & text_words_set
                        if common_words:
                            word_score = len(common_words) * 0.3
                            score += word_score
                            logger.debug(f"单词匹配: {common_words}, 得分: {word_score}")
                        
                        # 3. 字符级相似度 (用于处理拼写错误)
                        if len(query.lower()) > 3 and len(text_lower) > 3:
                            similarity = self._calculate_string_similarity(query.lower(), text_lower)
                            char_score = similarity * 0.4
                            score += char_score
                            if similarity > 0.5:
                                logger.debug(f"字符相似度: {similarity:.3f}, 得分: {char_score:.3f}")
                        
                        # 4. 部分单词匹配 (处理缩写、变体等)
                        for query_word in query_words:
                            if len(query_word) > 2:  # 只处理长度大于2的词
                                for text_word in text_keywords:
                                    if len(text_word) > 2:
                                        # 检查是否包含或相似
                                        if query_word in text_word or text_word in query_word:
                                            score += 0.2
                                        elif self._calculate_string_similarity(query_word, text_word) > 0.7:
                                            score += 0.3
                
                # 应用模糊匹配的较低阈值
                if score > 0.3:
                    results.append({
                        'doc': doc,
                        'score': score,
                        'source': 'fuzzy_search',
                        'layer': 4,
                        'search_method': 'fuzzy_text_matching'
                    })
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"第四层模糊匹配完成，找到 {len(results)} 个模糊匹配结果")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"模糊搜索失败: {e}")
            return []
    
    def _expansion_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        第五层：查询扩展召回
        
        通过查询扩展增加召回范围，处理同义词、相关概念等，
        提升长尾查询的召回率
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        
        try:
            logger.info(f"第五层查询扩展 - 原始查询: {query}")
            
            # 查询扩展策略
            expanded_queries = self._expand_query(query)
            logger.info(f"扩展查询列表: {expanded_queries}")
            
            if not expanded_queries:
                logger.info("没有生成扩展查询，跳过第五层")
                return results
            
            # 为每个扩展查询分配结果数量
            results_per_query = max(1, max_results // len(expanded_queries))
            
            for expanded_query in expanded_queries:
                logger.debug(f"处理扩展查询: {expanded_query}")
                
                # 使用扩展查询进行关键词搜索
                expansion_results = self._keyword_search(expanded_query, results_per_query)
                
                for result in expansion_results:
                    # 降低扩展查询的分数权重 (0.7)
                    original_score = result['score']
                    result['score'] *= 0.7
                    
                    # 更新结果信息
                    result['source'] = 'expansion_search'
                    result['layer'] = 5
                    result['search_method'] = 'query_expansion'
                    result['expanded_query'] = expanded_query
                    result['original_score'] = original_score
                    result['expansion_penalty'] = 0.7
                    
                    logger.debug(f"扩展查询结果: {expanded_query} -> 分数: {original_score:.3f} -> {result['score']:.3f}")
                
                results.extend(expansion_results)
            
            # 按分数排序并限制数量
            results.sort(key=lambda x: x['score'], reverse=True)
            logger.info(f"第五层查询扩展完成，扩展后结果数量: {len(results)}")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"查询扩展搜索失败: {e}")
            return []
    
    def _expand_query(self, query: str) -> List[str]:
        """
        查询扩展
        
        基于领域知识和语义相关性进行智能查询扩展，
        提升长尾查询的召回效果
        
        :param query: 原始查询
        :return: 扩展后的查询列表
        """
        expanded_queries = []
        query_lower = query.lower()
        
        # 1. 同义词扩展
        synonyms = {
            # 图表相关
            '图': ['图片', '图表', '图像', 'figure', 'chart', 'graph'],
            '表': ['表格', '图表', 'table', 'chart'],
            '图表': ['图', '表', '图像', 'figure', 'chart'],
            
            # 数据类型
            '数据': ['数据', '统计', '数字', 'data', 'statistics'],
            '统计': ['统计', '数据', '数字', 'statistics', 'data'],
            '数字': ['数字', '数据', '统计', 'number', 'data'],
            
            # 分析相关
            '分析': ['分析', '研究', '分析报告', 'analysis', 'research'],
            '研究': ['研究', '分析', '研究报告', 'research', 'analysis'],
            '报告': ['报告', '文档', '报告书', 'report', 'document'],
            
            # 财务相关
            '利润': ['利润', '净利润', '收入', '财务', '业绩', 'profit'],
            '收入': ['收入', '营收', '销售额', 'revenue', 'sales'],
            '财务': ['财务', '财务数据', '财务报表', 'financial'],
            '业绩': ['业绩', '表现', '财务表现', 'performance'],
            
            # 时间相关
            '季度': ['季度', 'Q1', 'Q2', 'Q3', 'Q4', 'quarter'],
            '年度': ['年度', '年', '全年', 'annual', 'year'],
            '月度': ['月度', '月', 'monthly', 'month']
        }
        
        # 应用同义词扩展
        for word, syns in synonyms.items():
            if word in query_lower:
                for syn in syns:
                    expanded_query = query_lower.replace(word, syn)
                    if expanded_query != query_lower and expanded_query not in expanded_queries:
                        expanded_queries.append(expanded_query)
        
        # 2. 领域相关概念扩展
        domain_concepts = {
            # 半导体行业
            '中芯国际': ['芯片', '半导体', '集成电路', 'IC', '晶圆', '制造'],
            '芯片': ['半导体', '集成电路', 'IC', '晶圆', '制造', '中芯国际'],
            '半导体': ['芯片', '集成电路', 'IC', '晶圆', '制造', '中芯国际'],
            
            # 财务指标
            '净利润': ['利润', '收入', '财务', '业绩', '盈利', '收益'],
            '营收': ['收入', '销售额', '财务', '业绩', 'revenue'],
            '毛利率': ['利润', '成本', '财务', '盈利能力', 'margin'],
            
            # 技术指标
            '良率': ['质量', '合格率', '技术', '制造', 'yield'],
            '产能': ['产量', '生产能力', '制造', '技术', 'capacity'],
            '工艺': ['技术', '制程', '制造', '工艺水平', 'process']
        }
        
        # 应用领域概念扩展
        for concept, related in domain_concepts.items():
            if concept in query:
                for related_concept in related:
                    if related_concept not in query_lower:
                        expanded_queries.append(related_concept)
        
        # 3. 查询结构扩展
        # 如果查询包含"中芯国际"，添加"中芯国际"作为独立查询
        if '中芯国际' in query and '中芯国际' not in expanded_queries:
            expanded_queries.append('中芯国际')
        
        # 4. 时间范围扩展
        time_patterns = {
            r'(\d{4})年': [r'\1年Q1', r'\1年Q2', r'\1年Q3', r'\1年Q4'],
            r'Q(\d)': [r'Q\1季度', r'\1季度'],
            r'(\d{4})年(\d{1,2})月': [r'\1年\2月', r'\1年\2季度']
        }
        
        import re
        for pattern, expansions in time_patterns.items():
            match = re.search(pattern, query)
            if match:
                for expansion in expansions:
                    expanded_query = re.sub(pattern, expansion, query)
                    if expanded_query != query and expanded_query not in expanded_queries:
                        expanded_queries.append(expanded_query)
        
        # 5. 去重和限制数量
        unique_expansions = list(set(expanded_queries))
        logger.info(f"查询扩展生成 {len(unique_expansions)} 个扩展查询")
        
        # 限制扩展查询数量，优先保留最相关的
        return unique_expansions[:8]  # 增加扩展查询数量上限
    
    def _calculate_text_match_score(self, query_words: Set[str], text: str, base_score: float) -> float:
        """
        计算文本匹配分数 - 参考TextEngine的实现，使用jieba分词和Jaccard相似度
        
        :param query_words: 查询词集合
        :param text: 目标文本
        :param base_score: 基础分数
        :return: 匹配分数
        """
        if not text or not query_words:
            return 0.0
        
        try:
            # 使用jieba进行中文分词，参考TextEngine的实现
            import jieba
            import jieba.analyse
            
            # 停用词列表（与TextEngine保持一致）
            stop_words = {
                '的', '是', '在', '有', '和', '与', '或', '但', '而', '如果', '那么', '什么', '怎么', '为什么', '如何',
                '这个', '那个', '这些', '那些', '一个', '一些', '可以', '应该', '能够', '需要', '必须', '可能', '也许',
                '大概', '大约', '左右', '根据', '显示', '表明', '说明', '指出', '提到', '包括', '涉及', '关于', '对于',
                '呢', '吗', '啊', '吧', '了', '着', '过', '来', '去', '上', '下', '里', '外', '前', '后', '左', '右'
            }
            
            # 提取文本关键词
            text_keywords = self._extract_semantic_keywords_from_text(text, stop_words)
            
            if not text_keywords:
                logger.debug(f"文本关键词提取失败，使用基本分词")
                # 降级到基本分词
                text_words_set = set(text.lower().split())
            else:
                text_words_set = set(text_keywords)
            
            # 计算Jaccard相似度（与TextEngine保持一致）
            intersection = query_words.intersection(text_words_set)
            union = query_words.union(text_words_set)
            
            if union:
                jaccard_score = len(intersection) / len(union)
                logger.debug(f"Jaccard相似度计算: 查询词={query_words}, 文本词={text_words_set}, 交集={intersection}, 并集={union}, 相似度={jaccard_score:.3f}")
                
                # 应用基础分数权重
                final_score = base_score * jaccard_score
                return final_score
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"jieba分词失败，降级到基本文本匹配: {e}")
            # 降级方案：使用基本的词汇重叠
            text_lower = text.lower()
            text_words_set = set(text_lower.split())
            
            intersection = query_words.intersection(text_words_set)
            total_query_words = len(query_words)
            
            if total_query_words > 0:
                match_ratio = len(intersection) / total_query_words
                return base_score * match_ratio
            else:
                return 0.0
    
    def _extract_semantic_keywords_from_text(self, text: str, stop_words: set) -> List[str]:
        """从文本中提取语义关键词 - 参考TextEngine的实现"""
        try:
            # 导入jieba分词工具
            import jieba
            import jieba.analyse
            
            # 添加领域专业词汇到jieba词典
            domain_words = [
                '中芯国际', 'SMIC', '晶圆代工', '半导体制造', '集成电路', 'IC', '微处理器',
                '良率', 'yield', '制程', '工艺', '封装', '测试', '晶圆', '硅片', '基板'
            ]
            for word in domain_words:
                jieba.add_word(word)
            
            # 方法1：使用jieba.lcut进行精确分词（优先使用，保证完整性）
            try:
                words = jieba.lcut(text, cut_all=False)
                keywords = [word for word in words if word not in stop_words and len(word) > 1]
                if keywords:
                    logger.debug(f"jieba精确分词成功，提取到 {len(keywords)} 个关键词")
                    return keywords
            except Exception as e:
                logger.warning(f"jieba精确分词失败: {e}")
            
            # 方法2：使用jieba.analyse.extract_tags提取关键词（基于TF-IDF，作为补充）
            try:
                keywords_tfidf = jieba.analyse.extract_tags(text, topK=15, allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'an'))
                if keywords_tfidf:
                    filtered_keywords = [word for word in keywords_tfidf if word not in stop_words and len(word) > 1]
                    if filtered_keywords:
                        logger.debug(f"jieba TF-IDF提取成功，提取到 {len(filtered_keywords)} 个关键词")
                        return filtered_keywords
            except Exception as e:
                logger.warning(f"jieba TF-IDF提取失败: {e}")
            
            # 方法3：使用jieba.analyse.textrank提取关键词（基于TextRank算法，作为补充）
            try:
                keywords_textrank = jieba.analyse.textrank(text, topK=15, allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'an'))
                if keywords_textrank:
                    filtered_keywords = [word for word in keywords_textrank if word not in stop_words and len(word) > 1]
                    if filtered_keywords:
                        logger.debug(f"jieba TextRank提取成功，提取到 {len(filtered_keywords)} 个关键词")
                        return filtered_keywords
            except Exception as e:
                logger.warning(f"jieba TextRank提取失败: {e}")
            
            # 方法4：降级到正则表达式（如果jieba都失败了）
            try:
                import re
                words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
                keywords = [word for word in words if word not in stop_words and len(word) > 1]
                if keywords:
                    return keywords
            except Exception as e:
                logger.warning(f"正则表达式提取失败: {e}")
            
            # 如果所有方法都失败，返回最基本的词
            basic_words = [word.strip() for word in text.split() if len(word.strip()) > 1]
            return basic_words[:10]  # 最多返回10个词
            
        except Exception as e:
            logger.error(f"关键词提取完全失败: {e}")
            # 最后的降级方案
            return [word.strip() for word in text.split() if len(word.strip()) > 1]
    
    def _extract_semantic_keywords_from_query(self, query: str) -> List[str]:
        """从查询中提取语义关键词 - 参考TextEngine的实现"""
        try:
            # 导入jieba分词工具
            import jieba
            import jieba.analyse
            
            # 添加领域专业词汇到jieba词典
            domain_words = [
                '中芯国际', 'SMIC', '晶圆代工', '半导体制造', '集成电路', 'IC', '微处理器',
                '良率', 'yield', '制程', '工艺', '封装', '测试', '晶圆', '硅片', '基板'
            ]
            for word in domain_words:
                jieba.add_word(word)
            
            # 停用词列表（与TextEngine保持一致）
            stop_words = {
                '的', '是', '在', '有', '和', '与', '或', '但', '而', '如果', '那么', '什么', '怎么', '为什么', '如何',
                '这个', '那个', '这些', '那些', '一个', '一些', '可以', '应该', '能够', '需要', '必须', '可能', '也许',
                '大概', '大约', '左右', '根据', '显示', '表明', '说明', '指出', '提到', '包括', '涉及', '关于', '对于',
                '呢', '吗', '啊', '吧', '了', '着', '过', '来', '去', '上', '下', '里', '外', '前', '后', '左', '右'
            }
            
            # 方法1：使用jieba.lcut进行精确分词（优先使用，保证完整性）
            try:
                words = jieba.lcut(query, cut_all=False)
                keywords = [word for word in words if word not in stop_words and len(word) > 1]
                if keywords:
                    logger.debug(f"jieba精确分词成功，提取到 {len(keywords)} 个查询关键词")
                    return keywords
            except Exception as e:
                logger.warning(f"jieba精确分词失败: {e}")
            
            # 方法2：使用jieba.analyse.extract_tags提取关键词（基于TF-IDF，作为补充）
            try:
                keywords_tfidf = jieba.analyse.extract_tags(query, topK=10, allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'an'))
                if keywords_tfidf:
                    filtered_keywords = [word for word in keywords_tfidf if word not in stop_words and len(word) > 1]
                    if filtered_keywords:
                        logger.debug(f"jieba TF-IDF提取成功，提取到 {len(filtered_keywords)} 个查询关键词")
                        return filtered_keywords
            except Exception as e:
                logger.warning(f"jieba TF-IDF提取失败: {e}")
            
            # 方法3：使用jieba.analyse.textrank提取关键词（基于TextRank算法，作为补充）
            try:
                keywords_textrank = jieba.analyse.textrank(query, topK=10, allowPOS=('n', 'nr', 'nt', 'nz', 'v', 'vn', 'a', 'an'))
                if keywords_textrank:
                    filtered_keywords = [word for word in keywords_textrank if word not in stop_words and len(word) > 1]
                    if filtered_keywords:
                        logger.debug(f"jieba TextRank提取成功，提取到 {len(filtered_keywords)} 个查询关键词")
                        return filtered_keywords
            except Exception as e:
                logger.warning(f"jieba TextRank提取失败: {e}")
            
            # 方法4：降级到正则表达式（如果jieba都失败了）
            try:
                import re
                words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query.lower())
                keywords = [word for word in words if word not in stop_words and len(word) > 1]
                if keywords:
                    return keywords
            except Exception as e:
                logger.warning(f"正则表达式提取失败: {e}")
            
            # 如果所有方法都失败，返回最基本的词
            basic_words = [word.strip() for word in query.split() if len(word.strip()) > 1]
            return basic_words[:5]  # 查询关键词最多返回5个词
            
        except Exception as e:
            logger.error(f"查询关键词提取完全失败: {e}")
            # 最后的降级方案
            return [word.strip() for word in query.split() if len(word.strip()) > 1]
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        计算字符串相似度
        
        :param str1: 字符串1
        :param str2: 字符串2
        :return: 相似度分数 (0-1)
        """
        if not str1 or not str2:
            return 0.0
        
        # 简单的字符级相似度计算
        set1 = set(str1)
        set2 = set(str2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _get_doc_id(self, doc) -> str:
        """
        获取文档ID
        
        :param doc: 文档对象
        :return: 文档ID字符串
        """
        if hasattr(doc, 'metadata') and doc.metadata:
            return doc.metadata.get('image_id', str(id(doc)))  # 修正：使用image_id而不是id
        return str(id(doc))
    
    def _find_image_chunk_by_id(self, image_id: str):
        """
        根据image_id查找对应的image chunk
        
        :param image_id: 图片ID
        :return: image chunk文档对象，如果未找到则返回None
        """
        if not self.vector_store:
            return None
        
        try:
            # 在向量存储中搜索image chunk
            results = self.vector_store.similarity_search(
                "",  # 空查询，只用于过滤
                k=1,
                filter={'chunk_type': 'image', 'image_id': image_id}
            )
            
            if results:
                return results[0]
            
            # 如果向量搜索没找到，尝试在docstore中查找
            if hasattr(self.vector_store, 'docstore') and hasattr(self.vector_store.docstore, '_dict'):
                for doc_id, doc in self.vector_store.docstore._dict.items():
                    metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                    if (metadata.get('chunk_type') == 'image' and 
                        metadata.get('image_id') == image_id):
                        return doc
            
            logger.warning(f"未找到image_id为 {image_id} 的image chunk")
            return None
            
        except Exception as e:
            logger.error(f"查找image chunk失败: {e}")
            return None
    
    def _deduplicate_and_sort_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重和排序结果
        
        :param results: 原始结果列表
        :return: 去重排序后的结果列表
        """
        # 去重（基于文档ID）
        seen_docs = set()
        unique_results = []
        
        for result in results:
            doc_id = self._get_doc_id(result['doc'])
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_results.append(result)
        
        # 按分数排序
        unique_results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"去重后结果数量: {len(unique_results)}")
        return unique_results
    
    def _final_ranking_and_limit(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        最终排序和限制结果数量
        
        :param query: 查询文本
        :param results: 候选结果列表
        :return: 最终结果列表
        """
        if not results:
            return []
        
        # 按分数排序
        sorted_results = sorted(results, key=lambda x: x.get('score', 0.0), reverse=True)
        
        # 限制结果数量
        max_results = getattr(self.config, 'max_results', 20)
        final_results = sorted_results[:max_results]
        
        logger.info(f"最终排序完成，返回 {len(final_results)} 个结果")
        return final_results
    
    def clear_cache(self):
        """清理图片引擎缓存"""
        self.image_docs = []
        self._docs_loaded = False
        logger.info("图片引擎缓存已清理")
