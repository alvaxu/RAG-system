'''
程序说明：

## 1. V2.0.0 QA系统包初始化文件
## 2. 定义版本信息和导出模块
## 3. 与老版本完全分离的独立架构
'''

__version__ = "2.0.0"
__author__ = "RAG-System Team"
__description__ = "RAG-System V2.0.0 - 智能问答系统重构版本"

# 导出主要模块
from .core import (
    BaseEngine,
    ImageEngine,
    TextEngine,
    TableEngine,
    HybridEngine
)

from .config import V2ConfigManager

__all__ = [
    'BaseEngine',
    'ImageEngine', 
    'TextEngine',
    'TableEngine',
    'HybridEngine',
    'V2ConfigManager'
]
