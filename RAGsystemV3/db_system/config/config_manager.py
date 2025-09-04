"""
配置管理器主类

统一管理所有配置，提供配置访问接口，管理配置的加载和验证，支持配置热更新，集成失败处理管理。
"""

import os
import logging
import time
from typing import Dict, Any, Optional, Union, List
from pathlib import Path

from .environment_manager import EnvironmentManager
from .config_validator import ConfigValidator
from .config_loader import ConfigLoader
from .path_manager import PathManager
from .failure_handler import FailureHandler

class ConfigManager:
    """
    配置管理器主类

    功能：
    - 统一管理所有配置
    - 提供配置访问接口
    - 管理配置的加载和验证
    - 支持配置热更新
    - 集成失败处理管理
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        :param config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 设置配置文件路径
        if config_path is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(config_dir, "v3_config.json")
        else:
            self.config_path = config_path

        # 初始化配置数据
        self.config_data = {}
        self.config_schema = {}
        self.last_modified_time = 0

        # 初始化各个管理器
        self.environment_manager = EnvironmentManager()
        self.validator = ConfigValidator()
        self.loader = ConfigLoader(config_manager=self)  # 传递配置管理器实例
        self.path_manager = PathManager()
        self.failure_handler = FailureHandler()

        # 配置状态
        self.is_loaded = False
        self.is_valid = False

        logging.info("配置管理器已初始化")

    def load_config(self) -> bool:
        """
        加载配置文件

        :return: 是否加载成功
        """
        try:
            logging.info(f"开始加载配置文件: {self.config_path}")

            # 检查配置文件是否存在
            if not os.path.exists(self.config_path):
                logging.error(f"配置文件不存在: {self.config_path}")
                return False

            # 加载配置文件
            self.config_data = self.loader.load_json(self.config_path)
            logging.info("配置文件加载成功")

            # 加载配置模式
            schema_path = self._get_schema_path()
            if os.path.exists(schema_path):
                self.config_schema = self.loader.load_json(schema_path)
                logging.info("配置模式文件加载成功")
            else:
                logging.warning(f"配置模式文件不存在: {schema_path}")
                self.config_schema = {}

            # 验证配置
            if self.config_schema:
                self.is_valid = self.validator.validate(self.config_data, self.config_schema)
                if not self.is_valid:
                    logging.error("配置验证失败")
                    validation_errors = self.validator.get_validation_errors()
                    for error in validation_errors:
                        logging.error(f"  - {error}")
                    return False
            else:
                logging.warning("跳过配置验证（无模式文件）")
                self.is_valid = True

            # 处理环境变量
            self._process_environment_variables()

            # 验证路径
            paths_config = self.config_data.get('paths', {})
            is_valid_paths, path_messages = self.path_manager.validate_paths(paths_config)
            if not is_valid_paths:
                logging.error("路径配置验证失败")
                for message in path_messages:
                    logging.error(f"  - {message}")
                return False

            # 初始化失败处理器
            failure_config = self.config_data.get('failure_handling', {})
            self.failure_handler.initialize(failure_config)

            # 更新状态
            self.is_loaded = True
            self.last_modified_time = os.path.getmtime(self.config_path)

            logging.info("配置加载完成")
            return True

        except Exception as e:
            logging.error(f"配置加载失败: {e}")
            self.is_loaded = False
            self.is_valid = False
            return False

    def _get_schema_path(self) -> str:
        """
        获取配置模式文件路径

        :return: 模式文件路径
        """
        config_dir = os.path.dirname(self.config_path)
        schema_filename = Path(self.config_path).stem + "_schema.json"
        return os.path.join(config_dir, schema_filename)

    def _process_environment_variables(self) -> None:
        """
        处理环境变量覆盖
        """
        try:
            # 验证必需的环境变量
            validation_results = self.environment_manager.validate_required_vars()
            if not all(validation_results.values()):
                missing_vars = [k for k, v in validation_results.items() if not v]
                logging.error(f"缺少必需的环境变量: {missing_vars}")
                raise ValueError(f"环境变量验证失败: {missing_vars}")

            logging.info("环境变量验证通过")
        except Exception as e:
            logging.error(f"环境变量处理失败: {e}")
            raise

    def reload_config(self) -> bool:
        """
        重新加载配置（用于热更新）

        :return: 是否重新加载成功
        """
        try:
            # 检查配置文件是否被修改
            if os.path.exists(self.config_path):
                current_mtime = os.path.getmtime(self.config_path)
                if current_mtime > self.last_modified_time:
                    logging.info("检测到配置文件修改，开始重新加载")
                    return self.load_config()
                else:
                    logging.debug("配置文件未修改，无需重新加载")
                    return True
            else:
                logging.error(f"配置文件不存在: {self.config_path}")
                return False

        except Exception as e:
            logging.error(f"重新加载配置失败: {e}")
            return False

    def get(self, key: str, default=None) -> Any:
        """
        获取配置值

        :param key: 配置键，支持点号分隔的嵌套键
        :param default: 默认值
        :return: 配置值
        """
        if not self.is_loaded:
            logging.warning("配置未加载，使用默认值")
            return default

        keys = key.split('.')
        value = self.config_data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_path(self, path_key: str) -> Optional[str]:
        """
        获取路径配置，支持相对路径转换为绝对路径

        :param path_key: 路径键
        :return: 绝对路径
        """
        relative_path = self.get(f"paths.{path_key}")
        if relative_path:
            return self.path_manager.get_absolute_path(relative_path)
        return None

    def get_config_backups_dir(self) -> Optional[str]:
        """
        获取配置备份目录

        :return: 配置备份目录的绝对路径
        """
        return self.get_path('config_backups_dir')

    def get_config_versions_dir(self) -> Optional[str]:
        """
        获取配置版本目录

        :return: 配置版本目录的绝对路径
        """
        return self.get_path('config_versions_dir')

    def get_failure_handler(self) -> FailureHandler:
        """
        获取失败处理器实例

        :return: 失败处理器实例
        """
        return self.failure_handler

    def get_environment_manager(self) -> EnvironmentManager:
        """
        获取环境变量管理器实例

        :return: 环境变量管理器实例
        """
        return self.environment_manager

    def get_path_manager(self) -> PathManager:
        """
        获取路径管理器实例

        :return: 路径管理器实例
        """
        return self.path_manager

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        :param key: 配置键
        :param value: 配置值
        """
        keys = key.split('.')
        config = self.config_data

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        logging.debug(f"配置已更新: {key} = {value}")

    def save_config(self) -> bool:
        """
        保存配置到文件

        :return: 是否保存成功
        """
        try:
            self.loader.save_json(self.config_path, self.config_data)
            self.last_modified_time = os.path.getmtime(self.config_path)
            logging.info("配置已保存")
            return True
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要

        :return: 配置摘要字典
        """
        return {
            'is_loaded': self.is_loaded,
            'is_valid': self.is_valid,
            'config_path': self.config_path,
            'schema_path': self._get_schema_path(),
            'version': self.get('version', 'unknown'),
            'system_mode': self.get('system.mode', 'unknown'),
            'paths_count': len(self.get('paths', {})),
            'last_modified': time.ctime(self.last_modified_time) if self.last_modified_time else None
        }

    def validate_config(self) -> Dict[str, Any]:
        """
        验证当前配置

        :return: 验证结果字典
        """
        if not self.is_loaded:
            return {
                'valid': False,
                'errors': ['配置未加载'],
                'warnings': []
            }

        # 重新验证配置
        is_valid = self.validator.validate(self.config_data, self.config_schema)

        return {
            'valid': is_valid,
            'errors': self.validator.get_validation_errors(),
            'warnings': self.validator.get_validation_warnings()
        }

    def get_all_config(self) -> Dict[str, Any]:
        """
        获取所有配置（调试用）

        :return: 完整配置字典
        """
        return self.config_data.copy()



    def reset_to_defaults(self) -> bool:
        """
        重置配置为默认值

        :return: 是否重置成功
        """
        try:
            # 这里应该实现默认配置的重置逻辑
            # 暂时只是记录日志
            logging.warning("重置配置功能暂未实现")
            return False
        except Exception as e:
            logging.error(f"重置配置失败: {e}")
            return False

    def export_config(self, export_path: str) -> bool:
        """
        导出配置到指定路径

        :param export_path: 导出路径
        :return: 是否导出成功
        """
        try:
            self.loader.save_json(export_path, self.config_data)
            logging.info(f"配置已导出到: {export_path}")
            return True
        except Exception as e:
            logging.error(f"导出配置失败: {e}")
            return False

    def import_config(self, import_path: str) -> bool:
        """
        从指定路径导入配置

        :param import_path: 导入路径
        :return: 是否导入成功
        """
        try:
            imported_config = self.loader.load_json(import_path)

            # 验证导入的配置
            if self.config_schema:
                is_valid = self.validator.validate(imported_config, self.config_schema)
                if not is_valid:
                    logging.error("导入的配置验证失败")
                    return False

            # 更新配置
            self.config_data = imported_config
            self.last_modified_time = time.time()

            logging.info(f"配置已从 {import_path} 导入")
            return True

        except Exception as e:
            logging.error(f"导入配置失败: {e}")
            return False

    def cleanup_temp_files(self) -> int:
        """
        清理临时文件

        :return: 清理的文件数量
        """
        try:
            cleaned_count = self.path_manager.cleanup_temp_dirs()
            logging.info(f"清理了 {cleaned_count} 个临时目录")
            return cleaned_count
        except Exception as e:
            logging.error(f"清理临时文件失败: {e}")
            return 0


if __name__ == "__main__":
    # 测试配置管理器
    config_manager = ConfigManager()

    print("=== 配置管理器测试 ===")

    # 加载配置
    if config_manager.load_config():
        print("✓ 配置加载成功")

        # 获取配置摘要
        summary = config_manager.get_config_summary()
        print(f"配置版本: {summary['version']}")
        print(f"系统模式: {summary['system_mode']}")
        print(f"路径数量: {summary['paths_count']}")

        # 测试配置获取
        chunk_size = config_manager.get('document_processing.chunk_size')
        print(f"文档分块大小: {chunk_size}")

        # 测试路径获取
        pdf_dir = config_manager.get_path('input_pdf_dir')
        print(f"PDF输入目录: {pdf_dir}")

    else:
        print("✗ 配置加载失败")

    # 验证配置
    validation_result = config_manager.validate_config()
    if validation_result['valid']:
        print("✓ 配置验证通过")
    else:
        print("✗ 配置验证失败")
        for error in validation_result['errors']:
            print(f"  - {error}")
