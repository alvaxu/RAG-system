'''
程序说明：
## 1. 表格处理器模块 V2 - 使用Pandas + LangChain平替
## 2. 处理文档中的表格内容，提供更强大的表格解析能力
## 3. 支持表格分块和元数据提取
## 4. 与配置系统集成，保持与原版本相同的接口
'''

import re
import json
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    """
    表格信息数据结构（与原版本保持一致）
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
    表格分块数据结构（与原版本保持一致）
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
    可配置的表格处理器 - V2版本，使用Pandas进行表格解析
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_table_rows = self.config.get('max_table_rows', 100)
        self.enable_table_processing = self.config.get('enable_table_processing', True)
    
    def extract_tables_from_json(self, json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从JSON数据中提取表格信息（与原版本保持一致）
        """
        tables = []
        
        for item in json_data:
            if item.get('type') == 'table':
                table_info = {
                    'table_id': item.get('id', f'table_{len(tables)}'),
                    'table_type': 'html_table',
                    'content': item.get('table_body', ''),
                    'page_number': item.get('page_idx', 0) + 1,
                    'metadata': {
                        'table_id': item.get('id', f'table_{len(tables)}'),
                        'table_type': 'html_table',
                        'chunk_type': 'table'
                    }
                }
                tables.append(table_info)
        
        return tables
    
    def parse_html_table(self, html_content: str, table_type: str = "未知表格") -> TableInfo:
        """
        解析HTML表格内容 - 使用Pandas进行更强大的解析
        """
        try:
            # 使用Pandas解析HTML表格
            tables = pd.read_html(html_content)
            
            if not tables:
                # 如果Pandas无法解析，回退到正则表达式方法
                return self._fallback_parse_html_table(html_content, table_type)
            
            # 使用第一个表格
            df = tables[0]
            
            # 提取表头和数据
            headers = df.columns.tolist()
            rows = []
            
            for _, row in df.iterrows():
                row_data = []
                for cell in row:
                    if pd.isna(cell):
                        row_data.append("")
                    else:
                        row_data.append(str(cell))
                rows.append(row_data)
            
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
            
            logger.info(f"Pandas表格解析完成: {table_type}, 行数: {len(rows)}, 列数: {len(headers) if headers else 1}")
            return table_info
            
        except Exception as e:
            logger.error(f"Pandas解析HTML表格失败，使用回退方法: {e}")
            return self._fallback_parse_html_table(html_content, table_type)
    
    def _fallback_parse_html_table(self, html_content: str, table_type: str) -> TableInfo:
        """
        回退的HTML表格解析方法（使用正则表达式）
        """
        try:
            rows = []
            headers = []
            
            # 使用正则表达式解析HTML表格结构
            tr_pattern = r'<tr[^>]*>(.*?)</tr>'
            tr_matches = re.findall(tr_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for i, tr_content in enumerate(tr_matches):
                cell_pattern = r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>'
                cell_matches = re.findall(cell_pattern, tr_content, re.DOTALL | re.IGNORECASE)
                
                if cell_matches:
                    cleaned_cells = []
                    for cell in cell_matches:
                        clean_cell = re.sub(r'<[^>]+>', '', cell)
                        clean_cell = re.sub(r'\s+', ' ', clean_cell).strip()
                        cleaned_cells.append(clean_cell)
                    
                    if i == 0:  # 第一行作为表头
                        headers = cleaned_cells
                    else:
                        rows.append(cleaned_cells)
            
            # 如果没有解析到结构，使用简单方法
            if not headers and not rows:
                clean_content = re.sub(r'<[^>]+>', '', html_content)
                clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                lines = [line.strip() for line in clean_content.split('\n') if line.strip()]
                if lines:
                    headers = ["表格内容"]
                    rows = [[clean_content]]
            
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
            
            logger.info(f"回退方法表格解析完成: {table_type}, 行数: {len(rows)}, 列数: {len(headers) if headers else 1}")
            return table_info
            
        except Exception as e:
            logger.error(f"回退解析HTML表格失败: {e}")
            return TableInfo(
                table_id='error_table',
                table_type=table_type,
                headers=["错误"],
                rows=[["表格解析失败"]],
                row_count=1,
                column_count=1,
                html_content=html_content
            )
    
    def _table_to_structured_text(self, table_info: TableInfo) -> str:
        """
        将表格转换为结构化文本
        """
        lines = []
        lines.append(f"表格类型: {table_info.table_type}")
        lines.append(f"表格ID: {table_info.table_id}")
        lines.append(f"行数: {table_info.row_count}, 列数: {table_info.column_count}")
        lines.append("")
        
        if table_info.headers and table_info.rows:
            lines.append("表格结构说明:")
            lines.append(f"  列标题（字段定义）: {', '.join(table_info.headers)}")
            lines.append("")
            
            lines.append("数据记录:")
            for row_idx, row in enumerate(table_info.rows):
                if len(row) == len(table_info.headers):
                    record_parts = []
                    for col_idx, cell_value in enumerate(row):
                        if col_idx < len(table_info.headers):
                            field_name = table_info.headers[col_idx]
                            record_parts.append(f"{field_name}={cell_value}")
                    
                    primary_key = row[0] if row else f"记录{row_idx+1}"
                    lines.append(f"  {primary_key}: {', '.join(record_parts[1:])}")
                else:
                    lines.append(f"  记录{row_idx+1}: {', '.join(row)}")
            lines.append("")
            
            lines.append("表格结构总结:")
            lines.append(f"  包含 {len(table_info.headers)} 个字段")
            lines.append(f"  包含 {len(table_info.rows)} 条数据记录")
            lines.append("")
        
        lines.append("原始表格内容:")
        lines.append(table_info.html_content)
        
        return "\n".join(lines)


class ConfigurableTableChunkGenerator:
    """
    可配置的表格分块生成器 - V2版本，使用LangChain进行智能分块
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_chunk_size = self.config.get('chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 200)
        
        # 使用LangChain的文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""],
            chunk_size=self.max_chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
    
    def generate_table_chunks(self, table_info: TableInfo, chunk_size: int = None) -> List[str]:
        """
        生成表格分块 - 使用LangChain进行智能分块
        """
        try:
            if not table_info or not table_info.rows:
                return []
            
            chunk_size = chunk_size or self.max_chunk_size
            
            # 将表格转换为结构化文本
            table_text = self._table_to_structured_text(table_info)
            
            # 如果表格内容小于分块大小，直接返回
            if len(table_text) <= chunk_size:
                return [table_text]
            
            # 使用LangChain的文本分割器进行智能分块
            chunks = self.text_splitter.split_text(table_text)
            
            # 过滤空分块
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
            
            return chunks
            
        except Exception as e:
            logger.error(f"生成表格分块失败: {e}")
            return [f"表格内容: {table_info.html_content}"]
    
    def _table_to_structured_text(self, table_info: TableInfo) -> str:
        """
        将表格转换为结构化文本
        """
        lines = []
        lines.append(f"表格类型: {table_info.table_type}")
        lines.append(f"表格ID: {table_info.table_id}")
        lines.append(f"行数: {table_info.row_count}, 列数: {table_info.column_count}")
        lines.append("")
        
        if table_info.headers and table_info.rows:
            lines.append("表格结构说明:")
            lines.append(f"  列标题（字段定义）: {', '.join(table_info.headers)}")
            lines.append("")
            
            lines.append("数据记录:")
            for row_idx, row in enumerate(table_info.rows):
                if len(row) == len(table_info.headers):
                    record_parts = []
                    for col_idx, cell_value in enumerate(row):
                        if col_idx < len(table_info.headers):
                            field_name = table_info.headers[col_idx]
                            record_parts.append(f"{field_name}={cell_value}")
                    
                    primary_key = row[0] if row else f"记录{row_idx+1}"
                    lines.append(f"  {primary_key}: {', '.join(record_parts[1:])}")
                else:
                    lines.append(f"  记录{row_idx+1}: {', '.join(row)}")
            lines.append("")
            
            lines.append("表格结构总结:")
            lines.append(f"  包含 {len(table_info.headers)} 个字段")
            lines.append(f"  包含 {len(table_info.rows)} 条数据记录")
            lines.append("")
        
        lines.append("原始表格内容:")
        lines.append(table_info.html_content)
        
        return "\n".join(lines)


def process_tables_from_document_with_config(json_data: List[Dict[str, Any]], 
                                           document_name: str, 
                                           config: Dict[str, Any] = None) -> List[TableChunk]:
    """
    使用配置处理文档中的表格 - V2版本
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


# 为了兼容性，提供别名（与原版本保持一致）
TableProcessor = ConfigurableTableProcessor
TableChunkGenerator = ConfigurableTableChunkGenerator
process_tables_from_document = process_tables_from_document_with_config
