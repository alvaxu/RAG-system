'''
程序说明：
## 1. 统一设置类，整合所有配置项
## 2. 支持从配置文件、环境变量、命令行参数加载
## 3. 提供默认配置和验证功能
## 4. 简化配置管理
'''

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class Settings:
    """
    统一设置类，管理所有配置项
    """
    
    # API配置
    dashscope_api_key: str = field(default='')
    mineru_api_key: str = field(default='')
    
    # 路径配置
    base_dir: str = field(default_factory=lambda: os.getcwd())
    pdf_dir: str = field(default='./pdf')
    md_dir: str = field(default='./md_test')
    output_dir: str = field(default='./md_test')
    vector_db_dir: str = field(default='./vector_db_test')
    memory_db_dir: str = field(default='./memory_db')
    images_dir: str = field(default='./md_test/images')
    web_app_dir: str = field(default='./web_app')
    
    # 处理配置
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_table_rows: int = 100
    enable_logging: bool = True
    
    # 向量存储配置
    vector_dimension: int = 1536
    similarity_top_k: int = 3
    
    # 问答系统配置
    model_name: str = 'qwen-turbo'
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # 记忆配置
    memory_enabled: bool = True
    memory_max_size: int = 10
    
    # 预设问题配置
    preset_questions_file: str = field(default='./preset_questions_test.json')
    
    def __post_init__(self):
        """
        初始化后处理
        """
        # 确保所有路径都是绝对路径
        self._normalize_paths()
        
        # 验证配置
        self._validate_settings()
    
    def _normalize_paths(self):
        """
        标准化路径
        """
        base_path = Path(self.base_dir)
        
        self.pdf_dir = str(base_path / self.pdf_dir)
        self.md_dir = str(base_path / self.md_dir)
        self.output_dir = str(base_path / self.output_dir)
        self.vector_db_dir = str(base_path / self.vector_db_dir)
        self.memory_db_dir = str(base_path / self.memory_db_dir)
        self.images_dir = str(base_path / self.images_dir)
        self.web_app_dir = str(base_path / self.web_app_dir)
        self.preset_questions_file = str(base_path / self.preset_questions_file)
    
    def _validate_settings(self):
        """
        验证配置
        """
        # 检查API密钥 - 只在真正未配置时才警告
        if not self.dashscope_api_key or self.dashscope_api_key in ['你的APIKEY', '你的DashScope API密钥']:
            print("警告: 未配置DashScope API密钥")
        
        if not self.mineru_api_key or self.mineru_api_key == '你的minerU API密钥':
            print("警告: 未配置minerU API密钥")
        
        # 检查路径（不自动创建，让用户自己管理）
        # required_dirs = [self.pdf_dir, self.md_dir, self.output_dir]
        # for dir_path in required_dirs:
        #     if not os.path.exists(dir_path):
        #         os.makedirs(dir_path, exist_ok=True)
        #         print(f"创建目录: {dir_path}")
    
    def get_vector_db_path(self, name: str = None) -> str:
        """
        获取向量数据库路径
        :param name: 数据库名称，如果为None则返回基础路径
        :return: 路径
        """
        if name is None:
            return self.vector_db_dir
        return os.path.join(self.vector_db_dir, name)
    
    def get_memory_db_path(self) -> str:
        """
        获取记忆数据库路径
        :return: 路径
        """
        return self.memory_db_dir
    
    def get_path(self, name: str) -> str:
        """
        获取指定路径
        :param name: 路径名称
        :return: 路径
        """
        path_map = {
            'pdf': self.pdf_dir,
            'md': self.md_dir,
            'output': self.output_dir,
            'vector_db': self.vector_db_dir,
            'memory_db': self.memory_db_dir,
            'images': self.images_dir,
            'web_app': self.web_app_dir
        }
        return path_map.get(name, '')
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        :return: 配置字典
        """
        return {
            'api': {
                'dashscope_api_key': self.dashscope_api_key,
                'mineru_api_key': self.mineru_api_key
            },
            'paths': {
                'pdf_dir': self.pdf_dir,
                'md_dir': self.md_dir,
                'output_dir': self.output_dir,
                'vector_db_dir': self.vector_db_dir,
                'memory_db_dir': self.memory_db_dir,
                'images_dir': self.images_dir,
                'web_app_dir': self.web_app_dir
            },
            'processing': {
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'max_table_rows': self.max_table_rows,
                'enable_logging': self.enable_logging
            },
            'vector_store': {
                'vector_dimension': self.vector_dimension,
                'similarity_top_k': self.similarity_top_k
            },
            'qa_system': {
                'model_name': self.model_name,
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            },
            'memory': {
                'memory_enabled': self.memory_enabled,
                'memory_max_size': self.memory_max_size
            },
            'preset_questions': {
                'preset_questions_file': self.preset_questions_file
            }
        }
    
    def save_to_file(self, file_path: str):
        """
        保存配置到文件
        :param file_path: 文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'Settings':
        """
        从文件加载配置
        :param file_path: 文件路径
        :return: 设置对象
        """
        if not os.path.exists(file_path):
            return cls()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # 创建设置对象
        settings = cls()
        
        # 更新API配置 - 按照优先级：配置文件 > 环境变量 > 默认值
        if 'api' in config_dict:
            api_config = config_dict['api']
            # 检查配置文件中的值
            config_dashscope_key = api_config.get('dashscope_api_key', '')
            if config_dashscope_key and config_dashscope_key != '你的DashScope API密钥':
                settings.dashscope_api_key = config_dashscope_key
            else:
                # 如果配置文件中的值无效，使用环境变量
                env_dashscope_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
                if env_dashscope_key:
                    settings.dashscope_api_key = env_dashscope_key
            
            config_mineru_key = api_config.get('mineru_api_key', '')
            if config_mineru_key and config_mineru_key != '你的minerU API密钥':
                settings.mineru_api_key = config_mineru_key
            else:
                # 如果配置文件中的值无效，使用环境变量
                env_mineru_key = os.getenv('MINERU_API_KEY', '')
                if env_mineru_key:
                    settings.mineru_api_key = env_mineru_key
        
        # 更新路径配置
        if 'paths' in config_dict:
            paths_config = config_dict['paths']
            for key, value in paths_config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        # 更新处理配置
        if 'processing' in config_dict:
            processing_config = config_dict['processing']
            for key, value in processing_config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        # 更新向量存储配置
        if 'vector_store' in config_dict:
            vector_config = config_dict['vector_store']
            for key, value in vector_config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        # 更新问答系统配置
        if 'qa_system' in config_dict:
            qa_config = config_dict['qa_system']
            for key, value in qa_config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        # 更新记忆配置
        if 'memory' in config_dict:
            memory_config = config_dict['memory']
            for key, value in memory_config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        # 更新预设问题配置
        if 'preset_questions' in config_dict:
            preset_config = config_dict['preset_questions']
            for key, value in preset_config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        # 重新标准化路径（确保从配置文件加载的路径也转换为绝对路径）
        settings._normalize_paths()
        
        return settings 