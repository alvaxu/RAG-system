'''
程序说明：
## 1. 基础引擎类，定义所有引擎的通用接口
## 2. 提供统一的配置管理和日志记录
## 3. 支持插件化扩展和自定义实现
## 4. 向后兼容现有系统
'''

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

# 配置日志
logger = logging.getLogger(__name__)


class QueryType(Enum):
    """查询类型枚举"""
    IMAGE = "image"
    TEXT = "text"
    TABLE = "table"
    HYBRID = "hybrid"
    SMART = "smart"
    AUTO = "auto"


class EngineStatus(Enum):
    """引擎状态枚举"""
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class QueryResult:
    """查询结果数据类"""
    success: bool
    query: str
    query_type: QueryType
    results: List[Any]
    total_count: int
    processing_time: float
    engine_name: str
    metadata: Dict[str, Any]
    error_message: Optional[str] = None
    
    def __len__(self):
        """返回结果数量"""
        return len(self.results) if self.results else 0


@dataclass
class EngineConfig:
    """引擎配置数据类"""
    enabled: bool = True
    name: str = "base_engine"
    version: str = "2.0.0"
    debug: bool = False
    max_results: int = 10
    timeout: float = 30.0
    cache_enabled: bool = True
    cache_ttl: int = 300


class BaseEngine(ABC):
    """
    基础引擎抽象类
    
    所有专用引擎都应该继承此类，实现统一的接口
    """
    
    def __init__(self, config: EngineConfig):
        """
        初始化基础引擎
        
        :param config: 引擎配置
        """
        self.config = config
        self.status = EngineStatus.INITIALIZING
        self.name = config.name
        self.version = config.version
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
        # 性能统计
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0
        }
        
        # 注意：不在这里调用_initialize，让子类在设置完必要属性后调用
        # self._initialize()
    
    def _initialize(self):
        """初始化引擎内部组件"""
        try:
            self._setup_components()
            self._validate_config()
            self.status = EngineStatus.READY
            self.logger.info(f"引擎 {self.name} 初始化成功")
        except Exception as e:
            self.status = EngineStatus.ERROR
            self.logger.error(f"引擎 {self.name} 初始化失败: {e}")
            raise
    
    @abstractmethod
    def _setup_components(self):
        """设置引擎组件 - 子类必须实现"""
        pass
    
    @abstractmethod
    def _validate_config(self):
        """验证配置 - 子类必须实现"""
        pass
    
    @abstractmethod
    def process_query(self, query: str, **kwargs) -> QueryResult:
        """处理查询 - 子类必须实现"""
        pass
    
    def is_ready(self) -> bool:
        """检查引擎是否就绪"""
        return self.status == EngineStatus.READY
    
    def is_enabled(self) -> bool:
        """检查引擎是否启用"""
        return self.config.enabled and self.is_ready()
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态信息"""
        return {
            'name': self.name,
            'version': self.version,
            'status': self.status.value,
            'enabled': self.config.enabled,
            'stats': self.stats.copy()
        }
    
    def _update_stats(self, success: bool, processing_time: float):
        """更新性能统计"""
        self.stats['total_queries'] += 1
        if success:
            self.stats['successful_queries'] += 1
        else:
            self.stats['failed_queries'] += 1
        
        self.stats['total_processing_time'] += processing_time
        self.stats['average_processing_time'] = (
            self.stats['total_processing_time'] / self.stats['total_queries']
        )
    
    def _execute_with_timing(self, func, *args, **kwargs):
        """执行函数并记录时间"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            processing_time = time.time() - start_time
            self._update_stats(True, processing_time)
            return result, processing_time
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(False, processing_time)
            raise
    
    def reset_stats(self):
        """重置性能统计"""
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0
        }
        self.logger.info(f"引擎 {self.name} 统计已重置")
    
    def enable(self):
        """启用引擎"""
        if self.is_ready():
            self.config.enabled = True
            self.logger.info(f"引擎 {self.name} 已启用")
        else:
            self.logger.warning(f"引擎 {self.name} 未就绪，无法启用")
    
    def disable(self):
        """禁用引擎"""
        self.config.enabled = False
        self.logger.info(f"引擎 {self.name} 已禁用")
    
    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name}, status={self.status.value})"
    
    def __repr__(self):
        return self.__str__()
