"""
RAG系统配置集成管理器

严格按照36.RAG系统配置管理详细设计文档实现
负责RAG系统与V3配置管理系统的集成
"""

import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

# 导入V3配置管理器 - 使用完整包路径
try:
    from db_system.config.config_manager import ConfigManager
    from db_system.config.environment_manager import EnvironmentManager
    logger = logging.getLogger(__name__)
except ImportError as e:
    logging.error(f"无法导入V3配置管理器: {e}")
    raise

logger = logging.getLogger(__name__)


class ConfigIntegration:
    """配置集成管理器 - 严格按照设计文档实现"""
    
    def __init__(self):
        """初始化配置集成管理器"""
        try:
            # 初始化配置管理器
            self.config_manager = ConfigManager()
            self.env_manager = EnvironmentManager()
            
            # 加载配置
            if not self.config_manager.load_config():
                logger.warning("配置加载失败，将使用默认配置")
            
            # 扩展配置，添加RAG节点
            self._extend_config()
            
            # 验证RAG配置完整性
            self._validate_rag_config()
            
            logger.info("配置集成管理器初始化完成")
            
        except Exception as e:
            logger.error(f"RAG配置集成管理器初始化失败: {e}")
            raise
    
    def _extend_config(self) -> bool:
        """扩展配置，添加RAG系统配置节点"""
        try:
            # 检查是否已有RAG配置
            if self.config_manager.get('rag_system.enabled', False):
                logger.info("RAG配置已存在，跳过扩展")
                return True
            
            # 添加默认RAG配置
            default_rag_config = self._get_default_rag_config()
            self.config_manager.config_data['rag_system'] = default_rag_config
            
            # 保存扩展后的配置
            if self.config_manager.save_config():
                logger.info("配置扩展成功，已添加RAG系统配置节点")
                return True
            else:
                logger.error("配置保存失败")
                return False
                
        except Exception as e:
            logger.error(f"配置扩展失败: {e}")
            return False
    
    def _get_default_rag_config(self) -> Dict[str, Any]:
        """获取默认RAG配置 - 严格按照设计文档"""
        return {
            "enabled": True,
            "version": "3.0.0",
            "models": {
                "llm": {
                    "model_name": "qwen-turbo",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "system_prompt": "你是一个专业的AI助手，能够基于提供的上下文信息生成准确、相关、完整的答案。"
                },
                "reranking": {
                    "model_name": "gte-rerank-v2",
                    "batch_size": 32,
                    "similarity_threshold": 0.7
                }
            },
            "query_processing": {
                "max_context_length": 4000,
                "max_results": 10,
                "relevance_threshold": 0.5,
                "cache_enabled": True,
                "cache_ttl": 3600
            },
            "engines": {
                "text_engine": {"enabled": True, "max_results": 10, "similarity_threshold": 0.7},
                "image_engine": {"enabled": True, "max_results": 20, "similarity_threshold": 0.3},
                "table_engine": {"enabled": True, "max_results": 15, "similarity_threshold": 0.65},
                "hybrid_engine": {"enabled": True, "max_results": 25, "weights": {"image": 0.3, "text": 0.4, "table": 0.3}}
            },
            "performance": {
                "max_concurrent_queries": 10,
                "query_timeout": 60,
                "enable_monitoring": True
            },
            "prompt_templates": {
                "general_qa": "基于以下上下文信息回答问题：\n\n上下文：{context}\n\n问题：{question}",
                "table_qa": "基于以下表格信息回答问题：\n\n表格内容：{context}\n\n问题：{question}",
                "image_qa": "基于以下图像信息回答问题：\n\n图像描述：{context}\n\n问题：{question}"
            }
        }
    
    def get_rag_config(self, key: str, default=None):
        """获取RAG配置值"""
        try:
            rag_config = self.config_manager.get(f'rag_system.{key}', default)
            if rag_config is None:
                return default
            return rag_config
            
        except Exception as e:
            logger.error(f"获取RAG配置失败: {e}")
            return default
    
    def get_rag_engine_config(self, engine_name: str) -> Dict[str, Any]:
        """获取特定RAG引擎配置"""
        engines_config = self.get_rag_config('engines', {})
        return engines_config.get(engine_name, {})
    
    def get_rag_model_config(self, model_type: str) -> Dict[str, Any]:
        """获取模型配置"""
        models_config = self.get_rag_config('models', {})
        return models_config.get(model_type, {})
    
    def validate_rag_config(self) -> Dict[str, Any]:
        """验证RAG配置完整性"""
        try:
            rag_config = self.config_manager.get('rag_system', {})
            if not rag_config:
                return {
                    'valid': False,
                    'errors': ['RAG配置节点不存在'],
                    'warnings': [],
                    'missing_fields': [],
                    'invalid_values': [],
                    'validation_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
            
            errors = []
            warnings = []
            missing_fields = []
            invalid_values = []
            
            # 验证必需字段
            required_fields = ['models', 'query_processing', 'engines']
            for field in required_fields:
                if field not in rag_config:
                    missing_fields.append(field)
                    errors.append(f"缺少必需字段: {field}")
            
            # 验证模型配置
            if 'models' in rag_config:
                models = rag_config['models']
                if 'llm' not in models:
                    missing_fields.append('models.llm')
                    warnings.append("缺少LLM模型配置，将使用默认配置")
                
                if 'reranking' not in models:
                    missing_fields.append('models.reranking')
                    warnings.append("缺少重排序模型配置，将使用默认配置")
            
            # 验证引擎配置
            if 'engines' in rag_config:
                engines = rag_config['engines']
                required_engines = ['text_engine', 'image_engine', 'table_engine', 'hybrid_engine']
                for engine in required_engines:
                    if engine not in engines:
                        missing_fields.append(f'engines.{engine}')
                        warnings.append(f"缺少{engine}配置，将使用默认配置")
            
            # 验证配置值
            if 'query_processing' in rag_config:
                qp = rag_config['query_processing']
                if 'max_context_length' in qp and qp['max_context_length'] <= 0:
                    invalid_values.append('query_processing.max_context_length')
                    errors.append("max_context_length必须大于0")
                
                if 'max_results' in qp and qp['max_results'] <= 0:
                    invalid_values.append('query_processing.max_results')
                    errors.append("max_results必须大于0")
            
            valid = len(errors) == 0
            
            return {
                'valid': valid,
                'errors': errors,
                'warnings': warnings,
                'missing_fields': missing_fields,
                'invalid_values': invalid_values,
                'validation_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"RAG配置验证失败: {e}")
            return {
                'valid': False,
                'errors': [f"配置验证异常: {str(e)}"],
                'warnings': [],
                'missing_fields': [],
                'invalid_values': [],
                'validation_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _validate_rag_config(self):
        """内部验证RAG配置 - 初始化时调用"""
        validation_result = self.validate_rag_config()
        if not validation_result['valid']:
            logger.warning(f"RAG配置验证失败: {validation_result['errors']}")
            logger.warning("将使用默认RAG配置继续运行")
        else:
            logger.info("RAG配置验证通过")
    
    def reload_rag_config(self) -> bool:
        """重新加载RAG配置"""
        try:
            # 重新加载配置文件
            if not self.config_manager.load_config():
                return False
            
            # 验证RAG配置
            validation_result = self.validate_rag_config()
            if not validation_result['valid']:
                logger.error(f"RAG配置验证失败: {validation_result['errors']}")
                return False
            
            logger.info("RAG配置重载成功")
            return True
            
        except Exception as e:
            logger.error(f"RAG配置重载失败: {e}")
            return False
    
    def get_env_var(self, key: str, default=None):
        """获取环境变量值 - 复用V3环境变量管理"""
        try:
            return self.env_manager.get_required_var(key) or default
        except Exception as e:
            logger.error(f"获取环境变量失败: {e}")
            return default
    
    def validate_rag_environment(self) -> Dict[str, Any]:
        """验证RAG系统运行环境"""
        try:
            # 复用V3的环境变量管理器
            env_status = self.env_manager.validate_required_vars()
            
            # RAG系统只需要验证DashScope API密钥
            dashscope_ready = env_status.get('DASHSCOPE_API_KEY', False)
            
            # 检查是否有缺失的环境变量
            missing_vars = []
            if not dashscope_ready:
                missing_vars.append('DASHSCOPE_API_KEY')
            
            rag_system_ready = dashscope_ready
            
            return {
                'DASHSCOPE_API_KEY': dashscope_ready,
                'MINERU_API_KEY': env_status.get('MINERU_API_KEY', False),
                'rag_system_ready': rag_system_ready,
                'missing_vars': missing_vars,
                'validation_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"RAG环境验证失败: {e}")
            return {
                'DASHSCOPE_API_KEY': False,
                'MINERU_API_KEY': False,
                'rag_system_ready': False,
                'missing_vars': ['环境验证异常'],
                'validation_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
