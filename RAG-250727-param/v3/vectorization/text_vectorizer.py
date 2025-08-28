"""
文本向量化器

负责文本内容的向量化处理，通过ModelCaller调用文本嵌入模型。
完全符合设计文档规范，位于vectorization模块下。
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

class TextVectorizer:
    """
    文本向量化器
    
    功能：
    - 通过ModelCaller调用文本嵌入模型
    - 支持批量文本向量化
    - 生成标准化的向量化结果
    - 完全符合设计文档规范
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        self.text_embedding_model = self.config.get('vectorization.text_embedding_model', 'text-embedding-v1')
        self.batch_size = self.config.get('api_rate_limiting.text_vectorization_batch_size', 10)
        self.delay_seconds = self.config.get('api_rate_limiting.text_vectorization_delay_seconds', 1)
        self.failure_handler = config_manager.get_failure_handler()
        
        # 初始化ModelCaller
        from utils.model_caller import ModelCaller
        self.model_caller = ModelCaller(config_manager)
        
        logging.info("文本向量化器初始化完成")
    
    def vectorize(self, text_content: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        对单个文本进行向量化
        
        :param text_content: 文本内容
        :param metadata: 文本元数据
        :return: 向量化结果字典
        """
        try:
            if not text_content or not text_content.strip():
                raise ValueError("文本内容为空")
            
            logging.info(f"开始向量化文本: {text_content[:50]}...")
            
            # 步骤1: 文本预处理
            processed_text = self._preprocess_text(text_content)
            
            # 步骤2: 调用文本向量化模型
            text_embedding = self._call_text_embedding_model(processed_text)
            
            # 步骤3: 生成向量化元数据
            vectorization_metadata = self._generate_vectorization_metadata(
                text_embedding, processed_text, metadata
            )
            
            # 整合结果
            vectorization_result = {
                'vectorization_status': 'success',
                'vectorization_timestamp': int(time.time()),
                'text_embedding': text_embedding,
                'text_embedding_model': self.text_embedding_model,
                'vectorization_metadata': vectorization_metadata,
                'processing_metadata': {
                    'vectorization_version': '3.0.0',
                    'processing_pipeline': 'Text_Embedding_Pipeline',
                    'optimization_features': [
                        'text_preprocessing',
                        'batch_processing',
                        'api_rate_limiting',
                        'complete_metadata'
                    ]
                }
            }
            
            logging.info(f"文本向量化完成: {len(text_embedding)} 维向量")
            return vectorization_result
            
        except Exception as e:
            error_msg = f"文本向量化失败: {str(e)}"
            logging.error(error_msg)
            self.failure_handler.record_failure(text_content, 'text_vectorization', str(e))
            
            # 返回错误结果
            return self._create_error_vectorization_result(str(e))
    
    def _preprocess_text(self, text_content: str) -> str:
        """
        文本预处理
        """
        if not text_content:
            return ""
        
        # 移除多余的空白字符
        processed_text = ' '.join(text_content.split())
        
        # 移除特殊字符（保留中文、英文、数字、基本标点）
        import re
        processed_text = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：""''（）【】]', '', processed_text)
        
        # 限制文本长度（避免过长的文本）
        max_length = self.config.get('vectorization.max_text_length', 8000)
        if len(processed_text) > max_length:
            processed_text = processed_text[:max_length] + "..."
            logging.info(f"文本长度超过限制，已截断至 {max_length} 字符")
        
        return processed_text.strip()
    
    def _call_text_embedding_model(self, processed_text: str) -> List[float]:
        """
        调用文本向量化模型
        """
        try:
            # 调用ModelCaller进行文本向量化
            text_embedding = self.model_caller.call_text_embedding(processed_text)
            
            if not text_embedding:
                raise ValueError("文本向量生成失败")
            
            return text_embedding
            
        except Exception as e:
            logging.error(f"文本向量化模型调用失败: {e}")
            raise
    
    def _generate_vectorization_metadata(self, text_embedding: List[float], processed_text: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        生成向量化元数据
        """
        return {
            'text_length': len(processed_text),
            'vector_dimensions': len(text_embedding) if text_embedding else 0,
            'vector_quality': self._assess_vector_quality(text_embedding),
            'text_features': self._analyze_text_features(processed_text),
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
    
    def _analyze_text_features(self, text: str) -> Dict[str, Any]:
        """
        分析文本特征
        """
        if not text:
            return {}
        
        import re
        
        # 字符统计
        total_chars = len(text)
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        digit_chars = len(re.findall(r'\d', text))
        space_chars = len(re.findall(r'\s', text))
        
        # 词汇统计
        words = text.split()
        word_count = len(words)
        unique_words = len(set(words))
        
        # 句子统计
        sentences = re.split(r'[。！？.!?]', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # 语言检测
        if chinese_chars > english_chars:
            primary_language = 'chinese'
        elif english_chars > chinese_chars:
            primary_language = 'english'
        else:
            primary_language = 'mixed'
        
        return {
            'character_statistics': {
                'total': total_chars,
                'chinese': chinese_chars,
                'english': english_chars,
                'digits': digit_chars,
                'spaces': space_chars
            },
            'word_statistics': {
                'total': word_count,
                'unique': unique_words,
                'diversity': unique_words / word_count if word_count > 0 else 0
            },
            'sentence_statistics': {
                'count': sentence_count,
                'avg_length': word_count / sentence_count if sentence_count > 0 else 0
            },
            'language_info': {
                'primary_language': primary_language,
                'chinese_ratio': chinese_chars / total_chars if total_chars > 0 else 0,
                'english_ratio': english_chars / total_chars if total_chars > 0 else 0
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
            'text_embedding': [],
            'text_embedding_model': self.text_embedding_model,
            'vectorization_metadata': {
                'text_length': 0,
                'vector_dimensions': 0,
                'vector_quality': {'quality_score': 0, 'quality_level': 'poor'},
                'text_features': {},
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
    
    def vectorize_batch(self, texts: List[Dict]) -> List[Dict[str, Any]]:
        """
        批量文本向量化
        """
        vectorized_texts = []
        
        for i, text_item in enumerate(texts):
            try:
                # 获取文本内容
                text_content = text_item.get('text_content', '')
                metadata = text_item.get('metadata', {})
                
                if not text_content:
                    logging.warning(f"文本 {i+1} 缺少内容")
                    continue
                
                # 执行向量化
                vectorization_result = self.vectorize(text_content, metadata)
                
                # 更新文本项信息
                text_item.update(vectorization_result)
                vectorized_texts.append(text_item)
                
                # API限流控制
                if (i + 1) % self.batch_size == 0 and i < len(texts) - 1:
                    logging.info(f"批量向量化进度: {i+1}/{len(texts)}，等待 {self.delay_seconds} 秒...")
                    time.sleep(self.delay_seconds)
                
            except Exception as e:
                error_msg = f"批量向量化文本 {i+1} 失败: {str(e)}"
                logging.error(error_msg)
                self.failure_handler.record_failure(text_item, 'batch_text_vectorization', str(e))
                
                # 创建错误结果
                error_result = self._create_error_vectorization_result(str(e))
                text_item.update(error_result)
                vectorized_texts.append(text_item)
        
        logging.info(f"批量文本向量化完成: {len(vectorized_texts)}/{len(texts)} 成功")
        return vectorized_texts
    
    def get_vectorization_status(self) -> Dict[str, Any]:
        """
        获取向量化状态信息
        """
        return {
            'vectorizer_type': 'text_vectorizer',
            'status': 'ready',
            'text_embedding_model': self.text_embedding_model,
            'batch_size': self.batch_size,
            'delay_seconds': self.delay_seconds,
            'capabilities': [
                'text_preprocessing',
                'single_vectorization',
                'batch_processing',
                'api_rate_limiting',
                'quality_assessment',
                'text_analysis'
            ],
            'version': '3.0.0'
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        """
        return {
            'text_model': {
                'name': self.text_embedding_model,
                'type': 'text_embedding',
                'provider': 'dashscope',
                'capabilities': ['text_understanding', 'semantic_feature_extraction']
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
        
        # 检查文本向量
        text_embedding = result.get('text_embedding', [])
        if not text_embedding:
            validation_result['is_valid'] = False
            validation_result['issues'].append("文本向量为空")
        elif len(text_embedding) < 256:
            validation_result['warnings'].append("文本向量维度较低")
        
        # 检查模型信息
        if not result.get('text_embedding_model'):
            validation_result['warnings'].append("缺少文本模型信息")
        
        # 检查元数据
        metadata = result.get('vectorization_metadata', {})
        if not metadata.get('text_length'):
            validation_result['warnings'].append("缺少文本长度信息")
        
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
                'total_texts': 0,
                'successful_vectorizations': 0,
                'failed_vectorizations': 0,
                'success_rate': 0.0
            }
        
        total_texts = len(results)
        successful = sum(1 for r in results if r.get('vectorization_status') == 'success')
        failed = total_texts - successful
        success_rate = successful / total_texts if total_texts > 0 else 0
        
        # 向量维度统计
        vector_dimensions = []
        text_lengths = []
        quality_scores = []
        
        for result in results:
            if result.get('vectorization_status') == 'success':
                text_embedding = result.get('text_embedding', [])
                metadata = result.get('vectorization_metadata', {})
                
                if text_embedding:
                    vector_dimensions.append(len(text_embedding))
                
                text_length = metadata.get('text_length', 0)
                if text_length:
                    text_lengths.append(text_length)
                
                quality_score = metadata.get('vector_quality', {}).get('quality_score', 0)
                if quality_score:
                    quality_scores.append(quality_score)
        
        return {
            'total_texts': total_texts,
            'successful_vectorizations': successful,
            'failed_vectorizations': failed,
            'success_rate': success_rate,
            'vector_dimensions': {
                'count': len(vector_dimensions),
                'min': min(vector_dimensions) if vector_dimensions else 0,
                'max': max(vector_dimensions) if vector_dimensions else 0,
                'average': sum(vector_dimensions) / len(vector_dimensions) if vector_dimensions else 0
            },
            'text_lengths': {
                'count': len(text_lengths),
                'min': min(text_lengths) if text_lengths else 0,
                'max': max(text_lengths) if text_lengths else 0,
                'average': sum(text_lengths) / len(text_lengths) if text_lengths else 0
            },
            'quality_statistics': {
                'count': len(quality_scores),
                'min': min(quality_scores) if quality_scores else 0,
                'max': max(quality_scores) if quality_scores else 0,
                'average': sum(quality_scores) / len(quality_scores) if quality_scores else 0
            }
        }
