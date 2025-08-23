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
from document_processing.enhanced_chunker import EnhancedDocumentChunk

# 导入图片处理器
from .image_processor import ImageProcessor

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key

# 配置日志
logger = logging.getLogger(__name__)


class VectorGenerator:
    """
    向量生成器，负责创建和管理向量存储
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化向量生成器
        
        :param config: 配置字典
        """
        self.config = config
        
        # 使用统一的API密钥管理模块获取API密钥
        self.api_key = get_dashscope_api_key(config.get('dashscope_api_key', ''))
        
        # 初始化嵌入模型
        if self.api_key:
            embedding_model = config.get('text_embedding_model', 'text-embedding-v1')
            self.embeddings = DashScopeEmbeddings(dashscope_api_key=self.api_key, model=embedding_model)
            logger.info("DashScope Embeddings初始化成功")
        else:
            self.embeddings = None
            logger.warning("未配置有效的DashScope API密钥，向量生成功能将受限")
        
        # 将配置传递给ImageProcessor
        self.image_processor = ImageProcessor(self.api_key, config) if self.api_key else None
        self._last_image_addition_result = 0  # 记录上次图片添加结果
    
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
                # 处理不同类型的文档对象
                if isinstance(doc, EnhancedDocumentChunk):
                    metadata = {
                        'document_name': doc.document_name,
                        'page_number': doc.page_number,
                        'chunk_index': doc.chunk_index,
                        'chunk_type': doc.chunk_type,
                        'table_id': doc.table_id if hasattr(doc, 'table_id') else None,
                        'table_type': doc.table_type if hasattr(doc, 'table_type') else None,
                        'table_title': doc.table_title if hasattr(doc, 'table_title') else '',
                        'table_summary': doc.table_summary if hasattr(doc, 'table_summary') else '',
                        'table_headers': doc.table_headers if hasattr(doc, 'table_headers') else [],
                        'related_text': doc.related_text if hasattr(doc, 'related_text') else '',
                        'processed_table_content': doc.processed_table_content if hasattr(doc, 'processed_table_content') else None,
                        'table_row_count': doc.table_row_count if hasattr(doc, 'table_row_count') else None,
                        'table_column_count': doc.table_column_count if hasattr(doc, 'table_column_count') else None
                    }
                    text = doc.processed_table_content if doc.chunk_type == 'table' and doc.processed_table_content else doc.content
                else:
                    metadata = doc.metadata.copy() if doc.metadata else {}
                    # 将page_content添加到元数据中，确保HTML内容被保存
                    if hasattr(doc, 'page_content') and doc.page_content:
                        metadata['page_content'] = doc.page_content
                    text = doc.page_content
                
                # 使用最语义化的文本内容
                if metadata.get('chunk_type') == 'table' and 'processed_table_content' in metadata and metadata['processed_table_content']:
                    texts.append(metadata['processed_table_content'])
                else:
                    texts.append(text)
                
                # 确保元数据包含必要的信息
                metadata = metadata.copy() if metadata else {}
                
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
            
            # 检查是否启用enhanced_description向量化
            # 支持嵌套配置，兼容两种配置结构
            if isinstance(self.config, dict):
                if 'image_processing' in self.config:
                    enable_vectorization = self.config['image_processing'].get('enable_enhanced_description_vectorization', False)
                else:
                    enable_vectorization = self.config.get('enable_enhanced_description_vectorization', False)
            else:
                # 如果是 Settings 对象，直接使用 get 方法
                enable_vectorization = self.config.get('enable_enhanced_description_vectorization', False)
            
            if enable_vectorization:
                logger.info("已启用enhanced_description向量化功能")
            
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
                
                # 新增：准备文本向量（如果启用向量化）
                text_documents = []
                
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
                    
                    # 新增：如果启用向量化且有文本向量，创建文本Document
                    if enable_vectorization and result.get('enhanced_description'):
                        try:
                            from langchain.schema import Document
                            
                            # 创建image_text Document对象（使用正确的chunk_type）
                            text_doc = Document(
                                page_content=result["enhanced_description"],
                                metadata={
                                    "chunk_type": "image_text",  # 修复：使用正确的chunk_type
                                    "source_type": "image_description",
                                    "image_id": result["image_id"],
                                    "document_name": result.get("document_name", "未知文档"),
                                    "page_number": result.get("page_number", 1),
                                    "enhanced_description": result["enhanced_description"],
                                    "text_embedding_vectorized": True,
                                    "related_image_id": result["image_id"],  # 关联字段
                                    "page_idx": result.get("page_idx", 0),
                                    "img_caption": result.get("img_caption", []),
                                    "img_footnote": result.get("img_footnote", [])
                                }
                            )
                            text_documents.append(text_doc)
                            
                            logger.info(f"已为图片 {result['image_id']} 创建image_text Document")
                            
                        except Exception as e:
                            logger.warning(f"创建文本Document失败: {e}")
                
                # 添加到向量存储
                vector_store.add_embeddings(text_embeddings, metadatas=metadatas)
                
                # 新增：添加文本向量到向量存储
                if text_documents:
                    try:
                        logger.info(f"开始添加 {len(text_documents)} 个文本向量到向量存储")
                        
                        # 使用text-embedding-v1生成文本向量
                        texts = [doc.page_content for doc in text_documents]
                        text_embeddings_list = self.embeddings.embed_documents(texts)
                        
                        # 准备文本向量对
                        text_embedding_pairs = []
                        text_metadatas = []
                        
                        for i, doc in enumerate(text_documents):
                            text_embedding_pairs.append((doc.page_content, text_embeddings_list[i]))
                            text_metadatas.append(doc.metadata)
                        
                        # 添加到向量存储
                        vector_store.add_embeddings(text_embedding_pairs, metadatas=text_metadatas)
                        
                        logger.info(f"成功添加 {len(text_documents)} 个文本向量")
                        
                    except Exception as e:
                        logger.error(f"添加文本向量失败: {e}")
                
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
                if text_documents:
                    logger.info(f"同时创建了 {len(text_documents)} 个文本向量")
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
            
            # DashScope API限制：最大2048字符
            max_text_length = 2048
            
            for doc in documents:
                text = doc.page_content
                
                # 使用最语义化的文本内容
                if doc.metadata.get('chunk_type') == 'table' and 'processed_table_content' in doc.metadata:
                    text = doc.metadata['processed_table_content']
                
                # 验证文本长度，如果超过限制则截断
                if len(text) > max_text_length:
                    logger.warning(f"文档内容超过{max_text_length}字符限制，已截断: {len(text)} -> {max_text_length}")
                    # 尝试在句号、换行符等位置截断
                    for separator in ["。", "！", "？", ".", "!", "?", "\n\n", "\n"]:
                        last_sep_pos = text[:max_text_length].rfind(separator)
                        if last_sep_pos > max_text_length * 0.8:  # 在80%位置之后找到分隔符
                            text = text[:last_sep_pos + len(separator)]
                            break
                    else:
                        # 如果没找到合适的分隔符，直接截断
                        text = text[:max_text_length]
                
                texts.append(text)
                
                # 确保元数据包含必要的信息
                metadata = doc.metadata.copy() if doc.metadata else {}
                
                # 将page_content添加到元数据中，确保HTML内容被保存
                if hasattr(doc, 'page_content') and doc.page_content:
                    metadata['page_content'] = doc.page_content
                
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
            
            # 更新向量存储的metadata
            current_metadata = vector_store.metadata if hasattr(vector_store, 'metadata') else []
            if current_metadata is None:
                current_metadata = []
            if not isinstance(current_metadata, list):
                current_metadata = list(current_metadata) if hasattr(current_metadata, '__iter__') else []
            current_metadata.extend(metadatas)
            vector_store.metadata = current_metadata
            
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
            # 从配置中获取安全反序列化设置，如果没有则使用默认值
            allow_dangerous_deserialization = getattr(self.config, 'allow_dangerous_deserialization', True)
            vector_store = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=allow_dangerous_deserialization)
            
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
            
            # 保存元数据到metadata.pkl文件
            metadata_path = save_path_obj / "metadata.pkl"
            logger.info(f"正在保存元数据到路径: {metadata_path}")
            
            # 直接使用vector_store.metadata保存元数据
            all_metadata = vector_store.metadata if hasattr(vector_store, 'metadata') else []
            if all_metadata is None:
                all_metadata = []
            if not isinstance(all_metadata, list):
                all_metadata = list(all_metadata) if hasattr(all_metadata, '__iter__') else []
            
            # 保存元数据到metadata.pkl
            with open(metadata_path, "wb") as f:
                pickle.dump(all_metadata, f)
            logger.info("元数据保存完成")
            logger.info(f"metadata.pkl包含 {len(all_metadata)} 个文档的完整元数据")
            
            # 显示元数据统计
            chunk_types = {}
            for metadata in all_metadata:
                chunk_type = metadata.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            logger.info("元数据统计:")
            for chunk_type, count in sorted(chunk_types.items()):
                logger.info(f"  {chunk_type}: {count} 个")
                
            logger.info(f"向量存储完整保存完成: {save_path}")
            
        except Exception as e:
            logger.error(f"保存向量存储失败: {e}")
            raise 