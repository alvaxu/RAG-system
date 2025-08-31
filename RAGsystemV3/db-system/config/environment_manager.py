"""
环境变量管理器（Windows兼容）

负责管理系统环境变量，包括API密钥和其他敏感信息的管理。
支持Windows系统的环境变量设置和读取。
"""

import os
import logging
from typing import Optional, Dict, Any
import platform

class EnvironmentManager:
    """
    环境变量管理器类

    功能：
    - 管理API密钥等敏感信息
    - 提供Windows兼容的环境变量操作
    - 验证必需的环境变量
    - 支持环境变量的设置和获取
    """

    def __init__(self):
        """
        初始化环境变量管理器
        """
        self.system = platform.system().lower()
        self.required_vars = {
            'DASHSCOPE_API_KEY': 'DashScope API密钥',
            'MINERU_API_KEY': 'MinerU API密钥'
        }
        self.optional_vars = {
            'LOG_LEVEL': '日志级别',
            'TEMP_DIR': '临时目录路径',
            'CUDA_VISIBLE_DEVICES': 'CUDA设备设置'
        }

    def get_required_var(self, var_name: str) -> Optional[str]:
        """
        获取必需的环境变量

        :param var_name: 环境变量名
        :return: 环境变量值，如果不存在返回None
        """
        value = os.getenv(var_name)
        if not value:
            logging.warning(f"必需的环境变量 '{var_name}' 未设置")
        return value

    def get_optional_var(self, var_name: str, default: str = None) -> str:
        """
        获取可选的环境变量

        :param var_name: 环境变量名
        :param default: 默认值
        :return: 环境变量值或默认值
        """
        return os.getenv(var_name, default)

    def validate_required_vars(self) -> Dict[str, bool]:
        """
        验证所有必需的环境变量

        :return: 验证结果字典
        """
        results = {}
        for var_name, description in self.required_vars.items():
            value = self.get_required_var(var_name)
            results[var_name] = value is not None
            if not results[var_name]:
                logging.error(f"缺少必需的环境变量: {var_name} ({description})")

        return results

    def get_all_required_vars(self) -> Dict[str, Optional[str]]:
        """
        获取所有必需的环境变量

        :return: 环境变量字典
        """
        return {
            var_name: self.get_required_var(var_name)
            for var_name in self.required_vars.keys()
        }

    def get_all_optional_vars(self) -> Dict[str, str]:
        """
        获取所有可选的环境变量

        :return: 环境变量字典
        """
        return {
            var_name: self.get_optional_var(var_name)
            for var_name in self.optional_vars.keys()
        }

    def is_windows(self) -> bool:
        """
        检查是否为Windows系统

        :return: 是否为Windows系统
        """
        return self.system == 'windows'

    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        :return: 系统信息字典
        """
        return {
            'system': self.system,
            'is_windows': self.is_windows(),
            'platform': platform.platform(),
            'python_version': platform.python_version()
        }

    def setup_environment(self) -> bool:
        """
        设置运行环境

        :return: 设置是否成功
        """
        try:
            # 验证必需的环境变量
            validation_results = self.validate_required_vars()
            if not all(validation_results.values()):
                missing_vars = [k for k, v in validation_results.items() if not v]
                logging.error(f"环境设置失败，缺少必需的环境变量: {missing_vars}")
                return False

            # 设置可选的环境变量默认值
            if not self.get_optional_var('LOG_LEVEL'):
                os.environ['LOG_LEVEL'] = 'INFO'

            if not self.get_optional_var('TEMP_DIR'):
                os.environ['TEMP_DIR'] = './temp'

            logging.info("环境变量设置完成")
            return True

        except Exception as e:
            logging.error(f"环境设置失败: {str(e)}")
            return False

    def print_environment_status(self) -> None:
        """
        打印环境变量状态
        """
        print("\n=== 环境变量状态 ===")

        print("\n必需的环境变量:")
        for var_name, description in self.required_vars.items():
            value = self.get_required_var(var_name)
            status = "✓ 设置" if value else "✗ 未设置"
            masked_value = f"{value[:8]}..." if value and len(value) > 8 else value
            print(f"  {var_name}: {status} ({description})")
            if value:
                print(f"    值: {masked_value}")

        print("\n可选的环境变量:")
        for var_name, description in self.optional_vars.items():
            value = self.get_optional_var(var_name)
            status = "✓ 设置" if value else "✗ 未设置"
            print(f"  {var_name}: {status} ({description})")
            if value:
                print(f"    值: {value}")

        print(f"\n系统信息: {self.system} ({platform.platform()})")
        print(f"Python版本: {platform.python_version()}")

    def get_environment_config(self) -> Dict[str, Any]:
        """
        获取环境配置

        :return: 环境配置字典
        """
        return {
            'required_vars': self.get_all_required_vars(),
            'optional_vars': self.get_all_optional_vars(),
            'system_info': self.get_system_info(),
            'validation_results': self.validate_required_vars()
        }


# 全局环境管理器实例
environment_manager = EnvironmentManager()

if __name__ == "__main__":
    # 测试环境管理器
    environment_manager.print_environment_status()
