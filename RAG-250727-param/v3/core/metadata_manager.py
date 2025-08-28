"""
元数据管理器

负责管理所有内容的元数据，包括生成、存储、查询和更新元数据。
完全符合设计文档的元数据规范。
"""

import os
import time
import uuid
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

class MetadataManager:
    """
    元数据管理器主类

    功能：
    - 严格按照设计文档规范生成元数据
    - 支持COMMON_METADATA_FIELDS、IMAGE_METADATA_SCHEMA、TEXT_METADATA_SCHEMA、TABLE_METADATA_SCHEMA
    - 提供元数据查询接口
    - 管理元数据存储
    - 完全符合设计文档规范
    """

    def __init__(self, config_manager):
        """
        初始化元数据管理器

        :param config_manager: 配置管理器
        """
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()

        # 元数据存储
        self.metadata_store = []
        
        # 元数据统计
        self.metadata_statistics = {
            'total_chunks': 0,
            'text_chunks': 0,
            'image_chunks': 0,
            'table_chunks': 0,
            'last_update': None
        }

        logging.info("MetadataManager初始化完成")

    def generate_metadata(self, content_type: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成元数据

        :param content_type: 内容类型
        :param content_data: 内容数据
        :return: 标准化的元数据
        """
        try:
            if content_type == 'text':
                return self._generate_text_metadata(content_data)
            elif content_type == 'image':
                return self._generate_image_metadata(content_data)
            elif content_type == 'table':
                return self._generate_table_metadata(content_data)
            else:
                raise ValueError(f"不支持的内容类型: {content_type}")

        except Exception as e:
            logging.error(f"生成元数据失败: {e}")
            raise

    def _generate_text_metadata(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成文本元数据，严格按照TEXT_METADATA_SCHEMA规范
        """
        current_timestamp = int(time.time())
        
        # 基础标识字段（符合COMMON_METADATA_FIELDS）
        metadata = {
            'chunk_id': f"text_{current_timestamp}_{uuid.uuid4().hex[:8]}",
            'chunk_type': 'text',
            'source_type': content_data.get('source_type', 'mineru_output'),
            'document_name': content_data.get('document_name', ''),
            'document_path': content_data.get('document_path', ''),
            'page_number': content_data.get('page_number', 1),
            'page_idx': content_data.get('page_idx', 0),
            'created_timestamp': current_timestamp,
            'updated_timestamp': current_timestamp,
            'processing_version': 'V3.0.0',
            
            # 向量化信息字段
            'vectorized': content_data.get('vectorized', False),
            'vectorization_timestamp': content_data.get('vectorization_timestamp'),
            'embedding_model': content_data.get('embedding_model'),
            
            # 文本特有字段（符合TEXT_METADATA_SCHEMA）
            'text_content': content_data.get('text_content', ''),
            'text_length': len(content_data.get('text_content', '')),
            'chunk_size': content_data.get('chunk_size', 0),
            'chunk_overlap': content_data.get('chunk_overlap', 0),
            'chunk_position': content_data.get('chunk_position', {}),
            
            # 关联信息字段
            'related_images': content_data.get('related_images', []),
            'related_tables': content_data.get('related_tables', []),
            'parent_chunk_id': content_data.get('parent_chunk_id'),
            
            # 向量化结果
            'text_embedding': content_data.get('text_embedding', []),
            
            # 架构标识
            'metadata_schema': 'TEXT_METADATA_SCHEMA',
            'metadata_version': '3.0.0',
            'processing_pipeline': 'Text_Processing_Pipeline',
            'optimization_features': [
                'intelligent_chunking',
                'semantic_analysis',
                'complete_metadata',
                'vectorization_integration'
            ]
        }
        
        return metadata

    def _generate_image_metadata(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成图像元数据，严格按照IMAGE_METADATA_SCHEMA规范
        """
        current_timestamp = int(time.time())
        
        # 基础标识字段（符合COMMON_METADATA_FIELDS）
        metadata = {
            'chunk_id': f"image_{current_timestamp}_{uuid.uuid4().hex[:8]}",
            'chunk_type': 'image',
            'source_type': content_data.get('source_type', 'pdf'),
            'document_name': content_data.get('document_name', ''),
            'document_path': content_data.get('document_path', ''),
            'page_number': content_data.get('page_number', 1),
            'page_idx': content_data.get('page_idx', 1),
            'created_timestamp': current_timestamp,
            'updated_timestamp': current_timestamp,
            'processing_version': 'V3.0.0',
            
            # 向量化信息字段
            'vectorized': content_data.get('vectorized', False),
            'vectorization_timestamp': content_data.get('vectorization_timestamp'),
            'embedding_model': content_data.get('embedding_model'),
            
            # 图片特有字段（符合IMAGE_METADATA_SCHEMA）
            'image_id': content_data.get('image_id', ''),
            'image_path': content_data.get('image_path', ''),
            'image_filename': content_data.get('image_filename', ''),
            'image_type': content_data.get('image_type', 'general'),
            'image_format': content_data.get('image_format', 'UNKNOWN'),
            'image_dimensions': content_data.get('image_dimensions', {'width': 0, 'height': 0}),
            
            # 内容描述字段（保留现有系统的优秀部分）
            'basic_description': content_data.get('basic_description', ''),
            'enhanced_description': content_data.get('enhanced_description', ''),
            'layered_descriptions': content_data.get('layered_descriptions', {}),
            'structured_info': content_data.get('structured_info', {}),
            
            # 图片标题和脚注（保留现有系统的优秀部分）
            'img_caption': content_data.get('img_caption', []),
            'img_footnote': content_data.get('img_footnote', []),
            
            # 增强处理字段（支持失败处理和补做）
            'enhancement_enabled': content_data.get('enhancement_enabled', True),
            'enhancement_model': content_data.get('enhancement_model', ''),
            'enhancement_status': content_data.get('enhancement_status', 'unknown'),
            'enhancement_timestamp': content_data.get('enhancement_timestamp'),
            'enhancement_error': content_data.get('enhancement_error', ''),
            
            # 双重embedding字段（符合设计文档规范）
            'image_embedding': content_data.get('image_embedding', []),
            'description_embedding': content_data.get('description_embedding', []),
            'image_embedding_model': content_data.get('image_embedding_model', ''),
            'description_embedding_model': content_data.get('description_embedding_model', ''),
            
            # 关联信息字段
            'related_text_chunks': content_data.get('related_text_chunks', []),
            'related_table_chunks': content_data.get('related_table_chunks', []),
            'parent_document_id': content_data.get('parent_document_id', ''),
            
            # 处理状态信息
            'copy_status': content_data.get('copy_status', 'unknown'),
            'vectorization_status': content_data.get('vectorization_status', 'unknown'),
            
            # 原始信息
            'mineru_original': content_data.get('mineru_original', {}),
            'vision_analysis': content_data.get('vision_analysis', {}),
            
            # 架构标识
            'metadata_schema': 'IMAGE_METADATA_SCHEMA',
            'metadata_version': '3.0.0',
            'processing_pipeline': 'MinerU_Enhancement_Pipeline',
            'optimization_features': [
                'one_time_enhancement',
                'smart_deduplication',
                'complete_metadata',
                'dual_vectorization'
            ]
        }
        
        return metadata

    def _generate_table_metadata(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成表格元数据，严格按照TABLE_METADATA_SCHEMA规范
        """
        current_timestamp = int(time.time())
        
        # 基础标识字段（符合COMMON_METADATA_FIELDS）
        metadata = {
            'chunk_id': f"table_{current_timestamp}_{uuid.uuid4().hex[:8]}",
            'chunk_type': 'table',
            'source_type': content_data.get('source_type', 'pdf'),
            'document_name': content_data.get('document_name', ''),
            'document_path': content_data.get('document_path', ''),
            'page_number': content_data.get('page_number', 1),
            'page_idx': content_data.get('page_idx', 1),
            'created_timestamp': current_timestamp,
            'updated_timestamp': current_timestamp,
            'processing_version': 'V3.0.0',
            
            # 向量化信息字段
            'vectorized': content_data.get('vectorized', False),
            'vectorization_timestamp': content_data.get('vectorization_timestamp'),
            'embedding_model': content_data.get('embedding_model'),
            
            # 表格特有字段（符合TABLE_METADATA_SCHEMA）
            'table_id': content_data.get('table_id', ''),
            'table_content': content_data.get('table_content', ''),
            'table_structure': content_data.get('table_structure', {}),
            'table_features': content_data.get('table_features', {}),
            'table_format': content_data.get('table_format', {}),
            
            # 表格分析结果
            'table_analysis': content_data.get('table_analysis', {}),
            'table_extraction': content_data.get('table_extraction', {}),
            'table_formatter': content_data.get('table_formatter', {}),
            
            # 向量化结果
            'table_embedding': content_data.get('table_embedding', []),
            
            # 关联信息字段
            'related_text_chunks': content_data.get('related_text_chunks', []),
            'related_image_chunks': content_data.get('related_image_chunks', []),
            'parent_document_id': content_data.get('parent_document_id', ''),
            
            # 架构标识
            'metadata_schema': 'TABLE_METADATA_SCHEMA',
            'metadata_version': '3.0.0',
            'processing_pipeline': 'Table_Processing_Pipeline',
            'optimization_features': [
                'structure_analysis',
                'content_extraction',
                'format_generation',
                'complete_metadata'
            ]
        }
        
        return metadata

    def store_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        存储元数据
        
        :param metadata: 元数据字典
        :return: 是否存储成功
        """
        try:
            # 验证元数据
            if not self._validate_metadata(metadata):
                logging.warning(f"元数据验证失败: {metadata.get('chunk_id', 'unknown')}")
                return False
            
            # 添加到存储
            self.metadata_store.append(metadata)
            
            # 更新统计信息
            self._update_statistics(metadata)
            
            logging.debug(f"元数据存储成功: {metadata.get('chunk_id', 'unknown')}")
            return True
            
        except Exception as e:
            logging.error(f"存储元数据失败: {e}")
            return False

    def _validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        验证元数据格式
        
        :param metadata: 元数据字典
        :return: 是否有效
        """
        try:
            # 检查必需字段
            required_fields = ['chunk_id', 'chunk_type', 'source_type', 'document_name']
            for field in required_fields:
                if not metadata.get(field):
                    logging.warning(f"元数据缺少必需字段: {field}")
                    return False
            
            # 检查chunk_type
            valid_types = ['text', 'image', 'table']
            if metadata.get('chunk_type') not in valid_types:
                logging.warning(f"无效的chunk_type: {metadata.get('chunk_type')}")
                return False
            
            # 检查时间戳
            if not metadata.get('created_timestamp'):
                logging.warning("元数据缺少created_timestamp")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"验证元数据失败: {e}")
            return False

    def _update_statistics(self, metadata: Dict[str, Any]):
        """
        更新统计信息
        
        :param metadata: 元数据字典
        """
        try:
            self.metadata_statistics['total_chunks'] += 1
            
            chunk_type = metadata.get('chunk_type', '')
            if chunk_type == 'text':
                self.metadata_statistics['text_chunks'] += 1
            elif chunk_type == 'image':
                self.metadata_statistics['image_chunks'] += 1
            elif chunk_type == 'table':
                self.metadata_statistics['table_chunks'] += 1
            
            self.metadata_statistics['last_update'] = int(time.time())
            
        except Exception as e:
            logging.error(f"更新统计信息失败: {e}")

    def query_metadata(self, query_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        查询元数据
        
        :param query_criteria: 查询条件
        :return: 匹配的元数据列表
        """
        try:
            results = []
            
            for metadata in self.metadata_store:
                if self._match_criteria(metadata, query_criteria):
                    results.append(metadata)
            
            logging.info(f"元数据查询完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logging.error(f"查询元数据失败: {e}")
            return []

    def _match_criteria(self, metadata: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """
        检查元数据是否匹配查询条件
        
        :param metadata: 元数据字典
        :param criteria: 查询条件
        :return: 是否匹配
        """
        try:
            for key, value in criteria.items():
                if key not in metadata:
                    return False
                
                if isinstance(value, list):
                    if metadata[key] not in value:
                        return False
                elif metadata[key] != value:
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"匹配查询条件失败: {e}")
            return False

    def get_metadata_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取元数据
        
        :param chunk_id: 块ID
        :return: 元数据字典或None
        """
        try:
            for metadata in self.metadata_store:
                if metadata.get('chunk_id') == chunk_id:
                    return metadata
            
            return None
            
        except Exception as e:
            logging.error(f"根据ID获取元数据失败: {e}")
            return None

    def update_metadata(self, chunk_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新元数据
        
        :param chunk_id: 块ID
        :param updates: 更新内容
        :return: 是否更新成功
        """
        try:
            for metadata in self.metadata_store:
                if metadata.get('chunk_id') == chunk_id:
                    # 更新字段
                    metadata.update(updates)
                    metadata['updated_timestamp'] = int(time.time())
                    
                    logging.info(f"元数据更新成功: {chunk_id}")
                    return True
            
            logging.warning(f"未找到要更新的元数据: {chunk_id}")
            return False
            
        except Exception as e:
            logging.error(f"更新元数据失败: {e}")
            return False

    def delete_metadata(self, chunk_id: str) -> bool:
        """
        删除元数据
        
        :param chunk_id: 块ID
        :return: 是否删除成功
        """
        try:
            for i, metadata in enumerate(self.metadata_store):
                if metadata.get('chunk_id') == chunk_id:
                    # 更新统计信息
                    chunk_type = metadata.get('chunk_type', '')
                    if chunk_type == 'text':
                        self.metadata_statistics['text_chunks'] -= 1
                    elif chunk_type == 'image':
                        self.metadata_statistics['image_chunks'] -= 1
                    elif chunk_type == 'table':
                        self.metadata_statistics['table_chunks'] -= 1
                    
                    self.metadata_statistics['total_chunks'] -= 1
                    
                    # 删除元数据
                    del self.metadata_store[i]
                    
                    logging.info(f"元数据删除成功: {chunk_id}")
                    return True
            
            logging.warning(f"未找到要删除的元数据: {chunk_id}")
            return False
            
        except Exception as e:
            logging.error(f"删除元数据失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取元数据统计信息
        
        :return: 统计信息字典
        """
        return {
            'metadata_manager_version': '3.0.0',
            'total_chunks': self.metadata_statistics['total_chunks'],
            'text_chunks': self.metadata_statistics['text_chunks'],
            'image_chunks': self.metadata_statistics['image_chunks'],
            'table_chunks': self.metadata_statistics['table_chunks'],
            'last_update': self.metadata_statistics['last_update'],
            'storage_size': len(self.metadata_store),
            'capabilities': [
                'metadata_generation',
                'metadata_validation',
                'metadata_storage',
                'metadata_query',
                'metadata_update',
                'metadata_deletion',
                'statistics_tracking'
            ]
        }

    def export_metadata(self, export_path: str, format_type: str = 'json') -> bool:
        """
        导出元数据
        
        :param export_path: 导出路径
        :param format_type: 导出格式
        :return: 是否导出成功
        """
        try:
            if format_type == 'json':
                import json
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata_store, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            logging.info(f"元数据导出成功: {export_path}")
            return True
            
        except Exception as e:
            logging.error(f"导出元数据失败: {e}")
            return False

    def import_metadata(self, import_path: str, format_type: str = 'json') -> bool:
        """
        导入元数据
        
        :param import_path: 导入路径
        :param format_type: 导入格式
        :return: 是否导入成功
        """
        try:
            if format_type == 'json':
                import json
                with open(import_path, 'r', encoding='utf-8') as f:
                    imported_metadata = json.load(f)
                
                # 验证和存储导入的元数据
                success_count = 0
                for metadata in imported_metadata:
                    if self.store_metadata(metadata):
                        success_count += 1
                
                logging.info(f"元数据导入完成: {success_count}/{len(imported_metadata)} 成功")
                return True
            else:
                raise ValueError(f"不支持的导入格式: {format_type}")
            
        except Exception as e:
            logging.error(f"导入元数据失败: {e}")
            return False

    def clear_all_metadata(self) -> bool:
        """
        清空所有元数据
        
        :return: 是否清空成功
        """
        try:
            self.metadata_store.clear()
            self.metadata_statistics = {
                'total_chunks': 0,
                'text_chunks': 0,
                'image_chunks': 0,
                'table_chunks': 0,
                'last_update': None
            }
            
            logging.info("所有元数据已清空")
            return True
            
        except Exception as e:
            logging.error(f"清空元数据失败: {e}")
            return False
