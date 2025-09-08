"""
记忆模块数据模型

定义记忆模块使用的所有数据结构和模型
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


@dataclass
class ConversationSession:
    """
    对话会话数据模型
    
    Attributes:
        session_id: 会话唯一标识
        user_id: 用户标识
        created_at: 创建时间
        updated_at: 更新时间
        status: 会话状态 (active, archived, deleted)
        metadata: 会话元数据
        memory_count: 记忆数量
        last_query: 最后查询内容
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, archived, deleted
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_count: int = 0
    last_query: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status,
            'metadata': self.metadata,
            'memory_count': self.memory_count,
            'last_query': self.last_query
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSession':
        """从字典创建实例"""
        return cls(
            session_id=data.get('session_id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
            status=data.get('status', 'active'),
            metadata=data.get('metadata', {}),
            memory_count=data.get('memory_count', 0),
            last_query=data.get('last_query', '')
        )


@dataclass
class MemoryChunk:
    """
    记忆块数据模型
    
    Attributes:
        chunk_id: 记忆块唯一标识
        session_id: 所属会话ID
        content: 记忆内容
        content_type: 内容类型 (text, image, table)
        relevance_score: 相关性分数
        importance_score: 重要性分数
        created_at: 创建时间
        metadata: 记忆元数据
        vector_embedding: 向量嵌入（可选）
    """
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    content: str = ""
    content_type: str = "text"  # text, image, table
    relevance_score: float = 0.0
    importance_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    vector_embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'chunk_id': self.chunk_id,
            'session_id': self.session_id,
            'content': self.content,
            'content_type': self.content_type,
            'relevance_score': self.relevance_score,
            'importance_score': self.importance_score,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata,
            'vector_embedding': self.vector_embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryChunk':
        """从字典创建实例"""
        return cls(
            chunk_id=data.get('chunk_id', str(uuid.uuid4())),
            session_id=data.get('session_id', ''),
            content=data.get('content', ''),
            content_type=data.get('content_type', 'text'),
            relevance_score=data.get('relevance_score', 0.0),
            importance_score=data.get('importance_score', 0.0),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            metadata=data.get('metadata', {}),
            vector_embedding=data.get('vector_embedding')
        )


@dataclass
class CompressionRecord:
    """
    压缩记录数据模型
    
    Attributes:
        record_id: 记录唯一标识
        session_id: 所属会话ID
        original_count: 原始记忆数量
        compressed_count: 压缩后记忆数量
        compression_ratio: 压缩比例
        strategy: 压缩策略
        created_at: 创建时间
        metadata: 压缩元数据
    """
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    original_count: int = 0
    compressed_count: int = 0
    compression_ratio: float = 0.0
    strategy: str = "semantic"  # semantic, temporal, importance
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'record_id': self.record_id,
            'session_id': self.session_id,
            'original_count': self.original_count,
            'compressed_count': self.compressed_count,
            'compression_ratio': self.compression_ratio,
            'strategy': self.strategy,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompressionRecord':
        """从字典创建实例"""
        return cls(
            record_id=data.get('record_id', str(uuid.uuid4())),
            session_id=data.get('session_id', ''),
            original_count=data.get('original_count', 0),
            compressed_count=data.get('compressed_count', 0),
            compression_ratio=data.get('compression_ratio', 0.0),
            strategy=data.get('strategy', 'semantic'),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            metadata=data.get('metadata', {})
        )


@dataclass
class MemoryQuery:
    """
    记忆查询数据模型
    
    Attributes:
        query_text: 查询文本
        session_id: 会话ID
        max_results: 最大返回结果数
        similarity_threshold: 相似度阈值
        content_types: 内容类型过滤
        time_range: 时间范围过滤
    """
    query_text: str = ""
    session_id: str = ""
    max_results: int = 5
    similarity_threshold: float = 0.7
    content_types: List[str] = field(default_factory=lambda: ["text"])
    time_range: Optional[Dict[str, datetime]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'query_text': self.query_text,
            'session_id': self.session_id,
            'max_results': self.max_results,
            'similarity_threshold': self.similarity_threshold,
            'content_types': self.content_types,
            'time_range': {
                'start': self.time_range['start'].isoformat() if self.time_range and 'start' in self.time_range else None,
                'end': self.time_range['end'].isoformat() if self.time_range and 'end' in self.time_range else None
            } if self.time_range else None
        }


@dataclass
class CompressionRequest:
    """
    压缩请求数据模型
    
    Attributes:
        session_id: 会话ID
        strategy: 压缩策略
        threshold: 压缩阈值
        max_ratio: 最大压缩比例
        force: 是否强制压缩
    """
    session_id: str = ""
    strategy: str = "semantic"  # semantic, temporal, importance
    threshold: int = 20
    max_ratio: float = 0.3
    force: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'session_id': self.session_id,
            'strategy': self.strategy,
            'threshold': self.threshold,
            'max_ratio': self.max_ratio,
            'force': self.force
        }
