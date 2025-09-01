'''
程序说明：
## 1. Reranking服务工厂类
## 2. 负责创建和管理不同类型的Reranking服务
## 3. 支持动态配置和服务扩展
## 4. 提供统一的服务创建接口
'''

import logging
from typing import Dict, Type, Optional, Any
from .base_reranking_service import BaseRerankingService
from .text_reranking_service import TextRerankingService
from .table_reranking_service import TableRerankingService
from .image_reranking_service import ImageRerankingService

logger = logging.getLogger(__name__)


class RerankingServiceFactory:
    """
    Reranking服务工厂类
    
    负责创建和管理不同类型的Reranking服务实例
    """
    
    def __init__(self):
        """初始化工厂类"""
        # 注册支持的服务类型
        self._services: Dict[str, Type[BaseRerankingService]] = {
            'text': TextRerankingService,
            'table': TableRerankingService,
            'image': ImageRerankingService,
            # 'hybrid': HybridRerankingService,
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Reranking服务工厂初始化完成，支持的服务类型: {list(self._services.keys())}")
    
    def create_service(self, service_type: str, config: Dict[str, Any]) -> Optional[BaseRerankingService]:
        """
        创建Reranking服务实例
        
        :param service_type: 服务类型
        :param config: 服务配置
        :return: Reranking服务实例，如果类型不支持则返回None
        """
        try:
            if service_type not in self._services:
                self.logger.warning(f"不支持的Reranking服务类型: {service_type}")
                return None
            
            service_class = self._services[service_type]
            service_instance = service_class(config)
            
            self.logger.info(f"成功创建 {service_type} Reranking服务")
            return service_instance
            
        except Exception as e:
            self.logger.error(f"创建 {service_type} Reranking服务失败: {e}")
            return None
    
    def get_supported_types(self) -> list[str]:
        """
        获取支持的服务类型列表
        
        :return: 支持的服务类型列表
        """
        return list(self._services.keys())
    
    def is_service_type_supported(self, service_type: str) -> bool:
        """
        检查指定的服务类型是否支持
        
        :param service_type: 服务类型
        :return: 是否支持
        """
        return service_type in self._services
    
    def register_service(self, service_type: str, service_class: Type[BaseRerankingService]):
        """
        注册新的服务类型
        
        :param service_type: 服务类型名称
        :param service_class: 服务类
        """
        if not issubclass(service_class, BaseRerankingService):
            raise ValueError(f"服务类必须继承自BaseRerankingService: {service_class}")
        
        self._services[service_type] = service_class
        self.logger.info(f"注册新的Reranking服务类型: {service_type}")
    
    def get_service_info(self, service_type: str) -> Optional[Dict[str, Any]]:
        """
        获取服务信息
        
        :param service_type: 服务类型
        :return: 服务信息字典
        """
        if service_type not in self._services:
            return None
        
        service_class = self._services[service_type]
        return {
            'type': service_type,
            'class': service_class.__name__,
            'module': service_class.__module__,
            'supported_types': service_class.get_supported_types() if hasattr(service_class, 'get_supported_types') else []
        }
    
    def list_all_services(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有注册的服务信息
        
        :return: 所有服务的详细信息
        """
        services_info = {}
        for service_type in self._services:
            services_info[service_type] = self.get_service_info(service_type)
        return services_info


# 创建全局工厂实例
_global_factory = None

def get_reranking_service_factory() -> RerankingServiceFactory:
    """
    获取全局Reranking服务工厂实例
    
    :return: 全局工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = RerankingServiceFactory()
    return _global_factory

def create_reranking_service(service_type: str, config: Dict[str, Any]) -> Optional[BaseRerankingService]:
    """
    便捷函数：创建Reranking服务实例
    
    :param service_type: 服务类型
    :param config: 服务配置
    :return: Reranking服务实例
    """
    factory = get_reranking_service_factory()
    return factory.create_service(service_type, config)
