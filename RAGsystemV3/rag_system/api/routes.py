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
# AttributionService已移除，溯源功能由向量数据库元数据直接提供
from ..core.display import DisplayService
from ..core.config_integration import ConfigIntegration
from ..core.vector_db_integration import VectorDBIntegration
from ..core.memory.memory_routes import router as memory_router, initialize_memory_module, cleanup_memory_module

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(tags=["RAG System"])

# 全局服务实例（在应用启动时初始化）
rag_services = {}

# 服务状态缓存
_service_status_cache = {}
_cache_timestamp = None
CACHE_DURATION = 30  # 缓存30秒


def get_rag_services():
    """获取RAG服务实例的依赖注入函数"""
    if not rag_services:
        raise HTTPException(status_code=503, detail="RAG服务未初始化")
    return rag_services


def analyze_content_for_display_mode(query_type: str, results: List[Dict], answer: str) -> tuple:
    """
    分析内容特征，选择展示模式
    
    :param query_type: 查询类型
    :param results: 查询结果
    :param answer: LLM回答
    :return: (display_mode, content_analysis, confidence)
    """
    try:
        # 分析结果中的内容类型
        content_types = set()
        image_count = 0
        table_count = 0
        text_count = 0
        
        for result in results:
            chunk_type = result.get('chunk_type', 'text')
            if chunk_type == 'image':
                content_types.add('image')
                image_count += 1
            elif chunk_type == 'table':
                content_types.add('table')
                table_count += 1
            else:
                content_types.add('text')
                text_count += 1
        
        # 根据查询类型和内容特征选择展示模式
        if query_type in ['text']:
            display_mode = 'text-focused'
            confidence = 1.0
        elif query_type in ['image']:
            display_mode = 'image-focused'
            confidence = 1.0
        elif query_type in ['table']:
            display_mode = 'table-focused'
            confidence = 1.0
        elif query_type in ['smart']:
            # 智能查询：根据实际内容类型选择
            if 'image' in content_types and image_count > 0:
                display_mode = 'image-focused'
                confidence = 0.9
            elif 'table' in content_types and table_count > 0:
                display_mode = 'table-focused'
                confidence = 0.9
            else:
                display_mode = 'text-focused'
                confidence = 0.8
        elif query_type in ['hybrid']:
            # 混合查询：根据内容类型组合选择
            if len(content_types) > 1:
                display_mode = 'hybrid-layout'
                confidence = 0.8
            elif 'image' in content_types:
                display_mode = 'image-focused'
                confidence = 0.7
            elif 'table' in content_types:
                display_mode = 'table-focused'
                confidence = 0.7
            else:
                display_mode = 'text-focused'
                confidence = 0.6
        else:
            # 默认情况
            display_mode = 'text-focused'
            confidence = 0.5
        
        # 构建内容分析结果
        content_analysis = {
            'content_types': list(content_types),
            'image_count': image_count,
            'table_count': table_count,
            'text_count': text_count,
            'total_results': len(results),
            'analysis_reason': f"检测到{len(content_types)}种内容类型，图片{image_count}个，表格{table_count}个，文本{text_count}个"
        }
        
        return display_mode, content_analysis, confidence
        
    except Exception as e:
        logger.error(f"内容分析失败: {e}")
        return 'text-focused', {'content_types': ['text'], 'analysis_reason': '分析失败，使用默认模式'}, 0.3


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
    # include_attribution已移除，溯源功能由向量数据库元数据直接提供
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


# AttributionRequest已移除，溯源功能由向量数据库元数据直接提供


class QueryResponse(BaseModel):
    """查询响应模型 - 适配新架构"""
    success: bool = Field(..., description="查询是否成功")
    query_type: Optional[str] = Field(None, description="检测到的查询类型")
    answer: Optional[str] = Field(None, description="生成的答案")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="检索结果")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="来源信息")
    # 展示模式相关字段
    display_mode: Optional[str] = Field(None, description="推荐的展示模式")
    content_analysis: Optional[Dict[str, Any]] = Field(None, description="内容分析结果")
    confidence: Optional[float] = Field(None, description="展示模式选择置信度")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="处理元数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    # 记忆模块相关字段
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")


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


# AttributionResponse已移除，溯源功能由向量数据库元数据直接提供


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


class PresetQuestionRequest(BaseModel):
    """预设问题请求模型"""
    query_type: Optional[str] = Field("all", description="查询类型", example="text")
    user_id: Optional[str] = Field(None, description="用户ID")
    limit: Optional[int] = Field(10, description="返回问题数量限制", ge=1, le=20)


class PresetQuestionResponse(BaseModel):
    """预设问题响应模型"""
    query_type: str = Field(..., description="查询类型")
    questions: List[Dict[str, Any]] = Field(..., description="预设问题列表")
    total_count: int = Field(..., description="总问题数量")
    generated_at: datetime = Field(..., description="生成时间")


# 健康检查端点
@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """RAG系统健康检查"""
    try:
        global _service_status_cache, _cache_timestamp
        
        # 检查缓存是否有效
        current_time = datetime.now()
        if (_cache_timestamp is None or 
            (current_time - _cache_timestamp).total_seconds() > CACHE_DURATION):
            
            # 缓存过期，重新获取服务状态
            services = get_rag_services()
            
            # 检查各服务状态（简化版本，减少响应时间）
            service_status = {}
            for service_name, service_instance in services.items():
                if hasattr(service_instance, 'get_service_status'):
                    try:
                        status = service_instance.get_service_status()
                        # 只保留关键状态信息
                        if isinstance(status, dict):
                            service_status[service_name] = {
                                'status': status.get('status', 'unknown'),
                                'service_type': status.get('service_type', 'unknown')
                            }
                        else:
                            service_status[service_name] = {'status': 'unknown'}
                    except Exception:
                        service_status[service_name] = {'status': 'error'}
                else:
                    service_status[service_name] = {'status': 'unknown'}
            
            # 更新缓存
            _service_status_cache = service_status
            _cache_timestamp = current_time
        else:
            # 使用缓存的服务状态
            service_status = _service_status_cache
        
        return HealthResponse(
            status="healthy",
            timestamp=current_time,
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
            'enable_streaming': request.enable_streaming,
            'session_id': request.session_id,
            'user_id': request.user_id or 'web_user',  # 如果user_id为None，使用默认值
            'query_type': request.query_type  # 添加查询类型到options中
        }
        
        # 执行查询处理 - 使用新的异步接口
        result = await query_processor.process_query(
            query=request.query,
            query_type=request.query_type,
            options=options
        )
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 添加查询重写信息到processing_metadata
        if hasattr(result, 'metadata') and result.metadata:
            if result.processing_metadata is None:
                result.processing_metadata = {}
            result.processing_metadata.update(result.metadata)
        
        # 构建响应 - 适配新的响应格式
        # 将results转换为sources格式，用于前端显示
        sources = []
        if result.results:
            for item in result.results:
                source = {
                    'chunk_id': item.get('chunk_id', ''),
                    'content': item.get('content', ''),
                    'content_type': item.get('content_type', 'text'),
                    'similarity_score': item.get('similarity_score', 0.0),
                    'document_name': item.get('document_name', ''),
                    'page_number': item.get('page_number', 0),
                    'chunk_type': item.get('chunk_type', 'text'),
                    'metadata': item.get('metadata', {}),
                    # 添加图片和表格展示字段
                    'image_path': item.get('image_path', ''),
                    'caption': item.get('caption', ''),
                    'image_title': item.get('image_title', ''),
                    'table_html': item.get('table_html', ''),
                    'table_title': item.get('table_title', ''),
                    'table_headers': item.get('table_headers', [])
                }
                sources.append(source)
        
        # 分析内容特征，选择展示模式
        display_mode, content_analysis, confidence = analyze_content_for_display_mode(
            request.query_type, result.results, result.answer
        )
        
        response = QueryResponse(
            success=result.success,
            query_type=result.query_type,
            answer=result.answer,
            results=result.results,
            sources=sources,
            display_mode=display_mode,
            content_analysis=content_analysis,
            confidence=confidence,
            processing_metadata=result.processing_metadata,
            error_message=result.error_message,
            session_id=options.get('session_id'),
            user_id=options.get('user_id')
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
# 溯源API接口已移除，溯源功能由向量数据库元数据直接提供


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
                    # include_attribution已移除
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
            # include_attribution已移除
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


# 注意：异常处理已在main.py中统一处理


def initialize_rag_services():
    """初始化RAG服务实例"""
    try:
        # 初始化核心服务
        config_integration = ConfigIntegration()
        
        # 初始化向量数据库集成
        vector_db_integration = VectorDBIntegration(config_integration)
        
        # 创建各核心服务
        llm_caller = LLMCaller(config_integration)
        
        # 初始化记忆模块
        initialize_memory_module(config_integration, vector_db_integration, llm_caller)
        reranking_service = MultiModelReranker(config_integration)
        # AttributionService已移除，溯源功能由向量数据库元数据直接提供
        display_service = DisplayService(config_integration)
        
        # 创建召回引擎
        retrieval_engine = RetrievalEngine(config_integration, vector_db_integration)
        
        # 获取记忆管理器实例
        from ..core.memory.memory_routes import get_memory_manager
        memory_manager = get_memory_manager()
        
        # 创建查询处理器
        query_processor = QueryProcessor(
            config_integration=config_integration,
            retrieval_engine=retrieval_engine,
            llm_caller=llm_caller,
            reranking_service=reranking_service,
            attribution_service=None,  # 已移除，溯源功能由向量数据库元数据直接提供
            display_service=display_service,
            memory_manager=memory_manager
        )
        
        # 注册所有服务
        global rag_services
        rag_services = {
            'config_integration': config_integration,
            'vector_db_integration': vector_db_integration,
            'llm_caller': llm_caller,
            'reranking_service': reranking_service,
            'display_service': display_service,
            'retrieval_engine': retrieval_engine,
            'query_processor': query_processor
        }
        
        logger.info("RAG服务初始化完成")
        
    except Exception as e:
        logger.error(f"RAG服务初始化失败: {e}")
        raise


# 系统状态端点
@router.get("/status", summary="系统状态")
async def get_system_status(services: Dict = Depends(get_rag_services)):
    """获取系统状态信息"""
    try:
        # 获取各个服务的状态
        status_info = {
            "timestamp": datetime.now().isoformat(),
            "service": "V3 RAG系统",
            "version": "3.0.0",
            "status": "running"
        }
        
        # 添加各服务状态
        if services.get('query_processor'):
            status_info['query_processor'] = "available"
        if services.get('retrieval_engine'):
            status_info['retrieval_engine'] = "available"
        if services.get('vector_db_integration'):
            status_info['vector_db_integration'] = "available"
        if services.get('llm_caller'):
            status_info['llm_caller'] = "available"
        
        return status_info
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


# 系统配置端点
@router.get("/config", summary="系统配置")
async def get_system_config(services: Dict = Depends(get_rag_services)):
    """获取系统配置信息"""
    try:
        config_integration = services.get('config_integration')
        if not config_integration:
            raise HTTPException(status_code=503, detail="配置集成服务不可用")
        
        # 获取配置信息（不包含敏感信息）
        config_info = {
            "timestamp": datetime.now().isoformat(),
            "service": "V3 RAG系统",
            "version": "3.0.0"
        }
        
        # 添加非敏感配置信息
        try:
            rag_config = config_integration.get('rag_system', {})
            config_info['rag_system'] = {
                'engines': {
                    'text_engine': {'enabled': True},
                    'image_engine': {'enabled': True},
                    'table_engine': {'enabled': True},
                    'hybrid_engine': {'enabled': True}
                },
                'performance': {
                    'batch_processing': {'enabled': True},
                    'caching': {'enabled': True}
                }
            }
        except Exception as config_e:
            logger.warning(f"获取配置信息时出错: {config_e}")
            config_info['rag_system'] = {'error': '配置获取失败'}
        
        return config_info
        
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")


# 预设问题生成端点
@router.get("/preset-questions", response_model=PresetQuestionResponse, summary="预设问题生成")
async def get_preset_questions(
    query_type: str = Query("all", description="查询类型"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    limit: int = Query(10, description="返回问题数量限制", ge=1, le=20),
    services: Dict = Depends(get_rag_services)
):
    """根据数据库内容和查询类型生成预设问题"""
    try:
        # 获取配置集成管理器
        config_integration = services.get('config_integration')
        if not config_integration:
            raise HTTPException(status_code=503, detail="配置集成管理器不可用")
        
        # 生成预设问题
        questions = generate_preset_questions(query_type, limit, config_integration)
        
        response = PresetQuestionResponse(
            query_type=query_type,
            questions=questions,
            total_count=len(questions),
            generated_at=datetime.now()
        )
        
        logger.info(f"预设问题生成完成，查询类型: {query_type}，问题数量: {len(questions)}")
        return response
        
    except Exception as e:
        logger.error(f"预设问题生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"预设问题生成失败: {str(e)}")


def generate_preset_questions(query_type: str, limit: int, config_integration) -> List[Dict[str, Any]]:
    """从配置文件生成预设问题"""
    try:
        # 使用配置集成管理器的配置管理器，遵循统一模式
        config_manager = config_integration.config_manager
        
        # 获取预设问题配置
        preset_config = config_manager.get('rag_system.preset_questions', {})
        if not preset_config.get('enabled', True):
            return []
        
        # 读取预设问题配置文件
        import json
        import os
        from db_system.config.path_manager import PathManager
        
        # 使用PathManager处理路径
        path_manager = PathManager()
        config_file = preset_config.get('config_file', './config/preset_questions.json')
        config_file = path_manager.get_absolute_path(config_file)
        
        if not os.path.exists(config_file):
            logger.warning(f"预设问题配置文件不存在: {config_file}")
            return []
        
        with open(config_file, 'r', encoding='utf-8') as f:
            preset_data = json.load(f)
        
        # 获取默认配置
        default_confidence = preset_data.get('default_confidence', 0.9)
        default_question_type = preset_data.get('default_question_type', 'static')
        questions_data = preset_data.get('questions', {})
        
        # 获取指定类型的问题
        if query_type == 'all':
            all_questions = []
            for qtype, questions in questions_data.items():
                for i, question_text in enumerate(questions):
                    all_questions.append({
                        'question_id': f'{qtype}_{i+1:03d}',
                        'question_text': question_text,
                        'question_type': default_question_type,
                        'confidence': default_confidence,
                        'source': 'config'
                    })
            return all_questions[:limit]
        else:
            questions = questions_data.get(query_type, [])
            result = []
            for i, question_text in enumerate(questions):
                result.append({
                    'question_id': f'{query_type}_{i+1:03d}',
                    'question_text': question_text,
                    'question_type': default_question_type,
                    'confidence': default_confidence,
                    'source': 'config'
                })
            return result[:limit]
            
    except Exception as e:
        logger.error(f"从配置文件读取预设问题失败: {e}")
        # 降级到硬编码的预设问题
        return _get_fallback_preset_questions(query_type, limit)

def _get_fallback_preset_questions(query_type: str, limit: int) -> List[Dict[str, Any]]:
    """降级方案：硬编码的预设问题"""
    # 基于中芯国际文档内容的预设问题
    preset_questions = {
        'text': [
            {
                'question_id': 'text_001',
                'question_text': '中芯国际2025年一季度业绩如何？',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            },
            {
                'question_id': 'text_002', 
                'question_text': '中芯国际的产能利用率情况如何？',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            },
            {
                'question_id': 'text_003',
                'question_text': '中芯国际的主要业务领域有哪些？',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            }
        ],
        'image': [
            {
                'question_id': 'image_001',
                'question_text': '中芯国际的股票走势图显示什么？',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            },
            {
                'question_id': 'image_002',
                'question_text': '产能利用率提升的图表分析',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            }
        ],
        'table': [
            {
                'question_id': 'table_001',
                'question_text': '中芯国际的基本财务数据表格',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            },
            {
                'question_id': 'table_002',
                'question_text': '中芯国际的营收和利润预测数据',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            }
        ],
        'smart': [
            {
                'question_id': 'smart_001',
                'question_text': '中芯国际的综合发展情况如何？',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            },
            {
                'question_id': 'smart_002',
                'question_text': '中芯国际的市场表现分析',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            }
        ],
        'hybrid': [
            {
                'question_id': 'hybrid_001',
                'question_text': '中芯国际的财务状况和图表分析',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            },
            {
                'question_id': 'hybrid_002',
                'question_text': '中芯国际的业务数据和趋势图表',
                'question_type': 'static',
                'confidence': 0.9,
                'source': 'fallback'
            }
        ]
    }
    
    if query_type == 'all':
        # 返回所有类型的问题，每种类型取2-3个
        all_questions = []
        for qtype, questions in preset_questions.items():
            all_questions.extend(questions[:3])  # 每种类型取前3个
        return all_questions[:limit]
    else:
        # 返回指定类型的问题
        questions = preset_questions.get(query_type, [])
        return questions[:limit]


# 展示模式配置获取端点
@router.get("/config/display-mode", summary="获取展示模式配置")
async def get_display_mode_config(
    services: Dict = Depends(get_rag_services)
):
    """获取展示模式配置信息"""
    try:
        # 获取配置集成服务
        config_integration = services.get('config_integration')
        if not config_integration:
            raise HTTPException(status_code=503, detail="配置集成服务不可用")
        
        # 构建展示模式配置
        display_mode_config = {
            "enabled": True,
            "defaultMode": "auto-detect",
            "autoSelectionRules": {
                "textThreshold": 0.7,
                "imageThreshold": 0.6,
                "tableThreshold": 0.5
            },
            "fallbackMode": "text-focused",
            "simplifiedAnalysis": True,
            "supportedModes": [
                {
                    "value": "text-focused",
                    "label": "文本优先",
                    "description": "以文本内容为主要展示方式，适合文档查询",
                    "queryTypes": ["text", "smart"]
                },
                {
                    "value": "image-focused",
                    "label": "图片优先",
                    "description": "以图片内容为主要展示方式，适合图片查询",
                    "queryTypes": ["image"]
                },
                {
                    "value": "table-focused",
                    "label": "表格优先",
                    "description": "以表格内容为主要展示方式，适合表格查询",
                    "queryTypes": ["table"]
                },
                {
                    "value": "hybrid-layout",
                    "label": "混合布局",
                    "description": "综合展示多种内容类型，适合混合查询",
                    "queryTypes": ["hybrid"]
                },
                {
                    "value": "auto-detect",
                    "label": "智能选择",
                    "description": "根据查询类型和内容自动选择最佳展示模式",
                    "queryTypes": ["smart", "all"]
                }
            ]
        }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "config": display_mode_config
        }
        
    except Exception as e:
        logger.error(f"获取展示模式配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取展示模式配置失败: {str(e)}")
