'''
程序说明：
## 1. 简化的向量存储管理模块
## 2. 只负责向量存储的加载、验证和搜索功能
## 3. 不重复vector_generator.py的创建功能
## 4. 提供向量存储的统计和验证功能
'''

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.schema import Document

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key

# 配置日志
logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    向量存储管理器类 - 只负责加载、验证和搜索
    """
    
    def __init__(self, api_key: str = None, config: dict = None):
        """
        初始化向量存储管理器
        :param api_key: DashScope API密钥
        :param config: 配置对象
        """
        # 使用统一的API密钥管理模块获取API密钥
        if api_key and api_key.strip():
            self.api_key = api_key
        else:
            # 从配置对象获取
            config_key = config.get('dashscope_api_key', '') if config else ''
            self.api_key = get_dashscope_api_key(config_key)
        
        self.config = config or {}
        self.embeddings = None
        
        if self.api_key and self.api_key.strip():
            # 从配置中获取嵌入模型名称，如果没有则使用默认值
            embedding_model = self.config.get('text_embedding_model', 'text-embedding-v1')
            self.embeddings = DashScopeEmbeddings(dashscope_api_key=self.api_key, model=embedding_model)
            logger.info("DashScope Embeddings初始化成功")
        else:
            logger.warning("未配置有效的DashScope API密钥，向量存储功能将受限")
    
    def load_vector_store(self, load_path: str) -> Optional[FAISS]:
        """
        加载向量存储
        :param load_path: 加载路径
        :return: FAISS向量存储实例
        """
        if not self.embeddings:
            logger.error("API密钥未配置，无法加载向量存储")
            return None
        
        try:
            if not os.path.exists(load_path):
                logger.error(f"向量存储路径不存在: {load_path}")
                return None
            
            # 检查必要文件是否存在
            index_file = os.path.join(load_path, "index.faiss")
            pkl_file = os.path.join(load_path, "index.pkl")
            
            if not os.path.exists(index_file) or not os.path.exists(pkl_file):
                logger.error(f"向量存储文件不完整: {load_path}")
                return None
            
            # 加载向量存储
            # 从配置中获取安全反序列化设置，如果没有则使用默认值
            allow_dangerous_deserialization = self.config.get('allow_dangerous_deserialization', True)
            vector_store = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=allow_dangerous_deserialization)
            
            logger.info(f"向量存储加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
            return vector_store
            
        except Exception as e:
            logger.error(f"加载向量存储失败: {e}")
            return None
    
    def get_vector_store_statistics(self, vector_store: FAISS) -> Dict[str, Any]:
        """
        获取向量存储统计信息
        :param vector_store: FAISS向量存储实例
        :return: 统计信息
        """
        if not vector_store:
            return {'error': '向量存储为空'}
        
        try:
            # 统计文档类型
            doc_types = {}
            text_docs = 0
            table_docs = 0
            image_docs = 0
            
            for doc in vector_store.docstore._dict.values():
                chunk_type = doc.metadata.get('chunk_type', 'text')
                doc_types[chunk_type] = doc_types.get(chunk_type, 0) + 1
                
                if chunk_type == 'text':
                    text_docs += 1
                elif chunk_type == 'table':
                    table_docs += 1
                elif chunk_type == 'image':
                    image_docs += 1
            
            # 统计文档来源
            doc_sources = {}
            for doc in vector_store.docstore._dict.values():
                doc_name = doc.metadata.get('document_name', '未知文档')
                doc_sources[doc_name] = doc_sources.get(doc_name, 0) + 1
            
            return {
                'total_documents': len(vector_store.docstore._dict),
                'index_size': vector_store.index.ntotal,
                'document_types': doc_types,
                'text_documents': text_docs,
                'table_documents': table_docs,
                'image_documents': image_docs,
                'document_sources': doc_sources,
                'embedding_dimension': vector_store.index.d if hasattr(vector_store.index, 'd') else '未知'
            }
            
        except Exception as e:
            logger.error(f"获取向量存储统计信息失败: {e}")
            return {'error': str(e)}
    
    def validate_vector_store(self, vector_store: FAISS) -> bool:
        """
        验证向量存储
        :param vector_store: FAISS向量存储实例
        :return: 是否有效
        """
        if not vector_store:
            return False
        
        try:
            # 检查基本属性
            if not hasattr(vector_store, 'index') or not hasattr(vector_store, 'docstore'):
                logger.error("向量存储缺少必要属性")
                return False
            
            # 检查索引和文档存储的一致性
            index_total = vector_store.index.ntotal
            docstore_count = len(vector_store.docstore._dict)
            
            if index_total != docstore_count:
                logger.error(f"索引和文档存储不一致: 索引数量={index_total}, 文档数量={docstore_count}")
                return False
            
            # 检查是否有文档
            if docstore_count == 0:
                logger.warning("向量存储为空")
                return False
            
            logger.info(f"向量存储验证通过，包含 {docstore_count} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"验证向量存储时发生错误: {e}")
            return False
    
    def search_similar(self, vector_store: FAISS, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        相似性搜索
        :param vector_store: FAISS向量存储实例
        :param query: 查询文本
        :param k: 返回结果数量
        :return: 搜索结果列表
        """
        if not vector_store:
            return []
        
        try:
            # 执行相似性搜索
            docs = vector_store.similarity_search(query, k=k)
            
            # 格式化结果
            results = []
            for doc in docs:
                result = {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'document_name': doc.metadata.get('document_name', '未知文档'),
                    'page_number': doc.metadata.get('page_number', 0),
                    'chunk_type': doc.metadata.get('chunk_type', 'text')
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"相似性搜索失败: {e}")
            return []
    
    def check_vector_store_files(self, vector_db_path: str) -> Dict[str, Any]:
        """
        检查向量存储文件完整性
        :param vector_db_path: 向量数据库路径
        :return: 文件检查结果
        """
        try:
            if not os.path.exists(vector_db_path):
                return {
                    'exists': False,
                    'error': '路径不存在'
                }
            
            # 检查必要文件
            index_file = os.path.join(vector_db_path, "index.faiss")
            pkl_file = os.path.join(vector_db_path, "index.pkl")
            metadata_file = os.path.join(vector_db_path, "metadata.pkl")
            
            files_status = {
                'index.faiss': os.path.exists(index_file),
                'index.pkl': os.path.exists(pkl_file),
                'metadata.pkl': os.path.exists(metadata_file)
            }
            
            # 获取文件大小
            file_sizes = {}
            for filename, exists in files_status.items():
                file_path = os.path.join(vector_db_path, filename)
                if exists:
                    file_sizes[filename] = os.path.getsize(file_path)
                else:
                    file_sizes[filename] = 0
            
            return {
                'exists': True,
                'files_status': files_status,
                'file_sizes': file_sizes,
                'all_files_present': all(files_status.values()),
                'missing_files': [k for k, v in files_status.items() if not v]
            }
            
        except Exception as e:
            return {
                'exists': False,
                'error': str(e)
            } 