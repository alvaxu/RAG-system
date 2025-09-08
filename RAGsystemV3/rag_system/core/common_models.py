"""
共享数据模型模块

RAG系统的共享数据模型，避免循环导入问题
"""

from enum import Enum
from typing import Dict, List, Optional, Any


class QueryType(Enum):
    """查询类型枚举"""
    SMART = "smart"           # 智能查询
    HYBRID = "hybrid"         # 混合查询
    TEXT = "text"             # 文本查询
    IMAGE = "image"           # 图片查询
    TABLE = "table"           # 表格查询
    AUTO = "auto"             # 自动检测


class QueryOptions:
    """查询选项数据类"""
    
    def __init__(self, max_results: int = 10, 
                 relevance_threshold: float = 0.5,
                 context_length_limit: int = 4000,
                 enable_streaming: bool = True,
                 context_memories: List[Dict[str, Any]] = None,
                 metadata: Dict[str, Any] = None):
        self.max_results = max_results
        self.relevance_threshold = relevance_threshold
        self.context_length_limit = context_length_limit
        self.enable_streaming = enable_streaming
        self.context_memories = context_memories or []
        self.metadata = metadata or {}


class QueryResult:
    """查询结果数据类"""
    
    def __init__(self):
        self.success = False
        self.query_type = None
        self.answer = None
        self.results = []
        self.processing_metadata = {}
        self.metadata = {}
        self.error_message = None
