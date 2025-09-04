"""
配置加载器

负责加载和保存配置文件，支持多种文件格式，提供配置备份和恢复功能。
"""

import json
import os
import shutil
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

class ConfigLoadError(Exception):
    """配置加载错误"""
    pass

class ConfigSaveError(Exception):
    """配置保存错误"""
    pass

class ConfigLoader:
    """
    配置加载器

    功能：
    - 加载配置文件
    - 支持多种文件格式 (JSON, YAML)
    - 提供配置备份和恢复功能
    - 支持配置合并和覆盖
    """

    def __init__(self, config_manager=None):
        """
        初始化配置加载器
        
        :param config_manager: 配置管理器实例，用于获取备份目录配置
        """
        self.supported_formats = ['.json', '.yaml', '.yml']
        self.backup_dir = None
        self.config_manager = config_manager

    def load_json(self, file_path: str) -> Dict[str, Any]:
        """
        加载JSON配置文件

        :param file_path: 文件路径
        :return: 配置数据
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"配置文件不存在: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logging.info(f"成功加载JSON配置文件: {file_path}")
            return data

        except json.JSONDecodeError as e:
            raise ConfigLoadError(f"JSON格式错误: {e}")
        except Exception as e:
            raise ConfigLoadError(f"加载配置文件失败: {e}")

    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """
        加载YAML配置文件

        :param file_path: 文件路径
        :return: 配置数据
        """
        if not HAS_YAML:
            raise ConfigLoadError("PyYAML未安装，无法加载YAML文件")

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"配置文件不存在: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            logging.info(f"成功加载YAML配置文件: {file_path}")
            return data

        except yaml.YAMLError as e:
            raise ConfigLoadError(f"YAML格式错误: {e}")
        except Exception as e:
            raise ConfigLoadError(f"加载YAML配置文件失败: {e}")

    def load_config(self, file_path: str) -> Dict[str, Any]:
        """
        自动检测文件格式并加载配置

        :param file_path: 文件路径
        :return: 配置数据
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.json':
            return self.load_json(file_path)
        elif file_ext in ['.yaml', '.yml']:
            return self.load_yaml(file_path)
        else:
            raise ConfigLoadError(f"不支持的文件格式: {file_ext}")

    def save_json(self, file_path: str, data: Dict[str, Any], create_backup: bool = True) -> None:
        """
        保存配置到JSON文件

        :param file_path: 文件路径
        :param data: 配置数据
        :param create_backup: 是否创建备份
        """
        try:
            # 创建备份
            if create_backup:
                self._create_backup(file_path)

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 保存新配置
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=False)

            logging.info(f"成功保存JSON配置文件: {file_path}")

        except Exception as e:
            raise ConfigSaveError(f"保存配置文件失败: {e}")

    def save_yaml(self, file_path: str, data: Dict[str, Any], create_backup: bool = True) -> None:
        """
        保存配置到YAML文件

        :param file_path: 文件路径
        :param data: 配置数据
        :param create_backup: 是否创建备份
        """
        if not HAS_YAML:
            raise ConfigSaveError("PyYAML未安装，无法保存YAML文件")

        try:
            # 创建备份
            if create_backup:
                self._create_backup(file_path)

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 保存新配置
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            logging.info(f"成功保存YAML配置文件: {file_path}")

        except Exception as e:
            raise ConfigSaveError(f"保存YAML配置文件失败: {e}")

    def save_config(self, file_path: str, data: Dict[str, Any], create_backup: bool = True) -> None:
        """
        自动检测文件格式并保存配置

        :param file_path: 文件路径
        :param data: 配置数据
        :param create_backup: 是否创建备份
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.json':
            self.save_json(file_path, data, create_backup)
        elif file_ext in ['.yaml', '.yml']:
            self.save_yaml(file_path, data, create_backup)
        else:
            raise ConfigSaveError(f"不支持的文件格式: {file_ext}")

    def _create_backup(self, file_path: str) -> Optional[str]:
        """
        创建配置文件备份

        :param file_path: 原文件路径
        :return: 备份文件路径
        """
        if not os.path.exists(file_path):
            return None

        try:
            # 生成备份文件名 - 使用日期时间格式
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{Path(file_path).stem}.backup.{timestamp}{Path(file_path).suffix}"
            
            # 优先使用配置管理器中的备份目录
            if self.config_manager:
                backup_dir = self.config_manager.get_config_backups_dir()
                if backup_dir:
                    backup_dir = backup_dir
                else:
                    # 如果配置管理器中没有配置，使用默认路径
                    backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
            else:
                # 如果没有配置管理器，使用默认路径
                backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
            
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, backup_filename)

            # 复制文件
            shutil.copy2(file_path, backup_path)

            logging.info(f"配置文件已备份到: {backup_path}")
            return backup_path

        except Exception as e:
            logging.warning(f"创建配置文件备份失败: {e}")
            return None

    def list_backups(self, config_dir: str) -> list:
        """
        列出所有备份文件

        :param config_dir: 配置目录
        :return: 备份文件列表
        """
        backup_dir = os.path.join(config_dir, 'backups')
        if not os.path.exists(backup_dir):
            return []

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith(('.json', '.yaml', '.yml')) and '.backup.' in filename:
                filepath = os.path.join(backup_dir, filename)
                backups.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size': os.path.getsize(filepath),
                    'mtime': os.path.getmtime(filepath)
                })

        # 按修改时间排序
        backups.sort(key=lambda x: x['mtime'], reverse=True)
        return backups

    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """
        从备份恢复配置

        :param backup_path: 备份文件路径
        :param target_path: 目标文件路径
        :return: 是否恢复成功
        """
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"备份文件不存在: {backup_path}")

            # 创建目标目录
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # 复制备份文件
            shutil.copy2(backup_path, target_path)

            logging.info(f"成功从备份恢复配置: {backup_path} -> {target_path}")
            return True

        except Exception as e:
            logging.error(f"从备份恢复配置失败: {e}")
            return False

    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并配置（override_config会覆盖base_config中的相同键）

        :param base_config: 基础配置
        :param override_config: 覆盖配置
        :return: 合并后的配置
        """
        merged = base_config.copy()

        for key, value in override_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # 递归合并嵌套字典
                merged[key] = self.merge_configs(merged[key], value)
            else:
                # 直接覆盖
                merged[key] = value

        return merged

    def validate_config_structure(self, config: Dict[str, Any], required_keys: list) -> tuple:
        """
        验证配置结构

        :param config: 配置数据
        :param required_keys: 必需的键列表
        :return: (是否有效, 缺失的键列表)
        """
        missing_keys = []

        def check_keys(data, keys, path=""):
            for key in keys:
                full_path = f"{path}.{key}" if path else key
                if key not in data:
                    missing_keys.append(full_path)
                elif isinstance(data[key], dict) and isinstance(keys, dict) and key in keys:
                    # 递归检查嵌套结构
                    if isinstance(keys[key], dict):
                        check_keys(data[key], keys[key], full_path)

        if isinstance(required_keys, list):
            check_keys(config, required_keys)
        else:
            check_keys(config, required_keys)

        return len(missing_keys) == 0, missing_keys

    def get_config_info(self, config_path: str) -> Dict[str, Any]:
        """
        获取配置文件的元信息

        :param config_path: 配置文件路径
        :return: 配置元信息
        """
        info = {
            'exists': os.path.exists(config_path),
            'size': 0,
            'modified_time': None,
            'format': Path(config_path).suffix.lower()
        }

        if info['exists']:
            stat = os.stat(config_path)
            info['size'] = stat.st_size
            info['modified_time'] = stat.st_mtime

        return info


if __name__ == "__main__":
    # 测试配置加载器
    loader = ConfigLoader()

    # 测试配置文件路径
    config_path = "v3/config/v3_config.json"

    try:
        # 加载配置
        config = loader.load_config(config_path)
        print(f"成功加载配置，版本: {config.get('version', 'unknown')}")

        # 获取配置信息
        info = loader.get_config_info(config_path)
        print(f"配置文件信息: {info}")

        # 列出备份
        backups = loader.list_backups("v3/config")
        print(f"找到 {len(backups)} 个备份文件")

    except Exception as e:
        print(f"测试失败: {e}")
