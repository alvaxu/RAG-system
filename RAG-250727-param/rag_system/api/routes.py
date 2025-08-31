"""
API路由文件

定义RAG系统的所有API接口
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..core.query_processor import QueryProcessor, QueryRequest, QueryType

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


# 数据模型定义
class QueryRequestModel(BaseModel):
    """查询请求模型"""
    query_text: str
    query_type: str = "smart"
    max_results: int = 10
    enable_streaming: bool = True
    reranking_enabled: bool = True
    source_attribution: str = "reverse"


class QueryResponseModel(BaseModel):
    """查询响应模型"""
    query_id: str
    status: str
    answer: Dict[str, Any] = None
    sources: List[Dict[str, Any]] = []
    display_config: Dict[str, Any] = {}
    error_message: str = None


class HealthResponseModel(BaseModel):
    """健康检查响应模型"""
    status: str
    service: str
    version: str
    timestamp: float


# 全局查询处理器实例
query_processor = None


def get_query_processor() -> QueryProcessor:
    """获取查询处理器实例"""
    global query_processor
    if query_processor is None:
        query_processor = QueryProcessor()
        logger.info("查询处理器实例已创建")
    return query_processor


# API端点定义
@router.post("/query", response_model=QueryResponseModel)
async def process_query(request: QueryRequestModel):
    """
    处理用户查询请求
    
    Args:
        request: 查询请求参数
        
    Returns:
        QueryResponseModel: 查询结果
    """
    try:
        logger.info(f"收到查询请求: {request.query_text[:50]}...")
        
        # 获取查询处理器
        processor = get_query_processor()
        
        # 创建查询请求对象
        query_request = QueryRequest(
            query_text=request.query_text,
            query_type=QueryType(request.query_type)
        )
        query_request.max_results = request.max_results
        query_request.enable_streaming = request.enable_streaming
        
        # 处理查询
        result = processor.process_query(query_request)
        
        # 转换为响应模型
        response = QueryResponseModel(
            query_id=result.query_id,
            status=result.status,
            answer=result.answer,
            sources=result.sources,
            error_message=result.error_message
        )
        
        logger.info(f"查询处理完成: {result.query_id}")
        return response
        
    except Exception as e:
        logger.error(f"查询处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询处理失败: {str(e)}")


@router.get("/health", response_model=HealthResponseModel)
async def health_check():
    """健康检查端点"""
    return HealthResponseModel(
        status="healthy",
        service="V3 RAG系统",
        version="3.0.0",
        timestamp=__import__("time").time()
    )


@router.get("/status")
async def get_system_status():
    """获取系统状态"""
    try:
        processor = get_query_processor()
        
        status = {
            "system": "V3 RAG系统",
            "version": "3.0.0",
            "status": "running",
            "components": {
                "query_processor": "initialized" if processor else "not_initialized",
                "retrieval_engine": "initialized" if processor.retrieval_engine else "not_initialized",
                "reranking_service": "initialized" if processor.reranking_service else "not_initialized",
                "llm_caller": "initialized" if processor.llm_caller else "not_initialized"
            },
            "timestamp": __import__("time").time()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


@router.post("/test")
async def test_endpoint():
    """测试端点"""
    return {
        "message": "V3 RAG系统 API 测试成功",
        "timestamp": __import__("time").time()
    }


# 错误处理
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return {
        "error": "HTTP异常",
        "status_code": exc.status_code,
        "detail": exc.detail,
        "timestamp": __import__("time").time()
    }


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error(f"通用异常: {str(exc)}", exc_info=True)
    return {
        "error": "内部服务器错误",
        "message": str(exc),
        "timestamp": __import__("time").time()
    }
