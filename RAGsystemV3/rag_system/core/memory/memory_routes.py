"""
记忆模块API路由

基于RAG系统V3的API设计规范，实现记忆模块的RESTful API接口
"""

import logging
import uuid
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from .conversation_memory_manager import ConversationMemoryManager
from .memory_config_manager import MemoryConfigManager
from .api_models import (
    SessionCreateRequest, SessionResponse, MemoryAddRequest, MemoryResponse,
    MemoryQueryRequest, CompressionRequest, CompressionResponse,
    MemoryStatsResponse, ErrorResponse, SuccessResponse
)
from .exceptions import (
    MemoryError, SessionNotFoundError, MemoryRetrievalError,
    MemoryStorageError, CompressionError, ValidationError
)

logger = logging.getLogger(__name__)

# 创建记忆模块API路由器
router = APIRouter(prefix="/memory", tags=["Memory Module"])

# 全局记忆管理器实例
memory_manager: ConversationMemoryManager = None
config_manager: MemoryConfigManager = None


def get_memory_manager() -> ConversationMemoryManager:
    """
    获取记忆管理器实例的依赖注入函数
    
    Returns:
        ConversationMemoryManager: 记忆管理器实例
        
    Raises:
        HTTPException: 记忆管理器未初始化
    """
    if not memory_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="记忆模块未初始化",
            headers={"X-Error-Code": "MEMORY_SERVICE_UNAVAILABLE"}
        )
    return memory_manager


def get_config_manager() -> MemoryConfigManager:
    """
    获取配置管理器实例的依赖注入函数
    
    Returns:
        MemoryConfigManager: 配置管理器实例
        
    Raises:
        HTTPException: 配置管理器未初始化
    """
    if not config_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="配置管理器未初始化",
            headers={"X-Error-Code": "CONFIG_SERVICE_UNAVAILABLE"}
        )
    return config_manager


def generate_request_id() -> str:
    """生成请求ID"""
    return str(uuid.uuid4())


def handle_memory_error(e: MemoryError) -> JSONResponse:
    """
    处理记忆模块异常
    
    Args:
        e: 记忆模块异常
        
    Returns:
        JSONResponse: 错误响应
    """
    error_response = ErrorResponse(
        error_code=e.error_code,
        message=e.message,
        details=e.details,
        timestamp=datetime.now().isoformat()
    )
    
    # 根据异常类型确定HTTP状态码
    if isinstance(e, SessionNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(e, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(e, MemoryRetrievalError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(e, MemoryStorageError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(e, CompressionError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict(),
        headers={"X-Error-Code": e.error_code}
    )


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    manager: ConversationMemoryManager = Depends(get_memory_manager)
):
    """
    创建新的对话会话
    
    Args:
        request: 创建会话请求
        manager: 记忆管理器实例
        
    Returns:
        SessionResponse: 创建的会话信息
        
    Raises:
        HTTPException: 创建会话失败
    """
    try:
        request_id = generate_request_id()
        logger.info(f"创建会话请求 [{request_id}]: 用户={request.user_id}")
        
        # 创建会话
        session = manager.create_session(
            user_id=request.user_id,
            metadata=request.metadata
        )
        
        # 构建响应
        response = SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            status=session.status,
            metadata=session.metadata,
            memory_count=session.memory_count,
            last_query=session.last_query
        )
        
        logger.info(f"会话创建成功 [{request_id}]: {session.session_id}")
        return response
        
    except MemoryError as e:
        logger.error(f"创建会话失败 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except Exception as e:
        logger.error(f"创建会话异常 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建会话失败",
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    manager: ConversationMemoryManager = Depends(get_memory_manager)
):
    """
    获取会话信息
    
    Args:
        session_id: 会话ID
        manager: 记忆管理器实例
        
    Returns:
        SessionResponse: 会话信息
        
    Raises:
        HTTPException: 获取会话失败
    """
    try:
        request_id = generate_request_id()
        logger.info(f"获取会话请求 [{request_id}]: {session_id}")
        
        # 获取会话
        session = manager.get_session(session_id)
        
        # 构建响应
        response = SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            status=session.status,
            metadata=session.metadata,
            memory_count=session.memory_count,
            last_query=session.last_query
        )
        
        logger.info(f"会话获取成功 [{request_id}]: {session_id}")
        return response
        
    except SessionNotFoundError as e:
        logger.warning(f"会话未找到 [{request_id}]: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except Exception as e:
        logger.error(f"获取会话异常 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话失败",
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    user_id: str = None,
    session_status: str = Query(default="active", description="会话状态"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量限制"),
    manager: ConversationMemoryManager = Depends(get_memory_manager)
):
    """
    列出会话
    
    Args:
        user_id: 用户ID（可选）
        session_status: 会话状态
        limit: 返回数量限制
        manager: 记忆管理器实例
        
    Returns:
        List[SessionResponse]: 会话列表
        
    Raises:
        HTTPException: 列出会话失败
    """
    try:
        request_id = generate_request_id()
        logger.info(f"列出会话请求 [{request_id}]: 用户={user_id}, 状态={session_status}")
        
        # 列出会话
        sessions = manager.list_sessions(
            user_id=user_id,
            status=session_status,
            limit=limit
        )
        
        # 构建响应
        responses = []
        for session in sessions:
            response = SessionResponse(
                session_id=session.session_id,
                user_id=session.user_id,
                created_at=session.created_at,
                updated_at=session.updated_at,
                status=session.status,
                metadata=session.metadata,
                memory_count=session.memory_count,
                last_query=session.last_query
            )
            responses.append(response)
        
        logger.info(f"会话列表获取成功 [{request_id}]: 数量={len(responses)}")
        return responses
        
    except Exception as e:
        logger.error(f"列出会话异常 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="列出会话失败",
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


@router.delete("/sessions/{session_id}", response_model=SuccessResponse)
async def delete_session(
    session_id: str,
    manager: ConversationMemoryManager = Depends(get_memory_manager)
):
    """
    删除会话及其所有记忆
    
    Args:
        session_id: 会话ID
        manager: 记忆管理器实例
        
    Returns:
        SuccessResponse: 删除成功响应
        
    Raises:
        HTTPException: 删除会话失败
    """
    try:
        request_id = generate_request_id()
        logger.info(f"删除会话请求 [{request_id}]: 会话={session_id}")
        
        # 删除会话
        success = manager.delete_session(session_id)
        
        if success:
            logger.info(f"会话删除成功 [{request_id}]: {session_id}")
            return SuccessResponse(
                success=True,
                message=f"会话 {session_id} 及其所有记忆已删除",
                timestamp=datetime.now().isoformat()
            )
        else:
            logger.warning(f"会话删除失败 [{request_id}]: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除会话失败",
                headers={"X-Error-Code": "DELETE_FAILED"}
            )
        
    except SessionNotFoundError as e:
        logger.warning(f"会话未找到 [{request_id}]: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except Exception as e:
        logger.error(f"删除会话异常 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除会话失败",
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


@router.post("/sessions/{session_id}/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def add_memory(
    session_id: str,
    request: MemoryAddRequest,
    manager: ConversationMemoryManager = Depends(get_memory_manager)
):
    """
    添加记忆
    
    Args:
        session_id: 会话ID
        request: 添加记忆请求
        manager: 记忆管理器实例
        
    Returns:
        MemoryResponse: 创建的记忆信息
        
    Raises:
        HTTPException: 添加记忆失败
    """
    try:
        request_id = generate_request_id()
        logger.info(f"添加记忆请求 [{request_id}]: 会话={session_id}")
        
        # 添加记忆
        memory = manager.add_memory(
            session_id=session_id,
            content=request.content,
            content_type=request.content_type,
            relevance_score=request.relevance_score,
            importance_score=request.importance_score,
            metadata=request.metadata
        )
        
        # 构建响应
        response = MemoryResponse(
            chunk_id=memory.chunk_id,
            session_id=memory.session_id,
            content=memory.content,
            content_type=memory.content_type,
            relevance_score=memory.relevance_score,
            importance_score=memory.importance_score,
            created_at=memory.created_at,
            metadata=memory.metadata
        )
        
        logger.info(f"记忆添加成功 [{request_id}]: {memory.chunk_id}")
        return response
        
    except SessionNotFoundError as e:
        logger.warning(f"会话未找到 [{request_id}]: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except MemoryStorageError as e:
        logger.error(f"记忆存储失败 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except Exception as e:
        logger.error(f"添加记忆异常 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加记忆失败",
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


@router.get("/sessions/{session_id}/memories", response_model=List[MemoryResponse])
async def get_memories(
    session_id: str,
    max_results: int = Query(default=100, ge=1, le=1000, description="最大返回结果数"),
    manager: ConversationMemoryManager = Depends(get_memory_manager)
):
    """
    获取会话的所有记忆
    
    Args:
        session_id: 会话ID
        max_results: 最大返回结果数
        manager: 记忆管理器实例
        
    Returns:
        List[MemoryResponse]: 记忆列表
        
    Raises:
        HTTPException: 获取记忆失败
    """
    try:
        request_id = generate_request_id()
        logger.info(f"获取记忆请求 [{request_id}]: 会话={session_id}")
        
        # 获取会话的所有记忆
        memories = manager.get_session_memories(session_id, max_results)
        
        # 构建响应
        responses = []
        for memory in memories:
            response = MemoryResponse(
                chunk_id=memory.chunk_id,
                session_id=memory.session_id,
                content=memory.content,
                content_type=memory.content_type,
                relevance_score=memory.relevance_score,
                importance_score=memory.importance_score,
                created_at=memory.created_at,
                metadata=memory.metadata
            )
            responses.append(response)
        
        logger.info(f"获取记忆成功 [{request_id}]: 返回 {len(responses)} 条记忆")
        return responses
        
    except SessionNotFoundError as e:
        logger.warning(f"会话未找到 [{request_id}]: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except Exception as e:
        logger.error(f"获取记忆异常 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取记忆失败",
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


@router.post("/sessions/{session_id}/memories/query", response_model=List[MemoryResponse])
async def query_memories(
    session_id: str,
    request: MemoryQueryRequest,
    manager: ConversationMemoryManager = Depends(get_memory_manager)
):
    """
    查询记忆
    
    Args:
        session_id: 会话ID
        request: 查询记忆请求
        manager: 记忆管理器实例
        
    Returns:
        List[MemoryResponse]: 相关记忆列表
        
    Raises:
        HTTPException: 查询记忆失败
    """
    try:
        request_id = generate_request_id()
        logger.info(f"查询记忆请求 [{request_id}]: 会话={session_id}, 查询={request.query_text[:50]}...")
        
        # 构建查询对象
        from .models import MemoryQuery
        query = MemoryQuery(
            query_text=request.query_text,
            session_id=session_id,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold,
            content_types=request.content_types,
            time_range=request.time_range
        )
        
        # 查询记忆
        memories = manager.retrieve_memories(query)
        
        # 构建响应
        responses = []
        for memory in memories:
            response = MemoryResponse(
                chunk_id=memory.chunk_id,
                session_id=memory.session_id,
                content=memory.content,
                content_type=memory.content_type,
                relevance_score=memory.relevance_score,
                importance_score=memory.importance_score,
                created_at=memory.created_at,
                metadata=memory.metadata
            )
            responses.append(response)
        
        logger.info(f"记忆查询成功 [{request_id}]: 结果数量={len(responses)}")
        return responses
        
    except SessionNotFoundError as e:
        logger.warning(f"会话未找到 [{request_id}]: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except MemoryRetrievalError as e:
        logger.error(f"记忆检索失败 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except Exception as e:
        logger.error(f"查询记忆异常 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询记忆失败",
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


@router.post("/sessions/{session_id}/compress", response_model=CompressionResponse)
async def compress_memories(
    session_id: str,
    request: CompressionRequest,
    manager: ConversationMemoryManager = Depends(get_memory_manager)
):
    """
    压缩会话记忆
    
    Args:
        session_id: 会话ID
        request: 压缩请求
        manager: 记忆管理器实例
        
    Returns:
        CompressionResponse: 压缩结果
        
    Raises:
        HTTPException: 压缩记忆失败
    """
    try:
        request_id = generate_request_id()
        logger.info(f"压缩记忆请求 [{request_id}]: 会话={session_id}, 策略={request.strategy}")
        
        # 构建压缩请求对象
        from .models import CompressionRequest as MemoryCompressionRequest
        compression_request = MemoryCompressionRequest(
            session_id=session_id,
            strategy=request.strategy,
            threshold=request.threshold,
            max_ratio=request.max_ratio,
            force=request.force
        )
        
        # 执行压缩
        compressed_memories, compression_info = manager.compress_session_memories(
            session_id=session_id,
            request=compression_request
        )
        
        # 构建响应
        response = CompressionResponse(
            original_count=compression_info['original_count'],
            compressed_count=compression_info['compressed_count'],
            compression_ratio=compression_info['compression_ratio'],
            strategy=compression_info['strategy'],
            compression_time=compression_info['compression_time']
        )
        
        logger.info(f"记忆压缩成功 [{request_id}]: 压缩比例={response.compression_ratio:.2f}")
        return response
        
    except SessionNotFoundError as e:
        logger.warning(f"会话未找到 [{request_id}]: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except CompressionError as e:
        logger.error(f"记忆压缩失败 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message,
            headers={"X-Error-Code": e.error_code}
        )
    except Exception as e:
        logger.error(f"压缩记忆异常 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="压缩记忆失败",
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    manager: ConversationMemoryManager = Depends(get_memory_manager)
):
    """
    获取记忆统计信息
    
    Args:
        manager: 记忆管理器实例
        
    Returns:
        MemoryStatsResponse: 记忆统计信息
        
    Raises:
        HTTPException: 获取统计信息失败
    """
    try:
        request_id = generate_request_id()
        logger.info(f"获取记忆统计请求 [{request_id}]")
        
        # 获取统计信息
        stats = manager.get_memory_stats()
        
        # 构建响应
        response = MemoryStatsResponse(
            total_sessions=stats.get('total_sessions', 0),
            total_memories=stats.get('total_memories', 0),
            active_sessions=stats.get('active_sessions', 0),
            avg_memories_per_session=stats.get('avg_memories_per_session', 0.0),
            last_activity=stats.get('last_activity').isoformat() if stats.get('last_activity') else None
        )
        
        logger.info(f"记忆统计获取成功 [{request_id}]: 会话={response.total_sessions}, 记忆={response.total_memories}")
        return response
        
    except Exception as e:
        logger.error(f"获取记忆统计异常 [{request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取记忆统计失败",
            headers={"X-Error-Code": "INTERNAL_ERROR"}
        )


def initialize_memory_module(config_integration, vector_db_integration=None, llm_caller=None):
    """
    初始化记忆模块
    
    Args:
        config_integration: 配置集成管理器
        vector_db_integration: 向量数据库集成实例（可选）
        llm_caller: LLM调用器实例（可选）
    """
    global memory_manager, config_manager
    
    try:
        # 初始化配置管理器
        config_manager = MemoryConfigManager(config_integration)
        
        # 检查记忆模块是否启用
        if not config_manager.is_enabled():
            logger.info("记忆模块已禁用")
            return
        
        # 初始化路径管理器（在API层导入）
        from db_system.config.path_manager import PathManager
        # 指定正确的项目根目录
        import os
        current_file = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        path_manager = PathManager(project_root)
        
        # 初始化记忆管理器
        memory_manager = ConversationMemoryManager(
            config_manager=config_manager,
            vector_db_integration=vector_db_integration,
            llm_caller=llm_caller,
            path_manager=path_manager
        )
        
        logger.info("记忆模块初始化完成")
        
    except Exception as e:
        logger.error(f"记忆模块初始化失败: {e}")
        raise


def cleanup_memory_module():
    """清理记忆模块资源"""
    global memory_manager
    
    try:
        if memory_manager:
            memory_manager.close()
            memory_manager = None
        logger.info("记忆模块资源已清理")
        
    except Exception as e:
        logger.error(f"清理记忆模块资源失败: {e}")
