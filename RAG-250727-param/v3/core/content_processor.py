"""
内容处理器

负责统一处理不同类型的内容（文本、图像、表格），协调各个专用处理器的工作。
完全符合设计文档规范，位于core模块下。
"""

import os
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

# 导入专用处理器
from processors.text_processor import TextProcessor
from processors.image_processor import ImageProcessor
from processors.table_processor import TableProcessor

# 导入元数据提取器
from utils.content_metadata_extractor import ContentMetadataExtractor

class ContentProcessor:
    """
    内容处理器主类

    功能：
    - 统一处理不同类型的内容
    - 协调各个专用处理器的工作
    - 管理内容处理流程
    - 完全符合设计文档规范
    """

    def __init__(self, config_manager):
        """
        初始化内容处理器

        :param config_manager: 配置管理器
        """
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        
        # 获取失败处理器
        self.failure_handler = config_manager.get_failure_handler()

        # 初始化专用处理器
        self._initialize_processors()
        
        # 初始化元数据提取器
        self.metadata_extractor = ContentMetadataExtractor(config_manager)
        
        # 处理统计信息
        self.processing_statistics = {
            'total_documents': 0,
            'total_text_chunks': 0,
            'total_images': 0,
            'total_tables': 0,
            'successful_processing': 0,
            'failed_processing': 0,
            'last_processing_time': None
        }

        logging.info("ContentProcessor初始化完成")

    def _initialize_processors(self):
        """初始化专用处理器"""
        try:
            # 初始化文本处理器
            self.text_processor = TextProcessor(self.config_manager)
            
            # 初始化图像处理器
            self.image_processor = ImageProcessor(self.config_manager)
            
            # 初始化表格处理器
            self.table_processor = TableProcessor(self.config_manager)
            
            logging.info("所有专用处理器初始化完成")
            
        except Exception as e:
            logging.error(f"专用处理器初始化失败: {e}")
            raise

    def process_content(self, content_type: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理内容

        :param content_type: 内容类型 (text, image, table)
        :param content_data: 内容数据
        :return: 处理结果
        """
        try:
            start_time = time.time()
            
            if content_type == 'text':
                result = self._process_text(content_data)
            elif content_type == 'image':
                result = self._process_image(content_data)
            elif content_type == 'table':
                result = self._process_table(content_data)
            else:
                raise ValueError(f"不支持的内容类型: {content_type}")

            # 更新统计信息
            processing_time = time.time() - start_time
            self._update_processing_statistics(content_type, 'success', processing_time)
            
            return result

        except Exception as e:
            error_msg = f"内容处理失败: {content_type}, 错误: {e}"
            logging.error(error_msg)
            
            # 记录失败
            self.failure_handler.record_failure(content_data, f'{content_type}_processing', str(e))
            
            # 更新统计信息
            self._update_processing_statistics(content_type, 'failed', 0)
            
            # 返回错误结果
            return {
                'content_type': content_type,
                'processed_content': {},
                'status': 'failed',
                'error': str(e),
                'processing_timestamp': int(time.time())
            }

    def process_document_content(self, json_path: str, doc_name: str) -> Dict[str, Any]:
        """
        处理文档内容，从JSON文件提取并处理所有内容类型
        
        :param json_path: JSON文件路径
        :param doc_name: 文档名称
        :return: 处理结果
        """
        try:
            start_time = time.time()
            logging.info(f"开始处理文档内容: {doc_name}")
            
            # 1. 提取元数据
            metadata_results = self.metadata_extractor.extract_metadata_from_json(json_path, doc_name)
            
            # 2. 处理文本内容
            if metadata_results.get('text_chunks'):
                text_count = len(metadata_results['text_chunks'])
                logging.info(f"处理文本块: {text_count} 个")
                metadata_results['text_chunks'] = self.text_processor.process_batch(
                    metadata_results['text_chunks']
                )
                self.processing_statistics['total_text_chunks'] += text_count
                logging.info(f"文本处理完成: {text_count} 个")
            
            # 3. 处理表格内容
            if metadata_results.get('tables'):
                table_count = len(metadata_results['tables'])
                logging.info(f"处理表格: {table_count} 个")
                metadata_results['tables'] = self.table_processor.process_batch(
                    metadata_results['tables']
                )
                self.processing_statistics['total_tables'] += table_count
                logging.info(f"表格处理完成: {table_count} 个")
            
            # 4. 处理图片内容（包括增强和向量化）
            if metadata_results.get('images'):
                image_count = len(metadata_results['images'])
                logging.info(f"处理图片: {image_count} 张")
                metadata_results['images'] = self.image_processor.process_images(
                    metadata_results['images']
                )
                self.processing_statistics['total_images'] += image_count
                logging.info(f"图片处理完成: {image_count} 张")
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self.processing_statistics['total_documents'] += 1
            self.processing_statistics['successful_processing'] += 1
            self.processing_statistics['last_processing_time'] = int(time.time())
            
            logging.info(f"✅ 文档内容处理完成: {doc_name}, 耗时: {processing_time:.2f}秒")
            return metadata_results
            
        except Exception as e:
            error_msg = f"文档内容处理失败: {doc_name}, 错误: {e}"
            logging.error(error_msg)
            
            # 记录失败
            self.failure_handler.record_failure(json_path, 'document_content_processing', str(e))
            
            # 更新统计信息
            self.processing_statistics['failed_processing'] += 1
            
            raise RuntimeError(error_msg)

    def _process_text(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理文本内容"""
        try:
            if not self.text_processor:
                raise RuntimeError("文本处理器未初始化")
            
            # 使用文本处理器处理
            result = self.text_processor.process_text(
                content_data.get('text_content', ''),
                content_data.get('source_type'),
                content_data
            )
            
            return {
                'content_type': 'text',
                'processed_content': result,
                'status': 'success',
                'processing_timestamp': int(time.time()),
                'processing_pipeline': 'Text_Processing_Pipeline',
                'optimization_features': [
                    'intelligent_chunking',
                    'semantic_analysis',
                    'complete_metadata'
                ]
            }
            
        except Exception as e:
            logging.error(f"文本处理失败: {e}")
            return {
                'content_type': 'text',
                'processed_content': [],
                'status': 'failed',
                'error': str(e),
                'processing_timestamp': int(time.time())
            }

    def _process_image(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理图像内容"""
        try:
            if not self.image_processor:
                raise RuntimeError("图像处理器未初始化")
            
            # 使用图像处理器处理
            result = self.image_processor.process_images([content_data])
            
            return {
                'content_type': 'image',
                'processed_content': result[0] if result else {},
                'status': 'success',
                'processing_timestamp': int(time.time()),
                'processing_pipeline': 'Image_Processing_Pipeline',
                'optimization_features': [
                    'one_time_enhancement',
                    'smart_deduplication',
                    'dual_vectorization'
                ]
            }
            
        except Exception as e:
            logging.error(f"图像处理失败: {e}")
            return {
                'content_type': 'image',
                'processed_content': {},
                'status': 'failed',
                'error': str(e),
                'processing_timestamp': int(time.time())
            }

    def _process_table(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理表格内容"""
        try:
            if not self.table_processor:
                raise RuntimeError("表格处理器未初始化")
            
            # 使用表格处理器处理
            result = self.table_processor.process_batch([content_data])
            
            return {
                'content_type': 'table',
                'processed_content': result[0] if result else {},
                'status': 'success',
                'processing_timestamp': int(time.time()),
                'processing_pipeline': 'Table_Processing_Pipeline',
                'optimization_features': [
                    'structure_analysis',
                    'content_extraction',
                    'format_generation'
                ]
            }
            
        except Exception as e:
            logging.error(f"表格处理失败: {e}")
            return {
                'content_type': 'table',
                'processed_content': {},
                'status': 'failed',
                'error': str(e),
                'processing_timestamp': int(time.time())
            }

    def _update_processing_statistics(self, content_type: str, status: str, processing_time: float):
        """
        更新处理统计信息
        
        :param content_type: 内容类型
        :param status: 处理状态
        :param processing_time: 处理时间
        """
        try:
            if status == 'success':
                self.processing_statistics['successful_processing'] += 1
            else:
                self.processing_statistics['failed_processing'] += 1
            
            self.processing_statistics['last_processing_time'] = int(time.time())
            
        except Exception as e:
            logging.error(f"更新处理统计信息失败: {e}")

    def get_processing_status(self) -> Dict[str, Any]:
        """
        获取处理状态信息
        
        :return: 处理状态信息
        """
        try:
            return {
                'content_processor_version': '3.0.0',
                'text_processor': self.text_processor.get_processing_status() if self.text_processor else 'not_initialized',
                'image_processor': self.image_processor.get_processing_status() if self.image_processor else 'not_initialized',
                'table_processor': self.table_processor.get_processing_status() if self.table_processor else 'not_initialized',
                'metadata_extractor': 'ready' if self.metadata_extractor else 'not_initialized',
                'overall_status': 'ready',
                'processing_statistics': self.processing_statistics,
                'capabilities': [
                    'unified_content_processing',
                    'batch_processing',
                    'error_handling',
                    'statistics_tracking',
                    'pipeline_management'
                ]
            }
        except Exception as e:
            logging.error(f"获取处理状态失败: {e}")
            return {
                'overall_status': 'error',
                'error_message': str(e)
            }

    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        :return: 统计信息字典
        """
        return {
            'content_processor_version': '3.0.0',
            'statistics': self.processing_statistics.copy(),
            'capabilities': [
                'document_processing',
                'content_type_processing',
                'batch_processing',
                'error_tracking',
                'performance_monitoring'
            ]
        }

    def reset_statistics(self) -> bool:
        """
        重置统计信息
        
        :return: 是否重置成功
        """
        try:
            self.processing_statistics = {
                'total_documents': 0,
                'total_text_chunks': 0,
                'total_images': 0,
                'total_tables': 0,
                'successful_processing': 0,
                'failed_processing': 0,
                'last_processing_time': None
            }
            
            logging.info("处理统计信息已重置")
            return True
            
        except Exception as e:
            logging.error(f"重置统计信息失败: {e}")
            return False

    def validate_processing_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证处理结果
        
        :param result: 处理结果
        :return: 验证结果
        """
        try:
            validation_result = {
                'is_valid': True,
                'issues': [],
                'warnings': [],
                'recommendations': []
            }
            
            # 检查基本字段
            if not result.get('content_type'):
                validation_result['is_valid'] = False
                validation_result['issues'].append("缺少content_type字段")
            
            if not result.get('status'):
                validation_result['is_valid'] = False
                validation_result['issues'].append("缺少status字段")
            
            # 检查处理状态
            if result.get('status') == 'failed':
                if not result.get('error'):
                    validation_result['warnings'].append("失败状态但缺少错误信息")
            
            # 检查处理内容
            if result.get('status') == 'success':
                if not result.get('processed_content'):
                    validation_result['warnings'].append("成功状态但缺少处理内容")
            
            # 生成建议
            if validation_result['warnings']:
                validation_result['recommendations'].append("完善处理结果信息")
            
            if not validation_result['is_valid']:
                validation_result['recommendations'].append("检查处理流程和错误处理")
            
            return validation_result
            
        except Exception as e:
            logging.error(f"验证处理结果失败: {e}")
            return {
                'is_valid': False,
                'issues': [f'验证失败: {str(e)}'],
                'warnings': [],
                'recommendations': ['检查验证流程']
            }
