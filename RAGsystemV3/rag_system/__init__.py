"""
V3版本RAG系统

这是一个基于V3向量数据库的智能问答系统，提供文本、图片、表格等多种内容的智能检索和问答服务。

主要功能：
- 智能查询处理
- 多模态内容召回
- 智能重排序
- LLM答案生成
- 溯源信息提取
- 智能展示模式选择

版本: 3.0.0
作者: V3开发团队
"""

__version__ = "3.0.0"
__author__ = "V3开发团队"
__description__ = "V3版本RAG智能问答系统"

from .core.query_processor import QueryProcessor
from .core.retrieval_engine import RetrievalEngine
from .core.reranking import RerankingService
from .core.llm import LLMCaller
from .core.attribution import AttributionService
from .core.display import DisplaySelector

__all__ = [
    "QueryProcessor",
    "RetrievalEngine", 
    "RerankingService",
    "LLMCaller",
    "AttributionService",
    "DisplaySelector"
]
