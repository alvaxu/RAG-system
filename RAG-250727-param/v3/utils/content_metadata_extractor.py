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
            
            # 解析新的JSON结构：从pdf_info[0]['preproc_blocks']中提取数据
            if 'pdf_info' in data and len(data['pdf_info']) > 0:
                preproc_blocks = data['pdf_info'][0].get('preproc_blocks', [])
                logging.info(f"从preproc_blocks中提取到 {len(preproc_blocks)} 个预处理块")
            else:
                # 兼容旧格式：直接使用data
                preproc_blocks = data
                logging.info(f"使用兼容模式，直接处理 {len(preproc_blocks)} 个数据项")
            
            # 提取文本块
            text_chunks = self._extract_text_chunks(preproc_blocks, doc_name)
            
            # 提取表格信息
            tables = self._extract_table_info(preproc_blocks, doc_name)
            
            # 提取图片信息
            images = self._extract_image_info(preproc_blocks, doc_name)
            
            return {
                'text_chunks': text_chunks,
                'tables': tables,
                'images': images,
                'document_name': doc_name,
                'total_items': len(preproc_blocks)
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
                # 从新的JSON结构中提取文本内容
                text_content = ""
                if 'lines' in item:
                    for line in item['lines']:
                        if 'spans' in line:
                            for span in line['spans']:
                                if span.get('type') == 'text':
                                    text_content += span.get('content', '') + " "
                
                text_content = text_content.strip()
                if not text_content:
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
                        'text': chunk_content,
                        'text_length': len(chunk_content),
                        'text_level': item.get('text_level', 0),
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
                table_body = item.get('table_body', '')
                if not table_body.strip():
                    continue

                # 分析表格结构
                table_structure = self._analyze_table_structure_from_html(table_body)

                # 智能分块处理（大表格分块）
                table_chunks = self._smart_table_chunking_html(table_body, table_structure)
                
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
                        
                        # 内容字段（根据MinerU JSON实际结构）
                        'table_body': chunk_content,        # HTML格式，用于web展现
                        'table_content': self._extract_text_from_html(chunk_content),  # 纯文本格式，用于向量化
                        'table_caption': item.get('table_caption', []),  # 表格标题
                        'table_footnote': item.get('table_footnote', []), # 表格脚注
                        
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
                    'final_image_path': final_image_path,  # 添加final_image_path字段，与ImageProcessor保持一致
                    'image_filename': os.path.basename(img_path),
                    'image_type': 'general',
                    'image_format': self._get_image_format(img_path),
                    'image_dimensions': {'width': 0, 'height': 0},  # 稍后填充
                    
                    # 内容描述字段（保留现有系统的优秀部分）
                    'basic_description': '',  # 稍后填充，避免直接使用外部字段
                    'enhanced_description': '',  # 稍后填充
                    'layered_descriptions': {},  # 稍后填充
                    'structured_info': {},  # 稍后填充
                    
                    # 图片标题和脚注（保留现有系统的优秀部分）
                    # 先获取外部数据，然后统一映射到内部字段
                    'img_caption': item.get('image_caption', []),  # 从JSON的image_caption映射到img_caption
                    'img_footnote': item.get('image_footnote', []),  # 从JSON的image_footnote映射到img_footnote
                    
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
    
    def _smart_table_chunking_html(self, table_html: str, table_structure: Dict) -> List[str]:
        """
        HTML-aware的智能表格分块
        
        按照设计文档要求实现：
        - 按内容长度分块：避免单个chunk过大
        - 保持表头完整性：每个分块都包含完整表头
        - 智能行数计算：根据内容长度动态计算分块大小
        - 保持HTML结构完整性

        :param table_html: 表格HTML内容
        :param table_structure: 表格结构信息
        :return: 分块后的HTML内容列表
        """
        if len(table_html) <= self.chunk_size:
            return [table_html]

        try:
            # 解析HTML表格结构
            parsed_table = self._parse_html_table(table_html)
            if not parsed_table:
                return [table_html]

            headers = parsed_table.get('headers', [])
            data_rows = parsed_table.get('data_rows', [])
            
            if len(data_rows) <= 1:
                return [table_html]

            # 计算分块策略
            header_html = self._generate_header_html(headers)
            header_length = len(header_html)
            
            # 估算每行平均长度
            if data_rows:
                avg_row_length = sum(len(self._row_to_text(row)) for row in data_rows) / len(data_rows)
            else:
                avg_row_length = 0
            
            # 计算每个分块的目标行数
            if avg_row_length > 0:
                # 考虑表头长度，计算每个分块能容纳的数据行数
                available_size = self.chunk_size - header_length
                target_rows_per_chunk = max(1, int(available_size / (avg_row_length * 1.2)))  # 1.2为安全系数
            else:
                target_rows_per_chunk = 10
            
            # 执行分块
            chunks = []
            current_rows = []
            
            for i, row in enumerate(data_rows):
                # 先尝试添加这一行
                test_rows = current_rows + [row]
                test_chunk_html = self._create_chunk_html(headers, test_rows)
                
                # 检查添加这一行后是否会超出chunk_size
                if len(test_chunk_html) > self.chunk_size and current_rows:
                    # 当前行集合已经达到大小限制，创建分块
                    chunk_html = self._create_chunk_html(headers, current_rows)
                    chunks.append(chunk_html)
                    
                    # 重置当前行集合，开始新分块
                    current_rows = [row]
                else:
                    # 可以添加这一行
                    current_rows = test_rows
                
                # 检查是否达到目标行数（作为额外条件）
                if len(current_rows) >= target_rows_per_chunk:
                    # 创建分块
                    chunk_html = self._create_chunk_html(headers, current_rows)
                    chunks.append(chunk_html)
                    
                    # 重置当前行集合
                    current_rows = []
            
            # 处理最后剩余的行
            if current_rows:
                chunk_html = self._create_chunk_html(headers, current_rows)
                chunks.append(chunk_html)
            
            # 如果没有生成任何分块，返回原表格
            if not chunks:
                return [table_html]
            
            return chunks
            
        except Exception as e:
            logging.warning(f"HTML表格分块失败，返回原表格: {e}")
            return [table_html]

    def _extract_text_from_html(self, table_html: str) -> str:
        """
        从HTML表格中提取纯文本用于向量化

        :param table_html: 表格HTML内容
        :return: 提取的纯文本内容
        """
        # 简单的HTML文本提取
        # 移除HTML标签，提取纯文本
        import re

        # 移除HTML标签
        text = re.sub(r'<[^>]+>', ' ', table_html)

        # 清理多余的空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _analyze_table_structure_from_html(self, table_html: str) -> Dict[str, Any]:
        """
        从HTML表格中分析表格结构

        :param table_html: 表格HTML内容
        :return: 表格结构信息
        """
        # 使用简单的正则表达式分析HTML表格结构
        import re

        # 提取行数（<tr>标签数量）
        rows = len(re.findall(r'<tr[^>]*>', table_html, re.IGNORECASE))

        # 提取列数（第一行的<td>或<th>标签数量）
        first_row_match = re.search(r'<tr[^>]*>(.*?)</tr>', table_html, re.IGNORECASE | re.DOTALL)
        if first_row_match:
            first_row_html = first_row_match.group(1)
            columns = len(re.findall(r'<t[dh][^>]*>', first_row_html, re.IGNORECASE))
        else:
            columns = 0

        # 提取表头（<th>标签内容）
        headers = []
        th_matches = re.findall(r'<th[^>]*>(.*?)</th>', table_html, re.IGNORECASE | re.DOTALL)
        for th_content in th_matches:
            # 移除嵌套的HTML标签
            clean_header = re.sub(r'<[^>]+>', '', th_content).strip()
            if clean_header:
                headers.append(clean_header)

        return {
            'rows': rows,
            'columns': columns,
            'headers': headers
        }


    
    def _generate_table_summary(self, table_html: str) -> str:
        """
        生成表格摘要（支持HTML格式）

        :param table_html: 表格HTML内容
        :return: 表格摘要
        """
        import re

        # 从HTML中提取行数和列数
        rows = len(re.findall(r'<tr[^>]*>', table_html, re.IGNORECASE))

        # 提取列数（第一行的<td>或<th>标签数量）
        first_row_match = re.search(r'<tr[^>]*>(.*?)</tr>', table_html, re.IGNORECASE | re.DOTALL)
        if first_row_match:
            first_row_html = first_row_match.group(1)
            columns = len(re.findall(r'<t[dh][^>]*>', first_row_html, re.IGNORECASE))
        else:
            columns = 0

        if rows == 0:
            return "空表格"

        return f"表格包含 {rows} 行 {columns} 列数据"
    

    
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

    def _parse_html_table(self, table_html: str) -> Dict[str, Any]:
        """
        解析HTML表格结构，提取表头和数据行
        
        :param table_html: 表格HTML内容
        :return: 解析后的表格结构
        """
        import re
        
        try:
            # 提取表头（<th>标签）
            headers = []
            th_matches = re.findall(r'<th[^>]*>(.*?)</th>', table_html, re.IGNORECASE | re.DOTALL)
            for th_content in th_matches:
                clean_header = re.sub(r'<[^>]+>', '', th_content).strip()
                if clean_header:
                    headers.append(clean_header)
            
            # 提取数据行（<tr>标签中的<td>）
            data_rows = []
            tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.IGNORECASE | re.DOTALL)
            
            for tr_content in tr_matches:
                # 跳过表头行（如果已经有表头）
                if headers and '<th' in tr_content.lower():
                    continue
                
                # 提取单元格内容
                td_matches = re.findall(r'<td[^>]*>(.*?)</td>', tr_content, re.IGNORECASE | re.DOTALL)
                if td_matches:
                    row = []
                    for td_content in td_matches:
                        clean_cell = re.sub(r'<[^>]+>', '', td_content).strip()
                        row.append(clean_cell)
                    data_rows.append(row)
            
            return {
                'headers': headers,
                'data_rows': data_rows
            }
            
        except Exception as e:
            logging.warning(f"HTML表格解析失败: {e}")
            return {'headers': [], 'data_rows': []}

    def _generate_header_html(self, headers: List[str]) -> str:
        """
        生成表头HTML
        
        :param headers: 表头列表
        :return: 表头HTML字符串
        """
        if not headers:
            return ""
        
        header_cells = []
        for header in headers:
            header_cells.append(f"<th>{header}</th>")
        
        return f"<thead><tr>{''.join(header_cells)}</tr></thead>"

    def _create_chunk_html(self, headers: List[str], data_rows: List[List[str]]) -> str:
        """
        创建分块HTML表格
        
        :param headers: 表头列表
        :param data_rows: 数据行列表
        :return: 分块HTML表格字符串
        """
        if not data_rows:
            return ""
        
        # 生成表头
        header_html = self._generate_header_html(headers)
        
        # 生成数据行
        data_html = "<tbody>"
        for row in data_rows:
            row_cells = []
            for cell in row:
                row_cells.append(f"<td>{cell}</td>")
            data_html += f"<tr>{''.join(row_cells)}</tr>"
        data_html += "</tbody>"
        
        # 组合完整表格
        return f"<table>{header_html}{data_html}</table>"

    def _row_to_text(self, row: List[str]) -> str:
        """
        将行数据转换为纯文本（用于长度计算）
        
        :param row: 行数据列表
        :return: 纯文本字符串
        """
        return " ".join(str(cell) for cell in row)
