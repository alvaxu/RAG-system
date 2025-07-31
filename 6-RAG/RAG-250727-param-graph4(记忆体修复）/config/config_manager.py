'''
程序说明：
## 1. 配置管理器，整合所有配置功能
## 2. 提供统一的配置接口
## 3. 支持多种配置源
## 4. 简化配置管理
'''

import os
import json
import argparse
from typing import Dict, Any, Optional
from pathlib import Path

from .settings import Settings
from .paths import PathManager


class ConfigManager:
    """
    配置管理器，统一管理所有配置
    """
    
    def __init__(self, config_file: str = None):
        """
        初始化配置管理器
        :param config_file: 配置文件路径
        """
        self.config_file = config_file or "config.json"
        self.settings = Settings.load_from_file(self.config_file)
        self.path_manager = PathManager(self.settings.base_dir, self.settings)
        
        # 确保所有目录存在
        self.path_manager.ensure_all_dirs()
    
    def get_settings(self) -> Settings:
        """
        获取设置对象
        :return: 设置对象
        """
        return self.settings
    
    def get_path_manager(self) -> PathManager:
        """
        获取路径管理器
        :return: 路径管理器
        """
        return self.path_manager
    
    def update_from_args(self, args: argparse.Namespace):
        """
        从命令行参数更新配置
        :param args: 命令行参数
        """
        # 更新路径配置
        if hasattr(args, 'input') and args.input:
            if args.mode == 'pdf':
                self.settings.pdf_dir = args.input
            else:
                self.settings.md_dir = args.input
        
        if hasattr(args, 'output') and args.output:
            self.settings.output_dir = args.output
        
        if hasattr(args, 'vector_db') and args.vector_db:
            self.settings.vector_db_dir = args.vector_db
        
        # 更新处理配置
        if hasattr(args, 'chunk_size') and args.chunk_size:
            self.settings.chunk_size = args.chunk_size
        
        if hasattr(args, 'chunk_overlap') and args.chunk_overlap:
            self.settings.chunk_overlap = args.chunk_overlap
        
        # 重新初始化路径管理器
        self.path_manager = PathManager(self.settings.base_dir, self.settings)
        self.path_manager.ensure_all_dirs()
    
    def save_config(self, file_path: str = None):
        """
        保存配置到文件
        :param file_path: 文件路径
        """
        save_path = file_path or self.config_file
        self.settings.save_to_file(save_path)
        print(f"配置已保存到: {save_path}")
    
    def load_config(self, file_path: str):
        """
        从文件加载配置
        :param file_path: 文件路径
        """
        self.settings = Settings.load_from_file(file_path)
        self.path_manager = PathManager(self.settings.base_dir, self.settings)
        self.path_manager.ensure_all_dirs()
        print(f"配置已从文件加载: {file_path}")
    
    def create_default_config(self, file_path: str = None):
        """
        创建默认配置文件
        :param file_path: 文件路径
        """
        save_path = file_path or self.config_file
        default_settings = Settings()
        default_settings.save_to_file(save_path)
        print(f"默认配置文件已创建: {save_path}")
    
    def validate_config(self) -> Dict[str, bool]:
        """
        验证配置
        :return: 验证结果
        """
        results = {
            'api_keys': self._validate_api_keys(),
            'paths': self._validate_paths(),
            'settings': self._validate_settings()
        }
        return results
    
    def _validate_api_keys(self) -> bool:
        """
        验证API密钥
        :return: 是否有效
        """
        dashscope_valid = bool(self.settings.dashscope_api_key and 
                              self.settings.dashscope_api_key != '你的APIKEY')
        mineru_valid = bool(self.settings.mineru_api_key)
        
        if not dashscope_valid:
            print("警告: DashScope API密钥未配置或无效")
        
        if not mineru_valid:
            print("警告: minerU API密钥未配置")
        
        return dashscope_valid and mineru_valid
    
    def _validate_paths(self) -> bool:
        """
        验证路径
        :return: 是否有效
        """
        return all(self.path_manager.validate_paths().values())
    
    def _validate_settings(self) -> bool:
        """
        验证设置
        :return: 是否有效
        """
        # 检查基本设置
        if self.settings.chunk_size <= 0:
            print("错误: chunk_size必须大于0")
            return False
        
        if self.settings.chunk_overlap < 0:
            print("错误: chunk_overlap不能为负数")
            return False
        
        if self.settings.chunk_overlap >= self.settings.chunk_size:
            print("错误: chunk_overlap必须小于chunk_size")
            return False
        
        return True
    
    def print_config_summary(self):
        """
        打印配置摘要
        """
        print("\n配置摘要:")
        print("=" * 60)
        
        # API配置
        print("API配置:")
        dashscope_status = "✅" if self.settings.dashscope_api_key and self.settings.dashscope_api_key != '你的APIKEY' else "❌"
        mineru_status = "✅" if self.settings.mineru_api_key else "❌"
        print(f"  {dashscope_status} DashScope API密钥: {'已配置' if dashscope_status == '✅' else '未配置'}")
        print(f"  {mineru_status} minerU API密钥: {'已配置' if mineru_status == '✅' else '未配置'}")
        
        # 路径配置
        print("\n路径配置:")
        path_names = ['pdf', 'md', 'output', 'vector_db', 'memory_db', 'images', 'web_app']
        for name in path_names:
            path = getattr(self.settings, f'{name}_dir', None)
            if path:
                status = "✅" if os.path.exists(path) else "❌"
                print(f"  {status} {name}: {path}")
        
        # 处理配置
        print("\n处理配置:")
        print(f"  分块大小: {self.settings.chunk_size}")
        print(f"  分块重叠: {self.settings.chunk_overlap}")
        print(f"  最大表格行数: {self.settings.max_table_rows}")
        
        # 向量存储配置
        print("\n向量存储配置:")
        print(f"  向量维度: {self.settings.vector_dimension}")
        print(f"  相似度Top-K: {self.settings.similarity_top_k}")
        
        # 问答系统配置
        print("\n问答系统配置:")
        print(f"  模型名称: {self.settings.model_name}")
        print(f"  温度: {self.settings.temperature}")
        print(f"  最大令牌数: {self.settings.max_tokens}")
        
        # 记忆配置
        print("\n记忆配置:")
        print(f"  记忆功能: {'启用' if self.settings.memory_enabled else '禁用'}")
        print(f"  最大记忆大小: {self.settings.memory_max_size}")
        
        print("=" * 60)
    
    def get_config_for_processing(self) -> Dict[str, Any]:
        """
        获取文档处理配置
        :return: 处理配置
        """
        return {
            'chunk_size': self.settings.chunk_size,
            'chunk_overlap': self.settings.chunk_overlap,
            'max_table_rows': self.settings.max_table_rows,
            'enable_logging': self.settings.enable_logging,
            'vector_dimension': self.settings.vector_dimension,
            'similarity_top_k': self.settings.similarity_top_k
        }
    
    def get_config_for_qa(self) -> Dict[str, Any]:
        """
        获取问答系统配置
        :return: 问答配置
        """
        return {
            'model_name': self.settings.model_name,
            'temperature': self.settings.temperature,
            'max_tokens': self.settings.max_tokens,
            'memory_enabled': self.settings.memory_enabled,
            'memory_max_size': self.settings.memory_max_size
        }
    
    @staticmethod
    def create_arg_parser() -> argparse.ArgumentParser:
        """
        创建命令行参数解析器
        :return: 参数解析器
        """
        parser = argparse.ArgumentParser(description='RAG系统统一文档处理器')
        
        # 配置管理参数（优先级最高）
        parser.add_argument('--show-config', action='store_true',
                          help='显示配置摘要')
        parser.add_argument('--validate', action='store_true',
                          help='验证配置')
        parser.add_argument('--save-config', action='store_true',
                          help='保存当前配置到文件')
        parser.add_argument('--config', default='config.json',
                          help='配置文件路径')
        
        # 处理参数（仅在非配置管理模式下需要）
        parser.add_argument('--mode', choices=['pdf', 'markdown'],
                          help='处理模式: pdf 或 markdown (使用配置文件中的路径)')
        parser.add_argument('--input',
                          help='输入目录路径 (可选，默认使用配置文件中的路径)')
        parser.add_argument('--output',
                          help='输出目录路径 (可选，仅PDF模式，默认使用配置文件中的路径)')
        parser.add_argument('--vector-db',
                          help='向量数据库路径 (可选，默认使用配置文件中的路径)')
        parser.add_argument('--chunk-size', type=int,
                          help='文档分块大小 (可选，默认使用配置文件中的值)')
        parser.add_argument('--chunk-overlap', type=int,
                          help='文档分块重叠大小 (可选，默认使用配置文件中的值)')
        
        return parser 