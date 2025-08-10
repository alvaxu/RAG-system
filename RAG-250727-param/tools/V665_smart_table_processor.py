"""
程序说明：

## 1. 智能表格处理器 - 解决表格截断问题
## 2. 实现完整的表格内容提取，避免简单截断
## 3. 智能识别表格结构，保持数据完整性
"""

import json
import re
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartTableProcessor:
    """
    智能表格处理器类
    解决表格截断问题，实现完整的表格内容提取
    """
    
    def __init__(self, max_cell_length: int = 1000, max_table_size: int = 10000):
        """
        初始化智能表格处理器
        
        :param max_cell_length: 单个单元格最大长度限制
        :param max_table_size: 整个表格最大大小限制
        """
        self.max_cell_length = max_cell_length
        self.max_table_size = max_table_size
        
    def process_table_content(self, table_body: str) -> Dict[str, Any]:
        """
        智能处理表格内容，避免简单截断
        
        :param table_body: 原始表格HTML内容
        :return: 处理后的表格数据
        """
        try:
            # 解析HTML表格
            parsed_table = self._parse_html_table(table_body)
            
            # 智能分析表格结构
            table_analysis = self._analyze_table_structure(parsed_table)
            
            # 根据分析结果智能处理
            processed_table = self._smart_process_table(parsed_table, table_analysis)
            
            return {
                'original_size': len(table_body),
                'processed_size': len(str(processed_table)),
                'table_data': processed_table,
                'analysis': table_analysis,
                'processing_method': 'smart_processing'
            }
            
        except Exception as e:
            logger.error(f"表格处理失败: {e}")
            return {
                'error': str(e),
                'original_content': table_body[:500] + "..." if len(table_body) > 500 else table_body
            }
    
    def _parse_html_table(self, html_content: str) -> List[List[str]]:
        """
        解析HTML表格内容
        
        :param html_content: HTML表格内容
        :return: 解析后的表格数据
        """
        # 移除HTML标签，提取纯文本内容
        clean_content = re.sub(r'<[^>]+>', '', html_content)
        
        # 分割行
        rows = [row.strip() for row in clean_content.split('\n') if row.strip()]
        
        # 解析表格结构
        table_data = []
        for row in rows:
            # 智能分割单元格，考虑多种分隔符
            cells = self._smart_split_cells(row)
            if cells:
                table_data.append(cells)
        
        return table_data
    
    def _smart_split_cells(self, row_text: str) -> List[str]:
        """
        智能分割表格行中的单元格
        
        :param row_text: 行文本
        :return: 分割后的单元格列表
        """
        # 尝试多种分割方式
        separators = ['\t', '|', '  ', '    ']  # 制表符、竖线、双空格、四空格
        
        for sep in separators:
            if sep in row_text:
                cells = [cell.strip() for cell in row_text.split(sep) if cell.strip()]
                if len(cells) > 1:
                    return cells
        
        # 如果没有找到明显的分隔符，尝试智能分割
        return self._intelligent_cell_split(row_text)
    
    def _intelligent_cell_split(self, text: str) -> List[str]:
        """
        智能分割没有明显分隔符的文本
        
        :param text: 待分割的文本
        :return: 分割后的单元格列表
        """
        # 基于数字、货币符号、百分比等特征进行智能分割
        patterns = [
            r'(\d+\.?\d*%)',  # 百分比
            r'(\d+\.?\d*[万亿]?)',  # 数字+单位
            r'([A-Za-z]+)',  # 英文单词
            r'([\u4e00-\u9fff]+)',  # 中文字符
        ]
        
        cells = []
        current_pos = 0
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                if match.start() >= current_pos:
                    # 添加匹配前的文本作为单元格
                    if match.start() > current_pos:
                        cell_text = text[current_pos:match.start()].strip()
                        if cell_text:
                            cells.append(cell_text)
                    
                    # 添加匹配的文本作为单元格
                    cells.append(match.group())
                    current_pos = match.end()
        
        # 添加剩余的文本
        if current_pos < len(text):
            remaining = text[current_pos:].strip()
            if remaining:
                cells.append(remaining)
        
        return cells if cells else [text]
    
    def _analyze_table_structure(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """
        分析表格结构特征
        
        :param table_data: 表格数据
        :return: 表格结构分析结果
        """
        if not table_data:
            return {'error': '空表格'}
        
        analysis = {
            'row_count': len(table_data),
            'column_count': max(len(row) for row in table_data) if table_data else 0,
            'has_header': False,
            'data_types': [],
            'content_patterns': []
        }
        
        # 分析第一行是否为表头
        if table_data:
            first_row = table_data[0]
            # 检查第一行是否包含典型的表头特征
            header_indicators = ['单位', '指标', '项目', '名称', '年份', '年度', '季度']
            analysis['has_header'] = any(indicator in str(cell) for cell in first_row)
        
        # 分析数据类型
        for row in table_data:
            for cell in row:
                cell_type = self._detect_cell_type(cell)
                if cell_type not in analysis['data_types']:
                    analysis['data_types'].append(cell_type)
        
        # 识别内容模式
        analysis['content_patterns'] = self._identify_content_patterns(table_data)
        
        return analysis
    
    def _detect_cell_type(self, cell: str) -> str:
        """
        检测单元格数据类型
        
        :param cell: 单元格内容
        :return: 数据类型
        """
        cell = str(cell).strip()
        
        if not cell:
            return 'empty'
        elif re.match(r'^\d+\.?\d*%$', cell):
            return 'percentage'
        elif re.match(r'^\d+\.?\d*$', cell):
            return 'number'
        elif re.match(r'^\d+\.?\d*[万亿]?$', cell):
            return 'number_with_unit'
        elif re.match(r'^[\u4e00-\u9fff]+$', cell):
            return 'chinese_text'
        elif re.match(r'^[A-Za-z\s]+$', cell):
            return 'english_text'
        else:
            return 'mixed'
    
    def _identify_content_patterns(self, table_data: List[List[str]]) -> List[str]:
        """
        识别表格内容模式
        
        :param table_data: 表格数据
        :return: 识别出的内容模式列表
        """
        patterns = []
        
        # 检查是否包含财务数据
        financial_indicators = ['营业收入', '净利润', '毛利率', '资产负债', '现金流量']
        if any(any(indicator in str(cell) for cell in row) for row in table_data):
            patterns.append('financial_data')
        
        # 检查是否包含时间序列数据
        time_indicators = ['2023', '2024', '2025', 'Q1', 'Q2', 'Q3', 'Q4']
        if any(any(indicator in str(cell) for cell in row) for row in table_data):
            patterns.append('time_series')
        
        # 检查是否包含比较数据
        if any('vs' in str(cell).lower() or '比较' in str(cell) for row in table_data for cell in row):
            patterns.append('comparison_data')
        
        return patterns
    
    def _smart_process_table(self, table_data: List[List[str]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据分析结果智能处理表格
        
        :param table_data: 原始表格数据
        :param analysis: 表格分析结果
        :return: 处理后的表格数据
        """
        processed_table = {
            'structure': analysis,
            'data': [],
            'summary': {}
        }
        
        # 根据表格类型选择处理策略
        if 'financial_data' in analysis['content_patterns']:
            processed_table = self._process_financial_table(table_data, analysis)
        elif 'time_series' in analysis['content_patterns']:
            processed_table = self._process_time_series_table(table_data, analysis)
        else:
            processed_table = self._process_general_table(table_data, analysis)
        
        return processed_table
    
    def _process_financial_table(self, table_data: List[List[str]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理财务数据表格
        
        :param table_data: 表格数据
        :param analysis: 分析结果
        :return: 处理后的财务表格
        """
        processed = {
            'type': 'financial_table',
            'data': table_data,
            'key_metrics': [],
            'trends': []
        }
        
        # 提取关键财务指标
        for row in table_data:
            for cell in row:
                if any(metric in str(cell) for metric in ['收入', '利润', '毛利率', '净利率']):
                    processed['key_metrics'].append(str(cell))
        
        return processed
    
    def _process_time_series_table(self, table_data: List[List[str]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理时间序列数据表格
        
        :param table_data: 表格数据
        :param analysis: 分析结果
        :return: 处理后的时间序列表格
        """
        processed = {
            'type': 'time_series_table',
            'data': table_data,
            'time_periods': [],
            'metrics': []
        }
        
        # 提取时间周期
        for row in table_data:
            for cell in row:
                if re.search(r'\d{4}', str(cell)) or any(q in str(cell) for q in ['Q1', 'Q2', 'Q3', 'Q4']):
                    processed['time_periods'].append(str(cell))
        
        return processed
    
    def _process_general_table(self, table_data: List[List[str]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理通用表格
        
        :param table_data: 表格数据
        :param analysis: 分析结果
        :return: 处理后的通用表格
        """
        return {
            'type': 'general_table',
            'data': table_data,
            'row_count': analysis['row_count'],
            'column_count': analysis['column_count']
        }

def test_smart_table_processor():
    """
    测试智能表格处理器
    """
    processor = SmartTableProcessor()
    
    # 测试用例1：财务数据表格
    test_table1 = """
    <table>
    <tr><td>指标</td><td>2023</td><td>2024</td><td>2025E</td></tr>
    <tr><td>营业收入</td><td>6,322</td><td>8,030</td><td>9,612</td></tr>
    <tr><td>净利润</td><td>903</td><td>493</td><td>793</td></tr>
    </table>
    """
    
    result1 = processor.process_table_content(test_table1)
    print("测试结果1 - 财务表格:")
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    
    # 测试用例2：复杂表格
    test_table2 = """
    <table>
    <tr><td>项目</td><td>Q1 2024</td><td>Q2 2024</td><td>Q3 2024</td><td>Q4 2024</td></tr>
    <tr><td>晶圆出货量</td><td>1,234</td><td>1,456</td><td>1,678</td><td>1,890</td></tr>
    <tr><td>平均售价</td><td>$1,234</td><td>$1,345</td><td>$1,456</td><td>$1,567</td></tr>
    </table>
    """
    
    result2 = processor.process_table_content(test_table2)
    print("\n测试结果2 - 复杂表格:")
    print(json.dumps(result2, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_smart_table_processor()
