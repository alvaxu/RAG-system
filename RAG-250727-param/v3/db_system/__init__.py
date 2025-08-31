"""
V3版本数据库系统核心包

包含以下核心模块：
- core: 核心处理逻辑
- metadata: 元数据管理
- processors: 处理器模块
- utils: 工具模块
- vectorization: 向量化模块
"""

# 导出主要类
from .core.v3_main_processor import V3MainProcessor
from .core.vector_store_manager import LangChainVectorStoreManager
from .core.metadata_manager import MetadataManager
from .core.vectorization_manager import VectorizationManager
from .core.content_processor import ContentProcessor
from .core.model_caller import LangChainModelCaller

# 导出工具类
from .utils.document_type_detector import DocumentTypeDetector
from .utils.mineru_integration import MinerUIntegration
from .utils.image_completion import ImageCompletion
from .utils.db_diagnostic_tool import DatabaseDiagnosticTool

# 导出处理器
from .processors.image_processor import ImageProcessor
from .processors.image_enhancer import ImageEnhancer

# 导出向量化器
from .vectorization.text_vectorizer import LangChainTextVectorizer
from .vectorization.image_vectorizer import ImageVectorizer
from .vectorization.table_vectorizer import TableVectorizer

__version__ = "3.0.0"
__author__ = "RAG System Team"
__description__ = "V3版本向量数据库构建系统核心包"
