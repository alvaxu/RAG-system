"""
混合查询处理器模块

RAG系统的混合查询处理器，负责混合查询类型的内容检索和处理
严格按照33.V3_RAG查询处理模块详细设计文档实现
"""

import logging
import time
from typing import Dict, List, Optional, Any
import asyncio

from .config_integration import ConfigIntegration
from .unified_services import UnifiedServices
from .common_models import QueryOptions, QueryResult
from .exceptions import (
    ServiceInitializationError,
    QueryProcessingError,
    ContentProcessingError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class SimpleHybridProcessor:
    """混合查询处理器 - 严格按照设计文档实现"""
    
    def __init__(self, config_integration: ConfigIntegration):
        """
        初始化混合查询处理器
        
        :param config_integration: 配置集成管理器实例
        """
        self.config = config_integration
        
        try:
            # 初始化统一服务接口
            self.unified_services = UnifiedServices(config_integration)
            
            # 获取混合查询配置
            self.hybrid_config = self.config.get_rag_config('query_processing.hybrid', {})
            self.content_weights = self.hybrid_config.get('content_weights', {
                'text': 0.4,
                'image': 0.3,
                'table': 0.3
            })
            
            logger.info("混合查询处理器初始化完成")
            
        except (ServiceInitializationError, ConfigurationError) as e:
            logger.error(f"混合查询处理器初始化失败: {e}")
            raise ServiceInitializationError(f"混合查询处理器初始化失败: {e}") from e
        except Exception as e:
            logger.error(f"混合查询处理器初始化失败（未知错误）: {e}")
            raise ServiceInitializationError(f"混合查询处理器初始化失败: {e}") from e
    
    async def process_hybrid_query(self, query: str, options: QueryOptions) -> QueryResult:
        """
        混合查询处理 - 严格按照设计文档实现
        
        :param query: 查询文本
        :param options: 查询选项
        :return: 混合查询结果
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始混合查询处理: {query[:50]}...")
            
            result = QueryResult()
            result.query_type = 'hybrid'
            
            # 1. 并行检索所有内容类型
            retrieval_tasks = [
                self._retrieve_content_type(query, 'text', options),
                self._retrieve_content_type(query, 'image', options),
                self._retrieve_content_type(query, 'table', options)
            ]
            
            # 等待所有检索任务完成
            retrieval_results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
            
            # 2. 处理检索结果
            all_results = []
            content_types = ['text', 'image', 'table']
            for i, content_type in enumerate(content_types):
                if isinstance(retrieval_results[i], Exception):
                    logger.warning(f"{content_type}类型检索失败: {retrieval_results[i]}")
                    continue
                
                results = retrieval_results[i]
                # 为结果添加类型标识和权重
                for item in results:
                    if isinstance(item, dict):
                        item['chunk_type'] = content_type
                        item['content_weight'] = self.content_weights.get(content_type, 0.3)
                    else:
                        # 如果不是字典，转换为字典格式
                        item = {
                            'content': str(item),
                            'chunk_type': content_type,
                            'content_weight': self.content_weights.get(content_type, 0.3),
                            'score': getattr(item, 'score', 0.5)
                        }
                    all_results.append(item)
            
            if not all_results:
                result.success = False
                result.error_message = "没有找到相关的内容"
                return result
            
            # 3. 智能融合和去重
            fused_results = self._fuse_and_deduplicate(all_results)
            
            # 4. 重排序
            reranked_results = await self.unified_services.rerank(query, fused_results)
            
            # 5. LLM问答
            context_memories = options.context_memories if hasattr(options, 'context_memories') else None
            answer = await self.unified_services.generate_answer(query, reranked_results, context_memories)
            
            # 6. 整合结果
            result.success = True
            result.answer = answer
            result.results = reranked_results
            
            # 7. 更新处理元数据
            processing_time = time.time() - start_time
            result.processing_metadata = {
                'processing_time': processing_time,
                'content_types': ['text', 'image', 'table'],
                'initial_results_count': len(all_results),
                'fused_results_count': len(fused_results),
                'final_results_count': len(reranked_results),
                'processing_strategy': 'hybrid_parallel',
                'content_weights': self.content_weights
            }
            
            logger.info(f"混合查询处理完成，初始结果: {len(all_results)}，融合后: {len(fused_results)}，最终: {len(reranked_results)}")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"混合查询处理失败: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            result.processing_metadata = {
                'processing_time': processing_time,
                'error': str(e)
            }
            return result
    
    async def _retrieve_content_type(self, query: str, content_type: str, 
                                   options: QueryOptions) -> List[Dict[str, Any]]:
        """
        检索指定内容类型
        
        :param query: 查询文本
        :param options: 查询选项
        :param content_type: 内容类型
        :return: 检索结果列表
        """
        try:
            # 根据内容类型调整检索参数
            type_specific_options = self._get_type_specific_options(content_type, options)
            
            # 调用统一检索服务
            results = await self.unified_services.retrieve(query, [content_type], type_specific_options)
            
            logger.debug(f"{content_type}类型检索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"{content_type}类型检索失败: {e}")
            return []
    
    def _get_type_specific_options(self, content_type: str, base_options: QueryOptions) -> Dict[str, Any]:
        """
        获取类型特定的检索选项
        
        :param content_type: 内容类型
        :param base_options: 基础选项
        :return: 类型特定选项
        """
        try:
            # 获取类型特定配置
            type_config = self.config.get_rag_config(f'query_processing.{content_type}', {})
            
            options = {
                'max_results': base_options.max_results,
                'relevance_threshold': base_options.relevance_threshold,
                'context_length_limit': base_options.context_length_limit
            }
            
            # 应用类型特定配置
            if 'max_results' in type_config:
                options['max_results'] = type_config['max_results']
            if 'relevance_threshold' in type_config:
                options['relevance_threshold'] = type_config['relevance_threshold']
            
            return options
            
        except Exception as e:
            logger.warning(f"获取{content_type}类型特定选项失败: {e}，使用基础选项")
            return {
                'max_results': base_options.max_results,
                'relevance_threshold': base_options.relevance_threshold,
                'context_length_limit': base_options.context_length_limit
            }
    
    def _fuse_and_deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        智能融合和去重
        
        :param results: 原始结果列表
        :return: 融合去重后的结果列表
        """
        try:
            if not results:
                return []
            
            # 1. 按内容类型分组
            type_groups = {}
            for result in results:
                content_type = result.get('chunk_type', 'unknown')
                if content_type not in type_groups:
                    type_groups[content_type] = []
                type_groups[content_type].append(result)
            
            # 2. 计算各类型的最优结果数量
            total_results = len(results)
            optimal_counts = {}
            for content_type, weight in self.content_weights.items():
                optimal_counts[content_type] = max(1, int(total_results * weight))
            
            # 3. 从各类型中选择最优结果
            fused_results = []
            for content_type, type_results in type_groups.items():
                # 按分数排序
                sorted_results = sorted(type_results, key=lambda x: x.get('score', 0.0), reverse=True)
                
                # 选择最优结果
                optimal_count = optimal_counts.get(content_type, len(sorted_results))
                selected_results = sorted_results[:optimal_count]
                
                # 为结果添加融合权重
                for result in selected_results:
                    result['fusion_weight'] = self.content_weights.get(content_type, 0.3)
                
                fused_results.extend(selected_results)
            
            # 4. 去重处理（基于内容相似性）
            deduplicated_results = self._remove_duplicates(fused_results)
            
            # 5. 最终排序（基于融合权重和分数）
            final_results = sorted(deduplicated_results, 
                                 key=lambda x: (x.get('fusion_weight', 0.3) * x.get('score', 0.0)), 
                                 reverse=True)
            
            logger.info(f"融合去重完成，原始: {len(results)}，融合后: {len(fused_results)}，去重后: {len(deduplicated_results)}，最终: {len(final_results)}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"融合去重失败: {e}，返回原始结果")
            return results
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        基于内容相似性去重
        
        :param results: 结果列表
        :return: 去重后的结果列表
        """
        try:
            if not results:
                return []
            
            # 简单的基于内容的去重
            seen_contents = set()
            unique_results = []
            
            for result in results:
                content = self._extract_content_for_dedup(result)
                if not content:
                    unique_results.append(result)
                    continue
                
                # 检查是否与已有内容相似
                is_duplicate = False
                for seen_content in seen_contents:
                    if self._is_content_similar(content, seen_content):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    seen_contents.add(content)
                    unique_results.append(result)
            
            return unique_results
            
        except Exception as e:
            logger.error(f"去重处理失败: {e}，返回原始结果")
            return results
    
    def _extract_content_for_dedup(self, result: Dict[str, Any]) -> str:
        """
        提取用于去重的内容
        
        :param result: 结果项
        :return: 内容字符串
        """
        try:
            # 尝试不同的内容字段
            for field in ['content', 'text', 'page_content', 'description']:
                if field in result and result[field]:
                    return str(result[field]).strip()
            
            return ""
            
        except Exception:
            return ""
    
    def _is_content_similar(self, content1: str, content2: str, threshold: float = 0.8) -> bool:
        """
        判断两个内容是否相似
        
        :param content1: 内容1
        :param content2: 内容2
        :param threshold: 相似度阈值
        :return: 是否相似
        """
        try:
            if not content1 or not content2:
                return False
            
            # 简单的相似度计算（基于共同字符比例）
            if len(content1) < 10 or len(content2) < 10:
                return False
            
            # 计算共同字符数量
            common_chars = sum(1 for c in content1 if c in content2)
            similarity = common_chars / max(len(content1), len(content2))
            
            return similarity >= threshold
            
        except Exception:
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'SimpleHybridProcessor',
            'unified_services': self.unified_services is not None,
            'content_weights': self.content_weights,
            'features': [
                'parallel_retrieval',
                'content_fusion',
                'intelligent_deduplication',
                'weighted_ranking',
                'hybrid_processing'
            ]
        }
