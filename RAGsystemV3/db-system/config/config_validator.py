"""
配置验证器

负责验证配置文件的完整性和正确性，支持JSON Schema验证和自定义验证规则。
"""

import json
import logging
from typing import Dict, List, Any, Tuple
import os

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema未安装，将使用基础验证模式")

class ConfigValidator:
    """
    配置验证器

    功能：
    - 验证配置的完整性和正确性
    - 提供详细的验证错误信息
    - 支持自定义验证规则
    """

    def __init__(self):
        """
        初始化配置验证器
        """
        self.validation_errors = []
        self.validation_warnings = []

    def validate(self, config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        验证配置

        :param config: 配置数据
        :param schema: 配置模式
        :return: 是否验证通过
        """
        self.validation_errors = []
        self.validation_warnings = []

        try:
            # 使用JSON Schema验证（如果可用）
            if HAS_JSONSCHEMA:
                self._validate_with_jsonschema(config, schema)
            else:
                self._validate_basic(config, schema)

            # 自定义验证规则
            self._validate_custom_rules(config)

            # 生成验证报告
            self._generate_validation_report()

            return len(self.validation_errors) == 0

        except Exception as e:
            self.validation_errors.append(f"验证过程出错: {str(e)}")
            return False

    def _validate_with_jsonschema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """
        使用JSON Schema进行验证

        :param config: 配置数据
        :param schema: 配置模式
        """
        try:
            jsonschema.validate(config, schema)
            logging.info("JSON Schema验证通过")
        except jsonschema.ValidationError as e:
            self.validation_errors.append(f"JSON Schema验证失败: {e}")
        except jsonschema.SchemaError as e:
            self.validation_errors.append(f"配置模式错误: {e}")

    def _validate_basic(self, config: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """
        基础验证模式（当jsonschema不可用时）

        :param config: 配置数据
        :param schema: 配置模式
        """
        required_fields = schema.get('required', [])
        properties = schema.get('properties', {})

        # 验证必需字段
        for field in required_fields:
            if field not in config:
                self.validation_errors.append(f"缺少必需字段: {field}")

        # 验证字段类型
        for field, field_schema in properties.items():
            if field in config:
                field_type = field_schema.get('type')
                field_value = config[field]
                if not self._validate_field_type(field_value, field_type):
                    self.validation_errors.append(f"字段类型不匹配: {field} 期望 {field_type}")

    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """
        验证字段类型

        :param value: 字段值
        :param expected_type: 期望类型
        :return: 是否类型匹配
        """
        type_mapping = {
            'string': str,
            'integer': int,
            'boolean': bool,
            'object': dict,
            'array': list
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True  # 未知类型默认为通过

    def _validate_custom_rules(self, config: Dict[str, Any]) -> None:
        """
        自定义验证规则

        :param config: 配置数据
        """
        # 验证chunk_overlap不能大于chunk_size
        doc_processing = config.get('document_processing', {})
        chunk_size = doc_processing.get('chunk_size', 0)
        chunk_overlap = doc_processing.get('chunk_overlap', 0)

        if chunk_overlap >= chunk_size:
            self.validation_errors.append(
                f"chunk_overlap ({chunk_overlap}) 不能大于或等于 chunk_size ({chunk_size})"
            )

        # 验证路径配置
        paths = config.get('paths', {})
        if paths:
            for key, path in paths.items():
                if path and ('<' in str(path) or '>' in str(path) or '|' in str(path)):
                    self.validation_errors.append(
                        f"路径配置包含非法字符: {key} = {path}"
                    )

        # 验证API限流配置
        api_config = config.get('api_rate_limiting', {})
        if api_config:
            enhancement_batch = api_config.get('enhancement_batch_size', 0)
            vectorization_batch = api_config.get('vectorization_batch_size', 0)

            if enhancement_batch <= 0 or vectorization_batch <= 0:
                self.validation_errors.append(
                    "API批量大小必须大于0"
                )

        # 验证版本号格式
        version = config.get('version', '')
        if version and not self._is_valid_version(version):
            self.validation_warnings.append(f"版本号格式不标准: {version}")

        # 验证系统模式
        system_config = config.get('system', {})
        mode = system_config.get('mode', '')
        if mode not in ['auto', 'new', 'incremental']:
            self.validation_errors.append(f"无效的系统模式: {mode}")

    def _is_valid_version(self, version: str) -> bool:
        """
        验证版本号格式

        :param version: 版本号
        :return: 是否为有效版本号
        """
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return re.match(pattern, version) is not None

    def _generate_validation_report(self) -> None:
        """
        生成验证报告
        """
        if self.validation_errors:
            logging.error(f"配置验证失败，发现 {len(self.validation_errors)} 个错误:")
            for error in self.validation_errors:
                logging.error(f"  - {error}")

        if self.validation_warnings:
            logging.warning(f"配置验证警告，发现 {len(self.validation_warnings)} 个警告:")
            for warning in self.validation_warnings:
                logging.warning(f"  - {warning}")

        if not self.validation_errors and not self.validation_warnings:
            logging.info("配置验证通过")

    def get_validation_errors(self) -> List[str]:
        """
        获取验证错误信息

        :return: 验证错误列表
        """
        return self.validation_errors.copy()

    def get_validation_warnings(self) -> List[str]:
        """
        获取验证警告信息

        :return: 验证警告列表
        """
        return self.validation_warnings.copy()

    def get_validation_report(self) -> Dict[str, Any]:
        """
        获取完整的验证报告

        :return: 验证报告字典
        """
        return {
            'errors': self.validation_errors,
            'warnings': self.validation_warnings,
            'is_valid': len(self.validation_errors) == 0,
            'error_count': len(self.validation_errors),
            'warning_count': len(self.validation_warnings)
        }

    def validate_config_file(self, config_path: str, schema_path: str) -> Tuple[bool, Dict[str, Any]]:
        """
        验证配置文件

        :param config_path: 配置文件路径
        :param schema_path: 模式文件路径
        :return: (是否有效, 验证报告)
        """
        try:
            # 加载配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 加载模式文件
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)

            # 验证配置
            is_valid = self.validate(config, schema)
            report = self.get_validation_report()

            return is_valid, report

        except FileNotFoundError as e:
            error_msg = f"配置文件不存在: {e}"
            self.validation_errors = [error_msg]
            return False, {'errors': [error_msg], 'warnings': [], 'is_valid': False}

        except json.JSONDecodeError as e:
            error_msg = f"JSON格式错误: {e}"
            self.validation_errors = [error_msg]
            return False, {'errors': [error_msg], 'warnings': [], 'is_valid': False}

        except Exception as e:
            error_msg = f"验证过程出错: {str(e)}"
            self.validation_errors = [error_msg]
            return False, {'errors': [error_msg], 'warnings': [], 'is_valid': False}


if __name__ == "__main__":
    # 测试配置验证器
    validator = ConfigValidator()

    # 示例配置
    test_config = {
        "version": "3.0.0",
        "system": {
            "mode": "auto",
            "log_level": "INFO"
        },
        "document_processing": {
            "chunk_size": 1000,
            "chunk_overlap": 200
        }
    }

    # 示例模式
    test_schema = {
        "type": "object",
        "required": ["version", "system"],
        "properties": {
            "version": {"type": "string"},
            "system": {"type": "object"}
        }
    }

    is_valid = validator.validate(test_config, test_schema)
    print(f"验证结果: {'通过' if is_valid else '失败'}")

    if not is_valid:
        print("错误信息:")
        for error in validator.get_validation_errors():
            print(f"  - {error}")
