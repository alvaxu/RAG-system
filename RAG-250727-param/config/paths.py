'''
程序说明：
## 1. 路径管理器，统一管理所有路径
## 2. 提供路径验证和创建功能
## 3. 支持相对路径和绝对路径转换
## 4. 简化路径管理
'''

import os
from pathlib import Path
from typing import Dict, List, Optional


class PathManager:
    """
    路径管理器
    """
    
    def __init__(self, base_dir: str = None, settings=None):
        """
        初始化路径管理器
        :param base_dir: 基础目录
        :param settings: 设置对象，用于加载路径配置
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.settings = settings
        self.paths = {}
        self._init_paths()
    
    def _init_paths(self):
        """
        初始化路径配置
        """
        if self.settings:
            # 从Settings对象加载路径配置
            self.paths = {
                'pdf': Path(self.settings.pdf_dir),
                'md': Path(self.settings.md_dir),
                'output': Path(self.settings.output_dir),
                'vector_db': Path(self.settings.vector_db_dir),
                'memory_db': Path(self.settings.memory_db_dir),
                'central_images': Path(self.settings.central_images_dir),
                'web_app': Path(self.settings.web_app_dir),
                'config': self.base_dir / 'config',
                'logs': self.base_dir / 'logs'
            }
        else:
            # 使用默认路径配置（向后兼容）
            self.paths = {
                'pdf': self.base_dir / 'pdf_test',
                'md': self.base_dir / 'md_test',
                'output': self.base_dir / 'md_test',
                'vector_db': self.base_dir / 'vector_db_test',
                'memory_db': self.base_dir / 'memory_db',
                'central_images': self.base_dir / 'central' / 'images',
                'web_app': self.base_dir / 'web_app_test',
                'config': self.base_dir / 'config',
                'logs': self.base_dir / 'logs'
            }
    
    def get_path(self, name: str) -> str:
        """
        获取路径
        :param name: 路径名称
        :return: 路径字符串
        """
        return str(self.paths.get(name, ''))
    
    def set_path(self, name: str, path: str):
        """
        设置路径
        :param name: 路径名称
        :param path: 路径
        """
        self.paths[name] = Path(path)
    
    def ensure_dir(self, name: str) -> bool:
        """
        确保目录存在
        :param name: 路径名称
        :return: 是否成功
        """
        try:
            path = self.paths.get(name)
            if path:
                path.mkdir(parents=True, exist_ok=True)
                return True
            return False
        except Exception:
            return False
    
    def ensure_all_dirs(self) -> Dict[str, bool]:
        """
        确保所有目录存在
        :return: 结果字典
        """
        results = {}
        for name in self.paths:
            results[name] = self.ensure_dir(name)
        return results
    
    def validate_paths(self) -> Dict[str, bool]:
        """
        验证路径
        :return: 验证结果
        """
        results = {}
        for name, path in self.paths.items():
            results[name] = path.exists()
        return results
    
    def get_relative_path(self, name: str) -> str:
        """
        获取相对路径
        :param name: 路径名称
        :return: 相对路径
        """
        path = self.paths.get(name)
        if path:
            try:
                return str(path.relative_to(self.base_dir))
            except ValueError:
                return str(path)
        return ''
    
    def list_files(self, name: str, pattern: str = "*") -> List[str]:
        """
        列出目录中的文件
        :param name: 路径名称
        :param pattern: 文件模式
        :return: 文件列表
        """
        path = self.paths.get(name)
        if path and path.exists():
            return [str(f) for f in path.glob(pattern)]
        return []
    
    def get_file_count(self, name: str, pattern: str = "*") -> int:
        """
        获取文件数量
        :param name: 路径名称
        :param pattern: 文件模式
        :return: 文件数量
        """
        return len(self.list_files(name, pattern))
    
    def get_dir_size(self, name: str) -> int:
        """
        获取目录大小（字节）
        :param name: 路径名称
        :return: 目录大小
        """
        path = self.paths.get(name)
        if not path or not path.exists():
            return 0
        
        total_size = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def get_path_info(self, name: str) -> Dict:
        """
        获取路径信息
        :param name: 路径名称
        :return: 路径信息
        """
        path = self.paths.get(name)
        if not path:
            return {}
        
        info = {
            'name': name,
            'path': str(path),
            'relative_path': self.get_relative_path(name),
            'exists': path.exists(),
            'is_dir': path.is_dir() if path.exists() else False,
            'is_file': path.is_file() if path.exists() else False
        }
        
        if path.exists() and path.is_dir():
            info.update({
                'file_count': self.get_file_count(name),
                'size_bytes': self.get_dir_size(name),
                'size_mb': self.get_dir_size(name) / (1024 * 1024)
            })
        
        return info
    
    def get_all_paths_info(self) -> Dict[str, Dict]:
        """
        获取所有路径信息
        :return: 路径信息字典
        """
        return {name: self.get_path_info(name) for name in self.paths}
    
    def print_paths_info(self):
        """
        打印路径信息
        """
        print("\n路径信息:")
        print("=" * 60)
        
        for name, info in self.get_all_paths_info().items():
            status = "✅" if info['exists'] else "❌"
            print(f"{status} {name}:")
            print(f"    路径: {info['relative_path']}")
            
            if info['exists']:
                if info['is_dir']:
                    print(f"    类型: 目录")
                    print(f"    文件数: {info.get('file_count', 0)}")
                    print(f"    大小: {info.get('size_mb', 0):.2f} MB")
                else:
                    print(f"    类型: 文件")
            else:
                print(f"    状态: 不存在")
            print() 