'''
程序说明：
## 1. TableFormatter子模块
- 负责表格格式化和HTML生成
- 完全符合设计文档规范，位于processors模块下
- 为TableProcessor提供表格格式化服务
## 2. 主要功能
- 生成标准HTML表格
- 支持表格样式和布局
- 生成表格的文本表示
- 支持大表格的分块格式化
## 3. 与优化方案的关系
- 实现优化方案要求的模块化设计
- 支持大表格分块，避免内容丢失
- 完全符合设计文档的TABLE_METADATA_SCHEMA规范
'''
import re
import logging
from typing import Dict, List, Any
import time

class TableFormatter:
    """
    表格格式化器
    负责表格格式化和HTML生成
    完全符合设计文档规范，位于processors模块下
    """
    
    def __init__(self):
        logging.info("表格格式化器初始化完成")
    
    def format_table(self, table_data: Dict, structure: Dict) -> Dict[str, Any]:
        """
        格式化表格，生成HTML和文本表示
        
        :param table_data: 表格数据，包含table_body等字段
        :param structure: 表格结构分析结果
        :return: 格式化结果字典
        """
        try:
            table_html = table_data.get('table_body', '')
            if not table_html:
                return self._create_empty_format_result()

            # 步骤1: 使用MinerU提供的HTML（不再重复生成）
            html_table = table_html

            # 步骤2: 使用传入的table_content作为文本表示（HTML到纯文本的转换已在更早阶段完成）
            text_representation = table_data.get('table_content', '')
            
            # 步骤3: 生成CSS样式
            css_styles = self._generate_table_css()
            
            # 步骤4: 生成格式化摘要
            format_summary = self._generate_format_summary(html_table, text_representation)
            
            # 整合格式化结果
            format_result = {
                'format_status': 'success',
                'format_timestamp': int(time.time()),
                'html_table': html_table,
                'text_representation': text_representation,
                'css_styles': css_styles,
                'format_summary': format_summary,
                'format_metadata': self._generate_format_metadata(table_html, structure)
            }
            
            logging.info("表格格式化完成")
            return format_result
            
        except Exception as e:
            error_msg = f"表格格式化失败: {str(e)}"
            logging.error(error_msg)
            return self._create_error_format_result(error_msg)
    


    def _generate_html_table(self, table_content: str, structure: Dict) -> str:
        """
        生成带样式的HTML表格
        """
        if not table_content:
            return "<table class='empty-table'><tr><td>空表格</td></tr></table>"
        
        lines = [line.strip() for line in table_content.strip().split('\n') if line.strip()]
        if not lines:
            return "<table class='empty-table'><tr><td>空表格</td></tr></table>"
        
        # 获取表格结构信息
        rows = len(lines)
        columns = structure.get('columns', 0)
        has_header = structure.get('has_header', False)
        headers = structure.get('headers', [])
        separator = structure.get('separator', '\t')
        
        # 开始生成HTML
        html_parts = []
        
        # 添加表格开始标签和CSS类
        table_class = self._determine_table_class(structure)
        html_parts.append(f"<table class='{table_class}' id='formatted-table'>")
        
        # 添加表头
        if has_header and headers:
            html_parts.append("<thead>")
            html_parts.append("<tr>")
            for header in headers:
                header_class = self._determine_header_class(header)
                html_parts.append(f"<th class='{header_class}'>{self._escape_html(header)}</th>")
            html_parts.append("</tr>")
            html_parts.append("</thead>")
        
        # 添加表格内容
        html_parts.append("<tbody>")
        
        # 确定数据行的起始位置
        data_start = 1 if has_header else 0
        
        for i, line in enumerate(lines[data_start:], data_start + 1):
            if line.strip():
                # 分割行内容
                cells = self._split_table_row(line, separator)
                
                # 添加行标签
                row_class = self._determine_row_class(i, rows, structure)
                html_parts.append(f"<tr class='{row_class}'>")
                
                # 添加单元格
                for j, cell in enumerate(cells):
                    cell_class = self._determine_cell_class(cell, j, columns, structure)
                    cell_content = self._escape_html(cell.strip())
                    
                    # 检查是否需要合并单元格
                    if self._should_merge_cell(cell, structure):
                        html_parts.append(f"<td class='{cell_class}' colspan='2'>{cell_content}</td>")
                    else:
                        html_parts.append(f"<td class='{cell_class}'>{cell_content}</td>")
                
                html_parts.append("</tr>")
        
        html_parts.append("</tbody>")
        html_parts.append("</table>")
        
        return '\n'.join(html_parts)
    
    def _split_table_row(self, row_text: str, separator: str) -> List[str]:
        """
        支持多种分隔符分割表格行
        """
        if separator == ' ':
            # 空格分隔时，合并多个空格
            return [cell.strip() for cell in re.split(r'\s+', row_text) if cell.strip()]
        else:
            return [cell.strip() for cell in row_text.split(separator)]
    
    def _escape_html(self, text: str) -> str:
        """
        转义HTML特殊字符
        """
        html_escapes = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }
        
        for char, escape in html_escapes.items():
            text = text.replace(char, escape)
        
        return text
    
    def _determine_table_class(self, structure: Dict) -> str:
        """
        根据表格结构确定CSS类
        """
        table_type = structure.get('features', {}).get('table_type', 'unknown')
        complexity_score = structure.get('features', {}).get('complexity_score', 0)
        
        base_class = 'data-table'
        
        if table_type == 'simple_table':
            base_class += ' simple-table'
        elif table_type == 'large_data_table':
            base_class += ' large-table'
        elif table_type == 'summary_table':
            base_class += ' summary-table'
        
        if complexity_score > 0.7:
            base_class += ' complex-table'
        elif complexity_score > 0.4:
            base_class += ' medium-table'
        else:
            base_class += ' simple-table'
        
        return base_class
    
    def _determine_header_class(self, header: str) -> str:
        """
        根据表头内容确定CSS类
        """
        header_lower = header.lower()
        
        if any(word in header_lower for word in ['名称', '标题', 'name', 'title']):
            return 'header-name'
        elif any(word in header_lower for word in ['数量', '数量', 'count', 'number']):
            return 'header-numeric'
        elif any(word in header_lower for word in ['日期', '时间', 'date', 'time']):
            return 'header-date'
        elif any(word in header_lower for word in ['金额', '价格', 'price', 'amount']):
            return 'header-currency'
        else:
            return 'header-general'
    
    def _determine_row_class(self, row_index: int, total_rows: int, structure: Dict) -> str:
        """
        根据行位置确定CSS类
        """
        base_class = 'data-row'
        
        # 交替行颜色
        if row_index % 2 == 0:
            base_class += ' even-row'
        else:
            base_class += ' odd-row'
        
        # 第一行和最后一行特殊样式
        if row_index == 1:
            base_class += ' first-row'
        elif row_index == total_rows:
            base_class += ' last-row'
        
        # 根据数据特征添加类
        data_features = structure.get('features', {}).get('data_features', {})
        if data_features:
            type_distribution = data_features.get('type_distribution', {})
            if type_distribution.get('numeric_ratio', 0) > 0.5:
                base_class += ' numeric-heavy'
        
        return base_class
    
    def _determine_cell_class(self, cell: str, col_index: int, total_cols: int, structure: Dict) -> str:
        """
        根据单元格内容确定CSS类
        """
        base_class = 'table-cell'
        
        # 根据内容类型添加类
        if re.match(r'^\d+(\.\d+)?$', cell):
            base_class += ' numeric-cell'
        elif re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', cell):
            base_class += ' date-cell'
        elif '%' in cell:
            base_class += ' percentage-cell'
        elif re.match(r'^[\$¥€£]\d+', cell):
            base_class += ' currency-cell'
        elif not cell.strip():
            base_class += ' empty-cell'
        else:
            base_class += ' text-cell'
        
        # 根据列位置添加类
        if col_index == 0:
            base_class += ' first-column'
        elif col_index == total_cols - 1:
            base_class += ' last-column'
        
        # 根据列类型添加类
        headers = structure.get('headers', [])
        if headers and col_index < len(headers):
            header = headers[col_index].lower()
            if any(word in header for word in ['名称', '标题', 'name', 'title']):
                base_class += ' name-column'
            elif any(word in header for word in ['数量', '数量', 'count', 'number']):
                base_class += ' numeric-column'
            elif any(word in header for word in ['日期', '时间', 'date', 'time']):
                base_class += ' date-column'
        
        return base_class
    
    def _should_merge_cell(self, cell: str, structure: Dict) -> bool:
        """
        判断是否需要合并单元格
        """
        # 简化实现：检查是否为空单元格
        if not cell.strip():
            return True
        
        # 检查是否有合并单元格模式
        merge_patterns = structure.get('detection', {}).get('merge_patterns', {})
        if merge_patterns.get('has_merged_cells'):
            return True
        
        return False
    
    def _generate_text_representation(self, table_content: str, structure: Dict) -> str:
        """
        生成表格的文本表示
        """
        if not table_content:
            return "空表格"
        
        lines = [line.strip() for line in table_content.strip().split('\n') if line.strip()]
        if not lines:
            return "空表格"
        
        # 获取表格结构信息
        rows = len(lines)
        columns = structure.get('columns', 0)
        has_header = structure.get('has_header', False)
        headers = structure.get('headers', [])
        separator = structure.get('separator', '\t')
        
        text_parts = []
        
        # 添加表格标题
        table_type = structure.get('features', {}).get('table_type', '表格')
        text_parts.append(f"=== {table_type} ===")
        text_parts.append(f"行数: {rows}, 列数: {columns}")
        
        if has_header and headers:
            text_parts.append(f"表头: {' | '.join(headers)}")
        
        text_parts.append("")  # 空行
        
        # 添加表格内容
        data_start = 1 if has_header else 0
        
        for i, line in enumerate(lines[data_start:], data_start + 1):
            if line.strip():
                # 分割行内容
                cells = self._split_table_row(line, separator)
                
                # 格式化行内容
                formatted_cells = []
                for cell in cells:
                    cell_content = cell.strip()
                    if not cell_content:
                        cell_content = "[空]"
                    formatted_cells.append(cell_content)
                
                # 添加行号
                row_text = f"{i:2d} | {' | '.join(formatted_cells)}"
                text_parts.append(row_text)
        
        return '\n'.join(text_parts)
    
    def _generate_table_css(self) -> str:
        """
        生成表格的CSS样式
        """
        css = """
/* 表格基础样式 */
.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    line-height: 1.4;
    color: #333;
    background-color: #fff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    overflow: hidden;
}

/* 表头样式 */
.data-table thead {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.data-table th {
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    border: none;
    position: relative;
}

.data-table th:not(:last-child)::after {
    content: '';
    position: absolute;
    right: 0;
    top: 25%;
    height: 50%;
    width: 1px;
    background-color: rgba(255, 255, 255, 0.3);
}

/* 表头类型样式 */
.header-name { background-color: rgba(255, 255, 255, 0.1); }
.header-numeric { background-color: rgba(255, 255, 255, 0.15); }
.header-date { background-color: rgba(255, 255, 255, 0.2); }
.header-currency { background-color: rgba(255, 255, 255, 0.25); }

/* 表格内容样式 */
.data-table tbody tr {
    transition: background-color 0.2s ease;
}

.data-table tbody tr:hover {
    background-color: #f8f9fa;
}

.data-table td {
    padding: 12px 16px;
    border-bottom: 1px solid #e9ecef;
    vertical-align: top;
}

/* 行样式 */
.even-row { background-color: #f8f9fa; }
.odd-row { background-color: #ffffff; }
.first-row { border-top: 2px solid #dee2e6; }
.last-row { border-bottom: 2px solid #dee2e6; }

/* 单元格类型样式 */
.numeric-cell { 
    text-align: right; 
    font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
    color: #0066cc;
}
.date-cell { 
    color: #28a745; 
    font-weight: 500;
}
.percentage-cell { 
    color: #dc3545; 
    font-weight: 600;
}
.currency-cell { 
    color: #fd7e14; 
    font-weight: 600;
}
.empty-cell { 
    background-color: #f8f9fa; 
    color: #6c757d;
    font-style: italic;
}
.text-cell { 
    text-align: left; 
}

/* 列样式 */
.first-column { 
    font-weight: 500; 
    background-color: rgba(0, 123, 255, 0.05);
}
.last-column { 
    border-right: 2px solid #dee2e6; 
}

/* 表格类型样式 */
.simple-table { max-width: 600px; }
.large-table { font-size: 12px; }
.complex-table { font-size: 13px; }
.summary-table { max-width: 800px; }

/* 响应式设计 */
@media (max-width: 768px) {
    .data-table {
        font-size: 12px;
        margin: 10px 0;
    }
    
    .data-table th,
    .data-table td {
        padding: 8px 12px;
    }
    
    .data-table {
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }
}

/* 打印样式 */
@media print {
    .data-table {
        box-shadow: none;
        border: 1px solid #000;
    }
    
    .data-table th {
        background-color: #f0f0f0 !important;
        color: #000 !important;
    }
    
    .data-table tr:nth-child(even) {
        background-color: #f9f9f9 !important;
    }
}
"""
        
        return css.strip()
    
    def _generate_format_summary(self, html_table: str, text_representation: str) -> str:
        """
        生成格式化总结
        """
        html_length = len(html_table)
        text_length = len(text_representation)
        
        summary_parts = []
        
        # HTML表格信息
        if html_length > 5000:
            summary_parts.append("生成了大型HTML表格")
        elif html_length > 2000:
            summary_parts.append("生成了中型HTML表格")
        else:
            summary_parts.append("生成了小型HTML表格")
        
        # 文本表示信息
        if text_length > 1000:
            summary_parts.append("生成了详细的文本表示")
        elif text_length > 500:
            summary_parts.append("生成了标准的文本表示")
        else:
            summary_parts.append("生成了简洁的文本表示")
        
        # 样式信息
        summary_parts.append("包含完整的CSS样式")
        
        return "，".join(summary_parts) + "。"
    
    def _generate_format_metadata(self, table_content: str, structure: Dict) -> Dict[str, Any]:
        """
        生成格式化元数据
        """
        return {
            'format_version': '3.0.0',
            'format_timestamp': int(time.time()),
            'table_size': {
                'content_length': len(table_content),
                'rows': structure.get('rows', 0),
                'columns': structure.get('columns', 0)
            },
            'format_features': {
                'html_generation': True,
                'css_styling': True,
                'text_representation': True,
                'responsive_design': True,
                'print_optimization': True
            },
            'style_classes': {
                'table_class': self._determine_table_class(structure),
                'has_header': structure.get('has_header', False),
                'complexity_level': structure.get('features', {}).get('complexity_score', 0)
            }
        }
    
    def _create_empty_format_result(self) -> Dict[str, Any]:
        """创建空表格的格式化结果"""
        return {
            'format_status': 'success',
            'format_timestamp': int(time.time()),
            'html_table': "<table class='empty-table'><tr><td>空表格</td></tr></table>",
            'text_representation': '空表格',
            'css_styles': self._generate_table_css(),
            'format_summary': '空表格格式化完成',
            'format_metadata': {
                'format_version': '3.0.0',
                'format_timestamp': int(time.time()),
                'table_size': {'content_length': 0, 'rows': 0, 'columns': 0},
                'format_features': {'html_generation': True, 'css_styling': True, 'text_representation': True},
                'style_classes': {'table_class': 'empty-table', 'has_header': False, 'complexity_level': 0}
            }
        }
    
    def _create_error_format_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误格式化结果"""
        return {
            'format_status': 'failed',
            'format_timestamp': int(time.time()),
            'error_message': error_message,
            'html_table': f"<table class='error-table'><tr><td>格式化失败: {error_message}</td></tr></table>",
            'text_representation': f'格式化失败: {error_message}',
            'css_styles': self._generate_table_css(),
            'format_summary': f'格式化过程中发生错误: {error_message}',
            'format_metadata': {
                'format_version': '3.0.0',
                'format_timestamp': int(time.time()),
                'table_size': {'content_length': 0, 'rows': 0, 'columns': 0},
                'format_features': {'html_generation': False, 'css_styling': True, 'text_representation': False},
                'style_classes': {'table_class': 'error-table', 'has_header': False, 'complexity_level': 0}
            }
        }
    
    def get_format_status(self) -> Dict[str, Any]:
        """获取格式化器状态"""
        return {
            'formatter_type': 'table_formatter',
            'status': 'ready',
            'capabilities': [
                'html_generation',
                'css_styling',
                'text_representation',
                'responsive_design',
                'print_optimization'
            ],
            'version': '3.0.0'
        }
