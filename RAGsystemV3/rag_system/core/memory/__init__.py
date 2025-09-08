"""
RAG系统记忆模块

提供多轮对话记忆管理功能，包括：
- 会话管理
- 记忆存储和检索
- 记忆压缩
- 上下文增强
"""

from .conversation_memory_manager import ConversationMemoryManager
from .memory_compression_engine import MemoryCompressionEngine
from .memory_config_manager import MemoryConfigManager
from .models import ConversationSession, MemoryChunk, CompressionRecord, MemoryQuery, CompressionRequest
from .exceptions import (
    MemoryError,
    SessionNotFoundError,
    MemoryRetrievalError,
    CompressionError,
    MemoryStorageError,
    DatabaseError,
    ConfigurationError,
    ValidationError
)

__all__ = [
    'ConversationMemoryManager',
    'MemoryCompressionEngine', 
    'MemoryConfigManager',
    'ConversationSession',
    'MemoryChunk',
    'CompressionRecord',
    'MemoryQuery',
    'CompressionRequest',
    'MemoryError',
    'SessionNotFoundError',
    'MemoryRetrievalError',
    'CompressionError',
    'MemoryStorageError',
    'DatabaseError',
    'ConfigurationError',
    'ValidationError'
]

__version__ = '1.0.0'
