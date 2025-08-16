#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 图片引擎核心实现
## 2. 支持图片查询的专用引擎
## 3. 集成向量搜索和关键词搜索
## 4. 支持图片描述和元数据匹配
"""

import logging
import time
from typing import List, Dict, Any, Optional
from ..core.base_engine import BaseEngine
from ..core.base_engine import EngineConfig
from ..core.base_engine import QueryResult, QueryType

logger = logging.getLogger(__name__)


class ImageEngine(BaseEngine):
    """
    图片引擎
    
    专门处理图片查询，支持多种搜索策略
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
                self.image_docs = self.document_loader.get_image_documents()
            elif self.vector_store:
                # 从向量数据库加载
                self.image_docs = self.vector_store.get_image_documents()
            else:
                logger.warning("未提供文档加载器或向量数据库，图片引擎将无法工作")
                return
                
            self._docs_loaded = True
            logger.info(f"图片引擎加载了 {len(self.image_docs)} 个图片文档")
            
        except Exception as e:
            logger.error(f"加载图片文档失败: {e}")
            self._docs_loaded = False
    
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
        # 图片引擎的组件设置逻辑
        # 目前主要依赖document_loader和vector_store，已在__init__中设置
        pass
    
    def process_query(self, query: str, **kwargs) -> QueryResult:
        """
        处理图片查询
        
        :param query: 查询文本
        :param kwargs: 其他参数
        :return: 搜索结果
        """
        if not self._docs_loaded:
            self._load_documents()
        
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
            # 执行图片搜索
            results = self._search_images(query)
            
            processing_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                query=query,
                query_type=QueryType.IMAGE,
                results=results,
                total_count=len(results),
                processing_time=processing_time,
                engine_name=self.name,
                metadata={'total_images': len(self.image_docs)}
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
    
    def _search_images(self, query: str) -> List[Dict[str, Any]]:
        """
        执行图片搜索
        
        :param query: 查询文本
        :return: 搜索结果列表
        """
        results = []
        
        # 获取配置参数
        threshold = getattr(self.config, 'image_similarity_threshold', 0.7)
        max_results = getattr(self.config, 'max_results', 10)
        
        try:
            # 向量搜索
            if self.vector_store and hasattr(self.config, 'enable_vector_search') and self.config.enable_vector_search:
                vector_results = self.vector_store.similarity_search(
                    query, 
                    k=max_results * 2,  # 获取更多结果用于重排序
                    filter={'type': 'image'}
                )
                
                for doc in vector_results:
                    # 计算相似度分数
                    score = getattr(doc, 'score', 0.5)
                    if score >= threshold:
                        results.append({
                            'doc': doc,
                            'score': score,
                            'type': 'vector_search'
                        })
            
            # 关键词搜索
            if hasattr(self.config, 'enable_keyword_search') and self.config.enable_keyword_search:
                keyword_results = self._keyword_search(query, max_results)
                for result in keyword_results:
                    if result['score'] >= threshold:
                        results.append(result)
            
            # 如果没有结果，降低阈值重试
            if not results and threshold > 0.3:
                logger.info(f"未找到结果，降低阈值从 {threshold} 到 0.3")
                return self._search_images_with_lower_threshold(query, 0.3)
            
            # 去重和排序
            results = self._deduplicate_and_sort_results(results)
            
            # 限制结果数量
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"图片搜索失败: {e}")
            return []
    
    def _keyword_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        关键词搜索
        
        :param query: 查询文本
        :param max_results: 最大结果数
        :return: 搜索结果列表
        """
        results = []
        query_lower = query.lower()
        
        for doc in self.image_docs:
            score = 0.0
            
            # 标题匹配
            title = doc.metadata.get('title', '').lower()
            if query_lower in title:
                score += 0.8
            
            # 图片描述匹配
            description = doc.metadata.get('description', '').lower()
            if query_lower in description:
                score += 0.7
            
            # 增强描述匹配
            enhanced_desc = doc.metadata.get('enhanced_description', '').lower()
            if query_lower in enhanced_desc:
                score += 0.6
            
            # 图片标题匹配
            image_title = doc.metadata.get('image_title', '').lower()
            if query_lower in image_title:
                score += 0.6
            
            # 图片说明匹配
            caption = doc.metadata.get('img_caption', '').lower()
            if query_lower in caption:
                score += 0.5
            
            if score > 0:
                results.append({
                    'doc': doc,
                    'score': score,
                    'type': 'keyword_search'
                })
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    def _search_images_with_lower_threshold(self, query: str, threshold: float) -> List[Dict[str, Any]]:
        """
        使用较低阈值重新搜索
        
        :param query: 查询文本
        :param threshold: 相似度阈值
        :return: 搜索结果列表
        """
        # 临时降低阈值
        original_threshold = getattr(self.config, 'image_similarity_threshold', 0.7)
        setattr(self.config, 'image_similarity_threshold', threshold)
        
        try:
            results = self._search_images(query)
            return results
        finally:
            # 恢复原始阈值
            setattr(self.config, 'image_similarity_threshold', original_threshold)
    
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
            doc_id = result['doc'].metadata.get('id', id(result['doc']))
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_results.append(result)
        
        # 按分数排序
        unique_results.sort(key=lambda x: x['score'], reverse=True)
        
        return unique_results
    
    def clear_cache(self):
        """清理图片引擎缓存"""
        self.image_docs = []
        self._docs_loaded = False
        logger.info("图片引擎缓存已清理")
