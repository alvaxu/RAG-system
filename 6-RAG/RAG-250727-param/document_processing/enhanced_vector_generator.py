'''
程序说明：
## 1. 增强版向量生成器，集成ONE-PEACE模型能力
## 2. 保持与现有VectorGenerator的兼容性
## 3. 提供更丰富的图片向量存储功能
## 4. 支持跨模态检索和语义理解
'''

import os
import logging
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path
import faiss
import numpy as np
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings

# 导入增强版图片处理器
from .enhanced_image_processor import EnhancedImageProcessor

# 配置日志
logger = logging.getLogger(__name__)


class EnhancedVectorGenerator:
    """
    增强版向量生成器，充分利用ONE-PEACE模型能力
    保持与现有VectorGenerator的兼容性
    """
    
    def __init__(self, config):
        """
        初始化增强版向量生成器
        :param config: 配置对象
        """
        self.config = config
        self.api_key = self._get_api_key()
        self.embeddings = DashScopeEmbeddings(dashscope_api_key=self.api_key, model="text-embedding-v4")
        self.enhanced_image_processor = EnhancedImageProcessor(self.api_key) if self.api_key else None
    
    def _get_api_key(self) -> str:
        """
        获取DashScope API密钥
        :return: API密钥
        """
        # 优先使用配置中的API KEY
        if hasattr(self, 'config') and self.config:
            config_api_key = self.config.get('dashscope_api_key', '')
            if config_api_key and config_api_key != '你的DashScope API密钥':
                return config_api_key
        
        # 备选环境变量
        api_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
        if not api_key or api_key == '你的APIKEY':
            logger.warning("未找到有效的DashScope API密钥")
        return api_key
    
    def create_vector_store(self, documents: List[Document], save_path: str) -> Optional[FAISS]:
        """
        创建向量存储，解决ID映射问题
        :param documents: 文档列表
        :param save_path: 保存路径
        :return: FAISS向量存储实例
        """
        try:
            if not documents:
                logger.error("没有提供文档")
                return None
            
            if not self.api_key:
                logger.error("API密钥未配置，无法创建向量存储")
                return None
            
            # 确保保存路径存在
            save_path_obj = Path(save_path)
            save_path_obj.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"开始创建向量存储，文档数量: {len(documents)}")
            
            # 提取文本和元数据
            texts = []
            metadatas = []
            
            for doc in documents:
                texts.append(doc.page_content)
                
                # 确保元数据包含必要的信息
                metadata = doc.metadata.copy() if doc.metadata else {}
                
                # 如果没有页码信息，尝试从元数据中获取
                if 'page_number' not in metadata:
                    metadata['page_number'] = metadata.get('page', 1)
                
                # 如果没有文档名称，使用默认值
                if 'document_name' not in metadata:
                    metadata['document_name'] = metadata.get('source', 'unknown')
                
                # 确保有分块类型
                if 'chunk_type' not in metadata:
                    metadata['chunk_type'] = 'text'
                
                metadatas.append(metadata)
            
            # 使用from_texts方法创建向量存储，这样可以保存元数据
            vector_store = FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
            
            # 修复索引映射问题
            self._fix_index_mapping(vector_store)
            
            # 保存向量存储
            self._save_vector_store_with_metadata(vector_store, save_path)
            
            logger.info(f"向量存储创建成功，保存到: {save_path}")
            return vector_store
            
        except Exception as e:
            logger.error(f"创建向量存储失败: {e}")
            return None
    
    def _fix_index_mapping(self, vector_store: FAISS):
        """
        修复FAISS索引映射问题
        :param vector_store: FAISS向量存储实例
        """
        try:
            # 确保索引和文档数量一致
            if hasattr(vector_store, 'index') and hasattr(vector_store, 'docstore'):
                index_size = vector_store.index.ntotal
                docstore_size = len(vector_store.docstore._dict)
                
                if index_size != docstore_size:
                    logger.warning(f"索引大小({index_size})与文档存储大小({docstore_size})不一致")
                    
                    # 重新构建索引
                    if index_size > docstore_size:
                        # 截断索引
                        vector_store.index = faiss.IndexFlatIP(vector_store.index.d)
                        vector_store.index.add(vector_store.index.reconstruct_n(0, docstore_size))
                        logger.info("已修复索引映射问题")
        except Exception as e:
            logger.warning(f"修复索引映射时出现问题: {e}")
    
    def add_images_to_store(self, vector_store: FAISS, image_files: List[Dict[str, Any]], save_path: str) -> bool:
        """
        添加图片向量到存储，增强版支持完整的图片元信息
        :param vector_store: 向量存储实例
        :param image_files: 图片文件信息列表
        :param save_path: 保存路径
        :return: 是否成功
        """
        try:
            if not self.enhanced_image_processor:
                logger.error("增强版图片处理器未初始化")
                return False
            
            if not image_files:
                logger.warning("没有图片文件需要处理")
                return True
            
            logger.info(f"开始添加 {len(image_files)} 张图片到向量存储")
            
            # 处理每张图片
            image_results = []
            for image_info in image_files:
                image_path = image_info.get('image_path')
                if not image_path or not os.path.exists(image_path):
                    logger.warning(f"图片文件不存在: {image_path}")
                    continue
                
                # 生成图片embedding，传递完整的元信息
                result = self.enhanced_image_processor.process_image_for_vector_store(
                    image_path=image_path,
                    image_id=image_info.get('image_hash', 'unknown'),
                    document_name=image_info.get('document_name', '未知文档'),
                    page_number=image_info.get('page_number', 1),
                    img_caption=image_info.get('img_caption', []),
                    img_footnote=image_info.get('img_footnote', [])
                )
                
                if result and 'embedding' in result:
                    # 增强：添加完整的图片元信息
                    result.update({
                        'img_caption': image_info.get('img_caption', []),
                        'img_footnote': image_info.get('img_footnote', []),
                        'page_idx': image_info.get('page_number', 1) - 1,  # 转换为0索引
                        'image_filename': image_info.get('image_filename', ''),
                        'extension': image_info.get('extension', ''),
                        'source_zip': image_info.get('source_zip', '')
                    })
                    image_results.append(result)
                    logger.debug(f"成功处理图片: {image_path}")
                else:
                    logger.warning(f"处理图片失败: {image_path}")
            
            if image_results:
                # 准备文本和embedding对
                text_embeddings = []
                
                for result in image_results:
                    # 构建图片描述文本，包含caption信息
                    caption_text = ""
                    if result.get('img_caption'):
                        caption_text = " ".join(result['img_caption'])
                    
                    # 构建完整的图片描述
                    image_description = f"图片: {result['image_id']}"
                    if caption_text:
                        image_description += f" - {caption_text}"
                    
                    text_embedding_pair = (image_description, result["embedding"])
                    text_embeddings.append(text_embedding_pair)
                    
                    # 构建完整的元数据
                    metadata = {
                        "image_id": result["image_id"],
                        "image_path": result.get("image_path", ""),
                        "image_filename": result.get("image_filename", ""),
                        "chunk_type": "image",
                        "document_name": result.get("document_name", "未知文档"),
                        "page_number": result.get("page_number", 1),
                        "page_idx": result.get("page_idx", 0),
                        "img_caption": result.get("img_caption", []),
                        "img_footnote": result.get("img_footnote", []),
                        "extension": result.get("extension", ""),
                        "source_zip": result.get("source_zip", ""),
                        "enhanced_description": result.get("enhanced_description", ""),
                        "image_type": result.get("image_type", "general"),
                        "semantic_features": result.get("semantic_features", {}),
                        **result.get("metadata", {})
                    }
                    
                    # 添加到向量存储
                    vector_store.add_texts(
                        texts=[image_description],
                        embeddings=[result["embedding"]],
                        metadatas=[metadata]
                    )
                
                # 保存更新后的向量存储
                self._save_vector_store_with_metadata(vector_store, save_path)
                
                logger.info(f"成功添加 {len(image_results)} 张图片到向量存储，包含完整元信息")
                return True
            else:
                logger.warning("没有成功处理的图片")
                return False
                
        except Exception as e:
            logger.error(f"添加图片到向量存储失败: {e}")
            return False
    
    def load_vector_store(self, load_path: str) -> Optional[FAISS]:
        """
        加载向量存储
        :param load_path: 加载路径
        :return: FAISS向量存储实例
        """
        try:
            if not os.path.exists(load_path):
                logger.error(f"向量存储路径不存在: {load_path}")
                return None
            
            # 检查必要文件是否存在
            index_path = os.path.join(load_path, "index.faiss")
            pkl_path = os.path.join(load_path, "index.pkl")
            
            if not os.path.exists(index_path) or not os.path.exists(pkl_path):
                logger.error(f"向量存储文件不完整: {load_path}")
                return None
            
            # 加载向量存储
            vector_store = FAISS.load_local(load_path, self.embeddings)
            
            logger.info(f"向量存储加载成功: {load_path}")
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
        try:
            if not vector_store:
                return {"error": "向量存储为空"}
            
            # 获取基本统计信息
            stats = {
                "total_documents": len(vector_store.docstore._dict),
                "index_size": vector_store.index.ntotal if hasattr(vector_store.index, 'ntotal') else 0,
                "embedding_dimension": vector_store.index.d if hasattr(vector_store.index, 'd') else 0
            }
            
            # 分析文档类型
            chunk_types = {}
            document_names = {}
            
            for doc_id, doc in vector_store.docstore._dict.items():
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                chunk_type = metadata.get('chunk_type', 'unknown')
                document_name = metadata.get('document_name', 'unknown')
                
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                document_names[document_name] = document_names.get(document_name, 0) + 1
            
            stats["chunk_types"] = chunk_types
            stats["document_names"] = document_names
            
            # 分析图片相关统计
            if 'image' in chunk_types:
                image_stats = {
                    "total_images": chunk_types['image'],
                    "images_with_caption": 0,
                    "images_with_footnote": 0,
                    "image_types": {}
                }
                
                for doc_id, doc in vector_store.docstore._dict.items():
                    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                    if metadata.get('chunk_type') == 'image':
                        if metadata.get('img_caption'):
                            image_stats["images_with_caption"] += 1
                        if metadata.get('img_footnote'):
                            image_stats["images_with_footnote"] += 1
                        
                        image_type = metadata.get('image_type', 'general')
                        image_stats["image_types"][image_type] = image_stats["image_types"].get(image_type, 0) + 1
                
                stats["image_statistics"] = image_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"获取向量存储统计信息失败: {e}")
            return {"error": str(e)}
    
    def validate_vector_store(self, vector_store: FAISS) -> bool:
        """
        验证向量存储的完整性
        :param vector_store: FAISS向量存储实例
        :return: 是否有效
        """
        try:
            if not vector_store:
                return False
            
            # 检查基本属性
            if not hasattr(vector_store, 'index') or not hasattr(vector_store, 'docstore'):
                logger.error("向量存储缺少必要属性")
                return False
            
            # 检查索引和文档存储的一致性
            index_size = vector_store.index.ntotal if hasattr(vector_store.index, 'ntotal') else 0
            docstore_size = len(vector_store.docstore._dict)
            
            if index_size != docstore_size:
                logger.warning(f"索引大小({index_size})与文档存储大小({docstore_size})不一致")
                return False
            
            # 检查文档内容
            for doc_id, doc in vector_store.docstore._dict.items():
                if not hasattr(doc, 'page_content') or not doc.page_content:
                    logger.warning(f"文档缺少内容: {doc_id}")
                    return False
            
            logger.info("向量存储验证通过")
            return True
            
        except Exception as e:
            logger.error(f"验证向量存储失败: {e}")
            return False
    
    def _save_vector_store_with_metadata(self, vector_store: FAISS, save_path: str):
        """
        保存向量存储和元数据
        :param vector_store: FAISS向量存储实例
        :param save_path: 保存路径
        """
        try:
            # 确保保存路径存在
            save_path_obj = Path(save_path)
            save_path_obj.mkdir(parents=True, exist_ok=True)
            
            # 保存向量存储
            vector_store.save_local(save_path)
            
            # 保存元数据
            metadata_path = os.path.join(save_path, "metadata.pkl")
            metadata_list = []
            
            for doc_id, doc in vector_store.docstore._dict.items():
                metadata = doc.metadata.copy() if hasattr(doc, 'metadata') and doc.metadata else {}
                metadata['doc_id'] = doc_id
                metadata['content'] = doc.page_content
                metadata_list.append(metadata)
            
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata_list, f)
            
            logger.info(f"向量存储和元数据已保存到: {save_path}")
            
        except Exception as e:
            logger.error(f"保存向量存储失败: {e}")
            raise
    
    def create_enhanced_search_query(self, user_query: str, image_context: Dict[str, Any] = None) -> str:
        """
        创建增强的搜索查询，充分利用ONE-PEACE模型的跨模态能力
        :param user_query: 用户查询
        :param image_context: 图片上下文信息
        :return: 增强的搜索查询
        """
        try:
            if not image_context:
                return user_query
            
            if not self.enhanced_image_processor:
                return user_query
            
            # 使用增强版图片处理器创建优化的搜索查询
            enhanced_query = self.enhanced_image_processor.create_image_search_query(user_query, image_context)
            
            logger.info(f"创建增强搜索查询: {enhanced_query}")
            return enhanced_query
            
        except Exception as e:
            logger.error(f"创建增强搜索查询失败: {e}")
            return user_query
    
    def analyze_image_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        分析两个图片的相似度
        :param embedding1: 第一个图片的embedding
        :param embedding2: 第二个图片的embedding
        :return: 相似度分数
        """
        try:
            if not self.enhanced_image_processor:
                return 0.0
            
            return self.enhanced_image_processor.analyze_image_similarity(embedding1, embedding2)
            
        except Exception as e:
            logger.error(f"分析图片相似度失败: {e}")
            return 0.0 