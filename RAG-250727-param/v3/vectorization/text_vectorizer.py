"""
LangChain文本向量化器

基于LangChain框架的文本向量化处理，替换原有的自开发版本。
支持文本分割、向量化和批量处理。
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    from langchain_community.embeddings import DashScopeEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain未安装，文本向量化功能将不可用")

class LangChainTextVectorizer:
    """
    LangChain文本向量化器
    
    功能：
    - 使用LangChain文本分割器进行智能分块
    - 通过DashScope API生成文本向量
    - 支持批量文本向量化
    - 生成标准化的向量化结果
    """
    
    def __init__(self, config_manager):
        """
        初始化LangChain文本向量化器
        
        :param config_manager: 配置管理器
        """
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError("LangChain未安装，无法初始化文本向量化器")
        
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        
        # 获取配置参数
        self.text_embedding_model = self.config.get('vectorization.text_embedding_model', 'text-embedding-v1')
        self.batch_size = self.config.get('api_rate_limiting.text_vectorization_batch_size', 10)
        self.delay_seconds = self.config.get('api_rate_limiting.text_vectorization_delay_seconds', 1)
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.get('processing.chunk_size', 1000),
            chunk_overlap=self.config.get('processing.overlap_size', 200),
            separators=["\n\n", "\n", " ", ""]
        )
        
        # 初始化embedding模型
        self._initialize_embedding_model()
        
        logging.info("LangChain文本向量化器初始化完成")
    
    def _initialize_embedding_model(self):
        """初始化embedding模型"""
        try:
            # 获取API密钥
            api_key = self.config_manager.get_environment_manager().get_required_var('DASHSCOPE_API_KEY')
            if not api_key:
                raise ValueError("未找到有效的DashScope API密钥")
            
            # 初始化DashScope Embeddings
            self.embeddings = DashScopeEmbeddings(
                dashscope_api_key=api_key,
                model=self.text_embedding_model
            )
            
            logging.info(f"Embedding模型初始化成功: {self.text_embedding_model}")
            
        except Exception as e:
            logging.error(f"Embedding模型初始化失败: {e}")
            raise
    
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
            text_embedding = self.embeddings.embed_query(processed_text)
            
            # 步骤3: 生成向量化元数据
            vectorization_metadata = self._generate_vectorization_metadata(
                text_embedding, processed_text, metadata
            )
            
            # 整合结果
            vectorization_result = {
                'vectorization_status': 'success',
                'vectorization_timestamp': int(time.time()),
                'vector': text_embedding,
                'text_embedding': text_embedding,  # 添加text_embedding字段，与图片向量器保持一致
                'text_embedding_model': self.text_embedding_model,
                'vectorization_metadata': vectorization_metadata,
                'metadata': metadata or {},  # 添加原始metadata
                'processing_metadata': {
                    'vectorization_version': '3.0.0',
                    'processing_pipeline': 'LangChain_Text_Embedding_Pipeline',
                    'optimization_features': [
                        'langchain_text_splitting',
                        'batch_processing',
                        'api_rate_limiting',
                        'complete_metadata'
                    ]
                }
            }
            
            logging.info(f"文本向量化完成: {len(text_embedding)} 维向量")
            logging.info(f"文本向量化结果包含字段: {list(vectorization_result.keys())}")
            logging.info(f"metadata字段存在: {'metadata' in vectorization_result}")
            if 'metadata' in vectorization_result:
                logging.info(f"metadata内容: {vectorization_result['metadata']}")
            return vectorization_result
            
        except Exception as e:
            error_msg = f"文本向量化失败: {str(e)}"
            logging.error(error_msg)
            
            # 返回错误结果
            return self._create_error_vectorization_result(str(e))
    
    def _preprocess_text(self, text_content: str) -> str:
        """
        文本预处理
        
        :param text_content: 原始文本内容
        :return: 预处理后的文本
        """
        if not text_content:
            return ""
        
        # 基本清理
        processed_text = text_content.strip()
        
        # 移除多余的空白字符
        processed_text = ' '.join(processed_text.split())
        
        # 长度控制（如果超过最大长度）
        max_length = self.config.get('processing.max_text_length', 8000)
        if len(processed_text) > max_length:
            processed_text = processed_text[:max_length] + "..."
            logging.warning(f"文本长度超过限制，已截断到 {max_length} 字符")
        
        return processed_text
    
    def _generate_vectorization_metadata(self, text_embedding: List[float], processed_text: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        生成向量化元数据
        
        :param text_embedding: 文本向量
        :param processed_text: 处理后的文本
        :param metadata: 原始元数据
        :return: 向量化元数据字典
        """
        try:
            # 基础元数据
            vectorization_metadata = {
                'text_content_length': len(processed_text),
                'vector_dimensions': len(text_embedding),
                'vector_quality': self._assess_vector_quality(text_embedding),
                'text_features': self._analyze_text_features(processed_text),
                'embedding_model': self.text_embedding_model,
                'vectorization_timestamp': int(time.time())
            }
            
            return vectorization_metadata
            
        except Exception as e:
            logging.error(f"生成向量化元数据失败: {e}")
            return {
                'error': str(e),
                'embedding_model': self.text_embedding_model,
                'vectorization_timestamp': int(time.time())
            }
    
    def _assess_vector_quality(self, vector: List[float]) -> Dict[str, Any]:
        """
        评估向量质量
        
        :param vector: 向量列表
        :return: 质量评估字典
        """
        try:
            if not vector:
                return {'quality_score': 0.0, 'quality_level': 'poor'}
            
            # 计算质量指标
            min_value = min(vector)
            max_value = max(vector)
            zero_count = sum(1 for x in vector if abs(x) < 1e-6)
            zero_ratio = zero_count / len(vector)
            
            # 计算质量分数
            quality_score = 1.0 - zero_ratio
            
            # 确定质量级别
            if quality_score >= 0.9:
                quality_level = 'excellent'
            elif quality_score >= 0.7:
                quality_level = 'good'
            elif quality_score >= 0.5:
                quality_level = 'fair'
            else:
                quality_level = 'poor'
            
            return {
                'quality_score': quality_score,
                'quality_level': quality_level,
                'issues': ['向量数值范围较小'] if max_value - min_value < 0.5 else [],
                'dimensions': len(vector),
                'min_value': min_value,
                'max_value': max_value,
                'zero_ratio': zero_ratio
            }
            
        except Exception as e:
            logging.error(f"向量质量评估失败: {e}")
            return {'quality_score': 0.0, 'quality_level': 'unknown', 'error': str(e)}
    
    def _analyze_text_features(self, text: str) -> Dict[str, Any]:
        """
        分析文本特征
        
        :param text: 文本内容
        :return: 特征分析字典
        """
        try:
            if not text:
                return {}
            
            # 字符统计
            total_chars = len(text)
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            english_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
            digit_chars = sum(1 for c in text if c.isdigit())
            
            # 结构统计
            lines = text.split('\n')
            total_lines = len(lines)
            non_empty_lines = len([line for line in lines if line.strip()])
            
            # 特征判断
            has_numbers = digit_chars > 0
            has_separators = any(sep in text for sep in ['|', ';', ',', '，', '；'])
            is_structured = has_separators or (non_empty_lines > 1 and total_lines > 2)
            
            return {
                'character_statistics': {
                    'total': total_chars,
                    'chinese': chinese_chars,
                    'english': english_chars,
                    'digits': digit_chars,
                    'separators': sum(1 for c in text if c in '|;,，；')
                },
                'structure_statistics': {
                    'total_lines': total_lines,
                    'non_empty_lines': non_empty_lines,
                    'fill_rate': non_empty_lines / total_lines if total_lines > 0 else 0
                },
                'text_features': {
                    'has_numbers': has_numbers,
                    'has_separators': has_separators,
                    'is_structured': is_structured
                }
            }
            
        except Exception as e:
            logging.error(f"文本特征分析失败: {e}")
            return {'error': str(e)}
    
    def _create_error_vectorization_result(self, error_message: str) -> Dict[str, Any]:
        """
        创建错误向量化结果
        
        :param error_message: 错误消息
        :return: 错误结果字典
        """
        return {
            'vectorization_status': 'failed',
            'vectorization_timestamp': int(time.time()),
            'error_message': error_message,
            'text_embedding': [],
            'text_embedding_model': self.text_embedding_model,
            'vectorization_metadata': {
                'error': error_message,
                'embedding_model': self.text_embedding_model,
                'vectorization_timestamp': int(time.time())
            },
            'processing_metadata': {
                'vectorization_version': '3.0.0',
                'processing_pipeline': 'LangChain_Text_Embedding_Pipeline',
                'error_occurred': True
            }
        }
    
    def vectorize_batch(self, texts: List[str], metadatas: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        批量文本向量化
        
        :param texts: 文本列表
        :param metadatas: 元数据列表
        :return: 向量化结果列表
        """
        try:
            if not texts:
                return []
            
            # 确保元数据列表长度匹配
            if metadatas is None:
                metadatas = [{} for _ in texts]
            elif len(metadatas) != len(texts):
                raise ValueError("文本列表和元数据列表长度不匹配")
            
            logging.info(f"开始批量向量化 {len(texts)} 个文本")
            
            results = []
            for i, (text, metadata) in enumerate(zip(texts, metadatas)):
                try:
                    # 向量化单个文本
                    result = self.vectorize(text, metadata)
                    results.append(result)
                    
                    # 批量大小控制和延迟
                    if (i + 1) % self.batch_size == 0 and i < len(texts) - 1:
                        time.sleep(self.delay_seconds)
                        logging.info(f"已处理 {i + 1}/{len(texts)} 个文本")
                    
                except Exception as e:
                    logging.error(f"批量向量化第 {i} 个文本失败: {e}")
                    error_result = self._create_error_vectorization_result(str(e))
                    results.append(error_result)
            
            logging.info(f"批量向量化完成，成功处理 {len([r for r in results if r['vectorization_status'] == 'success'])}/{len(texts)} 个文本")
            return results
            
        except Exception as e:
            logging.error(f"批量向量化失败: {e}")
            return [self._create_error_vectorization_result(str(e)) for _ in texts]
    
    def split_text(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
        """
        分割文本为块
        
        :param text: 原始文本
        :param chunk_size: 块大小
        :param chunk_overlap: 块重叠大小
        :return: 文本块列表
        """
        try:
            if chunk_size:
                self.text_splitter.chunk_size = chunk_size
            if chunk_overlap:
                self.text_splitter.chunk_overlap = chunk_overlap
            
            # 使用LangChain文本分割器
            chunks = self.text_splitter.split_text(text)
            
            logging.info(f"文本分割完成，生成了 {len(chunks)} 个块")
            return chunks
            
        except Exception as e:
            logging.error(f"文本分割失败: {e}")
            return [text]  # 分割失败时返回原文本
    
    def create_documents(self, texts: List[str], metadatas: List[Dict] = None) -> List[Document]:
        """
        创建LangChain Document对象
        
        :param texts: 文本列表
        :param metadatas: 元数据列表
        :return: Document对象列表
        """
        try:
            if not texts:
                return []
            
            # 确保元数据列表长度匹配
            if metadatas is None:
                metadatas = [{} for _ in texts]
            elif len(metadatas) != len(texts):
                raise ValueError("文本列表和元数据列表长度不匹配")
            
            # 创建Document对象
            documents = []
            for text, metadata in zip(texts, metadatas):
                doc = Document(
                    page_content=text,
                    metadata=metadata
                )
                documents.append(doc)
            
            logging.info(f"成功创建 {len(documents)} 个Document对象")
            return documents
            
        except Exception as e:
            logging.error(f"创建Document对象失败: {e}")
            return []
    
    def get_vectorization_status(self) -> Dict[str, Any]:
        """
        获取向量化状态
        
        :return: 状态信息字典
        """
        return {
            'text_embedding_model': self.text_embedding_model,
            'batch_size': self.batch_size,
            'delay_seconds': self.delay_seconds,
            'langchain_available': LANGCHAIN_AVAILABLE,
            'chunk_size': getattr(self.text_splitter, 'chunk_size', 'unknown'),
            'chunk_overlap': getattr(self.text_splitter, 'chunk_overlap', 'unknown')
        }
    
    def validate_vectorization_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证向量化结果
        
        :param result: 向量化结果字典
        :return: 验证结果字典
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
        if not metadata.get('text_content_length'):
            validation_result['warnings'].append("缺少文本内容长度信息")
        
        # 生成建议
        if validation_result['warnings']:
            validation_result['recommendations'].append("考虑使用更高维度的向量模型")
        
        if not validation_result['is_valid']:
            validation_result['recommendations'].append("检查向量化流程和模型配置")
        
        return validation_result
    
    def get_vectorization_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取向量化统计信息
        
        :param results: 向量化结果列表
        :return: 统计信息字典
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
        content_lengths = []
        quality_scores = []
        
        for result in results:
            if result.get('vectorization_status') == 'success':
                text_embedding = result.get('text_embedding', [])
                metadata = result.get('vectorization_metadata', {})
                
                if text_embedding:
                    vector_dimensions.append(len(text_embedding))
                
                content_length = metadata.get('text_content_length', 0)
                if content_length:
                    content_lengths.append(content_length)
                
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
