'''
程序说明：
## 1. RAG-System V2.0.0 核心模块
## 2. 模块化设计，支持图片、文本、表格分别处理
## 3. 插件化架构，易于扩展和维护
## 4. 向后兼容，不影响现有功能
'''

__version__ = "2.0.0"
__author__ = "RAG项目团队"
__description__ = "RAG-System V2.0.0 核心模块"

# 导出核心类
from .base_engine import BaseEngine
from .image_engine import ImageEngine
from .text_engine import TextEngine
from .table_engine import TableEngine

__all__ = [
    'BaseEngine',
    'ImageEngine', 
    'TextEngine',
    'TableEngine'
]
