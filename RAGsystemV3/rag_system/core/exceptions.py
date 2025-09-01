"""
RAG系统异常定义模块

定义RAG系统中使用的具体异常类型，符合技术规范要求
避免使用通用Exception，提供有意义的错误信息
"""

from typing import Optional, Any


class RAGSystemError(Exception):
    """RAG系统基础异常类"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ConfigurationError(RAGSystemError):
    """配置相关异常"""
    pass


class ServiceInitializationError(RAGSystemError):
    """服务初始化异常"""
    pass


class QueryProcessingError(RAGSystemError):
    """查询处理异常"""
    pass


class QueryRoutingError(RAGSystemError):
    """查询路由异常"""
    pass


class RetrievalError(RAGSystemError):
    """检索服务异常"""
    pass


class RerankingError(RAGSystemError):
    """重排序服务异常"""
    pass


class LLMServiceError(RAGSystemError):
    """LLM服务异常"""
    pass


class ValidationError(RAGSystemError):
    """数据验证异常"""
    pass


class InvalidInputError(RAGSystemError):
    """输入数据无效异常"""
    pass


class ContentProcessingError(RAGSystemError):
    """内容处理异常"""
    pass


class VectorDBError(RAGSystemError):
    """向量数据库异常"""
    pass


class MetadataError(RAGSystemError):
    """元数据管理异常"""
    pass


class AttributionError(RAGSystemError):
    """溯源服务异常"""
    pass


class DisplayError(RAGSystemError):
    """展示服务异常"""
    pass


class TimeoutError(RAGSystemError):
    """超时异常"""
    pass


class ResourceError(RAGSystemError):
    """资源相关异常"""
    pass


class NetworkError(RAGSystemError):
    """网络相关异常"""
    pass


class AuthenticationError(RAGSystemError):
    """认证异常"""
    pass


class AuthorizationError(RAGSystemError):
    """授权异常"""
    pass


class RateLimitError(RAGSystemError):
    """速率限制异常"""
    pass


class ServiceUnavailableError(RAGSystemError):
    """服务不可用异常"""
    pass


class DataIntegrityError(RAGSystemError):
    """数据完整性异常"""
    pass


class CacheError(RAGSystemError):
    """缓存相关异常"""
    pass


class LoggingError(RAGSystemError):
    """日志记录异常"""
    pass


class MonitoringError(RAGSystemError):
    """监控相关异常"""
    pass
