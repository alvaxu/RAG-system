'''
程序说明：
## 1. 表格处理器模块
## 2. 处理文档中的表格内容
## 3. 支持表格分块和元数据提取
## 4. 与配置系统集成
'''

import re
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from langchain.docstore.document import Document

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    """
    表格信息数据结构（从老代码移植）
    :param table_id: 表格唯一标识
    :param table_type: 表格类型（如：分支机构、变更记录等）
    :param headers: 表格列标题
    :param rows: 表格数据行
    :param row_count: 行数
    :param column_count: 列数
    :param html_content: 原始HTML内容
    """
    table_id: str
    table_type: str
    headers: List[str]
    rows: List[List[str]]
    row_count: int
    column_count: int
    html_content: str


@dataclass
class TableChunk:
    """
    表格分块数据结构
    """
    content: str
    table_id: str
    table_type: str
    document_name: str
    page_number: int
    chunk_index: int
    metadata: Dict[str, Any]


class ConfigurableTableProcessor:
    """
    可配置的表格处理器
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化表格处理器
        :param config: 配置字典
        """
        self.config = config or {}
        self.max_table_rows = self.config.get('max_table_rows', 100)
        self.enable_table_processing = self.config.get('enable_table_processing', True)
    
    def extract_tables_from_json(self, json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从JSON数据中提取表格信息
        :param json_data: JSON数据
        :return: 表格信息列表
        """
        tables = []
        
        for item in json_data:
            if item.get('type') == 'table':
                table_info = {
                    'table_id': item.get('id', f'table_{len(tables)}'),
                    'table_type': 'html_table',
                    'content': item.get('table_body', ''),  # 修复：使用table_body字段
                    'page_number': item.get('page_idx', 0) + 1,  # 修复：使用page_idx并转换为1索引
                    'metadata': {
                        'table_id': item.get('id', f'table_{len(tables)}'),
                        'table_type': 'html_table',
                        'chunk_type': 'table'
                    }
                }
                tables.append(table_info)
        
        return tables
    
    def process_table_content(self, table_content: str, table_id: str = None) -> str:
        """
        处理表格内容
        :param table_content: 表格内容
        :param table_id: 表格ID
        :return: 处理后的表格内容
        """
        try:
            # 简单的表格内容处理
            if table_content:
                # 移除HTML标签，保留文本内容
                clean_content = re.sub(r'<[^>]+>', '', table_content)
                clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                return clean_content
            return ""
        except Exception as e:
            logger.error(f"处理表格内容失败: {e}")
            return table_content or ""
    
    def parse_html_table(self, html_content: str, table_type: str = "未知表格") -> TableInfo:
        """
        解析HTML表格内容
        :param html_content: HTML格式的表格内容
        :param table_type: 表格类型描述
        :return: 表格信息对象
        """
        try:
            # 改进的HTML表格解析
            # 提取表格行
            rows = []
            headers = []
            
            # 使用正则表达式解析HTML表格结构
            # 匹配<tr>标签
            tr_pattern = r'<tr[^>]*>(.*?)</tr>'
            tr_matches = re.findall(tr_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for i, tr_content in enumerate(tr_matches):
                # 匹配<td>和<th>标签
                cell_pattern = r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>'
                cell_matches = re.findall(cell_pattern, tr_content, re.DOTALL | re.IGNORECASE)
                
                if cell_matches:
                    # 清理单元格内容
                    cleaned_cells = []
                    for cell in cell_matches:
                        # 移除HTML标签
                        clean_cell = re.sub(r'<[^>]+>', '', cell)
                        # 清理空白字符
                        clean_cell = re.sub(r'\s+', ' ', clean_cell).strip()
                        cleaned_cells.append(clean_cell)
                    
                    if i == 0:  # 第一行作为表头
                        headers = cleaned_cells
                    else:
                        rows.append(cleaned_cells)
            
            # 如果没有解析到结构，使用简单方法
            if not headers and not rows:
                # 移除HTML标签，保留文本内容
                clean_content = re.sub(r'<[^>]+>', '', html_content)
                clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                
                # 按行分割
                lines = [line.strip() for line in clean_content.split('\n') if line.strip()]
                if lines:
                    headers = ["表格内容"]
                    rows = [[clean_content]]
            
            # 生成表格ID
            table_id = f"table_{hash(html_content) % 1000000}"
            
            table_info = TableInfo(
                table_id=table_id,
                table_type=table_type,
                headers=headers,
                rows=rows,
                row_count=len(rows),
                column_count=len(headers) if headers else 1,
                html_content=html_content
            )
            
            logger.info(f"表格解析完成: {table_type}, 行数: {len(rows)}, 列数: {len(headers) if headers else 1}")
            return table_info
            
        except Exception as e:
            logger.error(f"解析HTML表格失败: {e}")
            # 返回错误表格信息
            return TableInfo(
                table_id='error_table',
                table_type=table_type,
                headers=["错误"],
                rows=[["表格解析失败"]],
                row_count=1,
                column_count=1,
                html_content=html_content
            )
    
    def process_tables(self, chunks: List[Document]) -> Optional[List[Document]]:
        """
        处理表格数据
        :param chunks: 文档分块列表
        :return: 表格分块列表
        """
        try:
            if not chunks:
                logger.warning("没有提供文档分块")
                return None
            
            logger.info(f"开始处理表格数据，输入分块数: {len(chunks)}")
            
            # 提取表格分块
            table_chunks = []
            for chunk in chunks:
                if chunk.metadata.get('chunk_type') == 'table':
                    table_chunks.append(chunk)
            
            if table_chunks:
                logger.info(f"找到 {len(table_chunks)} 个表格分块")
                return table_chunks
            else:
                logger.info("没有找到表格数据")
                return None
                
        except Exception as e:
            logger.error(f"表格处理失败: {e}")
            return None
    

class ConfigurableTableChunkGenerator:
    """
    可配置的表格分块生成器
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化表格分块生成器
        :param config: 配置字典
        """
        self.config = config or {}
        self.max_chunk_size = self.config.get('chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 200)
    
    def generate_table_chunks(self, table_info: TableInfo, chunk_size: int = None) -> List[str]:
        """
        生成表格分块（从老代码移植）
        :param table_info: 表格信息对象
        :param chunk_size: 分块大小
        :return: 表格分块文本列表
        """
        try:
            if not table_info or not table_info.rows:
                return []
            
            chunk_size = chunk_size or self.max_chunk_size
            chunks = []
            
            # 将表格转换为结构化文本
            table_text = self._table_to_structured_text(table_info)
            
            # 如果表格内容小于分块大小，直接返回
            if len(table_text) <= chunk_size:
                return [table_text]
            
            # 使用结构化文本进行分块
            # 直接返回结构化文本，不再按行分块
            return [table_text]
            
            return chunks
            
        except Exception as e:
            logger.error(f"生成表格分块失败: {e}")
            return [f"表格内容: {table_info.html_content}"]
    
    def _table_to_structured_text(self, table_info: TableInfo) -> str:
        """
        将表格转换为结构化文本 - 通用方法
        专注于表格的语义理解和结构化表示
        :param table_info: 表格信息对象
        :return: 结构化文本
        """
        lines = []
        lines.append(f"表格类型: {table_info.table_type}")
        lines.append(f"表格ID: {table_info.table_id}")
        lines.append(f"行数: {table_info.row_count}, 列数: {table_info.column_count}")
        lines.append("")
        
        if table_info.headers and table_info.rows:
            # 1. 表格结构说明
            lines.append("表格结构说明:")
            lines.append(f"  列标题（字段定义）: {', '.join(table_info.headers)}")
            lines.append("")
            
            # 2. 数据内容 - 每行作为一个完整的数据记录
            lines.append("数据记录:")
            for row_idx, row in enumerate(table_info.rows):
                if len(row) == len(table_info.headers):
                    # 构建完整的数据记录描述
                    record_parts = []
                    for col_idx, cell_value in enumerate(row):
                        if col_idx < len(table_info.headers):
                            field_name = table_info.headers[col_idx]
                            record_parts.append(f"{field_name}={cell_value}")
                    
                    # 首列作为主要标识符
                    primary_key = row[0] if row else f"记录{row_idx+1}"
                    lines.append(f"  {primary_key}: {', '.join(record_parts[1:])}")
                else:
                    # 列数不匹配的情况
                    lines.append(f"  记录{row_idx+1}: {', '.join(row)}")
            lines.append("")
            
            # 3. 表格结构总结
            lines.append("表格结构总结:")
            lines.append(f"  包含 {len(table_info.headers)} 个字段")
            lines.append(f"  包含 {len(table_info.rows)} 条数据记录")
            lines.append("")
        
        # 4. 原始内容作为参考
        lines.append("原始表格内容:")
        lines.append(table_info.html_content)
        
        return "\n".join(lines)
    



def process_tables_from_document_with_config(json_data: List[Dict[str, Any]], 
                                           document_name: str, 
                                           config: Dict[str, Any] = None) -> List[TableChunk]:
        """
    使用配置处理文档中的表格
    :param json_data: JSON数据
    :param document_name: 文档名称
    :param config: 配置字典
    :return: 表格分块列表
        """
        try:
            # 提取表格
            processor = ConfigurableTableProcessor(config)
            tables = processor.extract_tables_from_json(json_data)
            
            if not tables:
                return []
            
            # 生成表格分块
            chunk_generator = ConfigurableTableChunkGenerator(config)
            chunks = []
                
            for table in tables:
                try:
                    # 解析表格
                    table_info = processor.parse_html_table(table.get('content', ''), table.get('table_type', '未知表格'))
                    
                    # 生成表格分块
                    table_chunks = chunk_generator.generate_table_chunks(table_info)
                    
                    for i, chunk_text in enumerate(table_chunks):
                        if chunk_text.strip():
                            chunk = TableChunk(
                                content=chunk_text,
                                table_id=table_info.table_id,
                                table_type=table_info.table_type,
                                document_name=document_name,
                                page_number=table.get('page_number', 1),
                                chunk_index=i,
                                metadata={
                                    'table_id': table_info.table_id,
                                    'table_type': table_info.table_type,
                                    'chunk_type': 'table'
                                }
                            )
                            chunks.append(chunk)
                            
                except Exception as e:
                    logger.error(f"处理表格失败: {e}")
                    continue
            
            return chunks
                
        except Exception as e:
            logger.error(f"处理文档表格失败: {e}")
            return []


# 为了兼容性，提供别名
TableProcessor = ConfigurableTableProcessor
TableChunkGenerator = ConfigurableTableChunkGenerator
process_tables_from_document = process_tables_from_document_with_config 