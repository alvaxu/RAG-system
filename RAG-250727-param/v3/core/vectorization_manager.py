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
from vectorization.text_vectorizer import LangChainTextVectorizer as TextVectorizer
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
                # 提取文本内容和元数据
                texts = [item.get('content', '') for item in content_items]
                metadatas = [item.get('metadata', {}) for item in content_items]
                return self.text_vectorizer.vectorize_batch(texts, metadatas)
            elif content_type == 'image':
                # 图片向量化已在ImageProcessor中完成，这里只做状态检查
                logging.info("图片向量化已在ImageProcessor中完成，跳过重复处理")
                return content_items  # 直接返回，不做重复处理
            elif content_type == 'table':
                # 转换为表格向量化器期望的格式
                table_items = []
                for item in content_items:
                    table_item = {
                        'table_content': item.get('content', ''),
                        'metadata': item.get('metadata', {})
                    }
                    table_items.append(table_item)
                return self.table_vectorizer.vectorize_batch(table_items)
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
        :return: 向量化结果，符合设计文档规范
        """
        try:
            logging.info("开始向量化所有内容...")
            
            # 创建符合设计文档的vectorization_result结构
            vectorization_result = {
                'text_vectors': [],
                'image_vectors': [],
                'table_vectors': [],
                'vectorization_status': 'completed',
                'vectorization_timestamp': int(time.time())
            }
            
            # 向量化文本
            if metadata_results.get('text_chunks'):
                text_count = len(metadata_results['text_chunks'])
                logging.info(f"向量化文本块: {text_count} 个")
                # 提取文本内容和元数据（根据设计文档，文本内容字段是 'text'）
                text_items = metadata_results['text_chunks']
                texts = [item.get('text', '') for item in text_items]
                metadatas = [item for item in text_items]  # 直接传递整个item作为metadata
                text_vectors = self.text_vectorizer.vectorize_batch(texts, metadatas)
                vectorization_result['text_vectors'] = text_vectors
                logging.info(f"文本向量化完成: {text_count} 个")
            
            # 向量化表格
            if metadata_results.get('tables'):
                table_count = len(metadata_results['tables'])
                logging.info(f"向量化表格: {table_count} 个")
                # 转换为表格向量化器期望的格式（根据设计文档，表格内容字段是 'table_content'）
                table_items = metadata_results['tables']
                formatted_table_items = []
                for item in table_items:
                    table_item = {
                        'table_content': item.get('table_content', ''),  # 使用 'table_content' 字段
                        'metadata': item  # 直接传递整个item作为metadata
                    }
                    formatted_table_items.append(table_item)
                table_vectors = self.table_vectorizer.vectorize_batch(formatted_table_items)
                vectorization_result['table_vectors'] = table_vectors
                logging.info(f"表格向量化完成: {table_count} 个")
            
            # 图片向量化在ImageProcessor中已完成，这里收集结果
            if metadata_results.get('images'):
                image_count = len(metadata_results['images'])
                logging.info(f"图片向量化状态检查: {image_count} 个")
                
                # 收集图片向量化结果
                image_vectors = []
                for i, img in enumerate(metadata_results['images']):
                    logging.info(f"图片 {i}: image_id={img.get('image_id')}, 有image_embedding={('image_embedding' in img)}, 有description_embedding={('description_embedding' in img)}")
                    logging.info(f"图片 {i}: image_embedding长度={len(img.get('image_embedding', []))}, description_embedding长度={len(img.get('description_embedding', []))}")
                    logging.info(f"图片 {i} 从ImageProcessor接收的原始结构: {list(img.keys())}")
                    logging.info(f"图片 {i} 是否有metadata字段: {'metadata' in img}")

                    if img.get('image_embedding') and img.get('description_embedding'):
                        logging.info(f"✅ 图片 {i} 满足收集条件")
                        # 使用img对象本身，它已经包含了完整的metadata信息
                        image_vector = img.copy()  # 复制整个img对象
                        logging.info(f"图片 {i} 复制后的结构: {list(image_vector.keys())}")
                        logging.info(f"图片 {i} 复制后是否有metadata字段: {'metadata' in image_vector}")

                        # 更新向量化相关字段
                        image_vector.update({
                            'status': 'success',
                            'vectorization_status': 'success',
                            'embedding_model': 'multimodal-embedding-one-peace-v1',
                            'vectorization_timestamp': int(time.time()),
                            'vector_dimension': len(img.get('image_embedding', [])),
                            'quality_score': 0.95
                        })
                        logging.info(f"图片 {i} 更新后的结构: {list(image_vector.keys())}")
                        logging.info(f"图片 {i} 更新后是否有metadata字段: {'metadata' in image_vector}")
                        image_vectors.append(image_vector)
                    else:
                        logging.info(f"❌ 图片 {i} 不满足收集条件")
                
                vectorization_result['image_vectors'] = image_vectors
                vectorized_count = len(image_vectors)
                logging.info(f"图片向量化已在ImageProcessor中完成: {vectorized_count}/{image_count} 个")
                logging.info("✅ 图片向量化已在ImageProcessor中完成，结果已收集")
            
            logging.info("✅ 所有内容向量化完成")
            return vectorization_result
            
        except Exception as e:
            error_msg = f"内容向量化失败: {e}"
            logging.error(error_msg)
            self.failure_handler.record_failure('vectorization', 'content_vectorization', str(e))
            
            # 返回错误状态的结构，保持与设计文档一致
            return {
                'text_vectors': [],
                'image_vectors': [],
                'table_vectors': [],
                'vectorization_status': 'failed',
                'vectorization_timestamp': int(time.time()),
                'error': str(e)
            }
    
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
