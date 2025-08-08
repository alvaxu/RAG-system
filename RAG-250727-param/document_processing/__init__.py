'''
程序说明：
## 1. 文档处理模块的统一入口
## 2. 提供从PDF到向量数据库的完整处理流程
## 3. 整合现有的所有文档处理功能
## 4. 统一接口和错误处理
## 5. 解决向量存储ID映射问题
'''

from .pipeline import DocumentProcessingPipeline
from .pdf_processor import PDFProcessor
from .markdown_processor import MarkdownProcessor
from .image_extractor import ImageExtractor
from .document_chunker import DocumentChunker
from .table_processor import TableProcessor
from .vector_generator import VectorGenerator

__all__ = [
    'DocumentProcessingPipeline',
    'PDFProcessor',
    'MarkdownProcessor', 
    'ImageExtractor',
    'DocumentChunker',
    'TableProcessor',
    'VectorGenerator'
] 