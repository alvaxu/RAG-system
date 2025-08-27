"""
元数据管理器

负责管理所有内容的元数据，包括生成、存储、查询和更新元数据。
"""

import logging
from typing import Dict, List, Any, Optional

class MetadataManager:
    """
    元数据管理器主类

    功能：
    - 生成和管理系统元数据
    - 提供元数据查询接口
    - 管理元数据存储
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

        logging.info("MetadataManager初始化完成")

    def generate_metadata(self, content_type: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成元数据

        :param content_type: 内容类型
        :param content_data: 内容数据
        :return: 元数据
        """
        try:
            base_metadata = {
                'content_type': content_type,
                'processing_status': 'success',
                'created_at': None,  # 将在存储时设置
                'updated_at': None   # 将在存储时设置
            }

            if content_type == 'text':
                return self._generate_text_metadata(content_data, base_metadata)
            elif content_type == 'image':
                return self._generate_image_metadata(content_data, base_metadata)
            elif content_type == 'table':
                return self._generate_table_metadata(content_data, base_metadata)
            else:
                raise ValueError(f"不支持的内容类型: {content_type}")

        except Exception as e:
            logging.error(f"生成元数据失败: {e}")
            raise

    def _generate_text_metadata(self, content_data: Dict[str, Any], base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """生成文本元数据"""
        metadata = base_metadata.copy()
        metadata.update({
            'chunk_type': 'text',
            'text_content': content_data.get('content', ''),
            'text_length': len(content_data.get('content', '')),
            'chunk_index': content_data.get('chunk_index', 0)
        })
        return metadata

    def _generate_image_metadata(self, content_data: Dict[str, Any], base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """生成图像元数据"""
        metadata = base_metadata.copy()
        metadata.update({
            'chunk_type': 'image',
            'image_path': content_data.get('image_path', ''),
            'enhanced_description': content_data.get('enhanced_description', ''),
            'has_visual_embedding': True,
            'has_semantic_embedding': True
        })
        return metadata

    def _generate_table_metadata(self, content_data: Dict[str, Any], base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """生成表格元数据"""
        metadata = base_metadata.copy()
        metadata.update({
            'chunk_type': 'table',
            'table_content': content_data.get('content', ''),
            'table_html': content_data.get('html', ''),
            'table_rows': content_data.get('rows', 0),
            'table_cols': content_data.get('cols', 0)
        })
        return metadata

    def store_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        存储元数据

        :param metadata: 元数据
        :return: 元数据ID
        """
        import time
        import uuid

        # 生成ID和时间戳
        metadata_id = str(uuid.uuid4())
        current_time = int(time.time())

        # 更新元数据
        metadata.update({
            'id': metadata_id,
            'created_at': current_time,
            'updated_at': current_time
        })

        # 存储到内存中（后续可以改为持久化存储）
        self.metadata_store.append(metadata)

        logging.debug(f"元数据已存储，ID: {metadata_id}")
        return metadata_id

    def get_metadata(self, metadata_id: str) -> Optional[Dict[str, Any]]:
        """
        获取元数据

        :param metadata_id: 元数据ID
        :return: 元数据，如果不存在返回None
        """
        for metadata in self.metadata_store:
            if metadata.get('id') == metadata_id:
                return metadata.copy()
        return None

    def query_metadata(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        查询元数据

        :param filters: 查询条件
        :return: 匹配的元数据列表
        """
        results = []

        for metadata in self.metadata_store:
            match = True
            for key, value in filters.items():
                if metadata.get(key) != value:
                    match = False
                    break

            if match:
                results.append(metadata.copy())

        return results

    def update_metadata(self, metadata_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新元数据

        :param metadata_id: 元数据ID
        :param updates: 更新内容
        :return: 是否更新成功
        """
        import time

        for i, metadata in enumerate(self.metadata_store):
            if metadata.get('id') == metadata_id:
                # 更新内容
                updates['updated_at'] = int(time.time())
                self.metadata_store[i].update(updates)
                logging.debug(f"元数据已更新，ID: {metadata_id}")
                return True

        return False

    def delete_metadata(self, metadata_id: str) -> bool:
        """
        删除元数据

        :param metadata_id: 元数据ID
        :return: 是否删除成功
        """
        for i, metadata in enumerate(self.metadata_store):
            if metadata.get('id') == metadata_id:
                del self.metadata_store[i]
                logging.debug(f"元数据已删除，ID: {metadata_id}")
                return True

        return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取元数据统计信息

        :return: 统计信息
        """
        total_count = len(self.metadata_store)

        if total_count == 0:
            return {
                'total_count': 0,
                'content_types': {},
                'chunk_types': {}
            }

        # 按内容类型统计
        content_types = {}
        chunk_types = {}

        for metadata in self.metadata_store:
            content_type = metadata.get('content_type', 'unknown')
            chunk_type = metadata.get('chunk_type', 'unknown')

            content_types[content_type] = content_types.get(content_type, 0) + 1
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        return {
            'total_count': total_count,
            'content_types': content_types,
            'chunk_types': chunk_types
        }
