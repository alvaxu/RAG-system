"""
FastAPI应用主文件

RAG系统的API入口点，配置FastAPI应用和中间件
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from .routes import router
from .routes import initialize_rag_services

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    # 创建FastAPI应用实例
    app = FastAPI(
        title="V3 RAG系统 API",
        description="基于V3向量数据库的智能问答系统",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发环境允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 配置信任主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 开发环境允许所有主机
    )
    
    # 添加请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # 记录请求信息
        logger.info(f"收到请求: {request.method} {request.url}")
        
        # 处理请求
        response = await call_next(request)
        
        # 记录响应时间
        process_time = time.time() - start_time
        logger.info(f"请求处理完成: {request.method} {request.url} - 耗时: {process_time:.3f}s")
        
        return response
    
    # 添加全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"全局异常: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "内部服务器错误",
                "message": str(exc),
                "timestamp": time.time()
            }
        )
    
    # 注册路由
    app.include_router(router, prefix="/api/v3/rag")
    
    # 启动时初始化 RAG 服务
    try:
        initialize_rag_services()
        logger.info("RAG服务初始化已在启动时完成")
    except Exception as init_exc:
        logger.error(f"RAG服务初始化失败: {init_exc}")
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "V3 RAG系统",
            "version": "3.0.0",
            "timestamp": time.time()
        }
    
    # 根路径
    @app.get("/")
    async def root():
        return {
            "message": "V3 RAG系统 API",
            "version": "3.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    logger.info("FastAPI应用创建完成")
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
