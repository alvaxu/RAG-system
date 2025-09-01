"""
智能查询处理器模块

RAG系统的智能查询处理器，负责智能查询类型检测和单类型查询处理
严格按照33.V3_RAG查询处理模块详细设计文档实现
"""

import logging
import time
from typing import Dict, List, Optional, Any

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


class SimpleSmartProcessor:
    """智能查询处理器 - 严格按照设计文档实现"""
    
    def __init__(self, config_integration: ConfigIntegration):
        """
        初始化智能查询处理器
        
        :param config_integration: 配置集成管理器实例
        """
        self.config = config_integration
        
        try:
            # 初始化统一服务接口
            self.unified_services = UnifiedServices(config_integration)
            
            logger.info("智能查询处理器初始化完成")
            
        except (ServiceInitializationError, ConfigurationError) as e:
            logger.error(f"智能查询处理器初始化失败: {e}")
            raise ServiceInitializationError(f"智能查询处理器初始化失败: {e}") from e
        except Exception as e:
            logger.error(f"智能查询处理器初始化失败（未知错误）: {e}")
            raise ServiceInitializationError(f"智能查询处理器初始化失败: {e}") from e
    
    async def process_smart_query(self, query: str, options: QueryOptions) -> QueryResult:
        """
        智能查询处理 - 严格按照设计文档实现
        
        :param query: 查询文本
        :param options: 查询选项
        :return: 智能查询结果
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始智能查询处理: {query[:50]}...")
            
            result = QueryResult()
            
            # 1. 智能查询类型检测
            detected_type, confidence = self._detect_type(query)
            result.query_type = detected_type
            
            # 2. 根据检测结果选择处理策略
            if confidence >= 0.7:  # 高置信度，使用单类型处理
                result = await self._process_single_type(query, detected_type, options)
            else:  # 低置信度，回退到混合查询
                logger.info(f"检测置信度较低({confidence:.2f})，使用混合查询")
                result = await self._process_hybrid_query(query, options)
            
            # 3. 更新处理元数据
            processing_time = time.time() - start_time
            result.processing_metadata = {
                'processing_time': processing_time,
                'detection_confidence': confidence,
                'detected_type': detected_type,
                'processing_strategy': 'smart_query'
            }
            
            result.success = True
            logger.info(f"智能查询处理完成，耗时: {processing_time:.2f}秒")
            
            return result
            
        except (QueryProcessingError, ContentProcessingError) as e:
            processing_time = time.time() - start_time
            error_msg = f"智能查询处理失败: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            result.processing_metadata = {
                'processing_time': processing_time,
                'error': str(e)
            }
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"智能查询处理失败（未知错误）: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            result.processing_metadata = {
                'processing_time': processing_time,
                'error': str(e)
            }
            return result
    
    async def process_single_type_query(self, query: str, content_type: str, 
                                      options: QueryOptions) -> QueryResult:
        """
        单类型查询处理
        
        :param query: 查询文本
        :param content_type: 内容类型
        :param options: 查询选项
        :return: 查询结果
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始单类型查询处理: {query[:50]}...，类型: {content_type}")
            
            result = QueryResult()
            result.query_type = content_type
            
            # 1. 调用对应类型检索
            content_types = [content_type]
            retrieval_results = await self.unified_services.retrieve(query, content_types, {
                'max_results': options.max_results,
                'relevance_threshold': options.relevance_threshold
            })
            
            if not retrieval_results:
                result.success = False
                result.error_message = "没有找到相关的内容"
                return result
            
            # 2. 重排序
            reranked_results = await self.unified_services.rerank(query, retrieval_results)
            
            # 3. LLM问答
            answer = await self.unified_services.generate_answer(query, reranked_results)
            
            # 4. 整合结果
            result.success = True
            result.answer = answer
            result.results = reranked_results
            
            # 5. 更新处理元数据
            processing_time = time.time() - start_time
            result.processing_metadata = {
                'processing_time': processing_time,
                'content_type': content_type,
                'results_count': len(reranked_results),
                'processing_strategy': 'single_type'
            }
            
            logger.info(f"单类型查询处理完成，类型: {content_type}，结果数量: {len(reranked_results)}")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"单类型查询处理失败: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            result.processing_metadata = {
                'processing_time': processing_time,
                'content_type': content_type,
                'error': str(e)
            }
            return result
    
    async def _process_hybrid_query(self, query: str, options: QueryOptions) -> QueryResult:
        """
        处理混合查询（当智能检测不明确时）
        
        :param query: 查询文本
        :param options: 查询选项
        :return: 查询结果
        """
        try:
            logger.info(f"开始混合查询处理: {query[:50]}...")
            
            result = QueryResult()
            result.query_type = 'hybrid'
            
            # 1. 并行检索所有类型
            retrieval_results = await self.unified_services.retrieve(query, None, {
                'max_results': options.max_results,
                'relevance_threshold': options.relevance_threshold
            })
            
            if not retrieval_results:
                result.success = False
                result.error_message = "没有找到相关的内容"
                return result
            
            # 2. 重排序
            reranked_results = await self.unified_services.rerank(query, retrieval_results)
            
            # 3. LLM问答
            answer = await self.unified_services.generate_answer(query, reranked_results)
            
            # 4. 整合结果
            result.success = True
            result.answer = answer
            result.results = reranked_results
            
            logger.info(f"混合查询处理完成，结果数量: {len(reranked_results)}")
            return result
            
        except Exception as e:
            error_msg = f"混合查询处理失败: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            return result
    
    def _detect_type(self, query: str) -> tuple[str, float]:
        """
        查询类型检测 - 严格按照设计文档实现
        
        :param query: 查询文本
        :return: (检测类型, 置信度)
        """
        try:
            # 图片相关关键词检测
            image_keywords = ['图片', '图像', '照片', '图表', '截图', '界面', '显示', '展示', '图标', 'logo']
            image_matches = sum(1 for keyword in image_keywords if keyword in query)
            
            # 表格相关关键词检测
            table_keywords = ['表格', '数据', '统计', '数字', '金额', '数量', '比例', '百分比', '排名', '对比']
            table_matches = sum(1 for keyword in table_keywords if keyword in query)
            
            # 文本相关特征
            text_features = len(query) > 20  # 长文本倾向于文本查询
            
            # 计算各类型的匹配分数
            image_score = image_matches / len(image_keywords) if image_keywords else 0
            table_score = table_matches / len(table_keywords) if table_keywords else 0
            text_score = 0.5 if text_features else 0.3
            
            # 确定类型和置信度
            if image_score > 0.3 and table_score > 0.3:
                # 混合类型
                return 'hybrid', min(max(image_score, table_score), 0.8)
            elif image_score > 0.3:
                # 图片类型
                confidence = min(image_score + 0.2, 0.9)
                return 'image', confidence
            elif table_score > 0.3:
                # 表格类型
                confidence = min(table_score + 0.2, 0.9)
                return 'table', confidence
            elif text_score > 0.4:
                # 文本类型
                confidence = min(text_score + 0.1, 0.8)
                return 'text', confidence
            else:
                # 默认文本类型，置信度较低
                return 'text', 0.5
                
        except Exception as e:
            logger.warning(f"查询类型检测失败: {e}，使用默认文本类型")
            return 'text', 0.3
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'SimpleSmartProcessor',
            'unified_services': self.unified_services is not None,
            'features': [
                'type_detection',
                'single_type_processing',
                'hybrid_fallback',
                'confidence_based_routing'
            ]
        }
