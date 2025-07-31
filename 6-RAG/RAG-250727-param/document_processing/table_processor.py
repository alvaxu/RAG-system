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
        解析HTML表格内容（从老代码移植）
        :param html_content: HTML格式的表格内容
        :param table_type: 表格类型描述
        :return: 表格信息对象
        """
        try:
            # 简单的HTML表格解析
            # 移除HTML标签，保留文本内容
            clean_content = re.sub(r'<[^>]+>', '', html_content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            # 生成表格ID
            table_id = f"table_{hash(html_content) % 1000000}"
            
            # 简单的表格结构解析
            headers = ["表格内容"]
            rows = [[clean_content]]
            
            table_info = TableInfo(
                table_id=table_id,
                table_type=table_type,
                headers=headers,
                rows=rows,
                row_count=len(rows),
                column_count=len(headers),
                html_content=html_content
            )
            
            logger.info(f"表格解析完成: {table_type}, 行数: {len(rows)}, 列数: {len(headers)}")
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
            
            # 按行分块
            current_chunk = []
            current_length = 0
            
            for row in table_info.rows:
                row_text = " | ".join(row) + "\n"
                row_length = len(row_text)
                
                if current_length + row_length > chunk_size and current_chunk:
                    # 保存当前分块
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [row_text]
                    current_length = row_length
                else:
                    current_chunk.append(row_text)
                    current_length += row_length
            
            # 添加最后一个分块
            if current_chunk:
                chunks.append("\n".join(current_chunk))
            
            return chunks
            
        except Exception as e:
            logger.error(f"生成表格分块失败: {e}")
            return [f"表格内容: {table_info.html_content}"]
    
    def _table_to_structured_text(self, table_info: TableInfo) -> str:
        """
        将表格转换为结构化文本
        :param table_info: 表格信息对象
        :return: 结构化文本
        """
        lines = []
        lines.append(f"表格类型: {table_info.table_type}")
        lines.append(f"表格ID: {table_info.table_id}")
        lines.append(f"行数: {table_info.row_count}, 列数: {table_info.column_count}")
        lines.append("")
        
        # 添加表头
        if table_info.headers:
            lines.append("表头: " + " | ".join(table_info.headers))
            lines.append("")
        
        # 添加数据行
        for i, row in enumerate(table_info.rows):
            lines.append(f"第{i+1}行: " + " | ".join(row))
        
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