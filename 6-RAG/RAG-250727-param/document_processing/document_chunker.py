'''
程序说明：
## 1. 文档分块器，整合现有的V310_enhanced_document_chunker.py功能
## 2. 统一文档分块接口和错误处理
## 3. 支持文本和表格的分块处理
## 4. 为向量存储提供标准化的文档分块
'''

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain.docstore.document import Document

# 导入增强文档分块功能
from .enhanced_chunker import process_documents_with_tables, EnhancedDocumentChunk

# 配置日志
logger = logging.getLogger(__name__)


class DocumentChunker:
    """
    文档分块器，处理文档分块
    """
    
    def __init__(self, config):
        """
        初始化文档分块器
        :param config: 配置对象
        """
        self.config = config
        # 从配置中读取参数，如果没有则使用默认值
        self.chunk_size = config.get('chunk_size', 1000) if config else 1000
        self.chunk_overlap = config.get('chunk_overlap', 200) if config else 200
    
    def process_documents(self, md_files: List[str]) -> Optional[List[Document]]:
        """
        处理文档分块
        :param md_files: Markdown文件列表
        :return: 文档分块列表
        """
        try:
            if not md_files:
                logger.warning("没有提供Markdown文件")
                return None
            
            logger.info(f"开始处理 {len(md_files)} 个Markdown文件的文档分块")
            
            # 获取第一个文件的目录作为处理目录
            if md_files:
                md_dir = str(Path(md_files[0]).parent)
                logger.info(f"使用目录: {md_dir}")
                
                # 调用现有的文档分块功能
                enhanced_chunks = process_documents_with_tables(
                    md_dir=md_dir,
                    chunk_size=self.chunk_size, 
                    chunk_overlap=self.chunk_overlap
                )
                
                if enhanced_chunks:
                    # 转换为LangChain Document格式
                    documents = []
                    for chunk in enhanced_chunks:
                        doc = Document(
                            page_content=chunk.content,
                            metadata={
                                'document_name': chunk.document_name,
                                'page_number': chunk.page_number,
                                'chunk_index': chunk.chunk_index,
                                'chunk_type': chunk.chunk_type,
                                'table_id': chunk.table_id,
                                'table_type': chunk.table_type
                            }
                        )
                        documents.append(doc)
                    
                    # 统计分块信息
                    text_chunks = [d for d in documents if d.metadata.get('chunk_type') == 'text']
                    table_chunks = [d for d in documents if d.metadata.get('chunk_type') == 'table']
                    
                    logger.info(f"文档分块完成，生成了 {len(documents)} 个分块")
                    logger.info(f"  - 文本分块: {len(text_chunks)} 个")
                    logger.info(f"  - 表格分块: {len(table_chunks)} 个")
                    
                    return documents
                else:
                    logger.error("文档分块失败")
                    return None
            else:
                logger.error("没有有效的Markdown文件")
                return None
                
        except Exception as e:
            logger.error(f"文档分块处理失败: {e}")
            return None
    
    def get_chunk_statistics(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        获取分块统计信息
        :param chunks: 文档分块列表
        :return: 统计信息
        """
        try:
            if not chunks:
                return {'total_chunks': 0}
            
            # 按类型统计
            type_stats = {}
            for chunk in chunks:
                chunk_type = chunk.metadata.get('chunk_type', 'unknown')
                type_stats[chunk_type] = type_stats.get(chunk_type, 0) + 1
            
            # 计算内容长度统计
            content_lengths = [len(chunk.page_content) for chunk in chunks]
            avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
            
            return {
                'total_chunks': len(chunks),
                'type_distribution': type_stats,
                'average_content_length': avg_length,
                'min_content_length': min(content_lengths) if content_lengths else 0,
                'max_content_length': max(content_lengths) if content_lengths else 0
            }
            
        except Exception as e:
            logger.error(f"获取分块统计信息失败: {e}")
            return {'error': str(e)}
    
    def validate_chunks(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        验证文档分块
        :param chunks: 文档分块列表
        :return: 验证结果
        """
        try:
            valid_chunks = []
            invalid_chunks = []
            
            for i, chunk in enumerate(chunks):
                # 检查基本属性
                if not hasattr(chunk, 'page_content') or not chunk.page_content.strip():
                    invalid_chunks.append({
                        'index': i,
                        'error': '内容为空'
                    })
                    continue
                
                if not hasattr(chunk, 'metadata'):
                    invalid_chunks.append({
                        'index': i,
                        'error': '缺少元数据'
                    })
                    continue
                
                # 检查内容长度
                content_length = len(chunk.page_content)
                if content_length < 10:  # 内容太短
                    invalid_chunks.append({
                        'index': i,
                        'error': f'内容太短 ({content_length} 字符)'
                    })
                    continue
                
                valid_chunks.append(chunk)
            
            return {
                'total_chunks': len(chunks),
                'valid_chunks': len(valid_chunks),
                'invalid_chunks': len(invalid_chunks),
                'invalid_chunk_details': invalid_chunks
            }
            
        except Exception as e:
            logger.error(f"验证文档分块失败: {e}")
            return {'error': str(e)}
    
    def set_chunk_parameters(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        设置分块参数
        :param chunk_size: 分块大小
        :param chunk_overlap: 分块重叠
        """
        if chunk_size is not None:
            self.chunk_size = chunk_size
        if chunk_overlap is not None:
            self.chunk_overlap = chunk_overlap
        
        logger.info(f"分块参数已更新: chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}") 