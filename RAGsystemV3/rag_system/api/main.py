"""
FastAPI应用主文件

RAG系统的API入口点，配置FastAPI应用和中间件
"""

import logging
import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time

# 导入V3配置管理器 - 使用完整包路径
try:
    from db_system.config.config_manager import ConfigManager
    from db_system.config.path_manager import PathManager
except ImportError as e:
    logging.error(f"无法导入V3配置管理器: {e}")
    raise

from .routes import router
from .routes import initialize_rag_services
from .routes import memory_router

def setup_logging():
    """
    设置日志配置 - 支持配置化的日志目录
    """
    try:
        # 创建配置管理器并获取日志目录
        config_manager = ConfigManager()
        config_manager.load_config()  # 加载配置
        logs_dir = config_manager.get_path('logs_dir')  # 使用M06的路径管理功能
        
        # 设置日志文件路径
        log_file_path = os.path.join(logs_dir, 'rag_system.log')
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file_path)
        os.makedirs(log_dir, exist_ok=True)
        
        # 清除现有的日志配置
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # 创建新的日志配置
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 配置根日志器
        logging.root.setLevel(logging.INFO)
        logging.root.addHandler(console_handler)
        logging.root.addHandler(file_handler)
        
        logging.info(f"RAG系统API日志配置完成 - 文件: {log_file_path}")
        
    except Exception as e:
        logging.error(f"日志配置失败: {e}")
        raise

# 在应用创建前配置日志
setup_logging()

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    # 添加测试日志
    logging.info("开始创建FastAPI应用")
    
    # 创建FastAPI应用实例
    app = FastAPI(
        title="V3 RAG系统 API",
        description="基于V3向量数据库的智能问答系统",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 添加测试日志
    logging.info("FastAPI应用实例创建完成")
    
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
    app.include_router(memory_router, prefix="/api/v3")
    
    # 添加静态文件服务 - 提供图片访问
    # 使用V3配置管理系统中的路径配置
    try:
        from rag_system.core.config_integration import ConfigIntegration
        from db_system.config.path_manager import PathManager
        
        config = ConfigIntegration()
        # 使用项目根目录作为PathManager的基础目录
        path_manager = PathManager(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        # 从V3配置管理系统获取图片目录路径
        # 根据设计文档，图片路径属于V3基础配置的paths节点
        final_image_dir = config.get("paths.final_image_dir", "central/vector_db/images")
        # 使用PathManager处理相对路径，确保路径正确
        images_path = path_manager.get_absolute_path(f"./db_system/{final_image_dir}")
        
        # 检查图片目录是否存在
        if os.path.exists(images_path):
            app.mount("/images", StaticFiles(directory=images_path), name="images")
            logger.info(f"静态文件服务已配置: /images -> {images_path}")
        else:
            logger.warning(f"图片目录不存在: {images_path}")
    except Exception as e:
        logger.error(f"配置静态文件服务失败: {e}")
    
    # 启动时初始化 RAG 服务
    try:
        initialize_rag_services()
        logger.info("RAG服务初始化已在启动时完成")
    except Exception as init_exc:
        logger.error(f"RAG服务初始化失败: {init_exc}")
    
    # 轻量级健康检查端点（用于文档页面）
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "V3 RAG系统",
            "version": "3.0.0",
            "timestamp": time.time()
        }
    
    # 快速健康检查端点（用于文档页面预加载）
    @app.get("/health/quick")
    async def quick_health_check():
        return {"status": "healthy"}
    
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
