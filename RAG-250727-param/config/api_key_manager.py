'''
程序说明：

## 1. 统一的API密钥管理模块
## 2. 支持从配置文件和环境变量获取API密钥
## 3. 提供统一的接口供其他模块调用
## 4. 支持优先级：配置文件 > 环境变量
## 5. 包含日志记录和错误处理
'''

import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    API密钥管理器，统一管理所有API密钥的获取
    """
    
    # 环境变量名称
    DASHSCOPE_ENV_VAR = 'MY_DASHSCOPE_API_KEY'
    MINERU_ENV_VAR = 'MINERU_API_KEY'
    
    # 占位符字符串列表
    DASHSCOPE_PLACEHOLDERS = ['你的DashScope API密钥', '你的APIKEY']
    MINERU_PLACEHOLDERS = ['你的minerU API密钥']
    
    @classmethod
    def get_dashscope_api_key(cls, config_key: str = None) -> str:
        """
        获取DashScope API密钥
        
        :param config_key: 配置文件中的API密钥值
        :return: API密钥字符串，如果未找到则返回空字符串
        """
        # 优先级1：配置文件中的值（如果有效）
        if config_key and config_key.strip() and config_key not in cls.DASHSCOPE_PLACEHOLDERS:
            logger.info("使用配置文件中的DashScope API密钥")
            return config_key
        
        # 优先级2：环境变量
        env_key = os.getenv(cls.DASHSCOPE_ENV_VAR, '')
        if env_key and env_key.strip():
            logger.info("使用环境变量中的DashScope API密钥")
            return env_key
        
        # 未找到有效密钥
        logger.warning("未找到有效的DashScope API密钥，请检查配置文件或环境变量")
        return ""
    
    @classmethod
    def get_mineru_api_key(cls, config_key: str = None) -> str:
        """
        获取minerU API密钥
        
        :param config_key: 配置文件中的API密钥值
        :return: API密钥字符串，如果未找到则返回空字符串
        """
        # 优先级1：配置文件中的值（如果有效）
        if config_key and config_key.strip() and config_key not in cls.MINERU_PLACEHOLDERS:
            logger.info("使用配置文件中的minerU API密钥")
            return config_key
        
        # 优先级2：环境变量
        env_key = os.getenv(cls.MINERU_ENV_VAR, '')
        if env_key and env_key.strip():
            logger.info("使用环境变量中的minerU API密钥")
            return env_key
        
        # 未找到有效密钥
        logger.warning("未找到有效的minerU API密钥，请检查配置文件或环境变量")
        return ""
    
    @classmethod
    def get_all_api_keys(cls, dashscope_config_key: str = None, mineru_config_key: str = None) -> Tuple[str, str]:
        """
        一次性获取所有API密钥
        
        :param dashscope_config_key: 配置文件中的DashScope API密钥值
        :param mineru_config_key: 配置文件中的minerU API密钥值
        :return: (dashscope_api_key, mineru_api_key) 元组
        """
        dashscope_key = cls.get_dashscope_api_key(dashscope_config_key)
        mineru_key = cls.get_mineru_api_key(mineru_config_key)
        return dashscope_key, mineru_key
    
    @classmethod
    def validate_dashscope_key(cls, api_key: str) -> bool:
        """
        验证DashScope API密钥是否有效
        
        :param api_key: API密钥
        :return: 是否有效
        """
        return bool(api_key and api_key.strip() and api_key not in cls.DASHSCOPE_PLACEHOLDERS)
    
    @classmethod
    def validate_mineru_key(cls, api_key: str) -> bool:
        """
        验证minerU API密钥是否有效
        
        :param api_key: API密钥
        :return: 是否有效
        """
        return bool(api_key and api_key.strip() and api_key not in cls.MINERU_PLACEHOLDERS)
    
    @classmethod
    def get_api_keys_status(cls, dashscope_config_key: str = None, mineru_config_key: str = None) -> dict:
        """
        获取API密钥状态信息
        
        :param dashscope_config_key: 配置文件中的DashScope API密钥值
        :param mineru_config_key: 配置文件中的minerU API密钥值
        :return: 状态信息字典
        """
        dashscope_key = cls.get_dashscope_api_key(dashscope_config_key)
        mineru_key = cls.get_mineru_api_key(mineru_config_key)
        
        return {
            'dashscope': {
                'configured': cls.validate_dashscope_key(dashscope_key),
                'source': 'config' if cls.validate_dashscope_key(dashscope_config_key) else 'env' if cls.validate_dashscope_key(dashscope_key) else 'none'
            },
            'mineru': {
                'configured': cls.validate_mineru_key(mineru_key),
                'source': 'config' if cls.validate_mineru_key(mineru_config_key) else 'env' if cls.validate_mineru_key(mineru_key) else 'none'
            }
        }


# 便捷函数，用于向后兼容
def get_dashscope_api_key(config_key: str = None) -> str:
    """
    获取DashScope API密钥的便捷函数
    
    :param config_key: 配置文件中的API密钥值
    :return: API密钥字符串
    """
    return APIKeyManager.get_dashscope_api_key(config_key)


def get_mineru_api_key(config_key: str = None) -> str:
    """
    获取minerU API密钥的便捷函数
    
    :param config_key: 配置文件中的API密钥值
    :return: API密钥字符串
    """
    return APIKeyManager.get_mineru_api_key(config_key)


def get_all_api_keys(dashscope_config_key: str = None, mineru_config_key: str = None) -> Tuple[str, str]:
    """
    获取所有API密钥的便捷函数
    
    :param dashscope_config_key: 配置文件中的DashScope API密钥值
    :param mineru_config_key: 配置文件中的minerU API密钥值
    :return: (dashscope_api_key, mineru_api_key) 元组
    """
    return APIKeyManager.get_all_api_keys(dashscope_config_key, mineru_config_key)
