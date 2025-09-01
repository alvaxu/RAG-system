"""
查询路由器模块

RAG系统的查询路由器，负责查询类型判断和路由分发
严格按照33.V3_RAG查询处理模块详细设计文档实现
"""

import logging
from typing import Dict, List, Optional, Any

from .config_integration import ConfigIntegration
from .common_models import QueryType, QueryOptions, QueryResult
from .simple_smart_processor import SimpleSmartProcessor
from .simple_hybrid_processor import SimpleHybridProcessor
from .exceptions import (
    ServiceInitializationError, 
    QueryRoutingError, 
    ConfigurationError
)

logger = logging.getLogger(__name__)


class SimpleQueryRouter:
    """查询路由器 - 严格按照设计文档实现"""
    
    def __init__(self, config_integration: ConfigIntegration):
        """
        初始化查询路由器
        
        :param config_integration: 配置集成管理器实例
        """
        self.config = config_integration
        
        try:
            # 初始化处理器
            self.smart_processor = SimpleSmartProcessor(config_integration)
            self.hybrid_processor = SimpleHybridProcessor(config_integration)
            
            logger.info("查询路由器初始化完成")
            
        except (ServiceInitializationError, ConfigurationError) as e:
            logger.error(f"查询路由器初始化失败: {e}")
            raise ServiceInitializationError(f"查询路由器初始化失败: {e}") from e
        except Exception as e:
            logger.error(f"查询路由器初始化失败（未知错误）: {e}")
            raise ServiceInitializationError(f"查询路由器初始化失败: {e}") from e
    
    def route_query(self, query: str, query_type: str, options: QueryOptions) -> QueryResult:
        """
        查询路由分发主入口 - 严格按照设计文档实现
        
        :param query: 查询文本
        :param query_type: 查询类型
        :param options: 查询选项
        :return: 路由结果
        """
        try:
            logger.info(f"开始路由查询: {query[:50]}...，类型: {query_type}")
            
            result = QueryResult()
            
            # 查询类型判断和路由
            if query_type == QueryType.SMART.value:
                # 智能查询：转发到智能处理器
                result = self.smart_processor.process_smart_query(query, options)
                
            elif query_type == QueryType.HYBRID.value:
                # 混合查询：转发到混合处理器
                result = self.hybrid_processor.process_hybrid_query(query, options)
                
            elif query_type in [QueryType.TEXT.value, QueryType.IMAGE.value, QueryType.TABLE.value]:
                # 单类型查询：转发到智能处理器进行单类型处理
                result = self.smart_processor.process_single_type_query(query, query_type, options)
                
            elif query_type == QueryType.AUTO.value:
                # 自动查询：自动检测类型后路由
                detected_type = self._detect_query_type(query)
                if detected_type in [QueryType.TEXT.value, QueryType.IMAGE.value, QueryType.TABLE.value]:
                    result = self.smart_processor.process_single_type_query(query, detected_type, options)
                else:
                    # 不明确的类型，使用混合查询
                    result = self.hybrid_processor.process_hybrid_query(query, options)
            else:
                # 未知类型，默认使用智能查询
                logger.warning(f"未知查询类型: {query_type}，使用智能查询")
                result = self.smart_processor.process_smart_query(query, options)
            
            logger.info(f"查询路由完成，类型: {query_type}，结果状态: {result.success}")
            return result
            
        except (QueryRoutingError, ServiceInitializationError) as e:
            error_msg = f"查询路由失败: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            return result
        except Exception as e:
            error_msg = f"查询路由失败（未知错误）: {str(e)}"
            logger.error(error_msg)
            
            result = QueryResult()
            result.success = False
            result.error_message = error_msg
            return result
    
    def _detect_query_type(self, query: str) -> str:
        """
        自动检测查询类型
        
        :param query: 查询文本
        :return: 检测到的查询类型
        """
        try:
            # 图片相关关键词检测
            image_keywords = ['图片', '图像', '照片', '图表', '截图', '界面', '显示', '展示', '图标', 'logo']
            if any(keyword in query for keyword in image_keywords):
                return QueryType.IMAGE.value
            
            # 表格相关关键词检测
            table_keywords = ['表格', '数据', '统计', '数字', '金额', '数量', '比例', '百分比', '排名', '对比']
            if any(keyword in query for keyword in table_keywords):
                return QueryType.TABLE.value
            
            # 混合查询检测（包含多种类型关键词）
            has_image = any(keyword in query for keyword in image_keywords)
            has_table = any(keyword in query for keyword in table_keywords)
            has_text = len(query) > 20  # 长文本倾向于文本查询
            
            if has_image and has_table:
                return QueryType.HYBRID.value
            elif has_image and has_text:
                return QueryType.HYBRID.value
            elif has_table and has_text:
                return QueryType.HYBRID.value
            
            # 默认返回文本查询
            return QueryType.TEXT.value
            
        except Exception as e:
            logger.warning(f"查询类型检测失败: {e}，使用默认文本类型")
            return QueryType.TEXT.value
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'SimpleQueryRouter',
            'processors': {
                'smart_processor': self.smart_processor is not None,
                'hybrid_processor': self.hybrid_processor is not None
            },
            'supported_query_types': [qt.value for qt in QueryType],
            'features': [
                'query_routing',
                'type_detection',
                'smart_processing',
                'hybrid_processing'
            ]
        }
