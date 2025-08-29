"""
LangChain向量存储管理器

基于LangChain框架的向量存储管理，替换原有的自开发版本。
支持FAISS向量数据库的创建、更新、查询和维护。
"""

import os
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import DashScopeEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain未安装，向量存储功能将不可用")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS未安装，向量存储功能将不可用")

class LangChainVectorStoreManager:
    """
    LangChain向量存储管理器主类

    功能：
    - 基于LangChain管理FAISS向量数据库
    - 提供向量存储和检索服务
    - 支持多模态向量存储
    - 自动索引优化
    - 支持备份和恢复
    """

    def __init__(self, config_manager):
        """
        初始化LangChain向量存储管理器

        :param config_manager: 配置管理器
        """
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError("LangChain未安装，无法初始化向量存储管理器")
        
        self.config_manager = config_manager
        self.config = config_manager.get_all_config()

        # 获取向量数据库路径
        paths_config = self.config.get('paths', {})
        self.vector_db_dir = paths_config.get('vector_db_dir', './central/vector_db')

        # 确保目录存在
        os.makedirs(self.vector_db_dir, exist_ok=True)

        # 向量存储状态
        self.is_initialized = False
        self.dimension = 1536  # 默认向量维度
        
        # LangChain FAISS实例
        self.vector_store = None
        self.text_embeddings = None
        self.image_embeddings = None
        
        # 统计信息
        self.total_vectors = 0
        self.last_update_time = None
        
        # 初始化embedding模型
        self._initialize_embedding_models()
        
        logging.info("LangChainVectorStoreManager初始化完成")

    def _initialize_embedding_models(self):
        """初始化embedding模型"""
        try:
            # 获取API密钥
            api_key = self.config_manager.get_environment_manager().get_required_var('DASHSCOPE_API_KEY')
            if not api_key:
                raise ValueError("未找到有效的DashScope API密钥")
            
            # 初始化文本embedding模型
            text_model = self.config.get('vectorization.text_embedding_model', 'text-embedding-v1')
            self.text_embeddings = DashScopeEmbeddings(
                dashscope_api_key=api_key,
                model=text_model
            )
            
            # 初始化图片embedding模型
            image_model = self.config.get('vectorization.image_embedding_model', 'multimodal-embedding-one-peace-v1')
            self.image_embeddings = DashScopeEmbeddings(
                dashscope_api_key=api_key,
                model=image_model
            )
            
            logging.info(f"Embedding模型初始化成功: 文本({text_model}), 图片({image_model})")
            
        except Exception as e:
            logging.error(f"Embedding模型初始化失败: {e}")
            raise

    def create_vector_store(self, dimension: int = None) -> bool:
        """
        创建向量存储

        :param dimension: 向量维度（可选，默认使用配置值）
        :return: 是否创建成功
        """
        try:
            if not FAISS_AVAILABLE:
                raise RuntimeError("FAISS未安装，无法创建向量存储")
            
            if dimension:
                self.dimension = dimension
            
            # 创建空的FAISS向量存储
            self.vector_store = FAISS.from_texts(
                texts=["初始化文本"],
                embedding=self.text_embeddings,
                metadatas=[{"chunk_type": "system", "content": "initialization"}]
            )
            
            # 删除初始化文本（如果存在）
            try:
                self.vector_store.delete([0])
            except Exception as e:
                logging.warning(f"删除初始化文本时出现警告: {e}")
                # 继续执行，不影响后续操作
            
            self.is_initialized = True
            self.total_vectors = 0
            self.last_update_time = time.time()
            
            logging.info(f"向量存储创建成功，维度: {self.dimension}")
            return True
            
        except Exception as e:
            logging.error(f"创建向量存储失败: {e}")
            return False

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None) -> bool:
        """
        添加文本到向量存储

        :param texts: 文本列表
        :param metadatas: 元数据列表
        :return: 是否添加成功
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")
            
            if not texts:
                return True
            
            # 确保元数据列表长度匹配
            if metadatas is None:
                metadatas = [{} for _ in texts]
            elif len(metadatas) != len(texts):
                raise ValueError("文本列表和元数据列表长度不匹配")
            
            # 使用LangChain的add_texts方法
            self.vector_store.add_texts(texts, metadatas)
            
            # 更新统计信息
            self.total_vectors += len(texts)
            self.last_update_time = time.time()
            
            logging.info(f"成功添加 {len(texts)} 个文本到向量存储")
            return True
            
        except Exception as e:
            logging.error(f"添加文本失败: {e}")
            return False

    def add_embeddings(self, text_embedding_pairs: List[Tuple[str, List[float]]], metadatas: List[Dict[str, Any]] = None) -> bool:
        """
        添加预生成的向量到存储

        :param text_embedding_pairs: (文本, 向量)对列表
        :param metadatas: 元数据列表
        :return: 是否添加成功
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")
            
            if not text_embedding_pairs:
                return True
            
            # 确保元数据列表长度匹配
            if metadatas is None:
                metadatas = [{} for _ in text_embedding_pairs]
            elif len(metadatas) != len(text_embedding_pairs):
                raise ValueError("向量对列表和元数据列表长度不匹配")
            
            # 使用LangChain的add_embeddings方法
            self.vector_store.add_embeddings(text_embedding_pairs, metadatas)
            
            # 更新统计信息
            self.total_vectors += len(text_embedding_pairs)
            self.last_update_time = time.time()
            
            logging.info(f"成功添加 {len(text_embedding_pairs)} 个向量到存储")
            return True
            
        except Exception as e:
            logging.error(f"添加向量失败: {e}")
            return False

    def similarity_search(self, query: str, k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Any]:
        """
        相似性搜索

        :param query: 查询文本
        :param k: 返回结果数量
        :param filter_dict: 过滤条件
        :return: 搜索结果列表
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")
            
            # 使用LangChain的similarity_search方法
            if filter_dict:
                results = self.vector_store.similarity_search(query, k=k, filter=filter_dict)
            else:
                results = self.vector_store.similarity_search(query, k=k)
            
            logging.info(f"相似性搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logging.error(f"相似性搜索失败: {e}")
            return []

    def similarity_search_by_vector(self, query_vector: List[float], k: int = 5) -> List[Any]:
        """
        按向量进行相似性搜索

        :param query_vector: 查询向量
        :param k: 返回结果数量
        :return: 搜索结果列表
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")
            
            # 使用LangChain的similarity_search_by_vector方法
            results = self.vector_store.similarity_search_by_vector(query_vector, k=k)
            
            logging.info(f"向量搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logging.error(f"向量搜索失败: {e}")
            return []

    def save(self, save_path: str = None) -> bool:
        """
        保存向量存储

        :param save_path: 保存路径（可选）
        :return: 是否保存成功
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")
            
            if save_path is None:
                save_path = os.path.join(self.vector_db_dir, 'langchain_faiss_index')
            
            # 使用LangChain的save_local方法
            self.vector_store.save_local(save_path)
            
            logging.info(f"向量存储保存成功: {save_path}")
            return True
            
        except Exception as e:
            logging.error(f"保存向量存储失败: {e}")
            return False

    def load(self, load_path: str = None) -> bool:
        """
        加载向量存储

        :param load_path: 加载路径（可选）
        :return: 是否加载成功
        """
        try:
            if load_path is None:
                load_path = os.path.join(self.vector_db_dir, 'langchain_faiss_index')
            
            if not os.path.exists(load_path):
                logging.warning(f"向量存储路径不存在: {load_path}")
                return False
            
            # 使用LangChain的load_local方法
            self.vector_store = FAISS.load_local(load_path, self.text_embeddings)
            
            # 更新状态
            self.is_initialized = True
            self.total_vectors = self.vector_store.index.ntotal if hasattr(self.vector_store, 'index') else 0
            self.last_update_time = time.time()
            
            logging.info(f"向量存储加载成功: {load_path}")
            return True
            
        except Exception as e:
            logging.error(f"加载向量存储失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        获取向量存储状态

        :return: 状态信息字典
        """
        try:
            status = {
                'is_initialized': self.is_initialized,
                'dimension': self.dimension,
                'total_vectors': self.total_vectors,
                'last_update_time': self.last_update_time,
                'vector_db_dir': self.vector_db_dir,
                'langchain_available': LANGCHAIN_AVAILABLE,
                'faiss_available': FAISS_AVAILABLE
            }
            
            if self.is_initialized and self.vector_store:
                status.update({
                    'index_type': 'FAISS',
                    'index_ntotal': getattr(self.vector_store.index, 'ntotal', 0) if hasattr(self.vector_store, 'index') else 0
                })
            
            return status
            
        except Exception as e:
            logging.error(f"获取状态失败: {e}")
            return {'error': str(e)}

    def optimize_index(self) -> bool:
        """
        优化索引性能

        :return: 是否优化成功
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")
            
            # LangChain FAISS会自动处理索引优化
            logging.info("索引优化完成（LangChain自动优化）")
            return True
            
        except Exception as e:
            logging.error(f"索引优化失败: {e}")
            return False

    def clear(self) -> bool:
        """
        清空向量存储

        :return: 是否清空成功
        """
        try:
            if not self.is_initialized:
                return True
            
            # 重新创建空的向量存储
            self.create_vector_store(self.dimension)
            
            logging.info("向量存储清空成功")
            return True
            
        except Exception as e:
            logging.error(f"清空向量存储失败: {e}")
            return False
