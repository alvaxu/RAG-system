"""
RAG系统API路由模块

RAG系统的API路由模块，负责定义所有RESTful API端点
为RAG系统提供完整的HTTP接口服务
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.query_processor import QueryProcessor
from ..core.retrieval import RetrievalEngine
from ..core.llm_caller import LLMCaller
from ..core.reranking_enhanced import MultiModelReranker
from ..core.attribution import AttributionService
from ..core.display import DisplayService
from ..core.config_integration import ConfigIntegration
from ..core.vector_db_integration import VectorDBIntegration
from ..core.metadata_manager import RAGMetadataManager

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/api/v1", tags=["RAG System"])

# 全局服务实例（在应用启动时初始化）
rag_services = {}


def get_rag_services():
    """获取RAG服务实例的依赖注入函数"""
    if not rag_services:
        raise HTTPException(status_code=503, detail="RAG服务未初始化")
    return rag_services


# 请求/响应模型定义
class QueryRequest(BaseModel):
    """查询请求模型 - 适配新架构"""
    query: str = Field(..., description="用户查询文本", min_length=1, max_length=1000)
    query_type: Optional[str] = Field("auto", description="查询类型", example="auto")
    max_results: Optional[int] = Field(10, description="最大结果数量", ge=1, le=100)
    relevance_threshold: Optional[float] = Field(0.5, description="相关性阈值", ge=0.0, le=1.0)
    context_length_limit: Optional[int] = Field(4000, description="上下文长度限制", ge=1000, le=8000)
    enable_streaming: Optional[bool] = Field(True, description="是否启用流式响应")
    include_sources: Optional[bool] = Field(True, description="是否包含来源信息")
    include_attribution: Optional[bool] = Field(True, description="是否包含溯源信息")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询文本", min_length=1, max_length=1000)
    content_type: Optional[str] = Field("all", description="内容类型过滤", example="text")
    max_results: Optional[int] = Field(20, description="最大结果数量", ge=1, le=100)
    similarity_threshold: Optional[float] = Field(0.5, description="相似度阈值", ge=0.0, le=1.0)
    search_strategy: Optional[str] = Field("smart", description="搜索策略", example="smart")


class RerankRequest(BaseModel):
    """重排序请求模型"""
    query: str = Field(..., description="查询文本")
    documents: List[Dict[str, Any]] = Field(..., description="待重排序的文档列表")
    top_k: Optional[int] = Field(10, description="返回前k个结果", ge=1, le=100)


class AttributionRequest(BaseModel):
    """溯源请求模型"""
    answer_id: str = Field(..., description="答案ID")
    display_mode: Optional[str] = Field("summary", description="显示模式", example="summary")


class QueryResponse(BaseModel):
    """查询响应模型 - 适配新架构"""
    success: bool = Field(..., description="查询是否成功")
    query_type: Optional[str] = Field(None, description="检测到的查询类型")
    answer: Optional[str] = Field(None, description="生成的答案")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="检索结果")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="处理元数据")
    error_message: Optional[str] = Field(None, description="错误信息")


class SearchResponse(BaseModel):
    """搜索响应模型"""
    query: str = Field(..., description="搜索查询")
    results: List[Dict[str, Any]] = Field(..., description="搜索结果")
    total_count: int = Field(..., description="总结果数量")
    processing_time: float = Field(..., description="处理时间（秒）")
    search_stats: Dict[str, Any] = Field(default_factory=dict, description="搜索统计信息")


class RerankResponse(BaseModel):
    """重排序响应模型"""
    query: str = Field(..., description="查询文本")
    reranked_documents: List[Dict[str, Any]] = Field(..., description="重排序后的文档")
    processing_time: float = Field(..., description="处理时间（秒）")


class AttributionResponse(BaseModel):
    """溯源响应模型"""
    answer_id: str = Field(..., description="答案ID")
    sources: List[Dict[str, Any]] = Field(..., description="来源信息")
    overall_confidence: float = Field(..., description="整体置信度")
    attribution_summary: str = Field(..., description="溯源摘要")
    processing_time: float = Field(..., description="处理时间（秒）")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(..., description="检查时间")
    version: str = Field(..., description="服务版本")
    services: Dict[str, Any] = Field(..., description="各服务状态")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="错误详情")
    timestamp: datetime = Field(..., description="错误时间")
    request_id: Optional[str] = Field(None, description="请求ID")


# 健康检查端点
@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """RAG系统健康检查"""
    try:
        services = get_rag_services()
        
        # 检查各服务状态
        service_status = {}
        for service_name, service_instance in services.items():
            if hasattr(service_instance, 'get_service_status'):
                service_status[service_name] = service_instance.get_service_status()
            else:
                service_status[service_name] = {'status': 'unknown'}
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="3.0.0",
            services=service_status
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="服务不可用")


# 查询处理端点 - 适配新架构
@router.post("/query", response_model=QueryResponse, summary="智能查询")
async def process_query(
    request: QueryRequest,
    services: Dict = Depends(get_rag_services)
):
    """处理用户查询，生成智能答案 - 新架构版本"""
    try:
        start_time = datetime.now()
        
        # 获取查询处理器
        query_processor = services.get('query_processor')
        if not query_processor:
            raise HTTPException(status_code=503, detail="查询处理器不可用")
        
        # 构建查询选项
        options = {
            'max_results': request.max_results,
            'relevance_threshold': request.relevance_threshold,
            'context_length_limit': request.context_length_limit,
            'enable_streaming': request.enable_streaming
        }
        
        # 执行查询处理 - 使用新的异步接口
        result = await query_processor.process_query(
            query=request.query,
            query_type=request.query_type,
            options=options
        )
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 构建响应 - 适配新的响应格式
        response = QueryResponse(
            success=result.success,
            query_type=result.query_type,
            answer=result.answer,
            results=result.results,
            processing_metadata=result.processing_metadata,
            error_message=result.error_message
        )
        
        logger.info(f"查询处理完成，类型: {response.query_type}，成功: {response.success}，处理时间: {processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"查询处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询处理失败: {str(e)}")


# 内容搜索端点
@router.post("/search", response_model=SearchResponse, summary="内容搜索")
async def search_content(
    request: SearchRequest,
    services: Dict = Depends(get_rag_services)
):
    """执行内容搜索"""
    try:
        start_time = datetime.now()
        
        # 获取召回引擎
        retrieval_engine = services.get('retrieval_engine')
        if not retrieval_engine:
            raise HTTPException(status_code=503, detail="召回引擎不可用")
        
        # 根据内容类型选择搜索策略
        if request.content_type == "text":
            results = retrieval_engine.retrieve_texts(
                request.query, 
                request.max_results
            )
        elif request.content_type == "image":
            results = retrieval_engine.retrieve_images(
                request.query, 
                request.max_results
            )
        elif request.content_type == "table":
            results = retrieval_engine.retrieve_tables(
                request.query, 
                request.max_results
            )
        else:
            # 使用智能搜索
            results = retrieval_engine.smart_retrieve(
                request.query, 
                content_type=request.content_type,
                max_results=request.max_results
            )
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 构建响应
        response = SearchResponse(
            query=request.query,
            results=results,
            total_count=len(results),
            processing_time=processing_time,
            search_stats=retrieval_engine.get_retrieval_stats()
        )
        
        logger.info(f"内容搜索完成，查询: {request.query}，结果数量: {len(results)}，处理时间: {processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"内容搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"内容搜索失败: {str(e)}")


# 重排序端点
@router.post("/rerank", response_model=RerankResponse, summary="文档重排序")
async def rerank_documents(
    request: RerankRequest,
    services: Dict = Depends(get_rag_services)
):
    """对文档进行重排序"""
    try:
        start_time = datetime.now()
        
        # 获取重排序服务
        reranking_service = services.get('reranking_service')
        if not reranking_service:
            raise HTTPException(status_code=503, detail="重排序服务不可用")
        
        # 执行重排序
        reranked_docs = reranking_service.rerank_documents(
            query=request.query,
            documents=request.documents,
            top_k=request.top_k
        )
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 构建响应
        response = RerankResponse(
            query=request.query,
            reranked_documents=reranked_docs,
            processing_time=processing_time
        )
        
        logger.info(f"文档重排序完成，查询: {request.query}，处理时间: {processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"文档重排序失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档重排序失败: {str(e)}")


# 溯源端点
@router.post("/attribution", response_model=AttributionResponse, summary="答案溯源")
async def get_attribution(
    request: AttributionRequest,
    services: Dict = Depends(get_rag_services)
):
    """获取答案溯源信息"""
    try:
        start_time = datetime.now()
        
        # 获取溯源服务
        attribution_service = services.get('attribution_service')
        if not attribution_service:
            raise HTTPException(status_code=503, detail="溯源服务不可用")
        
        # 执行溯源
        attribution_result = attribution_service.get_source_attribution(
            answer_id=request.answer_id,
            display_mode=request.display_mode
        )
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 构建响应
        response = AttributionResponse(
            answer_id=request.answer_id,
            sources=attribution_result.sources,
            overall_confidence=attribution_result.overall_confidence,
            attribution_summary=attribution_result.attribution_summary,
            processing_time=processing_time
        )
        
        logger.info(f"答案溯源完成，答案ID: {request.answer_id}，处理时间: {processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"答案溯源失败: {e}")
        raise HTTPException(status_code=500, detail=f"答案溯源失败: {str(e)}")


# 统计信息端点
@router.get("/stats", summary="系统统计信息")
async def get_system_stats(services: Dict = Depends(get_rag_services)):
    """获取系统统计信息"""
    try:
        stats = {}
        
        # 获取各服务的统计信息
        for service_name, service_instance in services.items():
            if hasattr(service_instance, 'get_retrieval_stats'):
                stats[service_name] = service_instance.get_retrieval_stats()
            elif hasattr(service_instance, 'get_service_status'):
                stats[service_name] = service_instance.get_service_status()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"获取系统统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 配置信息端点
@router.get("/config", summary="系统配置信息")
async def get_system_config(services: Dict = Depends(get_rag_services)):
    """获取系统配置信息"""
    try:
        config_integration = services.get('config_integration')
        if not config_integration:
            raise HTTPException(status_code=503, detail="配置服务不可用")
        
        # 获取RAG系统配置
        rag_config = config_integration.get('rag_system', {})
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "rag_system_config": rag_config
        }
        
    except Exception as e:
        logger.error(f"获取系统配置信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置信息失败: {str(e)}")


# 向量数据库状态端点
@router.get("/vector-db/status", summary="向量数据库状态")
async def get_vector_db_status(services: Dict = Depends(get_rag_services)):
    """获取向量数据库状态"""
    try:
        vector_db_integration = services.get('vector_db_integration')
        if not vector_db_integration:
            raise HTTPException(status_code=503, detail="向量数据库集成服务不可用")
        
        status = vector_db_integration.get_vector_db_status()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "vector_db_status": status
        }
        
    except Exception as e:
        logger.error(f"获取向量数据库状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取向量数据库状态失败: {str(e)}")


# 批量查询端点
@router.post("/batch-query", summary="批量查询处理")
async def batch_process_queries(
    queries: List[QueryRequest],
    services: Dict = Depends(get_rag_services)
):
    """批量处理多个查询"""
    try:
        if len(queries) > 10:  # 限制批量查询数量
            raise HTTPException(status_code=400, detail="批量查询数量不能超过10个")
        
        start_time = datetime.now()
        results = []
        
        # 获取查询处理器
        query_processor = services.get('query_processor')
        if not query_processor:
            raise HTTPException(status_code=503, detail="查询处理器不可用")
        
        # 批量处理查询
        for i, query_request in enumerate(queries):
            try:
                result = query_processor.process_query(
                    query=query_request.query,
                    query_type=query_request.query_type,
                    content_type=query_request.content_type,
                    max_results=query_request.max_results,
                    similarity_threshold=query_request.similarity_threshold,
                    include_sources=query_request.include_sources,
                    include_attribution=query_request.include_attribution,
                    user_id=query_request.user_id,
                    session_id=query_request.session_id
                )
                
                results.append({
                    "index": i,
                    "status": "success",
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"批量查询第{i+1}个失败: {e}")
                results.append({
                    "index": i,
                    "status": "error",
                    "error": str(e)
                })
        
        # 计算总处理时间
        total_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(queries),
            "successful_queries": len([r for r in results if r["status"] == "success"]),
            "failed_queries": len([r for r in results if r["status"] == "error"]),
            "total_processing_time": total_time,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"批量查询处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量查询处理失败: {str(e)}")


# 流式查询端点（用于实时对话）
@router.post("/stream-query", summary="流式查询处理")
async def stream_process_query(
    request: QueryRequest,
    services: Dict = Depends(get_rag_services)
):
    """流式处理查询，支持实时响应"""
    try:
        # 获取查询处理器
        query_processor = services.get('query_processor')
        if not query_processor:
            raise HTTPException(status_code=503, detail="查询处理器不可用")
        
        # 这里应该实现流式响应
        # 由于FastAPI的流式响应比较复杂，这里先返回标准响应
        # 后续可以扩展为真正的流式API
        
        result = query_processor.process_query(
            query=request.query,
            query_type=request.query_type,
            content_type=request.content_type,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold,
            include_sources=request.include_sources,
            include_attribution=request.include_attribution,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return {
            "status": "success",
            "message": "流式查询功能待实现，当前返回标准响应",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"流式查询处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式查询处理失败: {str(e)}")


# 错误处理
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.now(),
            request_id=getattr(request, 'request_id', None)
        ).dict()
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="内部服务器错误",
            detail=str(exc),
            timestamp=datetime.now(),
            request_id=getattr(request, 'request_id', None)
        ).dict()
    )


def initialize_rag_services():
    """初始化RAG服务实例"""
    try:
        # 初始化核心服务
        config_integration = ConfigIntegration()
        
        # 初始化向量数据库集成
        vector_db_integration = VectorDBIntegration(config_integration)
        
        # 初始化元数据管理器
        metadata_manager = RAGMetadataManager(None)  # 暂时传入None
        
        # 创建各核心服务
        llm_caller = LLMCaller(config_integration)
        reranking_service = MultiModelReranker(config_integration)
        attribution_service = AttributionService(metadata_manager)
        display_service = DisplayService(config_integration)
        
        # 创建召回引擎
        retrieval_engine = RetrievalEngine(config_integration, vector_db_integration)
        
        # 创建查询处理器
        query_processor = QueryProcessor(
            config_integration=config_integration,
            retrieval_engine=retrieval_engine,
            llm_caller=llm_caller,
            reranking_service=reranking_service,
            attribution_service=attribution_service,
            display_service=display_service,
            metadata_manager=metadata_manager
        )
        
        # 注册所有服务
        global rag_services
        rag_services = {
            'config_integration': config_integration,
            'vector_db_integration': vector_db_integration,
            'metadata_manager': metadata_manager,
            'llm_caller': llm_caller,
            'reranking_service': reranking_service,
            'attribution_service': attribution_service,
            'display_service': display_service,
            'retrieval_engine': retrieval_engine,
            'query_processor': query_processor
        }
        
        logger.info("RAG服务初始化完成")
        
    except Exception as e:
        logger.error(f"RAG服务初始化失败: {e}")
        raise
