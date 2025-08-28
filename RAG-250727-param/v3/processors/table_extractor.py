'''
程序说明：
## 1. TableExtractor子模块
- 负责表格内容提取，包括文本内容、结构化信息等
- 完全符合设计文档规范，位于processors模块下
- 为TableProcessor提供表格内容提取服务
## 2. 主要功能
- 提取表格的文本内容和结构化信息
- 支持大表格的智能分块处理
- 提取表格的相关文本和上下文信息
- 为后续处理提供内容数据
## 3. 与优化方案的关系
- 实现优化方案要求的模块化设计
- 支持大表格分块，避免内容丢失
- 完全符合设计文档的TABLE_METADATA_SCHEMA规范
'''
import re
import logging
from typing import Dict, List, Any
import time

class TableExtractor:
    """
    表格提取器
    负责表格内容提取，包括文本内容、结构化信息等
    完全符合设计文档规范，位于processors模块下
    """
    
    def __init__(self):
        logging.info("表格提取器初始化完成")
    
    def extract(self, table_data: Dict, structure: Dict) -> Dict[str, Any]:
        """
        提取表格的文本内容、结构化信息、相关文本和上下文信息
        
        :param table_data: 表格数据，包含table_body等字段
        :param structure: 表格结构分析结果
        :return: 提取结果字典
        """
        try:
            # 优先从table_body获取HTML数据，如果没有则从table_content获取
            table_html = table_data.get('table_body', '')
            table_content = table_data.get('table_content', '')
            
            if not table_html and not table_content:
                return self._create_empty_extraction_result()
            
            # 如果有HTML数据，先转换为纯文本
            if table_html:
                # 使用简单的HTML文本提取，避免重复定义
                import re
                table_content = re.sub(r'<[^>]+>', ' ', table_html)
                table_content = re.sub(r'\s+', ' ', table_content).strip()
            
            # 步骤1: 基础内容提取
            basic_content = self._extract_basic_content(table_content, structure)
            
            # 步骤2: 智能分块处理
            chunked_content = self._extract_table_chunks(table_content, structure)
            
            # 步骤3: 相关文本提取
            related_text = self._extract_related_text(table_data)
            
            # 步骤4: 上下文信息提取
            context_info = self._extract_context_info(table_data, structure)
            
            # 步骤5: 生成表格摘要
            table_summary = self._generate_table_summary(table_content, structure)
            
            # 整合提取结果
            extraction_result = {
                'extraction_status': 'success',
                'extraction_timestamp': int(time.time()),
                'basic_content': basic_content,
                'chunked_content': chunked_content,
                'related_text': related_text,
                'context_info': context_info,
                'table_summary': table_summary,
                'extraction_summary': self._generate_extraction_summary(basic_content, chunked_content),
                # 新增：纯文本内容，用于向量化
                'table_content': table_content
            }
            
            logging.info(f"表格内容提取完成: {len(chunked_content)} 个分块")
            return extraction_result
            
        except Exception as e:
            error_msg = f"表格内容提取失败: {str(e)}"
            logging.error(error_msg)
            return self._create_error_extraction_result(error_msg)
    
    def _extract_basic_content(self, table_content: str, structure: Dict) -> Dict[str, Any]:
        """
        提取表格的基础内容信息
        """
        if not table_content:
            return {}
        
        lines = [line.strip() for line in table_content.strip().split('\n') if line.strip()]
        rows = len(lines)
        columns = structure.get('columns', 0)
        separator = structure.get('separator', '\t')
        
        # 提取所有单元格内容
        all_cells = []
        for line in lines:
            cells = self._split_table_row(line, separator)
            all_cells.extend(cells)
        
        # 统计内容信息
        non_empty_cells = [cell for cell in all_cells if cell.strip()]
        empty_cells = [cell for cell in all_cells if not cell.strip()]
        
        # 计算内容统计
        total_cells = len(all_cells)
        non_empty_count = len(non_empty_cells)
        empty_count = len(empty_cells)
        
        # 提取文本内容
        text_content = ' '.join(non_empty_cells)
        
        # 计算内容特征
        avg_cell_length = sum(len(cell) for cell in non_empty_cells) / non_empty_cells if non_empty_cells else 0
        max_cell_length = max(len(cell) for cell in non_empty_cells) if non_empty_cells else 0
        min_cell_length = min(len(cell) for cell in non_empty_cells) if non_empty_cells else 0
        
        return {
            'text_content': text_content,
            'row_count': rows,
            'column_count': columns,
            'total_cells': total_cells,
            'non_empty_cells': non_empty_count,
            'empty_cells': empty_count,
            'fill_rate': non_empty_count / total_cells if total_cells > 0 else 0,
            'avg_cell_length': avg_cell_length,
            'max_cell_length': max_cell_length,
            'min_cell_length': min_cell_length,
            'content_diversity': self._calculate_content_diversity(non_empty_cells)
        }
    
    def _split_table_row(self, row_text: str, separator: str) -> List[str]:
        """
        支持多种分隔符分割表格行
        """
        if separator == ' ':
            # 空格分隔时，合并多个空格
            return [cell.strip() for cell in re.split(r'\s+', row_text) if cell.strip()]
        else:
            return [cell.strip() for cell in row_text.split(separator)]
    
    def _calculate_content_diversity(self, cells: List[str]) -> Dict[str, Any]:
        """
        计算内容多样性指标
        """
        if not cells:
            return {'unique_ratio': 0, 'common_patterns': []}
        
        # 计算唯一内容比例
        unique_cells = set(cells)
        unique_ratio = len(unique_cells) / len(cells)
        
        # 检测常见模式
        common_patterns = self._detect_common_patterns(cells)
        
        return {
            'unique_ratio': unique_ratio,
            'unique_count': len(unique_cells),
            'total_count': len(cells),
            'common_patterns': common_patterns,
            'diversity_score': unique_ratio
        }
    
    def _detect_common_patterns(self, cells: List[str]) -> List[Dict[str, Any]]:
        """
        检测常见的内容模式
        """
        patterns = []
        
        # 检测数字模式
        numeric_cells = [cell for cell in cells if re.match(r'^\d+(\.\d+)?$', cell)]
        if numeric_cells:
            patterns.append({
                'type': 'numeric',
                'count': len(numeric_cells),
                'ratio': len(numeric_cells) / len(cells),
                'examples': numeric_cells[:3]  # 前3个例子
            })
        
        # 检测日期模式
        date_cells = [cell for cell in cells if re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', cell)]
        if date_cells:
            patterns.append({
                'type': 'date',
                'count': len(date_cells),
                'ratio': len(date_cells) / len(cells),
                'examples': date_cells[:3]
            })
        
        # 检测百分比模式
        percent_cells = [cell for cell in cells if '%' in cell]
        if percent_cells:
            patterns.append({
                'type': 'percentage',
                'count': len(percent_cells),
                'ratio': len(percent_cells) / len(cells),
                'examples': percent_cells[:3]
            })
        
        # 检测货币模式
        currency_cells = [cell for cell in cells if re.match(r'^[\$¥€£]\d+', cell)]
        if currency_cells:
            patterns.append({
                'type': 'currency',
                'count': len(currency_cells),
                'ratio': len(currency_cells) / len(cells),
                'examples': currency_cells[:3]
            })
        
        return patterns
    
    def _extract_table_chunks(self, table_content: str, structure: Dict, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """
        智能分块大表格内容
        """
        if not table_content:
            return []
        
        lines = [line.strip() for line in table_content.strip().split('\n') if line.strip()]
        rows = len(lines)
        columns = structure.get('columns', 0)
        separator = structure.get('separator', '\t')
        
        # 如果表格较小，不需要分块
        if len(table_content) <= chunk_size:
            return [{
                'chunk_id': 'chunk_0',
                'chunk_index': 0,
                'start_row': 0,
                'end_row': rows - 1,
                'content': table_content,
                'chunk_size': len(table_content),
                'is_subchunk': False,
                'row_count': rows,
                'column_count': columns
            }]
        
        # 智能分块：在行边界分割
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        start_row = 0
        
        for i, line in enumerate(lines):
            line_length = len(line)
            
            # 如果当前块加上新行会超过限制，且当前块不为空
            if current_length + line_length > chunk_size and current_chunk:
                # 保存当前块
                chunk_content = '\n'.join(current_chunk)
                chunks.append({
                    'chunk_id': f'chunk_{chunk_index}',
                    'chunk_index': chunk_index,
                    'start_row': start_row,
                    'end_row': i - 1,
                    'content': chunk_content,
                    'chunk_size': len(chunk_content),
                    'is_subchunk': len(chunks) > 0,
                    'row_count': len(current_chunk),
                    'column_count': columns
                })
                
                # 开始新块
                current_chunk = [line]
                current_length = line_length
                chunk_index += 1
                start_row = i
            else:
                current_chunk.append(line)
                current_length += line_length
        
        # 添加最后一个块
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append({
                'chunk_id': f'chunk_{chunk_index}',
                'chunk_index': chunk_index,
                'start_row': start_row,
                'end_row': rows - 1,
                'content': chunk_content,
                'chunk_size': len(chunk_content),
                'is_subchunk': len(chunks) > 0,
                'row_count': len(current_chunk),
                'column_count': columns
            })
        
        return chunks if chunks else [{
            'chunk_id': 'chunk_0',
            'chunk_index': 0,
            'start_row': 0,
            'end_row': rows - 1,
            'content': table_content,
            'chunk_size': len(table_content),
            'is_subchunk': False,
            'row_count': rows,
            'column_count': columns
        }]
    
    def _extract_related_text(self, table_data: Dict) -> str:
        """
        提取表格相关的文本信息
        """
        related_text_parts = []
        
        # 提取表格标题
        table_title = table_data.get('table_title', '')
        if table_title:
            related_text_parts.append(f"表格标题: {table_title}")
        
        # 提取表格描述
        table_description = table_data.get('table_description', '')
        if table_description:
            related_text_parts.append(f"表格描述: {table_description}")
        
        # 提取相关文本块
        related_text_chunks = table_data.get('related_text_chunks', [])
        if related_text_chunks:
            for chunk in related_text_chunks[:3]:  # 只取前3个
                chunk_content = chunk.get('content', '')
                if chunk_content:
                    related_text_parts.append(f"相关文本: {chunk_content[:100]}...")
        
        # 提取上下文信息
        context_info = table_data.get('context_info', {})
        if context_info:
            for key, value in context_info.items():
                if value and isinstance(value, str):
                    related_text_parts.append(f"{key}: {value}")
        
        return '\n'.join(related_text_parts) if related_text_parts else "无相关文本信息"
    
    def _extract_context_info(self, table_data: Dict, structure: Dict) -> Dict[str, Any]:
        """
        提取表格的上下文信息
        """
        context_info = {}
        
        # 文档上下文
        document_name = table_data.get('document_name', '')
        if document_name:
            context_info['document_name'] = document_name
        
        document_path = table_data.get('document_path', '')
        if document_path:
            context_info['document_path'] = document_path
        
        # 页面上下文
        page_number = table_data.get('page_number', 1)
        if page_number:
            context_info['page_number'] = page_number
        
        page_idx = table_data.get('page_idx', 1)
        if page_idx:
            context_info['page_idx'] = page_idx
        
        # 表格位置上下文
        table_position = table_data.get('table_position', {})
        if table_position:
            context_info['table_position'] = table_position
        
        # 相邻内容上下文
        adjacent_content = table_data.get('adjacent_content', {})
        if adjacent_content:
            context_info['adjacent_content'] = adjacent_content
        
        # 表格类型上下文
        table_type = structure.get('features', {}).get('table_type', 'unknown')
        if table_type:
            context_info['table_type'] = table_type
        
        # 表格复杂度上下文
        complexity_score = structure.get('features', {}).get('complexity_score', 0)
        if complexity_score:
            context_info['complexity_score'] = complexity_score
        
        return context_info
    
    def _generate_table_summary(self, table_content: str, structure: Dict) -> str:
        """
        生成表格摘要
        """
        if not table_content:
            return "空表格"
        
        lines = [line.strip() for line in table_content.strip().split('\n') if line.strip()]
        rows = len(lines)
        columns = structure.get('columns', 0)
        has_header = structure.get('has_header', False)
        table_type = structure.get('features', {}).get('table_type', 'unknown')
        
        # 基础信息
        summary_parts = [f"这是一个{rows}行{columns}列的{table_type}"]
        
        # 表头信息
        if has_header:
            headers = structure.get('headers', [])
            if headers:
                header_text = '、'.join(headers[:5])  # 只显示前5个表头
                if len(headers) > 5:
                    header_text += f"等{len(headers)}个字段"
                summary_parts.append(f"包含表头: {header_text}")
        
        # 数据特征
        data_features = structure.get('features', {}).get('data_features', {})
        if data_features:
            type_distribution = data_features.get('type_distribution', {})
            
            # 数字列信息
            numeric_ratio = type_distribution.get('numeric_ratio', 0)
            if numeric_ratio > 0.3:
                summary_parts.append(f"包含大量数值数据({numeric_ratio:.1%})")
            
            # 日期列信息
            date_ratio = type_distribution.get('date_ratio', 0)
            if date_ratio > 0.2:
                summary_parts.append(f"包含时间序列数据({date_ratio:.1%})")
        
        # 复杂度信息
        complexity_score = structure.get('features', {}).get('complexity_score', 0)
        if complexity_score > 0.7:
            summary_parts.append("表格结构复杂，需要仔细分析")
        elif complexity_score > 0.4:
            summary_parts.append("表格结构中等复杂")
        else:
            summary_parts.append("表格结构相对简单")
        
        # 质量信息
        structure_quality = structure.get('features', {}).get('structure_quality', {})
        if structure_quality:
            quality_level = structure_quality.get('quality_level', 'unknown')
            if quality_level == 'excellent':
                summary_parts.append("表格结构质量优秀")
            elif quality_level == 'good':
                summary_parts.append("表格结构质量良好")
            elif quality_level == 'fair':
                summary_parts.append("表格结构质量一般")
            elif quality_level == 'poor':
                summary_parts.append("表格结构质量较差")
        
        return "。".join(summary_parts) + "。"
    
    def _generate_extraction_summary(self, basic_content: Dict, chunked_content: List[Dict]) -> str:
        """
        生成提取总结
        """
        if not basic_content:
            return "无内容可提取"
        
        total_cells = basic_content.get('total_cells', 0)
        non_empty_cells = basic_content.get('non_empty_cells', 0)
        chunk_count = len(chunked_content)
        
        summary_parts = [f"成功提取{total_cells}个单元格，其中{non_empty_cells}个非空"]
        
        if chunk_count > 1:
            summary_parts.append(f"分为{chunk_count}个内容块")
        
        fill_rate = basic_content.get('fill_rate', 0)
        if fill_rate > 0.9:
            summary_parts.append("数据填充率很高")
        elif fill_rate > 0.7:
            summary_parts.append("数据填充率较高")
        elif fill_rate > 0.5:
            summary_parts.append("数据填充率中等")
        else:
            summary_parts.append("数据填充率较低")
        
        return "，".join(summary_parts) + "。"
    
    def _create_empty_extraction_result(self) -> Dict[str, Any]:
        """创建空表格的提取结果"""
        return {
            'extraction_status': 'success',
            'extraction_timestamp': int(time.time()),
            'basic_content': {},
            'chunked_content': [],
            'related_text': '',
            'context_info': {},
            'table_summary': '空表格',
            'extraction_summary': '无内容可提取'
        }
    
    def _create_error_extraction_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误提取结果"""
        return {
            'extraction_status': 'failed',
            'extraction_timestamp': int(time.time()),
            'error_message': error_message,
            'basic_content': {},
            'chunked_content': [],
            'related_text': '',
            'context_info': {},
            'table_summary': f'提取失败: {error_message}',
            'extraction_summary': '提取过程中发生错误'
        }
    
    def get_extraction_status(self) -> Dict[str, Any]:
        """获取提取器状态"""
        return {
            'extractor_type': 'table_extractor',
            'status': 'ready',
            'capabilities': [
                'basic_content_extraction',
                'smart_chunking',
                'related_text_extraction',
                'context_info_extraction',
                'summary_generation'
            ],
            'version': '3.0.0'
        }
