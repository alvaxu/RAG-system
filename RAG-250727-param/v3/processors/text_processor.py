"""
文本处理器

负责处理各种类型的文本内容，包括从PDF解析出的文本、Markdown文件内容、
以及JSON格式的结构化文本数据。完全符合设计文档规范。
"""

import os
import time
import logging
import re
from typing import Dict, List, Any

class TextProcessor:
    """
    文本处理器
    整合：分析 → 分块 → 向量化
    完全符合设计文档规范，位于processors模块下
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()
        
        # 初始化各个组件（符合设计文档规范）
        from .text_analyzer import TextAnalyzer
        self.text_analyzer = TextAnalyzer()
        
        # 使用失败处理（符合设计文档规范）
        self.failure_handler = config_manager.get_failure_handler()
        
        # 加载配置
        self._load_configuration()
        
        logging.info("文本处理器初始化完成")
    
    def _load_configuration(self):
        """
        加载配置
        """
        # 分块配置
        self.chunk_size = self.config.get('document_processing.chunk_size', 1000)
        self.chunk_overlap = self.config.get('document_processing.chunk_overlap', 200)
        
        # 向量化配置
        self.embedding_model = self.config.get('vectorization.text_embedding_model', 'text-embedding-v1')
    
    def process_text(self, text_data: Dict) -> List[Dict[str, Any]]:
        """
        处理单个文本
        """
        try:
            print(f"  📝 处理文本: {text_data.get('text_title', '未命名文本')}")
            
            # 步骤1: 文本结构分析
            print("  步骤1: 文本结构分析...")
            analysis_result = self.text_analyzer.analyze(text_data)
            if analysis_result.get('analysis_status') != 'success':
                print(f"  ⚠️ 文本分析失败: {analysis_result.get('error_message', '未知错误')}")
            
            # 步骤2: 智能文本分块
            print("  步骤2: 智能文本分块...")
            chunks = self._create_text_chunks(text_data, analysis_result)
            print(f"  ✅ 文本分块完成: {len(chunks)} 个分块")
            
            # 步骤3: 生成完整元数据
            print("  步骤3: 生成完整元数据...")
            complete_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = self._create_complete_text_metadata(
                    text_data, chunk, i, analysis_result
                )
                complete_metadata.append(chunk_metadata)
            
            print(f"  ✅ 文本处理完成: {text_data.get('text_title', '未命名文本')}")
            return complete_metadata
            
        except Exception as e:
            error_msg = f"文本处理失败: {e}"
            logging.error(error_msg)
            self.failure_handler.record_failure(text_data, 'text_processing', str(e))
            
            # 返回错误结果
            return [self._create_error_text_metadata(text_data, str(e))]
    
    def process_batch(self, texts: List[Dict]) -> List[List[Dict[str, Any]]]:
        """
        批量处理文本
        """
        processed_texts = []
        
        for i, text in enumerate(texts):
            try:
                print(f"正在处理文本 {i+1}/{len(texts)}")
                result = self.process_text(text)
                processed_texts.append(result)
            except Exception as e:
                error_msg = f"文本批量处理失败: {e}"
                logging.error(error_msg)
                self.failure_handler.record_failure(text, 'text_batch_processing', str(e))
                
                # 创建错误结果
                error_result = [self._create_error_text_metadata(text, str(e))]
                processed_texts.append(error_result)
        
        return processed_texts
    
    def _create_text_chunks(self, text_data: Dict, analysis_result: Dict) -> List[Dict[str, Any]]:
        """
        创建文本分块
        """
        text_content = text_data.get('text_content', '')
        if not text_content:
            return []
        
        # 获取文本结构信息
        structure_info = analysis_result.get('structure', {})
        paragraphs = structure_info.get('paragraphs', 0)
        
        # 如果段落数很少，不需要分块
        if paragraphs <= 1:
            return [{
                'content': text_content,
                'start_pos': 0,
                'end_pos': len(text_content),
                'chunk_index': 0,
                'is_subchunk': False
            }]
        
        # 智能分块：在段落边界分割
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        # 按段落分割
        paragraph_list = text_content.strip().split('\n\n')
        
        for i, paragraph in enumerate(paragraph_list):
            if paragraph.strip():
                paragraph_length = len(paragraph)
                
                # 如果当前块加上新段落会超过限制，且当前块不为空
                if current_length + paragraph_length > self.chunk_size and current_chunk:
                    # 保存当前块
                    chunk_content = '\n\n'.join(current_chunk)
                    chunks.append({
                        'content': chunk_content,
                        'start_pos': 0,  # 简化处理
                        'end_pos': len(chunk_content),
                        'chunk_index': chunk_index,
                        'is_subchunk': len(chunks) > 0
                    })
                    
                    # 开始新块
                    current_chunk = [paragraph]
                    current_length = paragraph_length
                    chunk_index += 1
                else:
                    current_chunk.append(paragraph)
                    current_length += paragraph_length
        
        # 添加最后一个块
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunks.append({
                'content': chunk_content,
                'start_pos': 0,  # 简化处理
                'end_pos': len(chunk_content),
                'chunk_index': chunk_index,
                'is_subchunk': len(chunks) > 0
            })
        
        return chunks if chunks else [{
            'content': text_content,
            'start_pos': 0,
            'end_pos': len(text_content),
            'chunk_index': 0,
            'is_subchunk': False
        }]
    
    def _create_complete_text_metadata(self, text_data: Dict, chunk: Dict, 
                                     chunk_index: int, analysis_result: Dict) -> Dict[str, Any]:
        """
        创建完整的文本元数据，完全符合设计文档的TEXT_METADATA_SCHEMA规范
        """
        return {
            # 基础标识字段（符合COMMON_METADATA_FIELDS）
            'chunk_id': f"{text_data.get('chunk_id', '')}_chunk_{chunk_index}",
            'chunk_type': 'text',
            'source_type': 'pdf',
            'document_name': text_data.get('document_name', ''),
            'document_path': text_data.get('document_path', ''),
            'page_number': text_data.get('page_number', 1),
            'page_idx': text_data.get('page_idx', 1),
            'created_timestamp': text_data.get('created_timestamp', int(time.time())),
            'updated_timestamp': int(time.time()),
            'processing_version': '3.0.0',
            
            # 文本特有字段（符合TEXT_METADATA_SCHEMA）
            'text_id': text_data.get('text_id', ''),
            'text_title': text_data.get('text_title', ''),
            'text_content': chunk.get('content', ''),
            'text_summary': self._generate_text_summary(chunk.get('content', '')),
            
            # 分块信息
            'chunk_info': {
                'chunk_index': chunk_index,
                'start_position': chunk.get('start_pos', 0),
                'end_position': chunk.get('end_pos', 0),
                'chunk_length': len(chunk.get('content', '')),
                'is_subchunk': chunk.get('is_subchunk', False)
            },
            
            # 文本结构信息
            'text_structure': analysis_result.get('structure', {}),
            
            # 文本特征信息
            'text_features': analysis_result.get('features', {}),
            
            # 语义信息
            'semantic_info': analysis_result.get('semantic', {}),
            
            # 相关文本信息
            'related_text': text_data.get('related_text', ''),
            'context_info': text_data.get('context_info', {}),
            
            # 处理状态信息
            'analysis_status': analysis_result.get('analysis_status', 'unknown'),
            'chunking_status': 'success',
            
            # 向量化信息字段（预留）
            'vectorized': False,
            'vectorization_timestamp': None,
            'embedding_model': self.embedding_model,
            'text_embedding': [],
            'vectorization_status': 'pending',
            
            # 关联信息字段
            'related_image_chunks': text_data.get('related_image_chunks', []),
            'related_table_chunks': text_data.get('related_table_chunks', []),
            'parent_document_id': text_data.get('parent_document_id', ''),
            
            # 架构标识
            'metadata_schema': 'TEXT_METADATA_SCHEMA',
            'metadata_version': '3.0.0',
            'processing_pipeline': 'Text_Analysis_Chunking_Pipeline',
            'optimization_features': [
                'modular_design',
                'smart_chunking',
                'complete_metadata',
                'semantic_analysis'
            ]
        }
    
    def _generate_text_summary(self, text_content: str) -> str:
        """
        生成文本摘要
        """
        if not text_content:
            return "空文本"
        
        # 简单的摘要生成：取前100个字符
        if len(text_content) <= 100:
            return text_content
        else:
            return text_content[:100] + "..."
    
    def _create_error_text_metadata(self, text_data: Dict, error_message: str) -> Dict[str, Any]:
        """
        创建错误文本元数据
        """
        return {
            # 基础标识字段
            'chunk_id': text_data.get('chunk_id', ''),
            'chunk_type': 'text',
            'source_type': 'pdf',
            'document_name': text_data.get('document_name', ''),
            'document_path': text_data.get('document_path', ''),
            'page_number': text_data.get('page_number', 1),
            'page_idx': text_data.get('page_idx', 1),
            'created_timestamp': text_data.get('created_timestamp', int(time.time())),
            'updated_timestamp': int(time.time()),
            'processing_version': '3.0.0',
            
            # 错误信息
            'error': error_message,
            'processing_status': 'failed',
            
            # 空的文本字段
            'text_id': text_data.get('text_id', ''),
            'text_title': text_data.get('text_title', ''),
            'text_content': text_data.get('text_content', ''),
            'text_summary': '处理失败',
            
            # 空的处理结果
            'chunk_info': {'chunk_index': 0, 'start_position': 0, 'end_position': 0, 'chunk_length': 0, 'is_subchunk': False},
            'text_structure': {'paragraphs': 0, 'sentences': 0, 'words': 0, 'characters': 0},
            'text_features': {'text_type': 'unknown', 'is_structured': True, 'has_numbers': False, 'has_special_chars': False, 'language': 'unknown', 'complexity_score': 0},
            'semantic_info': {'key_topics': [], 'key_phrases': [], 'sentiment': 'neutral', 'formality': 'medium'},
            
            # 架构标识
            'metadata_schema': 'TEXT_METADATA_SCHEMA',
            'metadata_version': '3.0.0',
            'processing_pipeline': 'Text_Error_Handling',
            'optimization_features': ['error_handling', 'graceful_degradation']
        }
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        获取处理状态
        """
        return {
            'analyzer_status': 'ready',
            'chunking_status': 'ready',
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'embedding_model': self.embedding_model,
            'total_texts_processed': 0  # 可以添加计数器
        }
