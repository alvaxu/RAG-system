'''
程序说明：
## 1. 统一设置类，整合所有配置项
## 2. 支持从配置文件、环境变量、命令行参数加载
## 3. 提供默认配置和验证功能
## 4. 简化配置管理
'''

import os
import json
from typing import Dict, Any, Optional, List
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
    
    def __init__(self, **kwargs):
        # 基本配置
        self.dashscope_api_key = kwargs.get('dashscope_api_key', '')
        self.mineru_api_key = kwargs.get('mineru_api_key', '')
        
        # 路径配置
        self.base_dir = kwargs.get('base_dir', os.getcwd())
        self.pdf_dir = kwargs.get('pdf_dir', '')
        self.output_dir = kwargs.get('output_dir', '')
        self.md_dir = kwargs.get('md_dir', '')
        self.central_images_dir = kwargs.get('central_images_dir', '')
        self.add_pdf_dir = kwargs.get('add_pdf_dir', '')
        self.add_output_dir = kwargs.get('add_output_dir', '')
        self.add_md_dir = kwargs.get('add_md_dir', '')
        self.vector_db_dir = kwargs.get('vector_db_dir', '')
        self.web_app_dir = kwargs.get('web_app_dir', '')
        self.memory_db_dir = kwargs.get('memory_db_dir', '')
        
        # 处理配置
        self.chunk_size = kwargs.get('chunk_size', 1000)
        self.chunk_overlap = kwargs.get('chunk_overlap', 200)
        self.max_table_rows = kwargs.get('max_table_rows', 10)
        self.enable_logging = kwargs.get('enable_logging', True)
        self.enable_smart_filtering = kwargs.get('enable_smart_filtering', True)
        self.semantic_similarity_threshold = kwargs.get('semantic_similarity_threshold', 0.7)
        self.content_relevance_threshold = kwargs.get('content_relevance_threshold', 0.65)
        self.max_filtered_results = kwargs.get('max_filtered_results', 50)
        
        # 召回策略配置
        self.recall_strategy = kwargs.get('recall_strategy', {
            'layer1_structure_search': {'top_k': 10},
            'layer2_vector_search': {'top_k': 50, 'similarity_threshold': 0.65},
            'layer3_keyword_search': {'top_k': 20},
            'layer4_hybrid_search': {'top_k': 30},
            'layer5_fuzzy_search': {'top_k': 15},
            'layer6_expansion_search': {'top_k': 10}
        })
        
        # 向量存储配置
        self.vector_dimension = kwargs.get('vector_dimension', 1536)
        self.similarity_top_k = kwargs.get('similarity_top_k', 5)
        self.similarity_threshold = kwargs.get('similarity_threshold', 0.1)
        self.enable_reranking = kwargs.get('enable_reranking', True)
        self.reranking_method = kwargs.get('reranking_method', 'hybrid')
        self.semantic_weight = kwargs.get('semantic_weight', 0.7)
        self.keyword_weight = kwargs.get('keyword_weight', 0.3)
        self.min_similarity_threshold = kwargs.get('min_similarity_threshold', 0.001)
        self.text_embedding_model = kwargs.get('text_embedding_model', 'text-embedding-v1')
        self.image_embedding_model = kwargs.get('image_embedding_model', 'multimodal-embedding-v1')
        self.allow_dangerous_deserialization = kwargs.get('allow_dangerous_deserialization', True)
        
        # QA系统配置
        self.model_name = kwargs.get('model_name', 'qwen-turbo')
        self.temperature = kwargs.get('temperature', 0.5)
        self.max_tokens = kwargs.get('max_tokens', 1500)
        self.enable_sources_filtering = kwargs.get('enable_sources_filtering', True)
        self.min_relevance_score = kwargs.get('min_relevance_score', 0.001)
        self.enable_keyword_matching = kwargs.get('enable_keyword_matching', True)
        self.enable_image_id_matching = kwargs.get('enable_image_id_matching', True)
        self.enable_similarity_filtering = kwargs.get('enable_similarity_filtering', True)
        
        # 内存配置
        self.memory_enabled = kwargs.get('memory_enabled', True)
        self.memory_max_size = kwargs.get('memory_max_size', 10)
        
        # 图像处理配置
        self.enable_enhancement = kwargs.get('enable_enhancement', True)
        self.enable_enhanced_description_vectorization = kwargs.get('enable_enhanced_description_vectorization', True)
        self.enhancement_model = kwargs.get('enhancement_model', 'qwen-vl-plus')
        self.enhancement_max_tokens = kwargs.get('enhancement_max_tokens', 1000)
        self.enhancement_temperature = kwargs.get('enhancement_temperature', 0.1)
        self.enhancement_batch_size = kwargs.get('enhancement_batch_size', 5)
        self.enable_progress_logging = kwargs.get('enable_progress_logging', True)
        self.depth_processing_markers = kwargs.get('depth_processing_markers', [
            '基础视觉描述:', '内容理解描述:', '数据趋势描述:', '语义特征描述:',
            'chart_type:', 'data_points:', 'trends:', 'key_insights:'
        ])
        
        # 预设问题配置
        self.preset_questions_file = kwargs.get('preset_questions_file', './preset_questions.json')
        
        # 处理嵌套结构
        if 'api' in kwargs:
            self.dashscope_api_key = kwargs['api'].get('dashscope_api_key', self.dashscope_api_key)
            self.mineru_api_key = kwargs['api'].get('mineru_api_key', self.mineru_api_key)
        if 'paths' in kwargs:
            self.pdf_dir = kwargs['paths'].get('pdf_dir', self.pdf_dir)
            self.output_dir = kwargs['paths'].get('output_dir', self.output_dir)
            self.md_dir = kwargs['paths'].get('md_dir', self.md_dir)
            self.central_images_dir = kwargs['paths'].get('central_images_dir', self.central_images_dir)
            self.add_pdf_dir = kwargs['paths'].get('add_pdf_dir', self.add_pdf_dir)
            self.add_output_dir = kwargs['paths'].get('add_output_dir', self.add_output_dir)
            self.add_md_dir = kwargs['paths'].get('add_md_dir', self.add_md_dir)
            self.vector_db_dir = kwargs['paths'].get('vector_db_dir', self.vector_db_dir)
            self.web_app_dir = kwargs['paths'].get('web_app_dir', self.web_app_dir)
            self.memory_db_dir = kwargs['paths'].get('memory_db_dir', self.memory_db_dir)
        if 'processing' in kwargs:
            self.chunk_size = kwargs['processing'].get('chunk_size', self.chunk_size)
            self.chunk_overlap = kwargs['processing'].get('chunk_overlap', self.chunk_overlap)
            self.max_table_rows = kwargs['processing'].get('max_table_rows', self.max_table_rows)
            self.enable_logging = kwargs['processing'].get('enable_logging', self.enable_logging)
            self.enable_smart_filtering = kwargs['processing'].get('enable_smart_filtering', self.enable_smart_filtering)
            self.semantic_similarity_threshold = kwargs['processing'].get('semantic_similarity_threshold', self.semantic_similarity_threshold)
            self.content_relevance_threshold = kwargs['processing'].get('content_relevance_threshold', self.content_relevance_threshold)
            self.max_filtered_results = kwargs['processing'].get('max_filtered_results', self.max_filtered_results)
        if 'vector_store' in kwargs:
            self.vector_dimension = kwargs['vector_store'].get('vector_dimension', self.vector_dimension)
            self.similarity_top_k = kwargs['vector_store'].get('similarity_top_k', self.similarity_top_k)
            self.similarity_threshold = kwargs['vector_store'].get('similarity_threshold', self.similarity_threshold)
            self.enable_reranking = kwargs['vector_store'].get('enable_reranking', self.enable_reranking)
            self.reranking_method = kwargs['vector_store'].get('reranking_method', self.reranking_method)
            self.semantic_weight = kwargs['vector_store'].get('semantic_weight', self.semantic_weight)
            self.keyword_weight = kwargs['vector_store'].get('keyword_weight', self.keyword_weight)
            self.min_similarity_threshold = kwargs['vector_store'].get('min_similarity_threshold', self.min_similarity_threshold)
            self.text_embedding_model = kwargs['vector_store'].get('text_embedding_model', self.text_embedding_model)
            self.image_embedding_model = kwargs['vector_store'].get('image_embedding_model', self.image_embedding_model)
            self.allow_dangerous_deserialization = kwargs['vector_store'].get('allow_dangerous_deserialization', self.allow_dangerous_deserialization)
        if 'qa_system' in kwargs:
            self.model_name = kwargs['qa_system'].get('model_name', self.model_name)
            self.temperature = kwargs['qa_system'].get('temperature', self.temperature)
            self.max_tokens = kwargs['qa_system'].get('max_tokens', self.max_tokens)
            self.enable_sources_filtering = kwargs['qa_system'].get('enable_sources_filtering', self.enable_sources_filtering)
            self.min_relevance_score = kwargs['qa_system'].get('min_relevance_score', self.min_relevance_score)
            self.enable_keyword_matching = kwargs['qa_system'].get('enable_keyword_matching', self.enable_keyword_matching)
            self.enable_image_id_matching = kwargs['qa_system'].get('enable_image_id_matching', self.enable_image_id_matching)
            self.enable_similarity_filtering = kwargs['qa_system'].get('enable_similarity_filtering', self.enable_similarity_filtering)
        if 'memory' in kwargs:
            self.memory_enabled = kwargs['memory'].get('memory_enabled', self.memory_enabled)
            self.memory_max_size = kwargs['memory'].get('memory_max_size', self.memory_max_size)
        if 'image_processing' in kwargs:
            self.enable_enhancement = kwargs['image_processing'].get('enable_enhancement', self.enable_enhancement)
            self.enable_enhanced_description_vectorization = kwargs['image_processing'].get('enable_enhanced_description_vectorization', self.enable_enhanced_description_vectorization)
            self.enhancement_model = kwargs['image_processing'].get('enhancement_model', self.enhancement_model)
            self.enhancement_max_tokens = kwargs['image_processing'].get('enhancement_max_tokens', self.enhancement_max_tokens)
            self.enhancement_temperature = kwargs['image_processing'].get('enhancement_temperature', self.enhancement_temperature)
            self.enhancement_batch_size = kwargs['image_processing'].get('enhancement_batch_size', self.enhancement_batch_size)
            self.enable_progress_logging = kwargs['image_processing'].get('enable_progress_logging', self.enable_progress_logging)
            self.depth_processing_markers = kwargs['image_processing'].get('depth_processing_markers', self.depth_processing_markers)
        if 'preset_questions' in kwargs:
            self.preset_questions_file = kwargs['preset_questions'].get('preset_questions_file', self.preset_questions_file)
    
    def __post_init__(self):
        """
        初始化后处理
        """
        # 确保所有路径都是绝对路径
        self._normalize_paths()
        
        # 注意：验证配置现在在load_from_file方法中手动调用
        # 避免在对象创建时自动验证（因为此时API密钥可能还未加载）
    
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
        self.central_images_dir = str(base_path / self.central_images_dir)
        self.web_app_dir = str(base_path / self.web_app_dir)
        self.preset_questions_file = str(base_path / self.preset_questions_file)
        
        # 新增文档路径标准化
        self.add_pdf_dir = str(base_path / self.add_pdf_dir)
        self.add_output_dir = str(base_path / self.add_output_dir)
        self.add_md_dir = str(base_path / self.add_md_dir)
    
    def _validate_settings(self):
        """
        验证配置
        """
        # 检查API密钥 - 只在真正未配置时才警告
        if not self.dashscope_api_key or self.dashscope_api_key in ['你的APIKEY', '你的DashScope API密钥', '']:
            print("警告: 未配置DashScope API密钥")
        
        if not self.mineru_api_key or self.mineru_api_key in ['你的minerU API密钥', '']:
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
            'central_images': self.central_images_dir,
            'web_app': self.web_app_dir,
            'add_pdf': self.add_pdf_dir,
            'add_output': self.add_output_dir,
            'add_md': self.add_md_dir
        }
        return path_map.get(name, '')
    
    def get(self, key: str, default=None):
        """
        获取配置值，兼容字典风格的访问
        """
        return getattr(self, key, default)

    def to_dict(self):
        """
        将设置对象转换为字典，确保包含所有字段
        """
        return {
            'dashscope_api_key': self.dashscope_api_key,
            'mineru_api_key': self.mineru_api_key,
            'pdf_dir': self.pdf_dir,
            'output_dir': self.output_dir,
            'md_dir': self.md_dir,
            'central_images_dir': self.central_images_dir,
            'add_pdf_dir': self.add_pdf_dir,
            'add_output_dir': self.add_output_dir,
            'add_md_dir': self.add_md_dir,
            'vector_db_dir': self.vector_db_dir,
            'web_app_dir': self.web_app_dir,
            'memory_db_dir': self.memory_db_dir,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'max_table_rows': self.max_table_rows,
            'enable_logging': self.enable_logging,
            'enable_smart_filtering': self.enable_smart_filtering,
            'semantic_similarity_threshold': self.semantic_similarity_threshold,
            'content_relevance_threshold': self.content_relevance_threshold,
            'max_filtered_results': self.max_filtered_results,
            'recall_strategy': self.recall_strategy
            # 其他字段...
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
        
        # 创建设置对象，但不调用__post_init__中的验证
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
        
        # 更新图像处理配置
        if 'image_processing' in config_dict:
            image_config = config_dict['image_processing']
            for key, value in image_config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        # 更新预设问题配置
        if 'preset_questions' in config_dict:
            preset_config = config_dict['preset_questions']
            for key, value in preset_config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        # 更新召回策略配置
        if 'recall_strategy' in config_dict:
            settings.recall_strategy = config_dict['recall_strategy']
        
        # 重新标准化路径（确保从配置文件加载的路径也转换为绝对路径）
        settings._normalize_paths()
        
        # 手动验证配置（在加载完成后）
        settings._validate_settings()
        
        return settings 