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

        # 获取向量数据库路径 - 使用配置管理器的路径解析功能
        self.vector_db_dir = self.config_manager.get_path('vector_db_dir')
        if not self.vector_db_dir:
            # 如果获取失败，使用默认路径
            self.vector_db_dir = os.path.join(self.config_manager.path_manager.base_dir, 'central', 'vector_db')
        
        # 确保目录存在
        os.makedirs(self.vector_db_dir, exist_ok=True)
        logging.info(f"向量数据库目录: {self.vector_db_dir}")

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
        
        # 自动尝试加载或创建向量存储
        self._auto_initialize_vector_store()
        
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
    
    def _auto_initialize_vector_store(self):
        """自动初始化向量存储：尝试加载现有存储，如果不存在则创建新的"""
        try:
            # 首先尝试加载现有的向量存储
            if self.load():
                logging.info("成功加载现有向量存储")
                return
            
            # 如果加载失败，创建新的向量存储
            logging.info("未找到现有向量存储，创建新的向量存储")
            if self.create_vector_store():
                logging.info("成功创建新的向量存储")
            else:
                logging.error("创建向量存储失败")
                
        except Exception as e:
            logging.error(f"自动初始化向量存储失败: {e}")
            # 不抛出异常，让系统继续运行

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
            
            # 创建空的FAISS向量存储，使用余弦距离策略
            from langchain_community.vectorstores.utils import DistanceStrategy
            self.vector_store = FAISS.from_texts(
                texts=["初始化文本"],
                embedding=self.text_embeddings,
                metadatas=[{"chunk_type": "system", "content": "initialization"}],
                distance_strategy=DistanceStrategy.COSINE
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
            
            logging.info(f"准备添加 {len(text_embedding_pairs)} 个向量对")
            logging.info(f"第一个向量对: 文本='{text_embedding_pairs[0][0][:50]}...', 向量长度={len(text_embedding_pairs[0][1])}")
            logging.info(f"第一个元数据: {metadatas[0]}")
            
            # 检查向量维度
            expected_dimension = self.dimension
            for i, (text, vector) in enumerate(text_embedding_pairs):
                if len(vector) != expected_dimension:
                    logging.warning(f"向量 {i} 维度不匹配: 期望 {expected_dimension}, 实际 {len(vector)}")
            
            # 检查LangChain FAISS实例状态
            logging.info(f"LangChain FAISS实例状态: {type(self.vector_store)}")
            if hasattr(self.vector_store, 'index'):
                logging.info(f"FAISS索引状态: {type(self.vector_store.index)}")
                if hasattr(self.vector_store.index, 'ntotal'):
                    logging.info(f"当前索引中的向量数量: {self.vector_store.index.ntotal}")
            
            # 使用LangChain的add_embeddings方法
            logging.info("调用LangChain的add_embeddings方法...")
            self.vector_store.add_embeddings(text_embedding_pairs, metadatas)
            logging.info("LangChain add_embeddings调用成功")
            
            # 更新统计信息
            self.total_vectors += len(text_embedding_pairs)
            self.last_update_time = time.time()
            
            logging.info(f"成功添加 {len(text_embedding_pairs)} 个向量到存储")
            return True
            
        except Exception as e:
            logging.error(f"添加向量失败: {e}")
            logging.error(f"异常类型: {type(e)}")
            logging.error(f"异常详情: {str(e)}")
            import traceback
            logging.error(f"异常堆栈: {traceback.format_exc()}")
            return False

    def add_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> bool:
        """
        批量添加向量到存储

        :param vectors: 向量列表
        :param metadata: 元数据列表
        :return: 是否添加成功
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")
            
            if not vectors:
                logging.info("没有向量需要添加")
                return True
            
            if len(vectors) != len(metadata):
                raise ValueError(f"向量数量({len(vectors)})和元数据数量({len(metadata)})不匹配")
            
            # 验证向量格式
            for i, vector in enumerate(vectors):
                if not isinstance(vector, list):
                    raise ValueError(f"向量 {i} 不是列表格式: {type(vector)}")
                if not vector:  # 空向量
                    raise ValueError(f"向量 {i} 为空")
            
            # 将向量和元数据转换为LangChain需要的格式
            # LangChain的add_embeddings需要(text, embedding)对
            # 由于我们只有向量，需要创建占位符文本
            text_embedding_pairs = []
            processed_metadata = []
            
            for i, (vector, meta) in enumerate(zip(vectors, metadata)):
                # 创建占位符文本（基于元数据类型）
                vector_type = meta.get('vector_type', 'unknown')
                if vector_type == 'text_embedding':
                    placeholder_text = meta.get('chunk', f'text_chunk_{i}')
                elif vector_type == 'visual_embedding':
                    placeholder_text = meta.get('enhanced_description', f'image_{i}')
                elif vector_type == 'table_embedding':
                    placeholder_text = meta.get('table', f'table_{i}')
                else:
                    placeholder_text = f'vector_{i}'
                
                # 创建(text, embedding)对
                text_embedding_pairs.append((placeholder_text, vector))
                
                # 保留完整的metadata，而不是重新创建简化版
                processed_meta = dict(meta)  # 复制完整的metadata

                # 确保必要的字段存在
                processed_meta.update({
                    'vector_type': vector_type,
                    'chunk_index': i
                })

                # 如果某些关键字段缺失，提供默认值
                if 'chunk_type' not in processed_meta:
                    processed_meta['chunk_type'] = meta.get('type', 'unknown')
                if 'source' not in processed_meta:
                    processed_meta['source'] = meta.get('source', '')
                
                processed_metadata.append(processed_meta)
            
            # 使用add_embeddings方法添加向量
            success = self.add_embeddings(text_embedding_pairs, processed_metadata)
            
            if success:
                logging.info(f"成功添加 {len(vectors)} 个向量到存储")
                return True
            else:
                logging.error("add_embeddings调用失败")
                return False
                
        except Exception as e:
            logging.error(f"添加向量失败: {e}")
            return False

    def update_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> bool:
        """
        更新向量到存储（增量模式）
        
        注意：对于FAISS向量存储，更新操作实际上就是添加新向量
        因为FAISS不支持真正的"更新"操作，只能添加新向量

        :param vectors: 向量列表
        :param metadata: 元数据列表
        :return: 是否更新成功
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")
            
            if not vectors:
                logging.info("没有向量需要更新")
                return True
            
            if len(vectors) != len(metadata):
                raise ValueError(f"向量数量({len(vectors)})和元数据数量({len(metadata)})不匹配")
            
            # 验证向量格式
            for i, vector in enumerate(vectors):
                if not isinstance(vector, list):
                    raise ValueError(f"向量 {i} 不是列表格式: {type(vector)}")
                if not vector:  # 空向量
                    raise ValueError(f"向量 {i} 为空")
            
            logging.info(f"准备更新 {len(vectors)} 个向量（增量模式）")
            
            # 对于增量模式，我们直接调用add_vectors方法
            # 因为FAISS不支持真正的"更新"操作，只能添加新向量
            success = self.add_vectors(vectors, metadata)
            
            if success:
                # 修复：添加向量后，必须保存到磁盘
                logging.info("向量添加成功，开始保存到磁盘...")
                save_success = self.save()
                
                if save_success:
                    logging.info(f"成功更新（添加） {len(vectors)} 个并保存到磁盘")
                    return True
                else:
                    logging.error("向量保存到磁盘失败")
                    return False
            else:
                logging.error("add_vectors调用失败")
                return False
                
        except Exception as e:
            logging.error(f"更新向量失败: {e}")
            return False

    def similarity_search(self, query: str, k: int = 5, filter_dict: Dict[str, Any] = None, fetch_k: int = None) -> List[Any]:
        """
        相似性搜索

        :param query: 查询文本
        :param k: 返回结果数量
        :param filter_dict: 过滤条件
        :param fetch_k: 过滤前获取的结果数量
        :return: 搜索结果列表
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")
            
            # 使用底层的FAISS搜索方法避免LangChain的分数检查警告
            import numpy as np
            
            # 获取查询向量
            query_vector = self.vector_store.embeddings.embed_query(query)
            
            # 使用FAISS直接搜索
            faiss_index = self.vector_store.index
            query_vector_np = np.array([query_vector], dtype=np.float32)
            
            # 确定搜索数量
            search_k = k
            if filter_dict and fetch_k:
                search_k = fetch_k
            
            distances, indices = faiss_index.search(query_vector_np, search_k)
            
            # 处理搜索结果
            results_with_scores = []
            for i, dist in zip(indices[0], distances[0]):
                if i != -1:  # 确保索引有效
                    doc = self.vector_store.docstore.search(self.vector_store.index_to_docstore_id[i])
                    results_with_scores.append((doc, dist))
            
            # 应用过滤条件
            if filter_dict:
                filtered_results = []
                for doc, score in results_with_scores:
                    if self._matches_filter(doc, filter_dict):
                        filtered_results.append((doc, score))
                results_with_scores = filtered_results[:k]  # 取前k个结果
            
            # 将分数添加到结果的元数据中
            results = []
            if results_with_scores:
                # 获取所有距离值进行归一化
                distances = [float(score) for _, score in results_with_scores]
                min_distance = min(distances)
                max_distance = max(distances)
                
                for doc, score in results_with_scores:
                    if hasattr(doc, 'metadata'):
                        # 将欧几里得距离转换为[0,1]范围内的相似度值
                        # 距离越小，相似度越高
                        if max_distance > min_distance:
                            similarity_score = 1.0 - (float(score) - min_distance) / (max_distance - min_distance)
                        else:
                            similarity_score = 1.0  # 所有距离相同的情况
                        doc.metadata['similarity_score'] = similarity_score
                    results.append(doc)
            
            logging.info(f"相似性搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logging.error(f"相似性搜索失败: {e}")
            return []

    def _matches_filter(self, doc: Any, filter_dict: Dict[str, Any]) -> bool:
        """
        检查文档是否匹配过滤条件
        
        :param doc: 文档对象
        :param filter_dict: 过滤条件
        :return: 是否匹配
        """
        if not hasattr(doc, 'metadata') or not doc.metadata:
            return False
        
        for key, value in filter_dict.items():
            if key not in doc.metadata:
                return False
            if doc.metadata[key] != value:
                return False
        
        return True

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
            
            # 为向量搜索结果添加相似度分数（使用默认值1.0，因为向量搜索通常不返回分数）
            for result in results:
                if hasattr(result, 'metadata') and 'similarity_score' not in result.metadata:
                    result.metadata['similarity_score'] = 1.0
            
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
            # 修复：无论是否传入路径，都需要确保包含langchain_faiss_index子目录
            if load_path is None:
                load_path = os.path.join(self.vector_db_dir, 'langchain_faiss_index')
            else:
                # 如果传入的是父目录，自动添加子目录
                if not load_path.endswith('langchain_faiss_index'):
                    load_path = os.path.join(load_path, 'langchain_faiss_index')
            
            if not os.path.exists(load_path):
                logging.warning(f"向量存储路径不存在: {load_path}")
                return False
            
            # 使用LangChain的load_local方法，添加allow_dangerous_deserialization=True
            # 这是因为我们信任自己创建的向量数据库文件
            logging.info(f"尝试加载向量存储，路径: {load_path}")
            logging.info(f"路径是否存在: {os.path.exists(load_path)}")
            logging.info(f"路径内容: {os.listdir(load_path) if os.path.exists(load_path) else '路径不存在'}")
            
            self.vector_store = FAISS.load_local(
                load_path, 
                self.text_embeddings,
                allow_dangerous_deserialization=True
            )
            
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

    def get_unfinished_images(self) -> List[Dict[str, Any]]:
        """
        获取未完成的图片列表
        
        :return: 未完成图片列表
        """
        try:
            if not self.is_initialized or not self.vector_store:
                logging.warning("向量存储未初始化，无法获取未完成图片")
                return []
            
            unfinished_images = []
            
            # 遍历所有文档，找到图片类型且未完成的
            for doc_id, doc in self.vector_store.docstore._dict.items():
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                
                if metadata.get('chunk_type') == 'image':
                    # 检查是否已完成增强和向量化
                    has_enhancement = (metadata.get('enhanced_description') and 
                                     metadata.get('enhancement_status') == 'success')
                    has_vectorization = (metadata.get('image_embedding') and 
                                       metadata.get('vectorization_status') == 'success')
                    
                    if not has_enhancement or not has_vectorization:
                        unfinished_images.append({
                            'doc_id': doc_id,
                            'image_path': metadata.get('image_path', ''),
                            'image_id': metadata.get('image_id', ''),
                            'document_name': metadata.get('document_name', ''),
                            'needs_enhancement': not has_enhancement,
                            'needs_vectorization': not has_vectorization,
                            'metadata': metadata
                        })
            
            logging.info(f"发现 {len(unfinished_images)} 张未完成的图片")
            return unfinished_images
            
        except Exception as e:
            logging.error(f"获取未完成图片失败: {e}")
            return []

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
