"""
表格向量化器

负责表格内容的向量化处理，通过ModelCaller调用文本嵌入模型。
完全符合设计文档规范，位于vectorization模块下。
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

'''
程序说明：
## 1. TableVectorizer子模块
- 负责表格向量化，使用text-embedding-v1模型
- 完全符合设计文档规范，位于vectorization模块下
- 为VectorizationManager提供表格向量化服务
## 2. 主要功能
- 对单个表格进行向量化
- 批量表格向量化
- 通过ModelCaller统一管理AI模型调用
- 完整的错误处理和状态管理
## 3. 与优化方案的关系
- 实现优化方案要求的表格向量化策略
- 支持批量处理和API限流控制
- 完全符合设计文档的TABLE_METADATA_SCHEMA规范
'''
import os
import time
import logging
from typing import Dict, List, Any

class TableVectorizer:
    """
    表格向量化器
    使用text-embedding-v1模型进行表格向量化
    完全符合设计文档规范，位于vectorization模块下
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        self.text_embedding_model = self.config.get('vectorization.text_embedding_model', 'text-embedding-v1')
        self.batch_size = self.config.get('api_rate_limiting.table_vectorization_batch_size', 8)
        self.delay_seconds = self.config.get('api_rate_limiting.table_vectorization_delay_seconds', 1)
        self.failure_handler = config_manager.get_failure_handler()
        
        # 初始化ModelCaller
        from utils.model_caller import ModelCaller
        self.model_caller = ModelCaller(config_manager)
        
        logging.info("表格向量化器初始化完成")
    
    def vectorize(self, table_content: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        对单个表格进行向量化
        
        :param table_content: 表格内容
        :param metadata: 表格元数据
        :return: 向量化结果字典
        """
        try:
            if not table_content or not table_content.strip():
                raise ValueError("表格内容为空")
            
            logging.info(f"开始向量化表格: {table_content[:50]}...")
            
            # 步骤1: 表格内容预处理
            processed_content = self._preprocess_table_content(table_content)
            
            # 步骤2: 调用文本向量化模型
            table_embedding = self._call_text_embedding_model(processed_content)
            
            # 步骤3: 生成向量化元数据
            vectorization_metadata = self._generate_vectorization_metadata(
                table_embedding, processed_content, metadata
            )
            
            # 整合结果
            vectorization_result = {
                'vectorization_status': 'success',
                'vectorization_timestamp': int(time.time()),
                'table_embedding': table_embedding,
                'table_embedding_model': self.text_embedding_model,
                'vectorization_metadata': vectorization_metadata,
                'processing_metadata': {
                    'vectorization_version': '3.0.0',
                    'processing_pipeline': 'Table_Embedding_Pipeline',
                    'optimization_features': [
                        'table_preprocessing',
                        'batch_processing',
                        'api_rate_limiting',
                        'complete_metadata'
                    ]
                }
            }
            
            logging.info(f"表格向量化完成: {len(table_embedding)} 维向量")
            return vectorization_result
            
        except Exception as e:
            error_msg = f"表格向量化失败: {str(e)}"
            logging.error(error_msg)
            self.failure_handler.record_failure(table_content, 'table_vectorization', str(e))
            
            # 返回错误结果
            return self._create_error_vectorization_result(str(e))
    
    def _preprocess_table_content(self, table_content: str) -> str:
        """
        表格内容预处理
        """
        if not table_content:
            return ""
        
        # 移除多余的空白字符
        processed_content = ' '.join(table_content.split())
        
        # 移除特殊字符（保留中文、英文、数字、基本标点、表格相关字符）
        import re
        processed_content = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：""''（）【】|\t\n]', '', processed_content)
        
        # 限制内容长度（避免过长的表格）
        max_length = self.config.get('vectorization.max_table_length', 6000)
        if len(processed_content) > max_length:
            processed_content = processed_content[:max_length] + "..."
            logging.info(f"表格内容长度超过限制，已截断至 {max_length} 字符")
        
        return processed_content.strip()
    
    def _call_text_embedding_model(self, processed_content: str) -> List[float]:
        """
        调用文本向量化模型
        """
        try:
            # 调用ModelCaller进行文本向量化
            table_embedding = self.model_caller.call_text_embedding(processed_content)
            
            if not table_embedding:
                raise ValueError("表格向量生成失败")
            
            return table_embedding
            
        except Exception as e:
            logging.error(f"表格向量化模型调用失败: {e}")
            raise
    
    def _generate_vectorization_metadata(self, table_embedding: List[float], processed_content: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        生成向量化元数据
        """
        return {
            'table_content_length': len(processed_content),
            'vector_dimensions': len(table_embedding) if table_embedding else 0,
            'vector_quality': self._assess_vector_quality(table_embedding),
            'table_features': self._analyze_table_features(processed_content),
            'embedding_model': self.text_embedding_model,
            'vectorization_timestamp': int(time.time()),
            'original_metadata': metadata or {}
        }
    
    def _assess_vector_quality(self, vector: List[float]) -> Dict[str, Any]:
        """
        评估向量质量
        """
        if not vector:
            return {'quality_score': 0, 'quality_level': 'poor', 'issues': ['向量为空']}
        
        quality_score = 0.0
        issues = []
        
        # 维度评估
        dimensions = len(vector)
        if dimensions >= 1024:
            quality_score += 0.4
        elif dimensions >= 512:
            quality_score += 0.3
        elif dimensions >= 256:
            quality_score += 0.2
        else:
            issues.append("向量维度较低")
        
        # 数值范围评估
        if vector:
            min_val = min(vector)
            max_val = max(vector)
            range_val = max_val - min_val
            
            if range_val > 10:
                quality_score += 0.3
            elif range_val > 5:
                quality_score += 0.2
            elif range_val > 1:
                quality_score += 0.1
            else:
                issues.append("向量数值范围较小")
            
            # 零值比例评估
            zero_count = sum(1 for v in vector if abs(v) < 1e-6)
            zero_ratio = zero_count / dimensions
            
            if zero_ratio < 0.1:
                quality_score += 0.3
            elif zero_ratio < 0.3:
                quality_score += 0.2
            elif zero_ratio < 0.5:
                quality_score += 0.1
            else:
                issues.append("向量包含过多零值")
        
        # 确定质量级别
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
            'issues': issues,
            'dimensions': dimensions,
            'min_value': min(vector) if vector else 0,
            'max_value': max(vector) if vector else 0,
            'zero_ratio': zero_ratio if vector else 0
        }
    
    def _analyze_table_features(self, content: str) -> Dict[str, Any]:
        """
        分析表格特征
        """
        if not content:
            return {}
        
        import re
        
        # 字符统计
        total_chars = len(content)
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_chars = len(re.findall(r'[a-zA-Z]', content))
        digit_chars = len(re.findall(r'\d', content))
        separator_chars = len(re.findall(r'[\t\n|]', content))
        
        # 行统计
        lines = content.split('\n')
        line_count = len(lines)
        non_empty_lines = len([line for line in lines if line.strip()])
        
        # 列统计（基于分隔符）
        max_columns = 0
        for line in lines:
            if line.strip():
                columns = line.split('\t')
                max_columns = max(max_columns, len(columns))
        
        # 表格结构特征
        has_headers = any(re.search(r'[名称|标题|项目|指标|参数]', line) for line in lines[:3])
        has_numbers = digit_chars > 0
        has_separators = separator_chars > 0
        
        return {
            'character_statistics': {
                'total': total_chars,
                'chinese': chinese_chars,
                'english': english_chars,
                'digits': digit_chars,
                'separators': separator_chars
            },
            'structure_statistics': {
                'total_lines': line_count,
                'non_empty_lines': non_empty_lines,
                'max_columns': max_columns,
                'fill_rate': non_empty_lines / line_count if line_count > 0 else 0
            },
            'table_features': {
                'has_headers': has_headers,
                'has_numbers': has_numbers,
                'has_separators': has_separators,
                'is_structured': has_separators and max_columns > 1
            }
        }
    
    def _create_error_vectorization_result(self, error_message: str) -> Dict[str, Any]:
        """
        创建错误向量化结果
        """
        return {
            'vectorization_status': 'failed',
            'vectorization_timestamp': int(time.time()),
            'error_message': error_message,
            'table_embedding': [],
            'table_embedding_model': self.text_embedding_model,
            'vectorization_metadata': {
                'table_content_length': 0,
                'vector_dimensions': 0,
                'vector_quality': {'quality_score': 0, 'quality_level': 'poor'},
                'table_features': {},
                'embedding_model': self.text_embedding_model,
                'vectorization_timestamp': int(time.time()),
                'original_metadata': {}
            },
            'processing_metadata': {
                'vectorization_version': '3.0.0',
                'processing_pipeline': 'Error_Handling_Pipeline',
                'optimization_features': ['error_handling', 'graceful_degradation']
            }
        }
    
    def vectorize_batch(self, tables: List[Dict]) -> List[Dict[str, Any]]:
        """
        批量表格向量化
        """
        vectorized_tables = []
        
        for i, table_item in enumerate(tables):
            try:
                # 获取表格内容
                table_content = table_item.get('table_content', '')
                metadata = table_item.get('metadata', {})
                
                if not table_content:
                    logging.warning(f"表格 {i+1} 缺少内容")
                    continue
                
                # 执行向量化
                vectorization_result = self.vectorize(table_content, metadata)
                
                # 更新表格项信息
                table_item.update(vectorization_result)
                vectorized_tables.append(table_item)
                
                # API限流控制
                if (i + 1) % self.batch_size == 0 and i < len(tables) - 1:
                    logging.info(f"批量向量化进度: {i+1}/{len(tables)}，等待 {self.delay_seconds} 秒...")
                    time.sleep(self.delay_seconds)
                
            except Exception as e:
                error_msg = f"批量向量化表格 {i+1} 失败: {str(e)}"
                logging.error(error_msg)
                self.failure_handler.record_failure(table_item, 'batch_table_vectorization', str(e))
                
                # 创建错误结果
                error_result = self._create_error_vectorization_result(str(e))
                table_item.update(error_result)
                vectorized_tables.append(table_item)
        
        logging.info(f"批量表格向量化完成: {len(vectorized_tables)}/{len(tables)} 成功")
        return vectorized_tables
    
    def get_vectorization_status(self) -> Dict[str, Any]:
        """
        获取向量化状态信息
        """
        return {
            'vectorizer_type': 'table_vectorizer',
            'status': 'ready',
            'table_embedding_model': self.text_embedding_model,
            'batch_size': self.batch_size,
            'delay_seconds': self.delay_seconds,
            'capabilities': [
                'table_preprocessing',
                'single_vectorization',
                'batch_processing',
                'api_rate_limiting',
                'quality_assessment',
                'table_analysis'
            ],
            'version': '3.0.0'
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        """
        return {
            'table_model': {
                'name': self.text_embedding_model,
                'type': 'text_embedding',
                'provider': 'dashscope',
                'capabilities': ['table_understanding', 'structured_data_embedding']
            }
        }
    
    def validate_vectorization_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证向量化结果
        """
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # 检查向量化状态
        if result.get('vectorization_status') != 'success':
            validation_result['is_valid'] = False
            validation_result['issues'].append("向量化状态异常")
        
        # 检查表格向量
        table_embedding = result.get('table_embedding', [])
        if not table_embedding:
            validation_result['is_valid'] = False
            validation_result['issues'].append("表格向量为空")
        elif len(table_embedding) < 256:
            validation_result['warnings'].append("表格向量维度较低")
        
        # 检查模型信息
        if not result.get('table_embedding_model'):
            validation_result['warnings'].append("缺少表格模型信息")
        
        # 检查元数据
        metadata = result.get('vectorization_metadata', {})
        if not metadata.get('table_content_length'):
            validation_result['warnings'].append("缺少表格内容长度信息")
        
        # 生成建议
        if validation_result['warnings']:
            validation_result['recommendations'].append("考虑使用更高维度的向量模型")
        
        if not validation_result['is_valid']:
            validation_result['recommendations'].append("检查向量化流程和模型配置")
        
        return validation_result
    
    def get_vectorization_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取向量化统计信息
        """
        if not results:
            return {
                'total_tables': 0,
                'successful_vectorizations': 0,
                'failed_vectorizations': 0,
                'success_rate': 0.0
            }
        
        total_tables = len(results)
        successful = sum(1 for r in results if r.get('vectorization_status') == 'success')
        failed = total_tables - successful
        success_rate = successful / total_tables if total_tables > 0 else 0
        
        # 向量维度统计
        vector_dimensions = []
        content_lengths = []
        quality_scores = []
        
        for result in results:
            if result.get('vectorization_status') == 'success':
                table_embedding = result.get('table_embedding', [])
                metadata = result.get('vectorization_metadata', {})
                
                if table_embedding:
                    vector_dimensions.append(len(table_embedding))
                
                content_length = metadata.get('table_content_length', 0)
                if content_length:
                    content_lengths.append(content_length)
                
                quality_score = metadata.get('vector_quality', {}).get('quality_score', 0)
                if quality_score:
                    quality_scores.append(quality_score)
        
        return {
            'total_tables': total_tables,
            'successful_vectorizations': successful,
            'failed_vectorizations': failed,
            'success_rate': success_rate,
            'vector_dimensions': {
                'count': len(vector_dimensions),
                'min': min(vector_dimensions) if vector_dimensions else 0,
                'max': max(vector_dimensions) if vector_dimensions else 0,
                'average': sum(vector_dimensions) / len(vector_dimensions) if vector_dimensions else 0
            },
            'content_lengths': {
                'count': len(content_lengths),
                'min': min(content_lengths) if content_lengths else 0,
                'max': max(content_lengths) if content_lengths else 0,
                'average': sum(content_lengths) / len(content_lengths) if content_lengths else 0
            },
            'quality_statistics': {
                'count': len(quality_scores),
                'min': min(quality_scores) if quality_scores else 0,
                'max': max(quality_scores) if quality_scores else 0,
                'average': sum(quality_scores) / len(quality_scores) if quality_scores else 0
            }
        }
