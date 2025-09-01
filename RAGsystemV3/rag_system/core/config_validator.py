"""
配置验证模块

RAG系统的配置验证模块，符合技术规范要求
提供配置完整性验证、配置值有效性验证等功能
"""

import logging
from typing import Dict, Any, Optional, List
from .exceptions import ConfigurationError, ValidationError

logger = logging.getLogger(__name__)


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        """初始化配置验证器"""
        self.required_fields = {
            'enabled': bool,
            'version': str,
            'models': dict,
            'query_processing': dict,
            'engines': dict,
            'performance': dict
        }
        
        self.value_ranges = {
            'query_processing.max_context_length': (1000, 8000),
            'query_processing.max_results': (1, 100),
            'query_processing.relevance_threshold': (0.0, 1.0),
            'engines.text_engine.similarity_threshold': (0.0, 1.0),
            'engines.image_engine.similarity_threshold': (0.0, 1.0),
            'engines.table_engine.similarity_threshold': (0.0, 1.0)
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置完整性
        
        :param config: 配置字典
        :return: 验证是否通过
        :raises: ConfigurationError 配置错误
        """
        try:
            logger.info("开始验证配置完整性")
            
            # 验证必需字段
            self._validate_required_fields(config)
            
            # 验证字段类型
            self._validate_field_types(config)
            
            # 验证值范围
            self._validate_value_ranges(config)
            
            # 验证配置逻辑
            self._validate_config_logic(config)
            
            logger.info("配置验证通过")
            return True
            
        except (ConfigurationError, ValidationError) as e:
            logger.error(f"配置验证失败: {e}")
            raise
        except Exception as e:
            logger.error(f"配置验证失败（未知错误）: {e}")
            raise ConfigurationError(f"配置验证失败: {e}") from e
    
    def _validate_required_fields(self, config: Dict[str, Any], path: str = "") -> None:
        """
        验证必需字段是否存在
        
        :param config: 配置字典
        :param path: 当前路径
        :raises: ConfigurationError 缺少必需字段
        """
        for field, field_type in self.required_fields.items():
            if path:
                current_path = f"{path}.{field}"
            else:
                current_path = field
            
            if field not in config:
                raise ConfigurationError(f"缺少必需字段: {current_path}")
            
            if isinstance(field_type, dict):
                if not isinstance(config[field], dict):
                    raise ConfigurationError(f"字段 {current_path} 应该是字典类型")
                self._validate_required_fields(config[field], current_path)
    
    def _validate_field_types(self, config: Dict[str, Any], path: str = "") -> None:
        """
        验证字段类型是否正确
        
        :param config: 配置字典
        :param path: 当前路径
        :raises: ValidationError 字段类型错误
        """
        for field, expected_type in self.required_fields.items():
            if path:
                current_path = f"{path}.{field}"
            else:
                current_path = field
            
            if field in config:
                value = config[field]
                if isinstance(expected_type, dict):
                    if isinstance(value, dict):
                        self._validate_field_types(value, current_path)
                elif not isinstance(value, expected_type):
                    raise ValidationError(
                        f"字段 {current_path} 类型错误，期望 {expected_type.__name__}，实际 {type(value).__name__}"
                    )
    
    def _validate_value_ranges(self, config: Dict[str, Any]) -> None:
        """
        验证配置值是否在有效范围内
        
        :param config: 配置字典
        :raises: ValidationError 值超出范围
        """
        for field_path, (min_val, max_val) in self.value_ranges.items():
            value = self._get_nested_value(config, field_path)
            if value is not None:
                if not (min_val <= value <= max_val):
                    raise ValidationError(
                        f"字段 {field_path} 值 {value} 超出范围 [{min_val}, {max_val}]"
                    )
    
    def _validate_config_logic(self, config: Dict[str, Any]) -> None:
        """
        验证配置逻辑一致性
        
        :param config: 配置字典
        :raises: ValidationError 配置逻辑错误
        """
        # 验证引擎配置
        engines = config.get('engines', {})
        for engine_name, engine_config in engines.items():
            if not engine_config.get('enabled', True):
                continue
            
            # 验证相似度阈值
            threshold = engine_config.get('similarity_threshold')
            if threshold is not None and not (0.0 <= threshold <= 1.0):
                raise ValidationError(f"引擎 {engine_name} 相似度阈值超出范围 [0.0, 1.0]")
            
            # 验证最大结果数
            max_results = engine_config.get('max_results')
            if max_results is not None and not (1 <= max_results <= 100):
                raise ValidationError(f"引擎 {engine_name} 最大结果数超出范围 [1, 100]")
    
    def _get_nested_value(self, config: Dict[str, Any], field_path: str) -> Any:
        """
        获取嵌套配置值
        
        :param config: 配置字典
        :param field_path: 字段路径，如 'rag_system.query_processing.max_results'
        :return: 配置值
        """
        keys = field_path.split('.')
        value = config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None
    
    def validate_rag_config(self, config: Dict[str, Any]) -> bool:
        """
        验证RAG系统配置
        
        :param config: RAG系统配置
        :return: 验证是否通过
        """
        try:
            rag_config = config.get('rag_system', {})
            if not rag_config:
                raise ConfigurationError("缺少RAG系统配置节点")
            
            return self.validate_config(rag_config)
            
        except Exception as e:
            logger.error(f"RAG系统配置验证失败: {e}")
            raise
    
    def get_config_issues(self, config: Dict[str, Any]) -> List[str]:
        """
        获取配置问题列表
        
        :param config: 配置字典
        :return: 问题列表
        """
        issues = []
        
        try:
            self.validate_config(config)
        except (ConfigurationError, ValidationError) as e:
            issues.append(str(e))
        except Exception as e:
            issues.append(f"未知配置错误: {e}")
        
        return issues
    
    def suggest_config_fixes(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        建议配置修复方案
        
        :param config: 配置字典
        :return: 修复建议
        """
        suggestions = {}
        
        # 检查缺失字段
        for field_path, (min_val, max_val) in self.value_ranges.items():
            value = self._get_nested_value(config, field_path)
            if value is None:
                suggestions[field_path] = f"建议设置值在 [{min_val}, {max_val}] 范围内"
            elif not (min_val <= value <= max_val):
                suggestions[field_path] = f"当前值 {value} 超出范围，建议在 [{min_val}, {max_val}] 内"
        
        return suggestions
