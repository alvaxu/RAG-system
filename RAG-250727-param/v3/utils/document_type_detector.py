"""
文档类型检测器

负责验证用户指定的输入源类型，并与配置管理系统集成，提供默认路径支持。
"""

import os
import logging
from typing import Dict, Optional, List
from pathlib import Path

class DocumentTypeDetector:
    """
    简化的文档类型检测器

    功能：
    - 验证用户指定的输入类型是否正确
    - 使用配置管理系统的默认路径
    - 基本的文件类型验证
    - 与V3MainProcessor集成
    """

    def __init__(self, config_manager):
        """
        初始化文档类型检测器

        :param config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self._load_configuration()

    def _load_configuration(self):
        """加载配置"""
        try:
            # 默认输入类型
            self.default_input_type = 'pdf'

            # 默认路径配置
            paths_config = self.config_manager.get('paths', {})
            self.default_input_pdf_dir = paths_config.get('input_pdf_dir', './document/orig_pdf')
            self.default_mineru_output_dir = paths_config.get('mineru_output_dir', './document/md')
            self.default_vector_db_dir = paths_config.get('vector_db_dir', './central/vector_db')

            logging.info("DocumentTypeDetector配置加载完成")
        except Exception as e:
            logging.error(f"DocumentTypeDetector配置加载失败: {e}")
            raise

    def validate_input_type(self, input_type: str = None, input_path: str = None,
                           output_path: str = None) -> Dict:
        """
        验证输入类型和路径

        :param input_type: 用户指定的输入类型，如果为None则使用默认值
        :param input_path: 用户指定的输入路径，如果为None则使用配置默认值
        :param output_path: 用户指定的输出路径，如果为None则使用配置默认值
        :return: 验证结果
        """
        try:
            # 1. 确定输入类型（使用默认值或用户指定）
            final_input_type = input_type or self.default_input_type

            # 验证输入类型
            if final_input_type not in ['pdf', 'mineru_output']:
                return {
                    'valid': False,
                    'error': 'invalid_input_type',
                    'message': f'不支持的输入类型: {final_input_type}，支持的类型: pdf, mineru_output'
                }

            # 2. 确定输入路径（使用配置默认值或用户指定）
            final_input_path = input_path or self._get_default_input_path(final_input_type)

            # 3. 确定输出路径（使用配置默认值或用户指定）
            final_output_path = output_path or self.default_vector_db_dir

            # 4. 验证输入类型和路径
            validation_result = self._validate_paths(final_input_type, final_input_path, final_output_path)

            # 5. 构建最终结果
            result = {
                'valid': validation_result['valid'],
                'input_type': final_input_type,
                'input_path': final_input_path,
                'output_path': final_output_path,
                'needs_mineru': final_input_type == 'pdf',
                'description': self._get_description(final_input_type, final_input_path),
                'file_count': validation_result.get('file_count', 0),
                'file_size': validation_result.get('file_size', 0)
            }

            if not validation_result['valid']:
                result['error'] = validation_result['error']
                result['message'] = validation_result['message']

            return result

        except Exception as e:
            logging.error(f"输入类型验证失败: {e}")
            return {
                'valid': False,
                'error': 'validation_error',
                'message': f'验证过程出错: {str(e)}'
            }

    def _get_default_input_path(self, input_type: str) -> str:
        """根据输入类型获取默认输入路径"""
        if input_type == 'pdf':
            return self.default_input_pdf_dir
        elif input_type == 'mineru_output':
            return self.default_mineru_output_dir
        else:
            return self.default_input_pdf_dir  # 默认使用PDF路径

    def _validate_paths(self, input_type: str, input_path: str, output_path: str) -> Dict:
        """验证输入和输出路径"""
        try:
            # 1. 验证输入路径
            input_validation = self._validate_input_path(input_path, input_type)
            if not input_validation['valid']:
                return input_validation

            # 2. 验证输出路径
            output_validation = self._validate_output_path(output_path)
            if not output_validation['valid']:
                return output_validation

            # 3. 合并验证结果
            return {
                'valid': True,
                'input_path': input_path,
                'output_path': output_path,
                'file_count': input_validation.get('file_count', 0),
                'file_size': input_validation.get('file_size', 0)
            }

        except Exception as e:
            return {
                'valid': False,
                'error': 'path_validation_error',
                'message': f'路径验证失败: {str(e)}'
            }

    def _validate_input_path(self, input_path: str, input_type: str) -> Dict:
        """验证输入路径"""
        try:
            # 如果路径是相对路径，先转换为绝对路径
            if not os.path.isabs(input_path):
                # 获取当前工作目录（v3目录）
                current_dir = os.getcwd()
                # 解析相对路径
                resolved_path = os.path.abspath(os.path.join(current_dir, input_path))
                logging.info(f"相对路径解析: {input_path} -> {resolved_path}")
                input_path = resolved_path
            
            if not os.path.exists(input_path):
                return {
                    'valid': False,
                    'error': 'path_not_found',
                    'message': f'输入路径不存在: {input_path}'
                }

            if input_type == 'pdf':
                return self._validate_pdf_input(input_path)
            elif input_type == 'mineru_output':
                return self._validate_mineru_input(input_path)
            else:
                return {
                    'valid': False,
                    'error': 'unsupported_input_type',
                    'message': f'不支持的输入类型: {input_type}'
                }

        except Exception as e:
            return {
                'valid': False,
                'error': 'input_validation_error',
                'message': f'输入路径验证失败: {str(e)}'
            }

    def _validate_pdf_input(self, input_path: str) -> Dict:
        """验证PDF输入路径"""
        try:
            if not os.path.isdir(input_path):
                return {
                    'valid': False,
                    'error': 'not_directory',
                    'message': f'PDF输入路径必须是目录: {input_path}'
                }

            # 查找PDF文件（只搜索直接子目录，避免递归搜索系统目录）
            pdf_files = []
            total_size = 0

            for item in Path(input_path).iterdir():
                if item.is_file() and item.suffix.lower() == '.pdf':
                    pdf_files.append(str(item))
                    try:
                        total_size += item.stat().st_size
                    except OSError:
                        pass  # 忽略无法获取大小的文件

            if len(pdf_files) == 0:
                return {
                    'valid': False,
                    'error': 'no_pdf_files',
                    'message': f'输入目录中未找到PDF文件: {input_path}'
                }

            return {
                'valid': True,
                'file_count': len(pdf_files),
                'file_size': total_size,
                'file_list': pdf_files[:10]  # 只返回前10个文件
            }

        except Exception as e:
            return {
                'valid': False,
                'error': 'pdf_validation_error',
                'message': f'PDF输入验证失败: {str(e)}'
            }

    def _validate_mineru_input(self, input_path: str) -> Dict:
        """验证minerU输出输入路径"""
        try:
            if not os.path.isdir(input_path):
                return {
                    'valid': False,
                    'error': 'not_directory',
                    'message': f'minerU输出路径必须是目录: {input_path}'
                }

            # 查找minerU输出文件（只搜索直接子目录，避免递归搜索系统目录）
            json_files = []
            md_files = []
            image_files = []
            total_size = 0

            # 只搜索直接子目录，避免递归搜索系统目录
            for item in Path(input_path).iterdir():
                if item.is_file():
                    # 只处理根目录下的文件
                    try:
                        total_size += item.stat().st_size
                    except OSError:
                        pass

                    if item.suffix.lower() == '.json':
                        json_files.append(str(item))
                    elif item.suffix.lower() == '.md':
                        md_files.append(str(item))
                    elif item.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        image_files.append(str(item))
                elif item.is_dir() and item.name not in ['__pycache__', '.git', '.vscode', 'logs', 'temp']:
                    # 搜索特定子目录（images目录）
                    if item.name == 'images':
                        for image_file in item.iterdir():
                            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                                try:
                                    total_size += image_file.stat().st_size
                                except OSError:
                                    pass
                                image_files.append(str(image_file))

            # 检查是否至少有JSON或MD文件
            if len(json_files) == 0 and len(md_files) == 0:
                return {
                    'valid': False,
                    'error': 'no_content_files',
                    'message': f'minerU输出目录中未找到内容文件（JSON或MD）: {input_path}'
                }

            return {
                'valid': True,
                'file_count': len(json_files) + len(md_files) + len(image_files),
                'file_size': total_size,
                'json_count': len(json_files),
                'md_count': len(md_files),
                'image_count': len(image_files)
            }

        except Exception as e:
            return {
                'valid': False,
                'error': 'mineru_validation_error',
                'message': f'minerU输出验证失败: {str(e)}'
            }

    def _validate_output_path(self, output_path: str) -> Dict:
        """验证输出路径"""
        try:
            # 检查输出路径是否可以创建
            output_dir = Path(output_path).parent
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return {
                        'valid': False,
                        'error': 'cannot_create_output_dir',
                        'message': f'无法创建输出目录: {output_dir}, 错误: {str(e)}'
                    }

            # 检查输出路径是否可以写入
            test_file = Path(output_path) / '.test_write'
            try:
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                return {
                    'valid': False,
                    'error': 'output_path_not_writable',
                    'message': f'输出路径不可写: {output_path}, 错误: {str(e)}'
                }

            return {
                'valid': True,
                'output_path': output_path
            }

        except Exception as e:
            return {
                'valid': False,
                'error': 'output_validation_error',
                'message': f'输出路径验证失败: {str(e)}'
            }

    def _get_description(self, input_type: str, input_path: str) -> str:
        """获取处理描述"""
        if input_type == 'pdf':
            return f"从PDF文档开始处理，输入路径: {input_path}（包含minerU解析步骤）"
        elif input_type == 'mineru_output':
            return f"从minerU输出开始处理，输入路径: {input_path}（跳过解析步骤）"
        else:
            return f"未知输入类型: {input_type}"

    def get_supported_input_types(self) -> List[str]:
        """获取支持的输入类型"""
        return ['pdf', 'mineru_output']

    def get_default_paths(self) -> Dict[str, str]:
        """获取默认路径配置"""
        return {
            'input_pdf_dir': self.default_input_pdf_dir,
            'mineru_output_dir': self.default_mineru_output_dir,
            'vector_db_dir': self.default_vector_db_dir
        }


if __name__ == "__main__":
    # 测试DocumentTypeDetector
    from v3.config.config_manager import ConfigManager

    config_manager = ConfigManager()
    if config_manager.load_config():
        detector = DocumentTypeDetector(config_manager)

        # 测试默认输入
        result = detector.validate_input_type()
        print(f"默认输入验证: {'通过' if result['valid'] else '失败'}")
        if not result['valid']:
            print(f"错误: {result.get('message', '未知错误')}")

        # 测试PDF输入
        result = detector.validate_input_type('pdf')
        print(f"PDF输入验证: {'通过' if result['valid'] else '失败'}")

        # 测试minerU输出输入
        result = detector.validate_input_type('mineru_output')
        print(f"minerU输出验证: {'通过' if result['valid'] else '失败'}")

    else:
        print("配置加载失败，无法测试DocumentTypeDetector")
