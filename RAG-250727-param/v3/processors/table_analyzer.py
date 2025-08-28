'''
程序说明：
## 1. TableAnalyzer子模块
- 负责表格结构分析，包括行数、列数、表头等信息
- 完全符合设计文档规范，位于processors模块下
- 为TableProcessor提供表格分析服务
## 2. 主要功能
- 分析表格结构（行数、列数、表头）
- 识别表格类型和特征
- 检测表格的规律性和合并单元格
- 为后续处理提供结构信息
## 3. 与优化方案的关系
- 实现优化方案要求的模块化设计
- 支持大表格的智能分块处理
- 完全符合设计文档的TABLE_METADATA_SCHEMA规范
'''
import re
import logging
from typing import Dict, List, Any
import time

class TableAnalyzer:
    """
    表格分析器
    负责表格结构分析，包括行数、列数、表头等信息
    完全符合设计文档规范，位于processors模块下
    """
    
    def __init__(self):
        logging.info("表格分析器初始化完成")
    
    def analyze(self, table_data: Dict) -> Dict[str, Any]:
        """
        分析表格结构
        
        :param table_data: 表格数据，包含table_body、table_content、table_structure等字段
        :return: 分析结果字典
        """
        try:
            # 从table_body获取HTML数据
            table_html = table_data.get('table_body', '')
            
            if not table_html:
                return self._create_empty_analysis_result()
            
            # 将HTML转换为纯文本进行分析
            table_content = self._extract_text_from_html(table_html)
            
            # 步骤1: 基础结构分析
            structure_info = self._analyze_table_structure(table_content)
            
            # 步骤2: 特征分析
            features_info = self._analyze_table_features(table_content, structure_info)
            
            # 步骤3: 智能检测
            detection_info = self._detect_table_patterns(table_content, structure_info)
            
            # 整合分析结果
            analysis_result = {
                'analysis_status': 'success',
                'analysis_timestamp': int(time.time()),
                'structure': structure_info,
                'features': features_info,
                'detection': detection_info,
                'summary': self._generate_analysis_summary(structure_info, features_info)
            }
            
            logging.info(f"表格分析完成: {structure_info.get('rows', 0)}行 x {structure_info.get('columns', 0)}列")
            return analysis_result
            
        except Exception as e:
            error_msg = f"表格分析失败: {str(e)}"
            logging.error(error_msg)
            return self._create_error_analysis_result(error_msg)
    
    def _analyze_table_structure(self, table_content: str) -> Dict[str, Any]:
        """
        分析表格的行、列、表头等基本结构
        """
        if not table_content:
            return {'rows': 0, 'columns': 0, 'headers': [], 'has_header': False}
        
        # 按行分割
        lines = [line.strip() for line in table_content.strip().split('\n') if line.strip()]
        rows = len(lines)
        
        if rows == 0:
            return {'rows': 0, 'columns': 0, 'headers': [], 'has_header': False}
        
        # 分析列数和分隔符
        separator_info = self._detect_separator(lines)
        columns = separator_info['columns']
        separator = separator_info['separator']
        
        # 识别表头
        headers = []
        has_header = False
        if rows > 0:
            headers, has_header = self._detect_header(lines, separator)
        
        # 计算数据行数
        data_rows = rows - (1 if has_header else 0)
        
        return {
            'rows': rows,
            'data_rows': data_rows,
            'columns': columns,
            'headers': headers,
            'has_header': has_header,
            'separator': separator,
            'separator_type': separator_info['type'],
            'avg_row_length': sum(len(line) for line in lines) / rows if rows > 0 else 0
        }
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """
        从HTML表格中提取纯文本内容
        
        :param html_content: HTML格式的表格内容
        :return: 纯文本内容
        """
        if not html_content:
            return ""
        
        # 使用简单的HTML文本提取
        import re
        # 移除HTML标签
        text_content = re.sub(r'<[^>]+>', ' ', html_content)
        # 合并多个空格
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        return text_content

    def _enhance_existing_structure(self, table_structure: Dict, table_data: Dict) -> Dict[str, Any]:
        """
        基于预分析的结构，进行验证和补充
        
        :param table_structure: 预分析的表格结构
        :param table_data: 表格数据
        :return: 增强后的结构信息
        """
        enhanced_structure = table_structure.copy()
        
        # 验证行数和列数
        if enhanced_structure.get('rows') == 0:
            enhanced_structure['rows'] = len(table_data.get('table_body', '').strip().split('\n'))
        
        if enhanced_structure.get('columns') == 0:
            enhanced_structure['columns'] = 1  # 默认一列
        
        # 验证是否有表头
        if enhanced_structure.get('has_header') is None:
            enhanced_structure['has_header'] = False  # 默认没有表头
        
        # 验证分隔符
        if enhanced_structure.get('separator') == '\t':
            enhanced_structure['separator'] = '\t'  # 保持默认值
        
        # 验证平均行长度
        if enhanced_structure.get('avg_row_length') == 0:
            enhanced_structure['avg_row_length'] = 0  # 默认值
        
        # 验证数据行数
        if enhanced_structure.get('data_rows') == 0:
            enhanced_structure['data_rows'] = enhanced_structure['rows'] - (1 if enhanced_structure['has_header'] else 0)
        
        # 验证特征分析
        if not enhanced_structure.get('features'):
            enhanced_structure['features'] = {'table_type': 'unknown', 'complexity_score': 0.0}
        
        # 验证模式检测
        if not enhanced_structure.get('detection'):
            enhanced_structure['detection'] = {'merge_patterns': {}, 'repetition_patterns': {}, 'sequence_patterns': {}}
        
        # 验证总结
        if not enhanced_structure.get('summary'):
            enhanced_structure['summary'] = f"表格包含 {enhanced_structure['rows']} 行 {enhanced_structure['columns']} 列数据"
        
        return enhanced_structure

    def _analyze_table_features(self, table_content: str, structure_info: Dict) -> Dict[str, Any]:
        """
        分析表格类型、规律性、合并单元格、数据密度、复杂度等特征
        """
        if not table_content:
            return {}
        
        lines = [line.strip() for line in table_content.strip().split('\n') if line.strip()]
        rows = len(lines)
        columns = structure_info.get('columns', 0)
        
        # 1. 表格类型判断
        table_type = self._determine_table_type(structure_info, lines)
        
        # 2. 数据密度分析
        density_info = self._analyze_data_density(lines, structure_info)
        
        # 3. 规律性分析
        regularity_info = self._analyze_regularity(lines, structure_info)
        
        # 4. 复杂度评分
        complexity_score = self._calculate_complexity_score(structure_info, density_info, regularity_info)
        
        # 5. 数据特征分析
        data_features = self._analyze_data_features(lines, structure_info)
        
        return {
            'table_type': table_type,
            'data_density': density_info,
            'regularity': regularity_info,
            'complexity_score': complexity_score,
            'data_features': data_features,
            'structure_quality': self._assess_structure_quality(structure_info)
        }
    
    def _determine_table_type(self, structure_info: Dict, lines: List[str]) -> str:
        """确定表格类型"""
        rows = structure_info.get('rows', 0)
        columns = structure_info.get('columns', 0)
        has_header = structure_info.get('has_header', False)
        
        if rows <= 1:
            return 'simple_table'
        elif columns <= 2:
            return 'list_table'
        elif rows <= 5 and columns <= 5:
            return 'summary_table'
        elif has_header and rows > 10:
            return 'data_table'
        elif rows > 20:
            return 'large_data_table'
        else:
            return 'standard_table'
    
    def _analyze_data_density(self, lines: List[str], structure_info: Dict) -> Dict[str, Any]:
        """分析数据密度"""
        if not lines:
            return {'overall_density': 0, 'row_densities': [], 'column_densities': []}
        
        separator = structure_info.get('separator', '\t')
        columns = structure_info.get('columns', 0)
        
        # 计算每行的数据密度
        row_densities = []
        total_cells = 0
        non_empty_cells = 0
        
        for line in lines:
            cells = self._split_table_row(line, separator)
            empty_cells = sum(1 for cell in cells if not cell.strip())
            density = (len(cells) - empty_cells) / len(cells) if cells else 0
            row_densities.append(density)
            total_cells += len(cells)
            non_empty_cells += (len(cells) - empty_cells)
        
        # 计算列密度
        column_densities = []
        for col_idx in range(columns):
            col_empty = 0
            for line in lines:
                cells = self._split_table_row(line, separator)
                if col_idx < len(cells) and not cells[col_idx].strip():
                    col_empty += 1
            density = (len(lines) - col_empty) / len(lines) if lines else 0
            column_densities.append(density)
        
        overall_density = non_empty_cells / total_cells if total_cells > 0 else 0
        
        return {
            'overall_density': overall_density,
            'row_densities': row_densities,
            'column_densities': column_densities,
            'avg_row_density': sum(row_densities) / len(row_densities) if row_densities else 0,
            'avg_column_density': sum(column_densities) / len(column_densities) if column_densities else 0
        }
    
    def _analyze_regularity(self, lines: List[str], structure_info: Dict) -> Dict[str, Any]:
        """分析表格规律性"""
        if not lines:
            return {'is_regular': False, 'irregularity_score': 1.0, 'issues': []}
        
        separator = structure_info.get('separator', '\t')
        expected_columns = structure_info.get('columns', 0)
        
        issues = []
        irregular_rows = 0
        
        for i, line in enumerate(lines):
            cells = self._split_table_row(line, separator)
            if len(cells) != expected_columns:
                issues.append(f"第{i+1}行列数不一致: 期望{expected_columns}列，实际{len(cells)}列")
                irregular_rows += 1
        
        # 计算规律性评分
        regularity_score = 1.0 - (irregular_rows / len(lines)) if lines else 0
        is_regular = regularity_score >= 0.9
        
        return {
            'is_regular': is_regular,
            'regularity_score': regularity_score,
            'irregularity_score': 1.0 - regularity_score,
            'issues': issues,
            'irregular_rows': irregular_rows,
            'total_rows': len(lines)
        }
    
    def _calculate_complexity_score(self, structure_info: Dict, density_info: Dict, regularity_info: Dict) -> float:
        """计算表格复杂度评分"""
        score = 0.0
        
        # 结构复杂度
        rows = structure_info.get('rows', 0)
        columns = structure_info.get('columns', 0)
        if rows > 50:
            score += 0.3
        elif rows > 20:
            score += 0.2
        elif rows > 10:
            score += 0.1
        
        if columns > 10:
            score += 0.3
        elif columns > 5:
            score += 0.2
        elif columns > 3:
            score += 0.1
        
        # 数据密度复杂度
        density = density_info.get('overall_density', 0)
        if density < 0.5:
            score += 0.2
        elif density < 0.8:
            score += 0.1
        
        # 规律性复杂度
        regularity = regularity_info.get('regularity_score', 1.0)
        if regularity < 0.8:
            score += 0.2
        
        return min(score, 1.0)
    
    def _analyze_data_features(self, lines: List[str], structure_info: Dict) -> Dict[str, Any]:
        """分析数据特征"""
        if not lines:
            return {}
        
        separator = structure_info.get('separator', '\t')
        
        # 统计数字、日期、文本等类型
        numeric_count = 0
        date_count = 0
        text_count = 0
        empty_count = 0
        
        for line in lines:
            cells = self._split_table_row(line, separator)
            for cell in cells:
                cell = cell.strip()
                if not cell:
                    empty_count += 1
                elif re.match(r'^\d+(\.\d+)?$', cell):
                    numeric_count += 1
                elif re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', cell):
                    date_count += 1
                else:
                    text_count += 1
        
        total_cells = sum(len(self._split_table_row(line, separator)) for line in lines)
        
        return {
            'data_types': {
                'numeric': numeric_count,
                'date': date_count,
                'text': text_count,
                'empty': empty_count
            },
            'type_distribution': {
                'numeric_ratio': numeric_count / total_cells if total_cells > 0 else 0,
                'date_ratio': date_count / total_cells if total_cells > 0 else 0,
                'text_ratio': text_count / total_cells if total_cells > 0 else 0,
                'empty_ratio': empty_count / total_cells if total_cells > 0 else 0
            },
            'total_cells': total_cells
        }
    
    def _assess_structure_quality(self, structure_info: Dict) -> Dict[str, Any]:
        """评估表格结构质量"""
        rows = structure_info.get('rows', 0)
        columns = structure_info.get('columns', 0)
        has_header = structure_info.get('has_header', False)
        
        quality_score = 0.0
        quality_issues = []
        
        # 行数评估
        if rows == 0:
            quality_issues.append("表格为空")
            quality_score = 0.0
        elif rows == 1:
            quality_issues.append("表格只有一行，可能不是标准表格")
            quality_score = 0.3
        elif rows < 5:
            quality_score = 0.6
        else:
            quality_score += 0.4
        
        # 列数评估
        if columns == 0:
            quality_issues.append("表格没有列")
            quality_score = 0.0
        elif columns == 1:
            quality_issues.append("表格只有一列，可能是列表")
            quality_score = 0.4
        elif columns < 3:
            quality_score += 0.2
        else:
            quality_score += 0.3
        
        # 表头评估
        if has_header:
            quality_score += 0.3
        else:
            quality_issues.append("表格没有明确的表头")
        
        # 总体质量评估
        if quality_score >= 0.8:
            quality_level = 'excellent'
        elif quality_score >= 0.6:
            quality_level = 'good'
        elif quality_score >= 0.4:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        return {
            'quality_score': quality_score,
            'quality_level': quality_level,
            'quality_issues': quality_issues,
            'recommendations': self._generate_quality_recommendations(quality_issues)
        }
    
    def _generate_quality_recommendations(self, issues: List[str]) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        for issue in issues:
            if "表格为空" in issue:
                recommendations.append("检查表格内容是否为空，可能需要重新解析")
            elif "只有一行" in issue:
                recommendations.append("考虑是否需要合并相邻的表格内容")
            elif "只有一列" in issue:
                recommendations.append("检查是否应该按列分割内容")
            elif "没有明确的表头" in issue:
                recommendations.append("考虑添加表头或识别现有表头")
        
        if not recommendations:
            recommendations.append("表格结构良好，可以直接处理")
        
        return recommendations
    
    def _detect_table_patterns(self, table_content: str, structure_info: Dict) -> Dict[str, Any]:
        """
        检测表格的模式和规律
        """
        if not table_content:
            return {}
        
        lines = [line.strip() for line in table_content.strip().split('\n') if line.strip()]
        
        # 检测合并单元格模式
        merge_patterns = self._detect_merge_patterns(lines, structure_info)
        
        # 检测数据重复模式
        repetition_patterns = self._detect_repetition_patterns(lines, structure_info)
        
        # 检测数据递增/递减模式
        sequence_patterns = self._detect_sequence_patterns(lines, structure_info)
        
        return {
            'merge_patterns': merge_patterns,
            'repetition_patterns': repetition_patterns,
            'sequence_patterns': sequence_patterns,
            'pattern_summary': self._generate_pattern_summary(merge_patterns, repetition_patterns, sequence_patterns)
        }
    
    def _detect_merge_patterns(self, lines: List[str], structure_info: Dict) -> Dict[str, Any]:
        """检测合并单元格模式"""
        # 简化实现：检测空单元格的模式
        separator = structure_info.get('separator', '\t')
        columns = structure_info.get('columns', 0)
        
        empty_cell_patterns = []
        for row_idx, line in enumerate(lines):
            cells = self._split_table_row(line, separator)
            empty_positions = [i for i, cell in enumerate(cells) if not cell.strip()]
            if empty_positions:
                empty_cell_patterns.append({
                    'row': row_idx + 1,
                    'empty_positions': empty_positions,
                    'pattern_type': 'consecutive' if self._is_consecutive(empty_positions) else 'scattered'
                })
        
        return {
            'has_merged_cells': len(empty_cell_patterns) > 0,
            'empty_cell_patterns': empty_cell_patterns,
            'total_patterns': len(empty_cell_patterns)
        }
    
    def _is_consecutive(self, positions: List[int]) -> bool:
        """检查位置是否连续"""
        if len(positions) <= 1:
            return True
        sorted_positions = sorted(positions)
        return all(sorted_positions[i+1] - sorted_positions[i] == 1 for i in range(len(sorted_positions)-1))
    
    def _detect_repetition_patterns(self, lines: List[str], structure_info: Dict) -> Dict[str, Any]:
        """检测数据重复模式"""
        # 简化实现：检测行重复
        separator = structure_info.get('separator', '\t')
        
        row_hashes = []
        for line in lines:
            cells = self._split_table_row(line, separator)
            row_hash = hash(tuple(cells))
            row_hashes.append(row_hash)
        
        # 统计重复行
        from collections import Counter
        hash_counts = Counter(row_hashes)
        duplicate_hashes = {h: c for h, c in hash_counts.items() if c > 1}
        
        return {
            'has_duplicates': len(duplicate_hashes) > 0,
            'duplicate_rows': len(duplicate_hashes),
            'total_duplicates': sum(duplicate_hashes.values()) - len(duplicate_hashes)
        }
    
    def _detect_sequence_patterns(self, lines: List[str], structure_info: Dict) -> Dict[str, Any]:
        """检测数据递增/递减模式"""
        # 简化实现：检测数字列的模式
        separator = structure_info.get('separator', '\t')
        columns = structure_info.get('columns', 0)
        
        sequence_patterns = []
        for col_idx in range(columns):
            column_values = []
            for line in lines:
                cells = self._split_table_row(line, separator)
                if col_idx < len(cells):
                    cell = cells[col_idx].strip()
                    if re.match(r'^\d+(\.\d+)?$', cell):
                        column_values.append(float(cell))
            
            if len(column_values) >= 3:
                pattern = self._analyze_numeric_sequence(column_values)
                if pattern['pattern_type'] != 'none':
                    sequence_patterns.append({
                        'column': col_idx + 1,
                        'pattern': pattern
                    })
        
        return {
            'has_sequences': len(sequence_patterns) > 0,
            'sequence_patterns': sequence_patterns,
            'total_sequences': len(sequence_patterns)
        }
    
    def _analyze_numeric_sequence(self, values: List[float]) -> Dict[str, Any]:
        """分析数值序列的模式"""
        if len(values) < 3:
            return {'pattern_type': 'none', 'confidence': 0.0}
        
        # 检查递增
        is_increasing = all(values[i] <= values[i+1] for i in range(len(values)-1))
        # 检查递减
        is_decreasing = all(values[i] >= values[i+1] for i in range(len(values)-1))
        
        if is_increasing:
            return {'pattern_type': 'increasing', 'confidence': 0.8}
        elif is_decreasing:
            return {'pattern_type': 'decreasing', 'confidence': 0.8}
        else:
            return {'pattern_type': 'none', 'confidence': 0.0}
    
    def _generate_pattern_summary(self, merge_patterns: Dict, repetition_patterns: Dict, sequence_patterns: Dict) -> str:
        """生成模式总结"""
        summary_parts = []
        
        if merge_patterns.get('has_merged_cells'):
            summary_parts.append("包含合并单元格")
        
        if repetition_patterns.get('has_duplicates'):
            summary_parts.append("包含重复数据")
        
        if sequence_patterns.get('has_sequences'):
            summary_parts.append("包含数值序列")
        
        if not summary_parts:
            summary_parts.append("无特殊模式")
        
        return "，".join(summary_parts)
    
    def _generate_analysis_summary(self, structure_info: Dict, features_info: Dict) -> str:
        """生成分析总结"""
        rows = structure_info.get('rows', 0)
        columns = structure_info.get('columns', 0)
        table_type = features_info.get('table_type', 'unknown')
        complexity = features_info.get('complexity_score', 0)
        
        summary = f"{rows}行 x {columns}列的{table_type}"
        
        if complexity > 0.7:
            summary += "，复杂度较高"
        elif complexity > 0.4:
            summary += "，复杂度中等"
        else:
            summary += "，复杂度较低"
        
        return summary
    
    def _create_empty_analysis_result(self) -> Dict[str, Any]:
        """创建空表格的分析结果"""
        return {
            'analysis_status': 'success',
            'analysis_timestamp': int(time.time()),
            'structure': {'rows': 0, 'columns': 0, 'headers': [], 'has_header': False},
            'features': {'table_type': 'empty', 'complexity_score': 0.0},
            'detection': {'merge_patterns': {}, 'repetition_patterns': {}, 'sequence_patterns': {}},
            'summary': '空表格'
        }
    
    def _create_error_analysis_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误分析结果"""
        return {
            'analysis_status': 'failed',
            'analysis_timestamp': int(time.time()),
            'error_message': error_message,
            'structure': {'rows': 0, 'columns': 0, 'headers': [], 'has_header': False},
            'features': {'table_type': 'error', 'complexity_score': 0.0},
            'detection': {'merge_patterns': {}, 'repetition_patterns': {}, 'sequence_patterns': {}},
            'summary': f'分析失败: {error_message}'
        }
    
    def get_analysis_status(self) -> Dict[str, Any]:
        """获取分析器状态"""
        return {
            'analyzer_type': 'table_analyzer',
            'status': 'ready',
            'capabilities': [
                'structure_analysis',
                'feature_analysis',
                'pattern_detection',
                'quality_assessment'
            ],
            'version': '3.0.0'
        }
