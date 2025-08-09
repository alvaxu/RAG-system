'''
程序说明：
## 1. 向量生成器，整合现有的向量存储功能
## 2. 解决向量存储ID映射不一致问题
## 3. 统一向量存储创建和管理接口
## 4. 支持文本、表格和图片的混合向量存储
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

# 导入图片处理器
from .image_processor import ImageProcessor

# 配置日志
logger = logging.getLogger(__name__)


class VectorGenerator:
    """
    向量生成器，处理向量存储的创建和管理
    """
    
    def __init__(self, config):
        """
        初始化向量生成器
        :param config: 配置对象
        """
        self.config = config
        self.api_key = self._get_api_key()
        self.embeddings = DashScopeEmbeddings(dashscope_api_key=self.api_key, model="text-embedding-v1")
        # 将配置传递给ImageProcessor
        self.image_processor = ImageProcessor(self.api_key, config) if self.api_key else None
        self._last_image_addition_result = 0  # 记录上次图片添加结果
    
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
            
            # 保存元数据到向量存储对象（用于后续保存到metadata.pkl）
            vector_store.metadata = metadatas
            
            # 修复ID映射问题
            self._fix_index_mapping(vector_store)
            
            # 保存向量存储（包括metadata.pkl）
            self._save_vector_store_with_metadata(vector_store, save_path)
            
            logger.info(f"向量存储创建完成，保存路径: {save_path}")
            return vector_store
            
        except Exception as e:
            logger.error(f"创建向量存储失败: {e}")
            return None
    
    # 移除此方法，因为分块器已经控制了文档长度
    
    def _fix_index_mapping(self, vector_store: FAISS):
        """
        修复索引映射问题
        :param vector_store: FAISS向量存储实例
        """
        try:
            # 获取索引和文档存储信息
            index_total = vector_store.index.ntotal
            docstore_ids = list(vector_store.docstore._dict.keys())
            
            logger.info(f"索引总数: {index_total}")
            logger.info(f"文档存储ID数量: {len(docstore_ids)}")
            
            # 检查ID映射是否一致
            if len(docstore_ids) != index_total:
                logger.warning(f"ID映射不一致: 索引数量({index_total}) != 文档数量({len(docstore_ids)})")
                
                # 重建索引映射
                new_index_to_docstore_id = {}
                for i, doc_id in enumerate(docstore_ids):
                    if i < index_total:
                        new_index_to_docstore_id[i] = str(doc_id)
                
                # 更新向量存储的索引映射
                vector_store.index_to_docstore_id = new_index_to_docstore_id
                
                logger.info(f"已修复ID映射，映射数量: {len(new_index_to_docstore_id)}")
            else:
                logger.info("ID映射正常")
                
        except Exception as e:
            logger.error(f"修复索引映射失败: {e}")
    
    def add_images_to_store(self, vector_store: FAISS, image_files: List[Dict[str, Any]], save_path: str) -> bool:
        """
        第五步使用，添加图片向量到存储，增强版支持完整的图片元信息
        :param vector_store: 向量存储实例
        :param image_files: 图片文件信息列表
        :param save_path: 保存路径
        :return: 是否成功
        """
        try:
            if not self.image_processor:
                logger.error("图片处理器未初始化")
                return False
            
            if not image_files:
                logger.warning("没有提供图片文件")
                return True  # 没有图片不算失败
            
            logger.info(f"开始添加 {len(image_files)} 张图片到向量存储")
            
            # 重置上次添加结果
            self._last_image_addition_result = 0
            
            # 处理图片并生成embedding
            image_results = []
            for image_info in image_files:
                try:
                    image_path = image_info.get('image_path')
                    if not image_path or not os.path.exists(image_path):
                        logger.warning(f"图片文件不存在: {image_path}")
                        continue
                    
                    # 生成图片embedding，传递完整的元信息
                    result = self.image_processor.process_image_for_vector_store(
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
                        logger.warning(f"图片处理失败: {image_path}")
                        
                except Exception as e:
                    logger.warning(f"处理图片 {image_info.get('image_path', 'unknown')} 时出错: {e}")
                    continue
            
            if image_results:
                # 准备图片文本和embedding
                text_embeddings = []
                metadatas = []
                
                for result in image_results:
                    # 使用增强的图片描述（如果可用）
                    if result.get('enhanced_description'):
                        image_description = result['enhanced_description']
                    else:
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
                    metadatas.append(metadata)
                
                # 添加到向量存储
                vector_store.add_embeddings(text_embeddings, metadatas=metadatas)
                
                # 确保metadata被正确保存
                # 获取当前的metadata列表
                current_metadata = vector_store.metadata if hasattr(vector_store, 'metadata') else []
                
                # 添加新的图片metadata
                if current_metadata is None:
                    current_metadata = []
                
                # 确保current_metadata是列表
                if not isinstance(current_metadata, list):
                    current_metadata = list(current_metadata) if hasattr(current_metadata, '__iter__') else []
                
                # 添加新的图片metadata
                current_metadata.extend(metadatas)
                
                # 更新向量存储的metadata
                vector_store.metadata = current_metadata
                
                # 使用自定义保存方法确保metadata被正确保存
                self._save_vector_store_with_metadata(vector_store, save_path)
                
                # 记录实际添加的图片数量
                self._last_image_addition_result = len(image_results)
                
                logger.info(f"成功添加 {len(image_results)} 张图片到向量存储，包含完整元信息")
                return True
            else:
                logger.warning("没有成功处理的图片")
                return False
                
        except Exception as e:
            logger.error(f"添加图片到向量存储失败: {e}")
            self._last_image_addition_result = 0
            return False
    
    def get_last_image_addition_result(self) -> int:
        """
        第五步使用，获取上次图片添加的实际结果
        :return: 实际添加的图片数量
        """
        return getattr(self, '_last_image_addition_result', 0)
    
    def add_documents_to_store(self, vector_store: FAISS, documents: List[Document], save_path: str) -> bool:
        """
        增量更新的第四步使用，向现有向量存储添加文档
        :param vector_store: 现有向量存储实例
        :param documents: 要添加的文档列表
        :param save_path: 保存路径
        :return: 是否成功
        """
        try:
            if not documents:
                logger.warning("没有提供要添加的文档")
                return True
            
            if not self.api_key:
                logger.error("API密钥未配置，无法添加文档到向量存储")
                return False
            
            logger.info(f"开始向向量存储添加文档，文档数量: {len(documents)}")
            
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
            
            # 生成嵌入向量
            embeddings = self.embeddings.embed_documents(texts)
            
            # 准备 (text, embedding) 元组列表
            text_embeddings = list(zip(texts, embeddings))
            
            # 添加到现有向量存储
            vector_store.add_embeddings(text_embeddings, metadatas=metadatas)
            
            # 保存更新后的向量存储
            self._save_vector_store_with_metadata(vector_store, save_path)
            
            logger.info(f"成功向向量存储添加 {len(documents)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"向向量存储添加文档失败: {e}")
            return False
    
    def load_vector_store(self, load_path: str) -> Optional[FAISS]:
        """
        增量更新的第四步使用：加载向量存储
        :param load_path: 加载路径
        :return: FAISS向量存储实例
        """
        try:
            if not os.path.exists(load_path):
                logger.error(f"向量存储路径不存在: {load_path}")
                return None
            
            # 使用LangChain标准的加载方法
            vector_store = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=True)
            
            # 修复ID映射问题
            self._fix_index_mapping(vector_store)
            
            logger.info(f"向量存储加载完成: {load_path}")
            return vector_store
            
        except Exception as e:
            logger.error(f"加载向量存储失败: {e}")
            return None
    
    def get_vector_store_statistics(self, vector_store: FAISS) -> Dict[str, Any]:
        """
        检测工具使用，主程序不适用，获取向量存储统计信息
        :param vector_store: 向量存储实例
        :return: 统计信息
        """
        try:
            if not vector_store:
                return {'error': '向量存储为空'}
            
            # 基本信息
            total_docs = len(vector_store.docstore._dict)
            vector_dimension = vector_store.index.d
            
            # 按类型统计
            type_distribution = {}
            for doc_id, doc in vector_store.docstore._dict.items():
                chunk_type = doc.metadata.get('chunk_type', 'text')
                type_distribution[chunk_type] = type_distribution.get(chunk_type, 0) + 1
            
            # 表格类型统计
            table_types = {}
            for doc_id, doc in vector_store.docstore._dict.items():
                if doc.metadata.get('chunk_type') == 'table':
                    table_type = doc.metadata.get('table_type', '未知表格')
                    table_types[table_type] = table_types.get(table_type, 0) + 1
            
            # 图片相关统计
            image_stats = {}
            if 'image' in type_distribution:
                image_stats = {
                    "total_images": type_distribution['image'],
                    "images_with_caption": 0,
                    "images_with_footnote": 0,
                    "images_with_enhanced_description": 0,
                    "image_types": {}
                }
                
                for doc_id, doc in vector_store.docstore._dict.items():
                    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                    if metadata.get('chunk_type') == 'image':
                        if metadata.get('img_caption'):
                            image_stats["images_with_caption"] += 1
                        if metadata.get('img_footnote'):
                            image_stats["images_with_footnote"] += 1
                        if metadata.get('enhanced_description'):
                            image_stats["images_with_enhanced_description"] += 1
                        
                        image_type = metadata.get('image_type', 'general')
                        image_stats["image_types"][image_type] = image_stats["image_types"].get(image_type, 0) + 1
            
            return {
                'total_documents': total_docs,
                'vector_dimension': vector_dimension,
                'type_distribution': type_distribution,
                'table_types': table_types,
                'image_statistics': image_stats
            }
            
        except Exception as e:
            logger.error(f"获取向量存储统计信息失败: {e}")
            return {'error': str(e)}
    
    # def validate_vector_store(self, vector_store: FAISS) -> bool:
    #     """
    #     验证向量存储
    #     :param vector_store: 向量存储实例
    #     :return: 验证结果
    #     """
    #     try:
    #         if not vector_store:
    #             return False
            
    #         # 检查基本属性
    #         if not hasattr(vector_store, 'index') or not hasattr(vector_store, 'docstore'):
    #             return False
            
    #         # 检查索引和文档存储的一致性
    #         index_total = vector_store.index.ntotal
    #         docstore_count = len(vector_store.docstore._dict)
            
    #         if index_total != docstore_count:
    #             logger.warning(f"索引和文档存储不一致: 索引数量({index_total}) != 文档数量({docstore_count})")
    #             return False
            
    #         # 尝试进行一次简单的搜索测试
    #         test_query = "test"
    #         try:
    #             results = vector_store.similarity_search(test_query, k=1)
    #             return True
    #         except Exception as e:
    #             logger.error(f"向量存储搜索测试失败: {e}")
    #             return False
                
    #     except Exception as e:
    #         logger.error(f"验证向量存储失败: {e}")
    #         return False
    
    def _save_vector_store_with_metadata(self, vector_store: FAISS, save_path: str):
        """
        保存向量存储，包括metadata.pkl文件
        这是从老代码中学到的优秀设计
        :param vector_store: 向量存储实例
        :param save_path: 保存路径
        """
        try:
            # 确保保存路径存在
            save_path_obj = Path(save_path)
            save_path_obj.mkdir(parents=True, exist_ok=True)
            
            # 使用LangChain的标准保存方法，确保兼容性
            logger.info(f"正在保存向量存储到路径: {save_path}")
            vector_store.save_local(save_path)
            logger.info("向量存储保存完成")
            
            # 保存元数据（这是关键功能，用于显示页码和文档来源）
            metadata_path = save_path_obj / "metadata.pkl"
            if hasattr(vector_store, 'metadata') and vector_store.metadata:
                logger.info(f"正在保存元数据到路径: {metadata_path}")
                with open(metadata_path, "wb") as f:
                    pickle.dump(vector_store.metadata, f)
                logger.info("元数据保存完成")
                logger.info(f"元数据包含 {len(vector_store.metadata)} 个文档的页码和来源信息")
            else:
                logger.warning("向量存储中没有元数据，无法保存metadata.pkl")
            
            logger.info(f"向量存储完整保存完成: {save_path}")
            
        except Exception as e:
            logger.error(f"保存向量存储失败: {e}")
            raise 