"""
记忆模块配置管理器

基于RAG系统V3的配置管理机制，管理记忆模块的配置参数
"""

import logging
from typing import Dict, Any, Optional
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class MemoryConfigManager:
    """
    记忆模块配置管理器
    
    基于现有ConfigIntegration，管理记忆模块的配置参数
    """
    
    def __init__(self, config_integration):
        """
        初始化记忆配置管理器
        
        Args:
            config_integration: RAG系统配置集成管理器实例
        """
        self.config = config_integration
        self.memory_config = self._load_memory_config()
        
        logger.info("记忆模块配置管理器初始化完成")
    
    def _load_memory_config(self) -> Dict[str, Any]:
        """
        加载记忆模块配置
        
        Returns:
            Dict[str, Any]: 记忆模块配置字典
            
        Raises:
            ConfigurationError: 配置加载失败
        """
        try:
            # 从RAG系统配置中获取记忆模块配置
            memory_config = self.config.get('rag_system.memory_module', {})
            
            if not memory_config:
                logger.warning("未找到记忆模块配置，使用默认配置")
                return self._get_default_config()
            
            # 验证配置完整性
            self._validate_config(memory_config)
            
            return memory_config
            
        except Exception as e:
            logger.error(f"加载记忆模块配置失败: {e}")
            raise ConfigurationError(f"加载记忆模块配置失败: {e}") from e
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return {
            "enabled": True,
            "database_path": "rag_memory.db",
            "compression": {
                "enabled": True,
                "threshold": 20,
                "strategy": "semantic",
                "max_compression_ratio": 0.3
            },
            "retrieval": {
                "similarity_threshold": 0.7,
                "max_results": 5,
                "time_decay_factor": 0.9
            },
            "session": {
                "max_sessions_per_user": 100,
                "session_timeout": 3600,
                "auto_cleanup": True
            },
            "vectorization": {
                "model": "text-embedding-v1",
                "dimensions": 1536,
                "chunk_type": "memory"
            }
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        验证配置完整性
        
        Args:
            config: 配置字典
            
        Raises:
            ConfigurationError: 配置验证失败
        """
        required_keys = [
            'database_path',
            'compression',
            'retrieval',
            'session',
            'vectorization'
        ]
        
        for key in required_keys:
            if key not in config:
                raise ConfigurationError(f"缺少必需的配置项: {key}")
        
        # 验证压缩配置
        compression_config = config.get('compression', {})
        if not isinstance(compression_config.get('threshold'), int):
            raise ConfigurationError("压缩阈值必须是整数")
        
        if compression_config.get('threshold', 0) < 0:
            raise ConfigurationError("压缩阈值不能为负数")
        
        # 验证检索配置
        retrieval_config = config.get('retrieval', {})
        similarity_threshold = retrieval_config.get('similarity_threshold', 0.7)
        if not 0 <= similarity_threshold <= 1:
            raise ConfigurationError("相似度阈值必须在0-1之间")
        
        # 验证会话配置
        session_config = config.get('session', {})
        max_sessions = session_config.get('max_sessions_per_user', 100)
        if not isinstance(max_sessions, int) or max_sessions <= 0:
            raise ConfigurationError("最大会话数必须是正整数")
    
    def get_database_path(self) -> str:
        """
        获取数据库路径
        
        Returns:
            str: 数据库文件路径
        """
        return self.memory_config.get('database_path', 'rag_memory.db')
    
    def is_enabled(self) -> bool:
        """
        检查记忆模块是否启用
        
        Returns:
            bool: 是否启用
        """
        return self.memory_config.get('enabled', True)
    
    def get_compression_config(self) -> Dict[str, Any]:
        """
        获取压缩配置
        
        Returns:
            Dict[str, Any]: 压缩配置字典
        """
        return self.memory_config.get('compression', {})
    
    def get_retrieval_config(self) -> Dict[str, Any]:
        """
        获取检索配置
        
        Returns:
            Dict[str, Any]: 检索配置字典
        """
        return self.memory_config.get('retrieval', {})
    
    def get_session_config(self) -> Dict[str, Any]:
        """
        获取会话配置
        
        Returns:
            Dict[str, Any]: 会话配置字典
        """
        return self.memory_config.get('session', {})
    
    def get_vectorization_config(self) -> Dict[str, Any]:
        """
        获取向量化配置
        
        Returns:
            Dict[str, Any]: 向量化配置字典
        """
        return self.memory_config.get('vectorization', {})
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            keys = key.split('.')
            value = self.memory_config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.warning(f"获取配置值失败: {key}, 使用默认值: {default}")
            return default
    
    def update_config(self, key: str, value: Any) -> None:
        """
        更新配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 新值
            
        Raises:
            ConfigurationError: 配置更新失败
        """
        try:
            keys = key.split('.')
            config = self.memory_config
            
            # 导航到目标位置
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            
            logger.info(f"配置已更新: {key} = {value}")
            
        except Exception as e:
            raise ConfigurationError(f"更新配置失败: {key}") from e
    
    def reload_config(self) -> None:
        """
        重新加载配置
        
        Raises:
            ConfigurationError: 配置重载失败
        """
        try:
            self.memory_config = self._load_memory_config()
            logger.info("记忆模块配置已重新加载")
            
        except Exception as e:
            raise ConfigurationError("重新加载配置失败") from e
    
    def get_full_config(self) -> Dict[str, Any]:
        """
        获取完整配置
        
        Returns:
            Dict[str, Any]: 完整配置字典
        """
        return self.memory_config.copy()
