'''
程序说明：

## 1. V2.0.0 核心引擎包初始化文件
## 2. 导出所有查询引擎
## 3. 与老版本核心系统完全分离
'''

from .base_engine import BaseEngine, QueryResult, QueryType, EngineStatus, EngineConfig
from .image_engine import ImageEngine
from .text_engine import TextEngine
from .table_engine import TableEngine
from .hybrid_engine import HybridEngine

__all__ = [
    'BaseEngine',
    'QueryResult',
    'QueryType', 
    'EngineStatus',
    'EngineConfig',
    'ImageEngine',
    'TextEngine',
    'TableEngine',
    'HybridEngine'
]
