"""
RAG系统API接口层

提供RAG系统的HTTP API接口：
- FastAPI应用主文件
- 路由定义
- 中间件配置
- 错误处理
"""

from .main import create_app
from .routes import router

__all__ = [
    "create_app",
    "router"
]
