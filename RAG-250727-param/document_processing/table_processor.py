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
    表格信息数据结构
    :param html_content: 原始HTML内容
    :param table_id: 表格ID
    :param table_type: 表格类型
    :param rows: 表格行数据
    :param row_count: 行数
    :param column_count: 列数
    :param headers: 列标题
    :param title: 表格标题
    :param summary: 表格摘要
    """
    html_content: str
    table_id: str
    table_type: str
    rows: List[List[str]]
    row_count: int
    column_count: int
    headers: List[str]
    title: str = ""
    summary: str = ""
    related_text: str = ""


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
    
    def _table_to_structured_text(self, table_info: TableInfo, table_type: str = "未知表格") -> str:
        """
        将表格信息转换为结构化文本
        :param table_info: 表格信息对象
        :param table_type: 表格类型
        :return: 结构化文本
        """
        try:
            # 生成表头
            headers = table_info.headers if table_info.headers else []
            header_text = " | ".join(headers) if headers else "(无表头)"
            
            # 生成表格内容
            rows_text = []
            for row in table_info.rows:
                if isinstance(row, list):
                    row_text = " | ".join([str(cell) for cell in row if str(cell).strip()])
                else:
                    row_text = str(row)
                if row_text:
                    rows_text.append(row_text)
            
            # 组合表头和内容
            table_text = header_text + "\n" + "\n".join(rows_text) if rows_text else header_text
            
            return table_text
        except Exception as e:
            logger.error(f"转换表格到结构化文本时出错: {e}")
            return "(表格内容转换失败)"
    
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
        解析HTML表格内容，智能提取标题、摘要和相关文本
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
            
            # 智能提取表格标题
            table_title = self._extract_table_title(html_content, headers, table_id)
            
            # 智能生成表格摘要
            table_summary = self._generate_table_summary(headers, rows, table_title)
            
            # 智能生成相关文本
            related_text = self._generate_related_text(headers, rows, table_title, table_type)
            
            table_info = TableInfo(
                html_content=html_content,  # 确保保存原始HTML内容
                table_id=table_id,
                table_type=table_type,
                headers=headers,
                rows=rows,
                row_count=len(rows),
                column_count=len(headers) if headers else 1,
                title=table_title,
                summary=table_summary,
                related_text=related_text
            )
            
            logger.info(f"表格解析完成: 行数: {len(rows)}, 列数: {len(headers) if headers else 1}")
            return table_info
            
        except Exception as e:
            logger.error(f"解析HTML表格失败: {e}")
            # 返回错误表格信息
            return TableInfo(
                html_content=html_content,
                table_id='error_table',
                table_type=table_type,
                headers=["错误"],
                rows=[["表格解析失败"]],
                row_count=1,
                column_count=1,
                title=table_type,
                summary=table_type,
                related_text="表格解析失败"
            )
    
    def _extract_table_title(self, html_content: str, headers: List[str], table_id: str) -> str:
        """
        智能提取表格标题
        :param html_content: HTML内容
        :param headers: 表头列表
        :param table_id: 表格ID
        :return: 表格标题
        """
        # 方法1: 从表头提取标题
        if headers and len(headers) > 0:
            # 寻找最有意义的表头作为标题
            meaningful_headers = []
            for header in headers:
                header = header.strip()
                if header and len(header) > 1:  # 过滤掉太短的标题
                    # 检查是否包含数字（可能是年份、序号等）
                    if not re.search(r'\d{4}', header):  # 排除纯年份
                        meaningful_headers.append(header)
            
            if meaningful_headers:
                # 选择最长的有意义的表头
                best_header = max(meaningful_headers, key=len)
                if len(best_header) > 3:  # 确保标题有意义
                    return best_header
        
        # 方法2: 从HTML中寻找表格上方的标题标签
        title_patterns = [
            r'<h[1-6][^>]*>(.*?)</h[1-6]>',  # h1-h6标签
            r'<caption[^>]*>(.*?)</caption>',  # caption标签
            r'<title[^>]*>(.*?)</title>',      # title标签
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if matches:
                title = re.sub(r'<[^>]+>', '', matches[0]).strip()
                if title and len(title) > 2:
                    return title
        
        # 方法3: 从表格内容推断标题
        if headers and len(headers) > 0:
            # 分析表头内容，生成描述性标题
            first_header = headers[0].strip()
            if first_header and len(first_header) > 2:
                # 如果第一个表头看起来像标题，使用它
                if not re.search(r'^\d+$', first_header):  # 不是纯数字
                    return first_header
        
        # 方法4: 生成默认标题
        return f"数据表格 {table_id}"
    
    def _generate_table_summary(self, headers: List[str], rows: List[List[str]], table_title: str) -> str:
        """
        智能生成表格摘要
        :param headers: 表头列表
        :param rows: 数据行列表
        :param table_title: 表格标题
        :return: 表格摘要
        """
        summary_parts = []
        
        # 方法1: 从表头生成摘要
        if headers and len(headers) > 0:
            header_summary = " | ".join([h.strip() for h in headers if h.strip()])
            if header_summary:
                summary_parts.append(f"表头: {header_summary}")
        
        # 方法2: 从数据行生成摘要
        if rows and len(rows) > 0:
            # 分析前几行数据，提取关键信息
            for i, row in enumerate(rows[:3]):  # 取前3行
                if isinstance(row, list):
                    # 过滤空单元格，保留有意义的数据
                    meaningful_cells = [str(cell).strip() for cell in row if str(cell).strip() and len(str(cell).strip()) > 1]
                    if meaningful_cells:
                        row_summary = " | ".join(meaningful_cells[:3])  # 最多取3个单元格
                        summary_parts.append(f"行{i+1}: {row_summary}")
                else:
                    row_text = str(row).strip()
                    if row_text and len(row_text) > 1:
                        summary_parts.append(f"行{i+1}: {row_text}")
        
        # 方法3: 生成统计摘要
        if rows:
            summary_parts.append(f"数据规模: {len(rows)}行 {len(headers) if headers else 1}列")
        
        # 组合摘要
        if summary_parts:
            return " | ".join(summary_parts)
        else:
            return f"包含 {len(rows)} 行数据的{table_title}"
    
    def _generate_related_text(self, headers: List[str], rows: List[List[str]], table_title: str, table_type: str) -> str:
        """
        智能生成相关文本
        :param headers: 表头列表
        :param rows: 数据行列表
        :param table_title: 表格标题
        :param table_type: 表格类型
        :return: 相关文本
        """
        # 分析表格内容，生成描述性文本
        content_analysis = []
        
        # 分析表头特征
        if headers:
            header_count = len(headers)
            if header_count > 5:
                content_analysis.append("多列数据表格")
            elif header_count > 2:
                content_analysis.append("标准数据表格")
            else:
                content_analysis.append("简单数据表格")
        
        # 分析数据类型
        if rows and len(rows) > 0:
            # 检查是否包含数值数据
            has_numbers = False
            has_text = False
            
            for row in rows[:5]:  # 检查前5行
                if isinstance(row, list):
                    for cell in row:
                        cell_str = str(cell).strip()
                        if cell_str:
                            # 检查是否包含数字
                            if re.search(r'\d', cell_str):
                                has_numbers = True
                            # 检查是否包含文本
                            if re.search(r'[a-zA-Z\u4e00-\u9fff]', cell_str):
                                has_text = True
            
            if has_numbers and has_text:
                content_analysis.append("混合型数据")
            elif has_numbers:
                content_analysis.append("数值型数据")
            elif has_text:
                content_analysis.append("文本型数据")
        
        # 生成最终描述
        if content_analysis:
            description = "，".join(content_analysis)
            return f"{table_title}: {description}，包含 {len(rows)} 行 {len(headers) if headers else 1} 列信息"
        else:
            return f"{table_title}，{table_type}，包含 {len(rows)} 行 {len(headers) if headers else 1} 列信息"
    
    def process_tables(self, chunks: List[Document]) -> Optional[List[Document]]:
        """
        处理表格数据，进行高级表格处理
        :param chunks: 文档分块列表
        :return: 处理后的表格分块列表
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
            
            if not table_chunks:
                logger.info("没有找到表格数据")
                return None
            
            logger.info(f"找到 {len(table_chunks)} 个表格分块，开始高级处理")
            
            # 对每个表格分块进行高级处理
            processed_chunks = []
            chunk_generator = ConfigurableTableChunkGenerator(self.config)
            
            # 统计信息
            total_tables = len(table_chunks)
            split_tables = 0
            normal_tables = 0
            
            for chunk in table_chunks:
                try:
                    table_id = chunk.metadata.get('table_id', 'unknown')
                    # 跳过已经是子表的表格分块
                    if '_sub_' in table_id:
                        logger.info(f"跳过子表: {table_id}")
                        processed_chunks.append(chunk)
                        continue
                    # 获取表格内容
                    table_content = chunk.page_content
                    table_type = chunk.metadata.get('table_type', '未知表格')
                    
                    logger.info(f"处理表格: {table_id}, 类型: {table_type}")
                    
                    # 解析HTML表格，确保使用的是原始HTML内容
                    if 'page_content' in chunk.metadata:
                        original_content = chunk.metadata['page_content']
                    else:
                        original_content = table_content # table_content is chunk.page_content
                    table_info = self.parse_html_table(original_content, table_type)
                    if not table_info:
                        logger.warning(f"无法解析表格: {table_id}")
                        processed_chunks.append(chunk)
                        continue
                    
                    # 转换为结构化文本
                    table_text = self._table_to_structured_text(table_info, table_type)
                    logger.info(f"表格 {table_id} 转换为结构化文本，长度: {len(table_text)} 字符")
                    
                    # 检查是否需要拆分表格
                    chunk_size = self.config.get('chunk_size', 1000) if isinstance(self.config, dict) else getattr(self.config, 'chunk_size', 1000)
                    if len(table_text) > chunk_size:
                        logger.info(f"检测到大表: {table_id}, 内容长度: {len(table_text)} 超过Chunk大小 {chunk_size}，进行分表处理")
                        sub_tables = self._split_table_into_subtables_by_size(table_info, table_type, chunk_size)
                        
                        # 汇总子表信息，避免重复日志
                        sub_table_summary = []
                        for i, sub_table in enumerate(sub_tables):
                            sub_table_text = self._table_to_structured_text(sub_table, table_type)
                            sub_table_summary.append(f"子表{i+1}: {len(sub_table.rows)}行, {len(sub_table_text)}字符")
                            
                            processed_chunk = Document(
                                page_content=sub_table.html_content,  # 确保每个分块都存储原始HTML内容
                                metadata={
                                    **chunk.metadata,
                                    'processed_table_content': sub_table_text,
                                    'processed_table_id': sub_table.table_id if i == 0 else f"{sub_table.table_id}_sub_{i}",
                                    'processed_table_type': sub_table.table_type,
                                    'table_row_count': sub_table.row_count if i == 0 else len(sub_table.rows),
                                    'table_column_count': sub_table.column_count,
                                    'table_title': sub_table.title,
                                    'table_summary': sub_table.summary,
                                    'table_headers': sub_table.headers if sub_table.headers else [],
                                    'related_text': sub_table.related_text
                                }
                            )
                            processed_chunks.append(processed_chunk)
                        
                        # 输出汇总信息
                        logger.info(f"表格 {table_id} 拆分完成: {' | '.join(sub_table_summary)}")
                        logger.info(f"表格 {table_id} 处理完成，生成 {len(sub_tables)} 个分块")
                        split_tables += 1
                    else:
                        logger.info(f"表格 {table_id} 内容长度 {len(table_text)} 不超过Chunk大小 {chunk_size}，不进行分表处理")
                        processed_chunk = Document(
                            page_content=table_info.html_content,  # 确保存储原始HTML内容
                            metadata={
                                **chunk.metadata,
                                'processed_table_content': table_text,
                                'processed_table_id': table_info.table_id,
                                'processed_table_type': table_info.table_type,
                                'table_row_count': table_info.row_count,
                                'table_column_count': table_info.column_count,
                                'table_title': table_info.title,
                                'table_summary': table_info.summary,
                                'table_headers': table_info.headers if table_info.headers else [],
                                'related_text': table_info.related_text
                            }
                        )
                        processed_chunks.append(processed_chunk)
                        logger.info(f"表格 {table_id} 处理完成，生成 1 个分块")
                        normal_tables += 1
                except Exception as e:
                    logger.error(f"处理表格 {chunk.metadata.get('table_id', 'unknown')} 时出错: {e}")
                    processed_chunks.append(chunk)  # 保留原始分块
            
            # 输出处理统计信息
            logger.info(f"表格高级处理完成，处理了 {len(processed_chunks)} 个表格分块")
            logger.info(f"处理统计: 正常表格 {normal_tables} 个, 拆分表格 {split_tables} 个, 总计 {total_tables} 个")
            return processed_chunks
                
        except Exception as e:
            logger.error(f"表格处理失败: {e}")
            return None
    
    def _split_table_into_subtables_by_size(self, table_info: TableInfo, table_type: str, chunk_size: int) -> List[TableInfo]:
        """
        根据Chunk大小将大表拆分为多个子表
        :param table_info: 原始表格信息对象
        :param table_type: 表格类型
        :param chunk_size: Chunk大小阈值
        :return: 子表信息对象列表
        """
        sub_tables = []
        total_rows = len(table_info.rows)
        current_rows = []
        sub_table_count = 0
        
        # 估算头部信息长度（不包括数据行）
        header_text = self._table_to_structured_text(TableInfo(
            html_content="",
            table_id=table_info.table_id,
            table_type=table_info.table_type,
            rows=[],
            row_count=0,
            column_count=table_info.column_count,
            headers=table_info.headers,
            title=table_info.title if hasattr(table_info, 'title') else "",
            summary=table_info.summary if hasattr(table_info, 'summary') else ""
        ), table_info.table_type)
        header_length = len(header_text)
        
        # 估算每行平均长度
        if total_rows > 0:
            sample_text = self._table_to_structured_text(TableInfo(
                html_content="",
                table_id=table_info.table_id,
                table_type=table_info.table_type,
                rows=table_info.rows[:min(5, total_rows)],
                row_count=min(5, total_rows),
                column_count=table_info.column_count,
                headers=table_info.headers,
                title=table_info.title if hasattr(table_info, 'title') else "",
                summary=table_info.summary if hasattr(table_info, 'summary') else ""
            ), table_info.table_type)
            avg_row_length = (len(sample_text) - header_length) // min(5, total_rows)
        else:
            avg_row_length = 0
        
        # 确定每组子表的行数，确保内容长度低于chunk_size
        if avg_row_length > 0:
            target_rows_per_subtable = max(1, (chunk_size - header_length) // (avg_row_length * 2))
        else:
            target_rows_per_subtable = 10  # 默认值
        
        for i, row in enumerate(table_info.rows):
            current_rows.append(row)
            
            if len(current_rows) >= target_rows_per_subtable or i == total_rows - 1:
                sub_table_id = f"{table_info.table_id}_sub_{sub_table_count}"
                sub_table = TableInfo(
                    html_content=table_info.html_content,  # 保存原始HTML内容
                    table_id=sub_table_id,
                    table_type=table_info.table_type,
                    rows=current_rows,
                    row_count=len(current_rows),
                    column_count=table_info.column_count,
                    headers=table_info.headers,
                    title=table_info.title if hasattr(table_info, 'title') else "",
                    summary=f"{table_info.summary if hasattr(table_info, 'summary') else ''} (部分 {sub_table_count + 1})"
                )
                # 移除重复的日志输出，改为在调用方汇总显示
                sub_tables.append(sub_table)
                sub_table_count += 1
                current_rows = []
        
        return sub_tables


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
    
    def generate_table_chunks(self, table_info: TableInfo) -> List[str]:
        """
        生成表格分块
        :param table_info: 表格信息对象
        :return: 表格分块文本列表
        """
        chunks = []
        chunk_size = self.config.get('chunk_size', 1000) if hasattr(self.config, 'get') else getattr(self.config, 'chunk_size', 1000)
        
        # 转换为结构化文本
        table_text = self._table_to_structured_text(table_info, table_info.table_type)
        logger.info(f"表格 {table_info.table_id} 转换为结构化文本，长度: {len(table_text)} 字符")
        
        # 检查是否为空表格
        if not table_text.strip():
            logger.warning(f"表格 {table_info.table_id} 转换后为空")
            return [""]
        
        # 检查表格内容长度是否超过Chunk大小
        if len(table_text) > chunk_size:
            logger.info(f"检测到大表: {table_info.table_id}, 内容长度: {len(table_text)} 超过Chunk大小 {chunk_size}，进行分表处理")
            sub_tables = self._split_table_into_subtables_by_size(table_info, chunk_size)
            logger.info(f"表格 {table_info.table_id} 被拆分为 {len(sub_tables)} 个子表")
            for sub_table in sub_tables:
                sub_table_text = self._table_to_structured_text(sub_table, sub_table.table_type)
                chunks.append(sub_table_text)
            logger.info(f"表格 {table_info.table_id} 处理完成，生成 {len(chunks)} 个分块")
        else:
            logger.info(f"表格 {table_info.table_id} 内容长度 {len(table_text)} 不超过Chunk大小 {chunk_size}，不进行分表处理")
            chunks.append(table_text)
            logger.info(f"表格 {table_info.table_id} 处理完成，生成 1 个分块")
        
        return chunks
    
    def _split_table_into_subtables_by_size(self, table_info: TableInfo, chunk_size: int) -> List[TableInfo]:
        """
        根据Chunk大小将大表拆分为多个子表
        :param table_info: 原始表格信息对象
        :param chunk_size: Chunk大小阈值
        :return: 子表信息对象列表
        """
        sub_tables = []
        total_rows = len(table_info.rows)
        current_rows = []
        sub_table_count = 0
        
        # 估算头部信息长度（不包括数据行）
        header_text = self._table_to_structured_text(TableInfo(
            html_content="",
            table_id=table_info.table_id,
            table_type=table_info.table_type,
            rows=[],
            row_count=0,
            column_count=table_info.column_count,
            headers=table_info.headers,
            title=table_info.title if hasattr(table_info, 'title') else "",
            summary=table_info.summary if hasattr(table_info, 'summary') else ""
        ), table_info.table_type)
        header_length = len(header_text)
        
        # 估算每行平均长度
        if total_rows > 0:
            sample_text = self._table_to_structured_text(TableInfo(
                html_content="",
                table_id=table_info.table_id,
                table_type=table_info.table_type,
                rows=table_info.rows[:min(5, total_rows)],
                row_count=min(5, total_rows),
                column_count=table_info.column_count,
                headers=table_info.headers,
                title=table_info.title if hasattr(table_info, 'title') else "",
                summary=table_info.summary if hasattr(table_info, 'summary') else ""
            ), table_info.table_type)
            avg_row_length = (len(sample_text) - header_length) // min(5, total_rows)
        else:
            avg_row_length = 0
        
        # 确定每组子表的行数，确保内容长度低于chunk_size
        if avg_row_length > 0:
            target_rows_per_subtable = max(1, (chunk_size - header_length) // (avg_row_length * 2))
        else:
            target_rows_per_subtable = 10  # 默认值
        
        for i, row in enumerate(table_info.rows):
            current_rows.append(row)
            
            if len(current_rows) >= target_rows_per_subtable or i == total_rows - 1:
                sub_table_id = f"{table_info.table_id}_sub_{sub_table_count}"
                sub_table = TableInfo(
                    html_content="",
                    table_id=sub_table_id,
                    table_type=table_info.table_type,
                    rows=current_rows,
                    row_count=len(current_rows),
                    column_count=table_info.column_count,
                    headers=table_info.headers,
                    title=table_info.title if hasattr(table_info, 'title') else "",
                    summary=f"{table_info.summary if hasattr(table_info, 'summary') else ''} (部分 {sub_table_count + 1})"
                )
                # 移除重复的日志输出，改为在调用方汇总显示
                sub_tables.append(sub_table)
                sub_table_count += 1
                current_rows = []
        
        return sub_tables
    
    def _table_to_structured_text(self, table_info: TableInfo, table_type: str = "未知表格") -> str:
        """
        将表格信息转换为结构化文本
        :param table_info: 表格信息对象
        :param table_type: 表格类型
        :return: 结构化文本
        """
        try:
            # 生成表头
            headers = table_info.headers if table_info.headers else []
            header_text = " | ".join(headers) if headers else "(无表头)"
            
            # 生成表格内容
            rows_text = []
            for row in table_info.rows:
                if isinstance(row, list):
                    row_text = " | ".join([str(cell) for cell in row if str(cell).strip()])
                else:
                    row_text = str(row)
                if row_text:
                    rows_text.append(row_text)
            
            # 组合表头和内容
            table_text = header_text + "\n" + "\n".join(rows_text) if rows_text else header_text
            
            return table_text
        except Exception as e:
            logger.error(f"转换表格到结构化文本时出错: {e}")
            return "(表格内容转换失败)"



def process_tables_from_document_with_config(json_data: List[Dict[str, Any]], 
                                           document_name: str, 
                                           config: Dict[str, Any] = None) -> List[TableChunk]:
        """
        使用配置处理文档中的表格
        
        使用场景：
        1. 测试场景：用于验证表格处理功能的正确性
           - 在 tools/V557_table_processing_test.py 中用于测试表格解析和分块
           - 验证表格数据是否正确提取和结构化
        
        2. 独立表格处理：当需要单独处理文档中的表格内容时
           - 不依赖完整的文档处理流程
           - 专注于表格数据的提取和分块
        
        3. 调试场景：用于调试表格处理逻辑
           - 可以单独测试表格处理功能
           - 便于定位表格处理中的问题
        
        注意：此函数主要用于测试和调试，核心处理流程使用 TableProcessor 和 TableChunkGenerator 类
        
        :param json_data: JSON数据，包含文档的结构化内容
        :param document_name: 文档名称，用于标识表格来源
        :param config: 配置字典，包含表格处理参数
        :return: 表格分块列表，每个分块包含表格的结构化内容
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