"""
路径管理器

负责管理系统中所有文件路径，支持相对路径和绝对路径转换，验证路径有效性，创建必要目录。
"""

import os
import time
import logging
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class PathManager:
    """
    路径管理器

    功能：
    - 管理所有文件路径
    - 验证路径的有效性
    - 创建必要的目录
    - 处理相对路径和绝对路径
    - 清理临时文件
    """

    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化路径管理器

        :param base_dir: 基础目录，默认使用当前文件所在目录的上级目录
        """
        if base_dir is None:
            # 获取当前文件的上级目录作为基础目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.base_dir = os.path.dirname(current_dir)  # v3目录
        else:
            self.base_dir = base_dir

        self.temp_dirs_created = []

    def validate_paths(self, paths_config: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        验证路径配置

        :param paths_config: 路径配置字典
        :return: (是否验证通过, 错误信息列表)
        """
        errors = []
        warnings = []

        # 必需的路径配置
        required_paths = [
            'input_pdf_dir',
            'mineru_output_dir',
            'final_image_dir',
            'vector_db_dir'
        ]

        # 检查必需路径
        for path_key in required_paths:
            if path_key not in paths_config:
                errors.append(f"缺少必需的路径配置: {path_key}")
                continue

            path = paths_config[path_key]
            is_valid, error_msg = self._validate_single_path(path, path_key)
            if not is_valid:
                errors.append(f"{path_key}: {error_msg}")

        # 检查可选路径
        optional_paths = ['temp_dir', 'logs_dir']
        for path_key in optional_paths:
            if path_key in paths_config:
                path = paths_config[path_key]
                is_valid, error_msg = self._validate_single_path(path, path_key, required=False)
                if not is_valid:
                    warnings.append(f"{path_key}: {error_msg}")

        return len(errors) == 0, errors + warnings

    def _validate_single_path(self, path: str, path_key: str, required: bool = True) -> Tuple[bool, str]:
        """
        验证单个路径

        :param path: 路径字符串
        :param path_key: 路径键名
        :param required: 是否为必需路径
        :return: (是否有效, 错误信息)
        """
        try:
            # 检查路径是否为空
            if not path or not path.strip():
                if required:
                    return False, "路径配置为空"
                else:
                    return True, ""  # 可选路径为空是允许的

            # 检查路径是否包含非法字符
            if any(char in path for char in ['<', '>', '|', '"']):
                return False, f"路径包含非法字符: {path}"

            # 转换为绝对路径
            abs_path = self.get_absolute_path(path)

            # 检查父目录是否存在
            parent_dir = os.path.dirname(abs_path)
            if not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                    logging.info(f"创建父目录: {parent_dir}")
                except Exception as e:
                    return False, f"无法创建父目录: {e}"

            # 对于输入目录，检查是否存在，不存在则创建
            if path_key == 'input_pdf_dir':
                if not os.path.exists(abs_path):
                    try:
                        os.makedirs(abs_path, exist_ok=True)
                        logging.info(f"创建输入PDF目录: {abs_path}")
                    except Exception as e:
                        return False, f"无法创建输入目录: {e}"

            # 对于输出目录，尝试创建
            elif path_key in ['mineru_output_dir', 'final_image_dir', 'vector_db_dir', 'temp_dir', 'logs_dir']:
                try:
                    os.makedirs(abs_path, exist_ok=True)
                    logging.debug(f"确保目录存在: {abs_path}")
                except Exception as e:
                    return False, f"无法创建目录: {e}"

            return True, ""

        except Exception as e:
            return False, f"路径验证失败: {str(e)}"

    def get_absolute_path(self, relative_path: str) -> str:
        """
        将相对路径转换为绝对路径

        :param relative_path: 相对路径
        :return: 绝对路径
        """
        if not relative_path:
            return ""

        # 如果已经是绝对路径，直接返回
        if os.path.isabs(relative_path):
            return relative_path

        # 转换为绝对路径
        return os.path.join(self.base_dir, relative_path)

    def get_relative_path(self, absolute_path: str) -> str:
        """
        将绝对路径转换为相对路径

        :param absolute_path: 绝对路径
        :return: 相对路径
        """
        if not absolute_path:
            return ""

        try:
            return os.path.relpath(absolute_path, self.base_dir)
        except ValueError:
            # 如果无法转换为相对路径，返回绝对路径
            return absolute_path

    def ensure_directory(self, path: str) -> bool:
        """
        确保目录存在，如果不存在则创建

        :param path: 目录路径
        :return: 是否成功
        """
        try:
            abs_path = self.get_absolute_path(path)
            os.makedirs(abs_path, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"创建目录失败: {path}, 错误: {e}")
            return False

    def create_temp_dir(self, prefix: str = "temp") -> str:
        """
        创建临时目录

        :param prefix: 临时目录前缀
        :return: 临时目录路径
        """
        timestamp = int(time.time())
        temp_dir_name = f"{prefix}_{timestamp}"
        temp_dir = os.path.join(self.base_dir, "temp", temp_dir_name)

        try:
            os.makedirs(temp_dir, exist_ok=True)
            self.temp_dirs_created.append(temp_dir)
            logging.debug(f"创建临时目录: {temp_dir}")
            return temp_dir
        except Exception as e:
            logging.error(f"创建临时目录失败: {e}")
            raise

    def cleanup_temp_dirs(self, max_age_hours: int = 24) -> int:
        """
        清理过期的临时目录

        :param max_age_hours: 最大保留时间（小时）
        :return: 清理的目录数量
        """
        temp_root = os.path.join(self.base_dir, "temp")
        if not os.path.exists(temp_root):
            return 0

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0

        try:
            for item in os.listdir(temp_root):
                item_path = os.path.join(temp_root, item)
                if os.path.isdir(item_path):
                    # 检查目录是否过期
                    try:
                        dir_mtime = os.path.getmtime(item_path)
                        if current_time - dir_mtime > max_age_seconds:
                            shutil.rmtree(item_path)
                            cleaned_count += 1
                            logging.info(f"清理过期临时目录: {item_path}")
                    except Exception as e:
                        logging.warning(f"清理临时目录失败: {item_path}, 错误: {e}")

        except Exception as e:
            logging.error(f"清理临时目录过程出错: {e}")

        return cleaned_count

    def get_file_info(self, file_path: str) -> Dict:
        """
        获取文件信息

        :param file_path: 文件路径
        :return: 文件信息字典
        """
        abs_path = self.get_absolute_path(file_path)

        if not os.path.exists(abs_path):
            return {
                'exists': False,
                'size': 0,
                'modified_time': None,
                'is_file': False,
                'is_dir': False
            }

        stat = os.stat(abs_path)

        return {
            'exists': True,
            'size': stat.st_size,
            'modified_time': stat.st_mtime,
            'is_file': os.path.isfile(abs_path),
            'is_dir': os.path.isdir(abs_path),
            'absolute_path': abs_path,
            'relative_path': self.get_relative_path(abs_path)
        }

    def list_files(self, directory: str, pattern: str = "*", recursive: bool = False) -> List[str]:
        """
        列出目录中的文件

        :param directory: 目录路径
        :param pattern: 文件模式匹配
        :param recursive: 是否递归查找
        :return: 文件列表
        """
        abs_dir = self.get_absolute_path(directory)

        if not os.path.exists(abs_dir):
            return []

        try:
            path_obj = Path(abs_dir)
            if recursive:
                files = path_obj.rglob(pattern)
            else:
                files = path_obj.glob(pattern)

            return [str(f) for f in files if f.is_file()]
        except Exception as e:
            logging.error(f"列出文件失败: {directory}, 错误: {e}")
            return []

    def get_base_dir(self) -> str:
        """
        获取基础目录

        :return: 基础目录路径
        """
        return self.base_dir

    def set_base_dir(self, base_dir: str) -> None:
        """
        设置基础目录

        :param base_dir: 新的基础目录
        """
        if not os.path.isabs(base_dir):
            raise ValueError("基础目录必须是绝对路径")

        if not os.path.exists(base_dir):
            raise ValueError(f"基础目录不存在: {base_dir}")

        self.base_dir = base_dir
        logging.info(f"基础目录已设置为: {base_dir}")

    def normalize_path(self, path: str) -> str:
        """
        规范化路径

        :param path: 路径字符串
        :return: 规范化后的路径
        """
        if not path:
            return ""

        # 替换路径分隔符
        path = path.replace('\\', '/')

        # 移除多余的斜杠
        while '//' in path:
            path = path.replace('//', '/')

        return path

    def join_paths(self, *paths: str) -> str:
        """
        安全地连接多个路径

        :param paths: 路径列表
        :return: 连接后的路径
        """
        if not paths:
            return ""

        # 过滤空路径
        valid_paths = [p for p in paths if p and p.strip()]

        if not valid_paths:
            return ""

        result = valid_paths[0]
        for path in valid_paths[1:]:
            result = os.path.join(result, path)

        return result

    def cleanup_created_temp_dirs(self) -> int:
        """
        清理本次运行中创建的临时目录

        :return: 清理的目录数量
        """
        cleaned_count = 0

        for temp_dir in self.temp_dirs_created:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    cleaned_count += 1
                    logging.debug(f"清理临时目录: {temp_dir}")
            except Exception as e:
                logging.warning(f"清理临时目录失败: {temp_dir}, 错误: {e}")

        self.temp_dirs_created.clear()
        return cleaned_count


if __name__ == "__main__":
    # 测试路径管理器
    path_manager = PathManager()

    print(f"基础目录: {path_manager.get_base_dir()}")

    # 测试路径验证
    test_paths = {
        'input_pdf_dir': './document/orig_pdf',
        'mineru_output_dir': './document/md',
        'final_image_dir': './central/images',
        'vector_db_dir': './central/vector_db'
    }

    is_valid, messages = path_manager.validate_paths(test_paths)
    print(f"路径验证结果: {'通过' if is_valid else '失败'}")

    if messages:
        print("消息:")
        for msg in messages:
            print(f"  - {msg}")

    # 测试临时目录创建
    temp_dir = path_manager.create_temp_dir("test")
    print(f"创建临时目录: {temp_dir}")

    # 清理临时目录
    cleaned = path_manager.cleanup_created_temp_dirs()
    print(f"清理临时目录数量: {cleaned}")
