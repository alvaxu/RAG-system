"""
向量存储管理器

负责管理FAISS向量数据库的创建、更新、查询和维护。
完全符合设计文档规范，支持多种索引类型和优化策略。
"""

import os
import logging
import pickle
import time
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS未安装，向量存储功能将不可用")

class VectorStoreManager:
    """
    向量存储管理器主类

    功能：
    - 管理FAISS向量数据库
    - 提供向量存储和检索服务
    - 优化索引性能
    - 支持备份和恢复
    - 完全符合设计文档规范
    """

    def __init__(self, config_manager):
        """
        初始化向量存储管理器

        :param config_manager: 配置管理器
        """
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
        self.index_type = 'faiss'
        
        # FAISS索引
        self.index = None
        self.index_file_path = None
        self.metadata_file_path = None
        
        # 统计信息
        self.total_vectors = 0
        self.last_update_time = None

        logging.info("VectorStoreManager初始化完成")

    def create_vector_store(self, dimension: int, index_type: str = 'faiss') -> bool:
        """
        创建向量存储

        :param dimension: 向量维度
        :param index_type: 索引类型
        :return: 是否创建成功
        """
        try:
            if not FAISS_AVAILABLE:
                raise RuntimeError("FAISS未安装，无法创建向量存储")
            
            self.dimension = dimension
            self.index_type = index_type

            # 创建索引文件路径
            index_dir = os.path.join(self.vector_db_dir, 'index')
            os.makedirs(index_dir, exist_ok=True)

            # 创建元数据目录
            metadata_dir = os.path.join(self.vector_db_dir, 'metadata')
            os.makedirs(metadata_dir, exist_ok=True)

            # 创建FAISS索引
            self.index = self._create_faiss_index(dimension, index_type)
            
            # 设置文件路径
            self.index_file_path = os.path.join(index_dir, f'faiss_index_{dimension}d')
            self.metadata_file_path = os.path.join(metadata_dir, 'metadata.pkl')
            
            # 初始化存储
            self._vectors = []
            self._metadata = []
            
            self.is_initialized = True
            self.last_update_time = int(time.time())
            
            logging.info(f"向量存储创建成功，维度: {dimension}，索引类型: {index_type}")
            return True

        except Exception as e:
            logging.error(f"创建向量存储失败: {e}")
            return False

    def _create_faiss_index(self, dimension: int, index_type: str = 'faiss'):
        """
        创建FAISS索引
        
        :param dimension: 向量维度
        :param index_type: 索引类型
        :return: FAISS索引对象
        """
        if index_type == 'faiss':
            # 使用IVFFlat索引，适合小到中等规模的数据集
            quantizer = faiss.IndexFlatL2(dimension)
            nlist = min(100, max(1, int(np.sqrt(self.total_vectors + 1000))))
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            index.nprobe = min(10, nlist)  # 搜索时检查的聚类数量
        elif index_type == 'flat':
            # 使用Flat索引，适合小数据集，搜索精度最高
            index = faiss.IndexFlatL2(dimension)
        elif index_type == 'hnsw':
            # 使用HNSW索引，适合大规模数据集，搜索速度快
            index = faiss.IndexHNSWFlat(dimension, 32)  # 32个邻居
            index.hnsw.efConstruction = 200  # 构建时的搜索深度
            index.hnsw.efSearch = 100  # 搜索时的深度
        else:
            # 默认使用Flat索引
            index = faiss.IndexFlatL2(dimension)
        
        return index

    def add_vectors(self, vectors: List[List[float]], metadata: List[Dict]) -> bool:
        """
        添加向量到存储

        :param vectors: 向量列表
        :param metadata: 元数据列表
        :return: 是否添加成功
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")

            if len(vectors) != len(metadata):
                raise ValueError("向量数量和元数据数量不匹配")

            # 验证向量格式
            for i, vector in enumerate(vectors):
                if not isinstance(vector, list) or len(vector) != self.dimension:
                    raise ValueError(f"向量 {i} 格式错误: 期望 {self.dimension} 维，实际 {len(vector) if isinstance(vector, list) else '非列表'}")

            # 转换为numpy数组
            vectors_array = np.array(vectors, dtype=np.float32)
            
            # 添加到FAISS索引
            if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                # 对于需要训练的索引（如IVF），先训练
                self.index.train(vectors_array)
            
            # 添加向量到索引
            self.index.add(vectors_array)
            
            # 存储到内存和文件
            if not hasattr(self, '_vectors'):
                self._vectors = []
                self._metadata = []
            
            self._vectors.extend(vectors)
            self._metadata.extend(metadata)
            
            # 更新统计信息
            self.total_vectors = len(self._vectors)
            self.last_update_time = int(time.time())
            
            # 保存到文件
            self._save_to_files()
            
            logging.info(f"成功添加 {len(vectors)} 个向量，总计: {self.total_vectors}")
            return True

        except Exception as e:
            logging.error(f"添加向量失败: {e}")
            return False

    def update_vectors(self, vectors: List[List[float]], metadata: List[Dict]) -> bool:
        """
        更新现有向量
        
        :param vectors: 新的向量列表
        :param metadata: 新的元数据列表
        :return: 是否更新成功
        """
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")

            if len(vectors) != len(metadata):
                raise ValueError("向量数量和元数据数量不匹配")

            if not vectors:
                logging.info("没有向量需要更新")
                return True

            # 验证向量格式
            for i, vector in enumerate(vectors):
                if not isinstance(vector, list) or len(vector) != self.dimension:
                    raise ValueError(f"向量 {i} 格式错误: 期望 {self.dimension} 维，实际 {len(vector) if isinstance(vector, list) else '非列表'}")

            # 转换为numpy数组
            vectors_array = np.array(vectors, dtype=np.float32)
            
            # 对于更新操作，我们采用添加策略（因为FAISS不支持直接更新）
            # 新向量会添加到现有数据库的末尾
            
            # 添加新向量到索引
            if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                self.index.train(vectors_array)
            
            self.index.add(vectors_array)
            
            # 更新内存存储
            self._vectors.extend(vectors)
            self._metadata.extend(metadata)
            
            # 更新统计信息
            self.total_vectors = len(self._vectors)
            self.last_update_time = int(time.time())
            
            # 保存到文件
            self._save_to_files()
            
            logging.info(f"成功更新 {len(vectors)} 个向量，总计: {self.total_vectors}")
            return True

        except Exception as e:
            logging.error(f"更新向量失败: {e}")
            return False

    def load_existing_database(self, database_path: str) -> bool:
        """加载现有的向量数据库"""
        try:
            if not database_path or not os.path.exists(database_path):
                logging.warning(f"数据库路径不存在: {database_path}")
                return False
            
            self.vector_db_dir = database_path
            index_dir = os.path.join(database_path, 'index')
            metadata_dir = os.path.join(database_path, 'metadata')
            
            self.index_file_path = os.path.join(index_dir, f'faiss_index_{self.dimension}d')
            self.metadata_file_path = os.path.join(metadata_dir, 'metadata.pkl')
            
            if self._load_from_files():
                self.is_initialized = True
                logging.info(f"成功加载现有向量数据库: {database_path}")
                return True
            else:
                logging.warning(f"无法从文件加载现有数据库: {database_path}")
                return False
                
        except Exception as e:
            logging.error(f"加载现有数据库失败: {e}")
            return False

    def update_vectors(self, vectors: List[List[float]], metadata: List[Dict]) -> bool:
        """更新现有向量"""
        try:
            if not self.is_initialized:
                raise RuntimeError("向量存储未初始化")

            if len(vectors) != len(metadata):
                raise ValueError("向量数量和元数据数量不匹配")

            if not vectors:
                logging.info("没有向量需要更新")
                return True

            # 验证向量格式
            for i, vector in enumerate(vectors):
                if not isinstance(vector, list) or len(vector) != self.dimension:
                    raise ValueError(f"向量 {i} 格式错误: 期望 {self.dimension} 维，实际 {len(vector) if isinstance(vector, list) else '非列表'}")

            # 转换为numpy数组并添加
            vectors_array = np.array(vectors, dtype=np.float32)
            
            if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                self.index.train(vectors_array)
            
            self.index.add(vectors_array)
            
            # 更新内存存储
            self._vectors.extend(vectors)
            self._metadata.extend(metadata)
            self.total_vectors = len(self._vectors)
            self.last_update_time = int(time.time())
            
            # 保存到文件
            self._save_to_files()
            
            logging.info(f"成功更新 {len(vectors)} 个向量，总计: {self.total_vectors}")
            return True

        except Exception as e:
            logging.error(f"更新向量失败: {e}")
            return False

    def _save_to_files(self):
        """保存向量和元数据到文件"""
        try:
            # 保存FAISS索引
            if self.index and self.index_file_path:
                faiss.write_index(self.index, self.index_file_path)
            
            # 保存元数据到pickle文件
            if self.metadata_file_path:
                with open(self.metadata_file_path, 'wb') as f:
                    pickle.dump(self._metadata, f)
            
            logging.debug(f"向量和元数据已保存到文件")
            
        except Exception as e:
            logging.error(f"保存到文件失败: {e}")

    def _load_from_files(self):
        """从文件加载向量和元数据"""
        try:
            # 加载FAISS索引
            if self.index_file_path and os.path.exists(self.index_file_path):
                self.index = faiss.read_index(self.index_file_path)
                logging.info("FAISS索引加载成功")
            
            # 加载元数据
            if self.metadata_file_path and os.path.exists(self.metadata_file_path):
                with open(self.metadata_file_path, 'rb') as f:
                    self._metadata = pickle.load(f)
                
                self._vectors = []  # 向量从索引中获取
                self.total_vectors = len(self._metadata)
                logging.info(f"从文件加载了 {self.total_vectors} 个元数据")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"从文件加载失败: {e}")
            return False

    def search_similar(self, query_vector: List[float], top_k: int = 10,
                       search_type: str = 'all') -> List[Dict]:
        """
        相似度搜索

        :param query_vector: 查询向量
        :param top_k: 返回结果数量
        :param search_type: 搜索类型（all/text/image/table）
        :return: 搜索结果列表
        """
        try:
            if not self.is_initialized or not self.index:
                raise RuntimeError("向量存储未初始化")

            if not query_vector or len(query_vector) != self.dimension:
                raise ValueError(f"查询向量格式错误: 期望 {self.dimension} 维")

            # 转换为numpy数组
            query_array = np.array([query_vector], dtype=np.float32)
            
            # 执行搜索
            distances, indices = self.index.search(query_array, min(top_k, self.total_vectors))
            
            # 构建搜索结果
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < 0:  # FAISS返回-1表示无效结果
                    continue
                
                if idx < len(self._metadata):
                    metadata = self._metadata[idx].copy()
                    metadata['similarity_score'] = 1.0 / (1.0 + distance)  # 转换为相似度分数
                    metadata['distance'] = float(distance)
                    metadata['rank'] = i + 1
                    
                    # 根据搜索类型过滤
                    if search_type == 'all' or metadata.get('chunk_type') == search_type:
                        results.append(metadata)
            
            logging.info(f"相似度搜索完成，返回 {len(results)} 个结果")
            return results

        except Exception as e:
            logging.error(f"相似度搜索失败: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息

        :return: 统计信息字典
        """
        try:
            # 计算存储大小
            storage_size_mb = 0
            if hasattr(self, '_vectors') and self._vectors:
                # 估算向量存储大小（每个float32占4字节）
                vector_size_bytes = len(self._vectors) * self.dimension * 4
                storage_size_mb = vector_size_bytes / (1024 * 1024)
            
            # 获取索引信息
            index_info = {}
            if self.index:
                index_info = {
                    'index_type': type(self.index).__name__,
                    'is_trained': getattr(self.index, 'is_trained', True),
                    'ntotal': getattr(self.index, 'ntotal', 0)
                }
            
            return {
                'is_initialized': self.is_initialized,
                'dimension': self.dimension,
                'index_type': self.index_type,
                'vector_db_dir': self.vector_db_dir,
                'total_vectors': self.total_vectors,
                'storage_size_mb': round(storage_size_mb, 2),
                'last_update_time': self.last_update_time,
                'index_info': index_info,
                'faiss_available': FAISS_AVAILABLE
            }
            
        except Exception as e:
            logging.error(f"获取统计信息失败: {e}")
            return {'error': str(e)}

    def create_backup(self, backup_path: Optional[str] = None) -> bool:
        """
        创建数据库备份

        :param backup_path: 备份路径
        :return: 是否备份成功
        """
        try:
            if backup_path is None:
                timestamp = int(time.time())
                backup_path = os.path.join(self.vector_db_dir, 'backup', f'backup_{timestamp}')

            # 确保备份目录存在
            os.makedirs(backup_path, exist_ok=True)

            # 备份索引文件
            if self.index_file_path and os.path.exists(self.index_file_path):
                backup_index_path = os.path.join(backup_path, 'faiss_index')
                faiss.write_index(self.index, backup_index_path)
            
            # 备份元数据文件
            if self.metadata_file_path and os.path.exists(self.metadata_file_path):
                import shutil
                backup_metadata_path = os.path.join(backup_path, 'metadata.pkl')
                shutil.copy2(self.metadata_file_path, backup_metadata_path)
            
            # 备份配置信息
            backup_info = {
                'backup_time': int(time.time()),
                'total_vectors': self.total_vectors,
                'dimension': self.dimension,
                'index_type': self.index_type
            }
            
            with open(os.path.join(backup_path, 'backup_info.json'), 'w', encoding='utf-8') as f:
                import json
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            logging.info(f"数据库备份创建成功: {backup_path}")
            return True

        except Exception as e:
            logging.error(f"创建数据库备份失败: {e}")
            return False

    def restore_from_backup(self, backup_path: str) -> bool:
        """
        从备份恢复数据库

        :param backup_path: 备份路径
        :return: 是否恢复成功
        """
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"备份路径不存在: {backup_path}")

            # 恢复索引文件
            backup_index_path = os.path.join(backup_path, 'faiss_index')
            if os.path.exists(backup_index_path):
                self.index = faiss.read_index(backup_index_path)
            
            # 恢复元数据文件
            backup_metadata_path = os.path.join(backup_path, 'metadata.pkl')
            if os.path.exists(backup_metadata_path):
                with open(backup_metadata_path, 'rb') as f:
                    self._metadata = pickle.load(f)
                
                self._vectors = []  # 向量从索引中获取
                self.total_vectors = len(self._metadata)
            
            # 更新状态
            self.is_initialized = True
            self.last_update_time = int(time.time())
            
            # 保存到当前工作目录
            self._save_to_files()

            logging.info(f"从备份恢复成功: {backup_path}")
            return True

        except Exception as e:
            logging.error(f"从备份恢复失败: {e}")
            return False

    def optimize_index(self) -> bool:
        """
        优化索引性能
        
        :return: 是否优化成功
        """
        try:
            if not self.index or not self.is_initialized:
                raise RuntimeError("索引未初始化，无法优化")
            
            # 对于IVF索引，可以重新训练以提高性能
            if hasattr(self.index, 'is_trained') and self.index.is_trained:
                if hasattr(self.index, 'train'):
                    # 获取所有向量进行重新训练
                    if hasattr(self, '_vectors') and self._vectors:
                        vectors_array = np.array(self._vectors, dtype=np.float32)
                        self.index.train(vectors_array)
                        logging.info("索引重新训练完成")
            
            # 保存优化后的索引
            self._save_to_files()
            
            logging.info("索引优化完成")
            return True
            
        except Exception as e:
            logging.error(f"索引优化失败: {e}")
            return False

    def clear_all(self) -> bool:
        """
        清空所有向量数据
        
        :return: 是否清空成功
        """
        try:
            if self.index:
                # 清空FAISS索引
                if hasattr(self.index, 'reset'):
                    self.index.reset()
                else:
                    # 重新创建索引
                    self.index = self._create_faiss_index(self.dimension, self.index_type)
            
            # 清空内存数据
            self._vectors = []
            self._metadata = []
            self.total_vectors = 0
            self.last_update_time = int(time.time())
            
            # 删除文件
            if self.index_file_path and os.path.exists(self.index_file_path):
                os.remove(self.index_file_path)
            
            if self.metadata_file_path and os.path.exists(self.metadata_file_path):
                os.remove(self.metadata_file_path)
            
            logging.info("所有向量数据已清空")
            return True
            
        except Exception as e:
            logging.error(f"清空数据失败: {e}")
            return False
