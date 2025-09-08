"""
记忆模块API数据模型

定义记忆模块RESTful API的请求和响应模型
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class SessionCreateRequest(BaseModel):
    """创建会话请求模型"""
    user_id: str = Field(..., min_length=1, max_length=100, description="用户标识")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="会话元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_123",
                "metadata": {
                    "source": "web",
                    "device": "desktop"
                }
            }
        }


class SessionResponse(BaseModel):
    """会话响应模型"""
    session_id: str = Field(..., description="会话唯一标识")
    user_id: str = Field(..., description="用户标识")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    status: str = Field(..., description="会话状态")
    metadata: Dict[str, Any] = Field(..., description="会话元数据")
    memory_count: int = Field(..., description="记忆数量")
    last_query: str = Field(..., description="最后查询内容")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_123",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:30:00Z",
                "status": "active",
                "metadata": {"source": "web"},
                "memory_count": 5,
                "last_query": "什么是人工智能？"
            }
        }


class MemoryAddRequest(BaseModel):
    """添加记忆请求模型"""
    content: str = Field(..., min_length=1, max_length=10000, description="记忆内容")
    content_type: str = Field(default="text", pattern="^(text|image|table)$", description="内容类型")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="相关性分数")
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="重要性分数")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="记忆元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "content": "用户询问了关于机器学习的问题",
                "content_type": "text",
                "relevance_score": 0.8,
                "importance_score": 0.7,
                "metadata": {"query_type": "technical"}
            }
        }


class MemoryResponse(BaseModel):
    """记忆响应模型"""
    chunk_id: str = Field(..., description="记忆块唯一标识")
    session_id: str = Field(..., description="所属会话ID")
    content: str = Field(..., description="记忆内容")
    content_type: str = Field(..., description="内容类型")
    relevance_score: float = Field(..., description="相关性分数")
    importance_score: float = Field(..., description="重要性分数")
    created_at: datetime = Field(..., description="创建时间")
    metadata: Dict[str, Any] = Field(..., description="记忆元数据")
    
    class Config:
        schema_extra = {
            "example": {
                "chunk_id": "mem_550e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "content": "用户询问了关于机器学习的问题",
                "content_type": "text",
                "relevance_score": 0.8,
                "importance_score": 0.7,
                "created_at": "2024-01-01T10:00:00Z",
                "metadata": {"query_type": "technical"}
            }
        }


class MemoryQueryRequest(BaseModel):
    """记忆查询请求模型"""
    query_text: str = Field(default="", min_length=0, max_length=1000, description="查询文本")
    max_results: int = Field(default=5, ge=1, le=100, description="最大返回结果数")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")
    content_types: List[str] = Field(default=["text"], description="内容类型过滤")
    time_range: Optional[Dict[str, str]] = Field(default=None, description="时间范围过滤")
    
    @validator('content_types')
    def validate_content_types(cls, v):
        valid_types = ["text", "image", "table"]
        for content_type in v:
            if content_type not in valid_types:
                raise ValueError(f"无效的内容类型: {content_type}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "机器学习相关的问题",
                "max_results": 5,
                "similarity_threshold": 0.7,
                "content_types": ["text"],
                "time_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-02T00:00:00Z"
                }
            }
        }


class CompressionRequest(BaseModel):
    """压缩请求模型"""
    strategy: str = Field(default="semantic", pattern="^(semantic|temporal|importance)$", description="压缩策略")
    threshold: int = Field(default=20, ge=1, le=1000, description="压缩阈值")
    max_ratio: float = Field(default=0.3, ge=0.1, le=1.0, description="最大压缩比例")
    force: bool = Field(default=False, description="是否强制压缩")
    
    class Config:
        schema_extra = {
            "example": {
                "strategy": "semantic",
                "threshold": 20,
                "max_ratio": 0.3,
                "force": False
            }
        }


class CompressionResponse(BaseModel):
    """压缩响应模型"""
    original_count: int = Field(..., description="原始记忆数量")
    compressed_count: int = Field(..., description="压缩后记忆数量")
    compression_ratio: float = Field(..., description="压缩比例")
    strategy: str = Field(..., description="压缩策略")
    compression_time: str = Field(..., description="压缩时间")
    
    class Config:
        schema_extra = {
            "example": {
                "original_count": 50,
                "compressed_count": 15,
                "compression_ratio": 0.3,
                "strategy": "semantic",
                "compression_time": "2024-01-01T10:00:00Z"
            }
        }


class MemoryStatsResponse(BaseModel):
    """记忆统计响应模型"""
    total_sessions: int = Field(..., description="总会话数")
    total_memories: int = Field(..., description="总记忆数")
    active_sessions: int = Field(..., description="活跃会话数")
    avg_memories_per_session: float = Field(..., description="平均每会话记忆数")
    last_activity: Optional[str] = Field(None, description="最后活动时间")
    
    class Config:
        schema_extra = {
            "example": {
                "total_sessions": 100,
                "total_memories": 5000,
                "active_sessions": 25,
                "avg_memories_per_session": 50.0,
                "last_activity": "2024-01-01T10:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error_code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    timestamp: str = Field(..., description="错误时间")
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "SESSION_NOT_FOUND",
                "message": "会话未找到",
                "details": {"session_id": "invalid_session_id"},
                "timestamp": "2024-01-01T10:00:00Z"
            }
        }


class SuccessResponse(BaseModel):
    """成功响应模型"""
    success: bool = Field(True, description="操作是否成功")
    message: str = Field(..., description="成功消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")
    timestamp: str = Field(..., description="响应时间")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {"session_id": "550e8400-e29b-41d4-a716-446655440000"},
                "timestamp": "2024-01-01T10:00:00Z"
            }
        }
