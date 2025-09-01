"""
查询处理器模块 - 重构版

RAG系统的查询处理器，严格按照33.V3_RAG查询处理模块详细设计文档重构
采用新的架构设计：查询路由器 + 统一服务接口 + 智能处理器
"""

import logging
import time
from typing import Dict, List, Optional, Any

from .config_integration import ConfigIntegration
from .query_router import SimpleQueryRouter
from .common_models import QueryOptions, QueryResult, QueryType
from .exceptions import (
    ServiceInitializationError,
    QueryProcessingError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class QueryProcessor:
    """查询处理器 - 重构版，严格按照设计文档实现"""
    
    def __init__(self, config_integration: ConfigIntegration, 
                 retrieval_engine=None, llm_caller=None, 
                 reranking_service=None, attribution_service=None, 
                 display_service=None, metadata_manager=None):
        """
        初始化查询处理器
        
        :param config_integration: 配置集成管理器实例
        :param retrieval_engine: 召回引擎实例（可选）
        :param llm_caller: LLM调用器实例（可选）
        :param reranking_service: 重排序服务实例（可选）
        :param attribution_service: 溯源服务实例（可选）
        :param display_service: 展示服务实例（可选）
        :param metadata_manager: 元数据管理器实例（可选）
        """
        self.config = config_integration
        
        # 存储传入的服务实例（如果提供）
        self.retrieval_engine = retrieval_engine
        self.llm_caller = llm_caller
        self.reranking_service = reranking_service
        self.attribution_service = attribution_service
        self.display_service = display_service
        self.metadata_manager = metadata_manager
        
        try:
            # 初始化查询路由器
            self.query_router = SimpleQueryRouter(config_integration)
            
            logger.info("查询处理器重构版初始化完成")
            
        except (ServiceInitializationError, ConfigurationError) as e:
            logger.error(f"查询处理器重构版初始化失败: {e}")
            raise ServiceInitializationError(f"查询处理器重构版初始化失败: {e}") from e
        except Exception as e:
            logger.error(f"查询处理器重构版初始化失败（未知错误）: {e}")
            raise ServiceInitializationError(f"查询处理器重构版初始化失败: {e}") from e
    
    def get_service_instance(self, service_name: str):
        """
        获取指定的服务实例
        
        :param service_name: 服务名称
        :return: 服务实例或None
        """
        service_map = {
            'retrieval_engine': self.retrieval_engine,
            'llm_caller': self.llm_caller,
            'reranking_service': self.reranking_service,
            'attribution_service': self.attribution_service,
            'display_service': self.display_service,
            'metadata_manager': self.metadata_manager
        }
        return service_map.get(service_name)
    
    def has_service(self, service_name: str) -> bool:
        """
        检查是否提供了指定的服务
        
        :param service_name: 服务名称
        :return: 是否可用
        """
        return self.get_service_instance(service_name) is not None
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息
        
        :return: 服务状态字典
        """
        return {
            'status': 'ready',
            'service_type': 'QueryProcessor',
            'config_integration': self.config is not None,
            'query_router': self.query_router is not None,
            'services': {
                'retrieval_engine': self.has_service('retrieval_engine'),
                'llm_caller': self.has_service('llm_caller'),
                'reranking_service': self.has_service('reranking_service'),
                'attribution_service': self.has_service('attribution_service'),
                'display_service': self.has_service('display_service'),
                'metadata_manager': self.has_service('metadata_manager')
            },
            'features': [
                'query_routing',
                'smart_processing',
                'hybrid_processing',
                'service_integration'
            ]
        }
    
    async def process_query(self, query: str, query_type: str = "auto", 
                          options: Dict[str, Any] = None) -> QueryResult:
        """
        查询处理主入口 - 重构版，严格按照设计文档实现
        
        :param query: 查询文本
        :param query_type: 查询类型，默认为"auto"自动检测
        :param options: 查询选项
        :return: 查询结果
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始查询处理: {query[:50]}...，类型: {query_type}")
            
            # 1. 构建查询选项
            query_options = self._build_query_options(options)
            
            # 2. 通过查询路由器处理查询
            result = await self.query_router.route_query(query, query_type, query_options)
            
            # 3. 更新处理元数据
            processing_time = time.time() - start_time
            if result.processing_metadata is None:
                result.processing_metadata = {}
            
            result.processing_metadata.update({
                'total_processing_time': processing_time,
                'query_processor_version': 'refactored_v2',
                'query_router_used': True
            })
            
            logger.info(f"查询处理完成，类型: {query_type}，结果状态: {result.success}，耗时: {processing_time:.2f}秒")
            
            return result
            
        except (QueryProcessingError, ServiceInitializationError) as e:
            processing_time = time.time() - start_time
            error_msg = f"查询处理失败: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            result.processing_metadata = {
                'total_processing_time': processing_time,
                'error': str(e),
                'query_processor_version': 'refactored_v2'
            }
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"查询处理失败（未知错误）: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            result.processing_metadata = {
                'total_processing_time': processing_time,
                'error': str(e),
                'query_processor_version': 'refactored_v2'
            }
            return result
    
    def _build_query_options(self, options: Dict[str, Any] = None) -> QueryOptions:
        """
        构建查询选项
        
        :param options: 原始选项字典
        :return: 查询选项对象
        """
        try:
            if options is None:
                options = {}
            
            # 从配置获取默认值
            default_max_results = self.config.get_rag_config('query_processing.max_results', 10)
            default_relevance_threshold = self.config.get_rag_config('query_processing.relevance_threshold', 0.5)
            default_context_length_limit = self.config.get_rag_config('query_processing.max_context_length', 4000)
            default_enable_streaming = self.config.get_rag_config('query_processing.enable_streaming', True)
            
            # 构建查询选项
            query_options = QueryOptions(
                max_results=options.get('max_results', default_max_results),
                relevance_threshold=options.get('relevance_threshold', default_relevance_threshold),
                context_length_limit=options.get('context_length_limit', default_context_length_limit),
                enable_streaming=options.get('enable_streaming', default_enable_streaming)
            )
            
            return query_options
            
        except Exception as e:
            logger.warning(f"构建查询选项失败: {e}，使用默认选项")
            return QueryOptions()
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        try:
            return {
                'processor_type': 'QueryProcessor_Refactored',
                'architecture': 'router_based',
                'components': {
                    'query_router': 'SimpleQueryRouter',
                    'smart_processor': 'SimpleSmartProcessor',
                    'hybrid_processor': 'SimpleHybridProcessor',
                    'unified_services': 'UnifiedServices'
                },
                'processing_flow': [
                    'query_input',
                    'router_dispatch',
                    'type_detection',
                    'content_retrieval',
                    'reranking',
                    'llm_generation',
                    'result_integration'
                ]
            }
            
        except Exception as e:
            logger.error(f"获取处理统计信息失败: {e}")
            return {
                'processor_type': 'QueryProcessor_Refactored',
                'error': str(e)
            }
