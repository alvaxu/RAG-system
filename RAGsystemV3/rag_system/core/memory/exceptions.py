"""
记忆模块异常定义

定义记忆模块专用的异常类型，遵循现有系统的异常处理规范
"""


class MemoryError(Exception):
    """记忆模块基础异常类"""
    
    def __init__(self, message: str, error_code: str = "MEMORY_ERROR", details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details
        }


class SessionNotFoundError(MemoryError):
    """会话未找到异常"""
    
    def __init__(self, session_id: str, message: str = None):
        message = message or f"会话未找到: {session_id}"
        super().__init__(message, "SESSION_NOT_FOUND", {'session_id': session_id})


class SessionAlreadyExistsError(MemoryError):
    """会话已存在异常"""
    
    def __init__(self, session_id: str, message: str = None):
        message = message or f"会话已存在: {session_id}"
        super().__init__(message, "SESSION_ALREADY_EXISTS", {'session_id': session_id})


class MemoryRetrievalError(MemoryError):
    """记忆检索异常"""
    
    def __init__(self, message: str, query: str = None, details: dict = None):
        super().__init__(message, "MEMORY_RETRIEVAL_ERROR", details or {})
        if query:
            self.details['query'] = query


class MemoryStorageError(MemoryError):
    """记忆存储异常"""
    
    def __init__(self, message: str, chunk_id: str = None, details: dict = None):
        super().__init__(message, "MEMORY_STORAGE_ERROR", details or {})
        if chunk_id:
            self.details['chunk_id'] = chunk_id


class CompressionError(MemoryError):
    """记忆压缩异常"""
    
    def __init__(self, message: str, session_id: str = None, strategy: str = None, details: dict = None):
        super().__init__(message, "COMPRESSION_ERROR", details or {})
        if session_id:
            self.details['session_id'] = session_id
        if strategy:
            self.details['strategy'] = strategy


class VectorizationError(MemoryError):
    """向量化异常"""
    
    def __init__(self, message: str, content: str = None, details: dict = None):
        super().__init__(message, "VECTORIZATION_ERROR", details or {})
        if content:
            self.details['content_length'] = len(content)


class DatabaseError(MemoryError):
    """数据库操作异常"""
    
    def __init__(self, message: str, operation: str = None, details: dict = None):
        super().__init__(message, "DATABASE_ERROR", details or {})
        if operation:
            self.details['operation'] = operation


class ConfigurationError(MemoryError):
    """配置错误异常"""
    
    def __init__(self, message: str, config_key: str = None, details: dict = None):
        super().__init__(message, "CONFIGURATION_ERROR", details or {})
        if config_key:
            self.details['config_key'] = config_key


class ValidationError(MemoryError):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = None, value: any = None, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details or {})
        if field:
            self.details['field'] = field
        if value is not None:
            self.details['value'] = str(value)


class RateLimitError(MemoryError):
    """频率限制异常"""
    
    def __init__(self, message: str, limit: int = None, current: int = None, details: dict = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details or {})
        if limit is not None:
            self.details['limit'] = limit
        if current is not None:
            self.details['current'] = current


class TimeoutError(MemoryError):
    """超时异常"""
    
    def __init__(self, message: str, timeout: float = None, operation: str = None, details: dict = None):
        super().__init__(message, "TIMEOUT_ERROR", details or {})
        if timeout is not None:
            self.details['timeout'] = timeout
        if operation:
            self.details['operation'] = operation
