"""
配置管理模块

提供统一的配置管理功能，包括：
- 配置管理器主类
- 配置验证器
- 配置加载器
- 环境变量管理器
- 路径管理器
- 失败处理管理器
"""

from .config_manager import ConfigManager
from .config_validator import ConfigValidator
from .config_loader import ConfigLoader
from .environment_manager import EnvironmentManager, environment_manager
from .path_manager import PathManager
from .failure_handler import FailureHandler

__all__ = [
    'ConfigManager',
    'ConfigValidator',
    'ConfigLoader',
    'EnvironmentManager',
    'PathManager',
    'FailureHandler',
    'environment_manager'  # 全局环境管理器实例
]

__version__ = "3.0.0"
