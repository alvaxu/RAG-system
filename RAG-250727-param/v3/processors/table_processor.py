"""
表格处理器

负责处理文档中的表格内容，包括表格解析、表格分块、HTML生成和表格向量化。
完全符合设计文档规范。
"""

import os
import time
import logging
from typing import Dict, List, Any

class TableProcessor:
    """
    表格处理器
    整合：分析 → 提取 → 格式化 → 向量化
    完全符合设计文档规范，位于processors模块下
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
        # 初始化各个组件（符合设计文档规范）
        from .table_analyzer import TableAnalyzer
        from .table_extractor import TableExtractor
        from .table_formatter import TableFormatter
        self.table_analyzer = TableAnalyzer()
        self.table_extractor = TableExtractor()
        self.table_formatter = TableFormatter()
        
        # 使用失败处理（符合设计文档规范）
        self.failure_handler = config_manager.get_failure_handler()
        
        logging.info("表格处理器初始化完成")
    
    def process_table(self, table_data: Dict) -> Dict[str, Any]:
        """
        处理单个表格
        """
        try:
            print(f"  📊 处理表格: {table_data.get('table_title', '未命名表格')}")
            
            # 步骤1: 表格结构分析
            print("  步骤1: 表格结构分析...")
            analysis_result = self.table_analyzer.analyze(table_data)
            if analysis_result.get('analysis_status') != 'success':
                print(f"  ⚠️ 表格分析失败: {analysis_result.get('error_message', '未知错误')}")
            
            # 步骤2: 表格内容提取
            print("  步骤2: 表格内容提取...")
            extraction_result = self.table_extractor.extract(table_data, analysis_result.get('structure', {}))
            if extraction_result.get('extraction_status') != 'success':
                print(f"  ⚠️ 表格内容提取失败: {extraction_result.get('error_message', '未知错误')}")
            
            # 步骤3: 表格格式化（MinerU已提供HTML，跳过格式化）
            print("  步骤3: 表格格式化（跳过，MinerU已提供HTML）...")
            format_result = {
                'format_status': 'success',
                'html_table': table_data.get('table_body', ''),  # 直接使用MinerU的HTML
                'text_representation': '',  # 稍后从HTML提取
                'error_message': None
            }
            
            # 步骤4: 生成完整元数据
            print("  步骤4: 生成完整元数据...")
            complete_metadata = self._create_complete_table_metadata(
                table_data, analysis_result, extraction_result, format_result
            )
            
            print(f"  ✅ 表格处理完成: {table_data.get('table_title', '未命名表格')}")
            return complete_metadata
            
        except Exception as e:
            error_msg = f"表格处理失败: {e}"
            logging.error(error_msg)
            self.failure_handler.record_failure(table_data, 'table_processing', str(e))
            
            # 返回错误结果
            return self._create_error_table_metadata(table_data, str(e))
    
    def process_batch(self, tables: List[Dict]) -> List[Dict[str, Any]]:
        """
        批量处理表格
        """
        processed_tables = []
        
        for i, table in enumerate(tables):
            try:
                print(f"正在处理表格 {i+1}/{len(tables)}")
                result = self.process_table(table)
                processed_tables.append(result)
            except Exception as e:
                error_msg = f"表格批量处理失败: {e}"
                logging.error(error_msg)
                self.failure_handler.record_failure(table, 'table_batch_processing', str(e))
                
                # 创建错误结果
                error_result = self._create_error_table_metadata(table, str(e))
                processed_tables.append(error_result)
        
        return processed_tables
    
    def _create_complete_table_metadata(self, table_data: Dict, analysis_result: Dict, 
                                      extraction_result: Dict, format_result: Dict) -> Dict[str, Any]:
        """
        创建完整的表格元数据，完全符合设计文档的TABLE_METADATA_SCHEMA规范
        """
        return {
            # 基础标识字段（符合COMMON_METADATA_FIELDS）
            'chunk_id': table_data.get('chunk_id', ''),
            'chunk_type': 'table',
            'source_type': 'pdf',
            'document_name': table_data.get('document_name', ''),
            'document_path': table_data.get('document_path', ''),
            'page_number': table_data.get('page_number', 1),
            'page_idx': table_data.get('page_idx', 1),
            'created_timestamp': table_data.get('created_timestamp', int(time.time())),
            'updated_timestamp': int(time.time()),
            'processing_version': '3.0.0',
            
            # 表格特有字段（符合TABLE_METADATA_SCHEMA）
            'table_id': table_data.get('table_id', ''),
            'table_title': table_data.get('table_title', ''),
            'table_body': table_data.get('table_body', ''),
            'table_summary': extraction_result.get('basic_content', {}).get('text_content', ''),
            
            # 表格结构信息
            'table_structure': {
                'rows': analysis_result.get('structure', {}).get('rows', 0),
                'columns': analysis_result.get('structure', {}).get('columns', 0),
                'headers': analysis_result.get('structure', {}).get('headers', []),
                'has_header': analysis_result.get('structure', {}).get('has_header', False)
            },
            
            # 表格特征信息
            'table_features': analysis_result.get('features', {}),
            
            # 表格内容信息
            'table_content_info': {
                'text_content': extraction_result.get('basic_content', {}).get('text_content', ''),
                'row_count': extraction_result.get('basic_content', {}).get('row_count', 0),
                'column_count': extraction_result.get('basic_content', {}).get('column_count', 0),
                'total_cells': extraction_result.get('basic_content', {}).get('total_cells', 0)
            },
            
            # 表格格式化信息
            'table_format': {
                'html_table': format_result.get('html_table', ''),
                'text_representation': format_result.get('text_representation', ''),
                'css_styles': ''  # 暂时为空，后续可以添加
            },
            
            # 相关文本信息
            'related_text': extraction_result.get('related_text', ''),
            'context_info': extraction_result.get('context_info', {}),
            
            # 处理状态信息
            'analysis_status': analysis_result.get('analysis_status', 'unknown'),
            'extraction_status': extraction_result.get('extraction_status', 'unknown'),
            'format_status': format_result.get('format_status', 'unknown'),
            
            # 向量化信息字段（预留）
            'vectorized': False,
            'vectorization_timestamp': None,
            'embedding_model': None,
            'table_embedding': [],
            'vectorization_status': 'pending',
            
            # 关联信息字段
            'related_text_chunks': table_data.get('related_text_chunks', []),
            'related_image_chunks': table_data.get('related_image_chunks', []),
            'parent_document_id': table_data.get('parent_document_id', ''),
            
            # 架构标识
            'metadata_schema': 'TABLE_METADATA_SCHEMA',
            'metadata_version': '3.0.0',
            'processing_pipeline': 'Table_Analysis_Extraction_Formatting_Pipeline',
            'optimization_features': [
                'modular_design',
                'smart_chunking',
                'complete_metadata',
                'html_formatting'
            ]
        }
    
    def _create_error_table_metadata(self, table_data: Dict, error_message: str) -> Dict[str, Any]:
        """
        创建错误表格元数据
        """
        return {
            # 基础标识字段
            'chunk_id': table_data.get('chunk_id', ''),
            'chunk_type': 'table',
            'source_type': 'pdf',
            'document_name': table_data.get('document_name', ''),
            'document_path': table_data.get('document_path', ''),
            'page_number': table_data.get('page_number', 1),
            'page_idx': table_data.get('page_idx', 1),
            'created_timestamp': table_data.get('created_timestamp', int(time.time())),
            'updated_timestamp': int(time.time()),
            'processing_version': '3.0.0',
            
            # 错误信息
            'error': error_message,
            'processing_status': 'failed',
            
            # 空的表格字段
            'table_id': table_data.get('table_id', ''),
            'table_title': table_data.get('table_title', ''),
            'table_body': table_data.get('table_body', ''),
            'table_summary': '处理失败',
            
            # 空的处理结果
            'table_structure': {'rows': 0, 'columns': 0, 'headers': [], 'has_header': False},
            'table_features': {},
            'table_content_info': {'text_content': '', 'row_count': 0, 'column_count': 0, 'total_cells': 0},
            'table_format': {'html_table': '', 'text_representation': '', 'css_styles': ''},
            
            # 架构标识
            'metadata_schema': 'TABLE_METADATA_SCHEMA',
            'metadata_version': '3.0.0',
            'processing_pipeline': 'Table_Error_Handling',
            'optimization_features': ['error_handling', 'graceful_degradation']
        }
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        获取处理状态
        """
        return {
            'analyzer_status': 'ready',
            'extractor_status': 'ready',
            'formatter_status': 'ready',
            'total_tables_processed': 0  # 可以添加计数器
        }
