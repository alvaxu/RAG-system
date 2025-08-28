"""
内容元数据提取器

基于MinerU解析的JSON文件提取text、table、image的元数据。
完全符合设计文档的元数据规范。
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

class ContentMetadataExtractor:
    """
    内容元数据提取器
    
    功能：
    - 基于MinerU解析的JSON文件提取text、table、image的元数据
    - 完全符合设计文档的元数据规范
    - 支持智能分块处理
    - 生成标准化的元数据结构
    """
    
    def __init__(self, config_manager):
        """
        初始化内容元数据提取器
        
        :param config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        
        # 使用配置（符合设计文档规范）
        self.chunk_size = self.config.get('document_processing.chunk_size', 1000)
        self.chunk_overlap = self.config.get('document_processing.chunk_overlap', 200)
        
        # 使用失败处理（符合设计文档规范）
        self.failure_handler = config_manager.get_failure_handler()
        
        logging.info("内容元数据提取器初始化完成")
    
    def extract_metadata_from_json(self, json_path: str, doc_name: str) -> Dict[str, Any]:
        """
        从JSON文件提取元数据，完全符合设计文档规范
        
        :param json_path: JSON文件路径
        :param doc_name: 文档名称
        :return: 提取的元数据结果
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取文本块
            text_chunks = self._extract_text_chunks(data, doc_name)
            
            # 提取表格信息
            tables = self._extract_table_info(data, doc_name)
            
            # 提取图片信息
            images = self._extract_image_info(data, doc_name)
            
            return {
                'text_chunks': text_chunks,
                'tables': tables,
                'images': images,
                'document_name': doc_name,
                'total_items': len(data)
            }
            
        except Exception as e:
            self.failure_handler.record_failure(json_path, 'metadata_extraction', str(e))
            logging.error(f"元数据提取失败: {json_path}, 错误: {e}")
            return {'text_chunks': [], 'tables': [], 'images': []}
    
    def _extract_text_chunks(self, data: List[Dict], doc_name: str) -> List[Dict]:
        """
        提取文本块，完全符合TEXT_METADATA_SCHEMA规范
        """
        text_chunks = []
        chunk_index = 0
        
        for item in data:
            if item.get('type') == 'text':
                # 获取文本内容
                text_content = item.get('content', '')
                if not text_content.strip():
                    continue
                
                # 智能分块处理
                chunks = self._smart_text_chunking(text_content, chunk_index)
                
                for i, chunk_content in enumerate(chunks):
                    chunk = {
                        # 基础标识字段（符合COMMON_METADATA_FIELDS）
                        'chunk_id': f"{doc_name}_text_{chunk_index}_{i}",
                        'chunk_type': 'text',
                        'source_type': 'pdf',
                        'document_name': doc_name,
                        'document_path': f"{doc_name}.pdf",
                        'page_number': item.get('page_idx', 1),
                        'page_idx': item.get('page_idx', 1),
                        'created_timestamp': int(time.time()),
                        'updated_timestamp': int(time.time()),
                        'processing_version': 'V3.0.0',
                        
                        # 向量化信息字段
                        'vectorized': False,
                        'vectorization_timestamp': None,
                        'embedding_model': None,
                        
                        # 文本特有字段（符合TEXT_METADATA_SCHEMA）
                        'text_content': chunk_content,
                        'text_length': len(chunk_content),
                        'chunk_size': len(chunk_content),
                        'chunk_overlap': 0,
                        'chunk_position': {
                            'start_char': i * self.chunk_size,
                            'end_char': min((i + 1) * self.chunk_size, len(text_content)),
                            'chunk_index': i,
                            'total_chunks': len(chunks)
                        },
                        
                        # 关联信息字段
                        'related_images': [],
                        'related_tables': [],
                        'parent_chunk_id': None
                    }
                    
                    text_chunks.append(chunk)
                    chunk_index += 1
        
        return text_chunks
    
    def _extract_table_info(self, data: List[Dict], doc_name: str) -> List[Dict]:
        """
        提取表格信息，完全符合TABLE_METADATA_SCHEMA规范
        """
        tables = []
        table_index = 0
        
        for item in data:
            if item.get('type') == 'table':
                # 获取表格内容
                table_content = item.get('table_content', '')
                if not table_content.strip():
                    continue
                
                # 分析表格结构
                table_structure = self._analyze_table_structure(table_content)
                
                # 智能分块处理（大表格分块）
                table_chunks = self._smart_table_chunking(table_content, table_structure)
                
                for i, chunk_content in enumerate(table_chunks):
                    table = {
                        # 基础标识字段（符合COMMON_METADATA_FIELDS）
                        'chunk_id': f"{doc_name}_table_{table_index}_{i}",
                        'chunk_type': 'table',
                        'source_type': 'pdf',
                        'document_name': doc_name,
                        'document_path': f"{doc_name}.pdf",
                        'page_number': item.get('page_idx', 1),
                        'page_idx': item.get('page_idx', 1),
                        'created_timestamp': int(time.time()),
                        'updated_timestamp': int(time.time()),
                        'processing_version': 'V3.0.0',
                        
                        # 向量化信息字段
                        'vectorized': False,
                        'vectorization_timestamp': None,
                        'embedding_model': None,
                        
                        # 表格特有字段（符合TABLE_METADATA_SCHEMA）
                        'table_id': f"{doc_name}_table_{table_index}_{i}",
                        'table_type': 'data_table',
                        'table_rows': table_structure.get('rows', 0),
                        'table_columns': table_structure.get('columns', 0),
                        'table_headers': table_structure.get('headers', []),
                        'table_title': item.get('table_title', ''),
                        'table_summary': self._generate_table_summary(chunk_content),
                        
                        # 内容字段（简化设计，去除冗余）
                        'table_content': chunk_content,
                        'table_html': self._generate_table_html(chunk_content, table_structure),
                        
                        # 分块信息字段（支持大表格分块）
                        'is_subtable': len(table_chunks) > 1,
                        'parent_table_id': f"{doc_name}_table_{table_index}" if len(table_chunks) > 1 else None,
                        'subtable_index': i if len(table_chunks) > 1 else None,
                        'chunk_start_row': i * self.chunk_size if len(table_chunks) > 1 else 0,
                        'chunk_end_row': min((i + 1) * self.chunk_size, table_structure.get('rows', 0)) if len(table_chunks) > 1 else table_structure.get('rows', 0),
                        
                        # 关联信息字段
                        'related_text': item.get('related_text', ''),
                        'related_images': [],
                        'related_text_chunks': [],
                        'table_context': item.get('table_context', '')
                    }
                    
                    tables.append(table)
                    table_index += 1
        
        return tables
    
    def _extract_image_info(self, data: List[Dict], doc_name: str) -> List[Dict]:
        """
        提取图片信息，完全符合IMAGE_METADATA_SCHEMA规范
        """
        images = []
        image_index = 0
        
        for item in data:
            if item.get('type') == 'image':
                # 获取图片路径
                img_path = item.get('img_path', '')
                
                # 构建完整路径
                mineru_output_dir = self.config_manager.get_path('mineru_output_dir')
                source_image_path = os.path.join(mineru_output_dir, 'images', os.path.basename(img_path))
                
                # 构建最终图片路径
                final_image_dir = self.config_manager.get_path('final_image_dir')
                final_image_path = os.path.join(final_image_dir, os.path.basename(img_path))
                
                image = {
                    # 基础标识字段（符合COMMON_METADATA_FIELDS）
                    'chunk_id': f"{doc_name}_image_{image_index}",
                    'chunk_type': 'image',
                    'source_type': 'pdf',
                    'document_name': doc_name,
                    'document_path': f"{doc_name}.pdf",
                    'page_number': item.get('page_idx', 1),
                    'page_idx': item.get('page_idx', 1),
                    'created_timestamp': int(time.time()),
                    'updated_timestamp': int(time.time()),
                    'processing_version': 'V3.0.0',
                    
                    # 向量化信息字段
                    'vectorized': False,
                    'vectorization_timestamp': None,
                    'embedding_model': None,
                    
                    # 图片特有字段（符合IMAGE_METADATA_SCHEMA）
                    'image_id': f"{doc_name}_image_{image_index}",
                    'image_path': final_image_path,
                    'image_filename': os.path.basename(img_path),
                    'image_type': 'general',
                    'image_format': self._get_image_format(img_path),
                    'image_dimensions': {'width': 0, 'height': 0},  # 稍后填充
                    
                    # 内容描述字段（保留现有系统的优秀部分）
                    'basic_description': ' | '.join(item.get('img_caption', [])),
                    'enhanced_description': '',  # 稍后填充
                    'layered_descriptions': {},  # 稍后填充
                    'structured_info': {},  # 稍后填充
                    
                    # 图片标题和脚注（保留现有系统的优秀部分）
                    'img_caption': item.get('img_caption', []),
                    'img_footnote': item.get('img_footnote', []),
                    
                    # 增强处理字段（支持失败处理和补做）
                    'enhancement_enabled': True,
                    'enhancement_model': None,  # 稍后填充
                    'enhancement_status': 'pending',
                    'enhancement_timestamp': None,
                    'enhancement_error': None,
                    
                    # 双重embedding字段（符合设计文档规范）
                    'image_embedding': None,  # 稍后填充
                    'description_embedding': None,  # 稍后填充
                    'image_embedding_model': None,  # 稍后填充
                    'description_embedding_model': None,  # 稍后填充
                    
                    # 关联信息字段
                    'related_text_chunks': [],
                    'related_table_chunks': [],
                    'parent_document_id': doc_name,
                    
                    # 原始路径信息
                    'source_image_path': source_image_path,
                    'img_path': img_path
                }
                
                images.append(image)
                image_index += 1
        
        return images
    
    def _smart_text_chunking(self, text: str, chunk_index: int) -> List[str]:
        """
        智能文本分块
        
        :param text: 文本内容
        :param chunk_index: 分块索引
        :return: 分块后的文本列表
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 如果还有更多内容，尝试在句子边界分割
            if end < len(text):
                # 寻找最近的句子结束符
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in '。！？；':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end
        
        return chunks
    
    def _smart_table_chunking(self, table_content: str, table_structure: Dict) -> List[str]:
        """
        智能表格分块
        
        :param table_content: 表格内容
        :param chunk_index: 分块索引
        :return: 分块后的表格内容列表
        """
        # 简单的表格分块实现
        # 实际应用中可能需要更复杂的表格解析逻辑
        if len(table_content) <= self.chunk_size:
            return [table_content]
        
        # 按行分割表格
        lines = table_content.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_length = len(line)
            if current_length + line_length > self.chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks if chunks else [table_content]
    
    def _analyze_table_structure(self, table_content: str) -> Dict[str, Any]:
        """
        分析表格结构
        
        :param table_content: 表格内容
        :return: 表格结构信息
        """
        lines = table_content.split('\n')
        rows = len(lines)
        columns = max(len(line.split('\t')) for line in lines) if lines else 0
        
        # 简单的表头识别
        headers = []
        if rows > 0:
            first_line = lines[0]
            headers = [h.strip() for h in first_line.split('\t')]
        
        return {
            'rows': rows,
            'columns': columns,
            'headers': headers
        }
    
    def _generate_table_summary(self, table_content: str) -> str:
        """
        生成表格摘要
        
        :param table_content: 表格内容
        :return: 表格摘要
        """
        lines = table_content.split('\n')
        if not lines:
            return "空表格"
        
        row_count = len(lines)
        col_count = max(len(line.split('\t')) for line in lines) if lines else 0
        
        return f"表格包含 {row_count} 行 {col_count} 列数据"
    
    def _generate_table_html(self, table_content: str, table_structure: Dict) -> str:
        """
        生成表格HTML
        
        :param table_content: 表格内容
        :param table_structure: 表格结构
        :return: HTML格式的表格
        """
        lines = table_content.split('\n')
        if not lines:
            return "<table><tr><td>空表格</td></tr></table>"
        
        html = ["<table border='1'>"]
        
        # 添加表头
        if table_structure.get('headers'):
            html.append("<thead><tr>")
            for header in table_structure['headers']:
                html.append(f"<th>{header}</th>")
            html.append("</tr></thead>")
        
        # 添加表格内容
        html.append("<tbody>")
        for line in lines:
            if line.strip():
                html.append("<tr>")
                cells = line.split('\t')
                for cell in cells:
                    html.append(f"<td>{cell.strip()}</td>")
                html.append("</tr>")
        html.append("</tbody>")
        
        html.append("</table>")
        return ''.join(html)
    
    def _get_image_format(self, image_path: str) -> str:
        """
        获取图片格式
        
        :param image_path: 图片路径
        :return: 图片格式
        """
        if not image_path:
            return 'UNKNOWN'
        
        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            return 'JPEG'
        elif ext == '.png':
            return 'PNG'
        elif ext == '.gif':
            return 'GIF'
        elif ext == '.bmp':
            return 'BMP'
        else:
            return 'UNKNOWN'
