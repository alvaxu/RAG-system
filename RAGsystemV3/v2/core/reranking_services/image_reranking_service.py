#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. ImageRerankingService - 图片重排序服务
## 2. 使用DashScope大模型进行智能重排序
## 3. 支持配置开关控制是否启用大模型
## 4. 专门针对图片内容进行优化

## 主要特点：
- 使用DashScope gte-rerank-v2模型
- 图片特化的重排序策略
- 考虑图片的视觉特征和描述质量
- 与TextRerankingService保持一致的接口
'''

import logging
from typing import List, Dict, Any, Optional
from .base_reranking_service import BaseRerankingService
import dashscope
from dashscope.rerank import text_rerank

logger = logging.getLogger(__name__)

class ImageRerankingService(BaseRerankingService):
    """图片重排序服务 - 使用DashScope大模型"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化图片重排序服务
        
        :param config: 配置字典
        """
        super().__init__(config)
        
        # 大模型配置 - 完全依赖配置文件，不设置硬编码默认值
        self.use_llm_enhancement = config.get('use_llm_enhancement')
        if self.use_llm_enhancement is None:
            raise ValueError("配置中缺少 'use_llm_enhancement' 参数")
            
        self.model_name = config.get('model_name')
        if not self.model_name:
            raise ValueError("配置中缺少 'model_name' 参数")
            
        self.top_k = config.get('target_count')
        if self.top_k is None:
            raise ValueError("配置中缺少 'target_count' 参数")
            
        self.similarity_threshold = config.get('similarity_threshold')
        if self.similarity_threshold is None:
            raise ValueError("配置中缺少 'similarity_threshold' 参数")
        
        # API密钥管理
        self.api_key = self._get_api_key()
        if self.api_key:
            dashscope.api_key = self.api_key
            logger.info(f"ImageRerankingService初始化完成，使用模型: {self.model_name}")
        else:
            logger.warning("ImageRerankingService初始化失败：未找到API密钥")
    
    def _get_api_key(self) -> Optional[str]:
        """获取DashScope API密钥"""
        try:
            # 尝试从配置中获取
            if hasattr(self.config, 'api_key') and self.config.api_key:
                return self.config.api_key
            
            # 尝试从环境变量获取
            import os
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if api_key:
                return api_key
            
            # 尝试从API密钥管理器获取（与主程序保持一致）
            try:
                from config.api_key_manager import APIKeyManager
                api_key_manager = APIKeyManager()
                api_key = api_key_manager.get_dashscope_api_key()
                if api_key:
                    return api_key
            except ImportError:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"获取API密钥失败: {e}")
            return None
    
    def get_service_name(self) -> str:
        """获取服务名称"""
        return "ImageRerankingService"
    
    def get_supported_types(self) -> List[str]:
        """获取支持的内容类型"""
        return ['image', 'figure', 'chart', 'graph']
    
    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用大模型对图片候选文档进行重排序
        
        :param query: 查询文本
        :param candidates: 候选文档列表
        :return: 重排序后的文档列表
        """
        if not self.use_llm_enhancement:
            logger.info("大模型增强未启用，返回原始候选列表")
            return candidates
        
        if not candidates:
            logger.info("候选列表为空，无需重排序")
            return []
        
        try:
            logger.info(f"开始图片重排序，查询: {query}, 候选数量: {len(candidates)}")
            
            # 准备用于重排序的文本内容
            rerank_texts = self._prepare_rerank_texts(query, candidates)
            
            if not rerank_texts:
                logger.warning("无法准备重排序文本，返回原始候选列表")
                return candidates
            
            # 调用DashScope重排序API
            reranked_results = self._call_dashscope_rerank(query, rerank_texts)
            
            if not reranked_results:
                logger.warning("DashScope重排序失败，返回原始候选列表")
                return candidates
            
            # 将重排序结果映射回原始候选文档
            final_results = self._map_reranked_results(candidates, reranked_results)
            
            logger.info(f"图片重排序完成，返回 {len(final_results)} 个结果")
            return final_results
            
        except Exception as e:
            logger.error(f"图片重排序失败: {e}")
            logger.info("大模型重排序失败，回退到原始候选列表")
            return candidates
    
    def _prepare_rerank_texts(self, query: str, candidates: List[Dict[str, Any]]) -> List[str]:
        """
        准备用于重排序的文本内容
        
        :param query: 查询文本
        :param candidates: 候选文档列表
        :return: 重排序文本列表
        """
        rerank_texts = []
        
        for candidate in candidates:
            doc = candidate.get('doc')
            if not doc or not hasattr(doc, 'metadata'):
                continue
            
            metadata = doc.metadata
            text_content = []
            
            # 构建图片的文本描述，用于重排序
            if 'img_caption' in metadata and metadata['img_caption']:
                # 图片标题数组
                caption_text = ' '.join(metadata['img_caption'])
                text_content.append(f"图片标题: {caption_text}")
            
            if 'enhanced_description' in metadata and metadata['enhanced_description']:
                # 增强描述
                enhanced_text = metadata['enhanced_description']
                text_content.append(f"增强描述: {enhanced_text}")
            
            if 'image_type' in metadata and metadata['image_type']:
                # 图片类型
                image_type = metadata['image_type']
                text_content.append(f"图片类型: {image_type}")
            
            if 'title' in metadata and metadata['title']:
                # 文档标题
                title = metadata['title']
                text_content.append(f"文档标题: {title}")
            
            if 'description' in metadata and metadata['description']:
                # 文档描述
                description = metadata['description']
                text_content.append(f"文档描述: {description}")
            
            # 组合所有文本内容
            if text_content:
                combined_text = ' | '.join(text_content)
                rerank_texts.append(combined_text)
            else:
                # 如果没有有效文本内容，使用默认描述
                rerank_texts.append("图片文档")
        
        return rerank_texts
    
    def _call_dashscope_rerank(self, query: str, texts: List[str]) -> List[Dict[str, Any]]:
        """
        调用DashScope重排序API
        
        :param query: 查询文本
        :param texts: 待重排序的文本列表
        :return: 重排序结果
        """
        try:
            # 构建重排序请求
            rerank_request = {
                'query': query,
                'documents': texts,
                'top_k': min(self.top_k, len(texts)),
                'model': self.model_name
            }
            
            logger.info(f"调用DashScope重排序API，模型: {self.model_name}, top_k: {rerank_request['top_k']}")
            
            # 调用API - 参考TextRerankingService的实现
            response = text_rerank.TextReRank.call(
                model=self.model_name,
                query=query,
                documents=texts,
                top_k=min(self.top_k, len(texts))
            )
            
            if response.status_code == 200:
                logger.info("DashScope重排序API调用成功")
                return response.output.results
            else:
                logger.error(f"DashScope重排序API调用失败: {response.message}")
                return []
                
        except Exception as e:
            logger.error(f"调用DashScope重排序API异常: {e}")
            return []
    
    def _map_reranked_results(self, original_candidates: List[Dict[str, Any]], 
                             reranked_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将重排序结果映射回原始候选文档
        
        :param original_candidates: 原始候选文档列表
        :param reranked_results: 重排序结果
        :return: 映射后的文档列表
        """
        if not reranked_results:
            return original_candidates
        
        # 创建索引映射
        index_mapping = {}
        for i, candidate in enumerate(original_candidates):
            doc = candidate.get('doc')
            if doc and hasattr(doc, 'metadata'):
                # 使用文档ID或索引作为键
                doc_id = doc.metadata.get('id', str(i))
                index_mapping[doc_id] = i
        
        # 根据重排序结果重新组织候选文档
        final_results = []
        seen_docs = set()
        
        for rerank_result in reranked_results:
            index = rerank_result.get('index')
            if index is not None and index < len(original_candidates):
                candidate = original_candidates[index]
                
                # 检查是否已添加（去重）
                doc = candidate.get('doc')
                if doc and hasattr(doc, 'metadata'):
                    doc_id = doc.metadata.get('id', str(index))
                    if doc_id not in seen_docs:
                        seen_docs.add(doc_id)
                        
                        # 更新分数和重排序信息
                        updated_candidate = candidate.copy()
                        updated_candidate['rerank_score'] = rerank_result.get('relevance_score', 0.0)
                        updated_candidate['rerank_rank'] = len(final_results) + 1
                        updated_candidate['source'] = 'image_reranking_service'
                        
                        final_results.append(updated_candidate)
        
        # # 如果重排序结果不足，补充原始候选文档
        # if len(final_results) < self.top_k:
        #     for candidate in original_candidates:
        #         if len(final_results) >= self.top_k:
        #             break
                    
        #         doc = candidate.get('doc')
        #         if doc and hasattr(doc, 'metadata'):
        #             doc_id = doc.metadata.get('id', str(id(doc)))
        #             if doc_id not in seen_docs:
        #                 seen_docs.add(doc_id)
                        
        #                 # 添加未重排序的候选文档
        #                 updated_candidate = candidate.copy()
        #                 updated_candidate['rerank_score'] = 0.0
        #                 updated_candidate['rerank_rank'] = len(final_results) + 1
        #                 updated_candidate['source'] = 'fallback_candidate'
                        
        #                 final_results.append(updated_candidate)
        
        # 按重排序分数排序
        final_results.sort(key=lambda x: x.get('rerank_score', 0.0), reverse=True)
        
        # return final_results[:self.top_k]
        return final_results
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            'service_name': self.get_service_name(),
            'supported_types': self.get_supported_types(),
            'use_llm_enhancement': self.use_llm_enhancement,
            'model_name': self.model_name,
            'top_k': self.top_k,
            'similarity_threshold': self.similarity_threshold,
            'api_key_available': bool(self.api_key)
        }
