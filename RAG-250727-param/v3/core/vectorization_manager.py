"""
向量化管理器

统一管理所有内容的向量化，支持双重embedding策略。
完全符合设计文档规范，位于core模块下。
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# 导入向量化器
from vectorization.text_vectorizer import TextVectorizer
from vectorization.image_vectorizer import ImageVectorizer
from vectorization.table_vectorizer import TableVectorizer

class VectorizationManager:
    """
    向量化管理器
    
    统一管理所有内容的向量化，支持双重embedding策略
    完全符合设计文档规范，位于core模块下
    """
    
    def __init__(self, config_manager):
        """
        初始化向量化管理器
        
        :param config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        
        # 获取失败处理器
        self.failure_handler = self.config_manager.get_failure_handler()
        
        # 初始化各个向量化器（符合设计文档规范）
        self.text_vectorizer = TextVectorizer(config_manager)
        self.image_vectorizer = ImageVectorizer(config_manager)
        self.table_vectorizer = TableVectorizer(config_manager)
        
        self._load_configuration()
        
        logging.info("向量化管理器初始化完成")
    
    def vectorize_content(self, content_items: List[Dict], content_type: str) -> List[Dict]:
        """
        统一向量化接口
        
        :param content_items: 内容项列表
        :param content_type: 内容类型（text/image/table）
        :return: 向量化后的内容项列表
        """
        try:
            if not content_items:
                logging.warning(f"向量化内容为空: {content_type}")
                return []
            
            logging.info(f"开始向量化 {content_type} 内容: {len(content_items)} 项")
            
            if content_type == 'text':
                return self.text_vectorizer.vectorize_batch(content_items)
            elif content_type == 'image':
                return self.image_vectorizer.vectorize_images_batch(content_items)
            elif content_type == 'table':
                return self.table_vectorizer.vectorize_batch(content_items)
            else:
                raise ValueError(f"不支持的内容类型: {content_type}")
                
        except Exception as e:
            error_msg = f"向量化 {content_type} 内容失败: {str(e)}"
            logging.error(error_msg)
            self.failure_handler.record_failure(content_items, f'{content_type}_vectorization', str(e))
            raise RuntimeError(error_msg)
    
    def vectorize_all_content(self, metadata_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        向量化所有内容
        
        :param metadata_results: 元数据结果
        :return: 向量化后的元数据结果
        """
        try:
            logging.info("开始向量化所有内容...")
            
            # 向量化文本
            if metadata_results.get('text_chunks'):
                text_count = len(metadata_results['text_chunks'])
                logging.info(f"向量化文本块: {text_count} 个")
                metadata_results['text_chunks'] = self.text_vectorizer.vectorize_batch(
                    metadata_results['text_chunks']
                )
                logging.info(f"文本向量化完成: {text_count} 个")
            
            # 向量化表格
            if metadata_results.get('tables'):
                table_count = len(metadata_results['tables'])
                logging.info(f"向量化表格: {table_count} 个")
                metadata_results['tables'] = self.table_vectorizer.vectorize_batch(
                    metadata_results['tables']
                )
                logging.info(f"表格向量化完成: {table_count} 个")
            
            # 图片向量化在ImageProcessor中已完成
            if metadata_results.get('images'):
                image_count = len(metadata_results['images'])
                logging.info(f"图片向量化状态检查: {image_count} 个")
                # 检查哪些图片需要向量化
                images_to_vectorize = []
                for image in metadata_results['images']:
                    if not image.get('image_embedding') or not image.get('description_embedding'):
                        images_to_vectorize.append(image)
                
                if images_to_vectorize:
                    logging.info(f"需要向量化的图片: {len(images_to_vectorize)} 个")
                    vectorized_images = self.image_vectorizer.vectorize_images_batch(images_to_vectorize)
                    # 更新原始图片列表
                    for i, image in enumerate(metadata_results['images']):
                        for vectorized_image in vectorized_images:
                            if vectorized_image.get('image_id') == image.get('image_id'):
                                image.update(vectorized_image)
                                break
            
            logging.info("✅ 所有内容向量化完成")
            return metadata_results
            
        except Exception as e:
            error_msg = f"内容向量化失败: {e}"
            logging.error(error_msg)
            self.failure_handler.record_failure('vectorization', 'content_vectorization', str(e))
            raise RuntimeError(error_msg)
    
    def get_vectorization_status(self) -> Dict[str, Any]:
        """
        获取向量化状态信息
        
        :return: 向量化状态信息
        """
        try:
            return {
                'text_vectorizer': self.text_vectorizer.get_vectorization_status(),
                'image_vectorizer': self.image_vectorizer.get_vectorization_status(),
                'table_vectorizer': self.table_vectorizer.get_vectorization_status(),
                'overall_status': 'ready',
                'vectorization_manager_version': '3.0.0',
                'capabilities': [
                    'unified_vectorization',
                    'dual_embedding_strategy',
                    'batch_processing',
                    'api_rate_limiting',
                    'quality_assessment',
                    'error_handling'
                ]
            }
        except Exception as e:
            logging.error(f"获取向量化状态失败: {e}")
            return {
                'overall_status': 'error',
                'error_message': str(e)
            }
    
    def validate_vectorization_results(self, results: List[Dict], content_type: str) -> Dict[str, Any]:
        """
        验证向量化结果
        
        :param results: 向量化结果列表
        :param content_type: 内容类型
        :return: 验证结果
        """
        try:
            if content_type == 'text':
                return self.text_vectorizer.validate_vectorization_result(results[0]) if results else {}
            elif content_type == 'image':
                return self.image_vectorizer.validate_vectorization_result(results[0]) if results else {}
            elif content_type == 'table':
                return self.table_vectorizer.validate_vectorization_result(results[0]) if results else {}
            else:
                return {'is_valid': False, 'issues': [f'不支持的内容类型: {content_type}']}
                
        except Exception as e:
            logging.error(f"验证向量化结果失败: {e}")
            return {'is_valid': False, 'issues': [f'验证失败: {str(e)}']}
    
    def get_vectorization_statistics(self, results: List[Dict], content_type: str) -> Dict[str, Any]:
        """
        获取向量化统计信息
        
        :param results: 向量化结果列表
        :param content_type: 内容类型
        :return: 统计信息
        """
        try:
            if content_type == 'text':
                return self.text_vectorizer.get_vectorization_statistics(results)
            elif content_type == 'image':
                return self.image_vectorizer.get_vectorization_statistics(results)
            elif content_type == 'table':
                return self.table_vectorizer.get_vectorization_statistics(results)
            else:
                return {'error': f'不支持的内容类型: {content_type}'}
                
        except Exception as e:
            logging.error(f"获取向量化统计信息失败: {e}")
            return {'error': f'获取统计信息失败: {str(e)}'}
    
    def _load_configuration(self):
        """加载配置"""
        try:
            # 验证必需的配置
            required_configs = [
                'vectorization.text_embedding_model',
                'vectorization.image_embedding_model',
                'document_processing.chunk_size',
                'document_processing.chunk_overlap'
            ]
            
            for config_path in required_configs:
                value = self.config
                for key in config_path.split('.'):
                    value = value.get(key, {})
                if not value:
                    logging.warning(f"配置中缺少参数: {config_path}")
            
            # 验证向量化器
            if not all([self.text_vectorizer, self.image_vectorizer, self.table_vectorizer]):
                logging.warning("部分向量化器初始化失败")
            
            logging.info("向量化管理器配置加载完成")
            
        except Exception as e:
            logging.error(f"加载配置失败: {e}")
            raise
