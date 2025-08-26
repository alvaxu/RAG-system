'''
程序说明：

## 1. 统一文档加载管理器 - 解决重复加载问题
## 2. 一次性加载所有文档，按类型分类管理
## 3. 为各个子引擎提供统一的文档访问接口
## 4. 优化内存使用和启动性能
## 5. 支持延迟加载和错误重试机制
'''

import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentLoader:
    """统一文档加载管理器"""
    
    def __init__(self, vector_store, max_retries: int = 3):
        """
        初始化文档加载管理器
        
        :param vector_store: 向量数据库存储
        :param max_retries: 最大重试次数
        """
        self.vector_store = vector_store
        self._docs_cache = {}  # 统一缓存
        self._loaded = False
        self._load_time = 0.0
        self._max_retries = max_retries
        self._retry_count = 0
        
        logger.info("文档加载管理器初始化完成")
    
    def load_all_documents(self, force_reload: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        一次性加载所有文档，按类型分类
        
        :param force_reload: 是否强制重新加载
        :return: 按类型分类的文档字典
        """
        if self._loaded and not force_reload:
            logger.debug("文档已加载，跳过重复加载")
            return self._docs_cache
        
        start_time = time.time()
        logger.info("开始统一加载所有文档...")
        
        # 按类型分类加载
        docs_by_type = {
            'text': {},
            'image': {},
            'table': {},
            'image_text': {},  # 新增：图片描述文本chunks
            'hybrid': {}
        }
        
        try:
            # 检查向量数据库状态
            if not self.vector_store or not hasattr(self.vector_store, 'docstore'):
                raise ValueError("向量数据库未提供或没有docstore属性")
            
            # 一次性遍历向量数据库
            total_docs = 0
            for doc_id, doc in self.vector_store.docstore._dict.items():
                # 检查文档对象是否有效
                if not hasattr(doc, 'metadata'):
                    logger.warning(f"跳过无效文档 {doc_id}: 缺少metadata属性，文档类型: {type(doc)}")
                    continue
                
                if not hasattr(doc, 'page_content'):
                    logger.warning(f"跳过无效文档 {doc_id}: 缺少page_content属性，文档类型: {type(doc)}")
                    continue
                
                # 获取chunk_type，如果metadata不是字典则跳过
                if not isinstance(doc.metadata, dict):
                    logger.warning(f"跳过无效文档 {doc_id}: metadata不是字典类型，实际类型: {type(doc.metadata)}")
                    continue
                
                chunk_type = doc.metadata.get('chunk_type', 'text')  # 默认text
                
                # 根据类型分类
                if chunk_type in docs_by_type:
                    docs_by_type[chunk_type][doc_id] = doc
                    total_docs += 1
                else:
                    # 未知类型，归类到text
                    docs_by_type['text'][doc_id] = doc
                    total_docs += 1
                    logger.debug(f"未知类型文档归类到text: {doc_id}, chunk_type: {chunk_type}")
            
            # 统计信息
            text_count = len(docs_by_type['text'])
            image_count = len(docs_by_type['image'])
            table_count = len(docs_by_type['table'])
            image_text_count = len(docs_by_type['image_text'])  # 新增统计
            hybrid_count = len(docs_by_type['hybrid'])
            
            # 添加文档结构调试日志
            logger.info("🔍 DEBUG: 统一文档加载器文档结构分析:")
            logger.info(f"🔍 DEBUG: text文档类型: {type(docs_by_type['text'])}")
            logger.info(f"🔍 DEBUG: image文档类型: {type(docs_by_type['image'])}")
            logger.info(f"🔍 DEBUG: table文档类型: {type(docs_by_type['table'])}")
            logger.info(f"🔍 DEBUG: image_text文档类型: {type(docs_by_type['image_text'])}")
            
            # 检查前几个文档的结构
            if docs_by_type['text']:
                first_text_doc = list(docs_by_type['text'].values())[0] if isinstance(docs_by_type['text'], dict) else docs_by_type['text'][0]
                logger.info(f"🔍 DEBUG: 第一个text文档类型: {type(first_text_doc)}")
                if hasattr(first_text_doc, 'metadata'):
                    logger.info(f"🔍 DEBUG: 第一个text文档的chunk_type: {first_text_doc.metadata.get('chunk_type', 'unknown')}")
                    logger.info(f"🔍 DEBUG: 第一个text文档的metadata: {first_text_doc.metadata}")
                    if hasattr(first_text_doc, 'page_content'):
                        logger.info(f"🔍 DEBUG: 第一个text文档的page_content: {first_text_doc.page_content[:100]}...")
            
            if docs_by_type['image']:
                first_image_doc = list(docs_by_type['image'].values())[0] if isinstance(docs_by_type['image'], dict) else docs_by_type['image'][0]
                logger.info(f"🔍 DEBUG: 第一个image文档类型: {type(first_image_doc)}")
                if hasattr(first_image_doc, 'metadata'):
                    logger.info(f"🔍 DEBUG: 第一个image文档的chunk_type: {first_image_doc.metadata.get('chunk_type', 'unknown')}")
                    logger.info(f"🔍 DEBUG: 第一个image文档的metadata: {first_image_doc.metadata}")
                    if hasattr(first_image_doc, 'page_content'):
                        logger.info(f"🔍 DEBUG: 第一个image文档的page_content: {first_image_doc.page_content[:100]}...")
            
            if docs_by_type['table']:
                first_table_doc = list(docs_by_type['table'].values())[0] if isinstance(docs_by_type['table'], dict) else docs_by_type['table'][0]
                logger.info(f"🔍 DEBUG: 第一个table文档类型: {type(first_table_doc)}")
                if hasattr(first_table_doc, 'metadata'):
                    logger.info(f"🔍 DEBUG: 第一个table文档的chunk_type: {first_table_doc.metadata.get('chunk_type', 'unknown')}")
                    logger.info(f"🔍 DEBUG: 第一个table文档的metadata: {first_table_doc.metadata}")
                    if hasattr(first_table_doc, 'page_content'):
                        logger.info(f"🔍 DEBUG: 第一个table文档的page_content: {first_table_doc.page_content[:100]}...")
            
            logger.info(f"文档加载完成:")
            logger.info(f"  - 文本文档: {text_count} 个")
            logger.info(f"  - 图片文档: {image_count} 个")
            logger.info(f"  - 表格文档: {table_count} 个")
            logger.info(f"  - 图片描述文本: {image_text_count} 个")
            logger.info(f"  - 混合文档: {hybrid_count} 个")
            logger.info(f"  - 总计: {total_docs} 个")
            
            # 更新缓存和状态
            self._docs_cache = docs_by_type
            self._loaded = True
            self._load_time = time.time() - start_time
            self._retry_count = 0  # 重置重试计数
            
            logger.info(f"文档加载成功，耗时: {self._load_time:.2f}秒")
            return self._docs_cache
            
        except Exception as e:
            logger.error(f"文档加载失败，第{self._retry_count}次尝试: {e}")
            
            if self._retry_count < self._max_retries:
                logger.info(f"等待1秒后进行第{self._retry_count + 1}次重试...")
                time.sleep(1)
                return self.load_all_documents(force_reload=True)
            else:
                logger.error(f"文档加载最终失败，已重试{self._max_retries}次")
                self._loaded = False
                self._docs_cache = {}
                raise RuntimeError(f"文档加载失败: {e}")
    
    def get_documents_by_type(self, doc_type: str, ensure_loaded: bool = True) -> list:
        """
        获取指定类型的文档
        
        :param doc_type: 文档类型 (text, image, table, hybrid)
        :param ensure_loaded: 是否确保文档已加载
        :return: 指定类型的文档对象列表
        """
        if ensure_loaded and not self._loaded:
            self.load_all_documents()
        
        # 返回文档对象列表，而不是字典
        docs_dict = self._docs_cache.get(doc_type, {})
        return list(docs_dict.values())
    
    def get_document_by_id(self, doc_id: str, doc_type: str = None) -> Optional[Any]:
        """
        根据ID获取指定文档
        
        :param doc_id: 文档ID
        :param doc_type: 文档类型（可选，用于优化查找）
        :return: 文档对象或None
        """
        if not self._loaded:
            self.load_all_documents()
        
        if doc_type:
            # 指定类型查找
            return self._docs_cache.get(doc_type, {}).get(doc_id)
        else:
            # 在所有类型中查找
            for docs in self._docs_cache.values():
                if doc_id in docs:
                    return docs[doc_id]
            return None
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """
        获取文档统计信息
        
        :return: 统计信息字典
        """
        if not self._loaded:
            return {'error': '文档未加载'}
        
        stats = {
            'total_documents': sum(len(docs) for docs in self._docs_cache.values()),
            'documents_by_type': {
                doc_type: len(docs) for doc_type, docs in self._docs_cache.items()
            },
            'load_time': self._load_time,
            'loaded': self._loaded,
            'cache_size': len(self._docs_cache)
        }
        
        # 计算总字符数（仅文本文档）
        if 'text' in self._docs_cache:
            total_chars = sum(
                len(doc.page_content) if hasattr(doc, 'page_content') else 0 
                for doc in self._docs_cache['text'].values()
            )
            stats['total_text_chars'] = total_chars
        
        return stats
    
    def refresh_cache(self) -> bool:
        """
        刷新文档缓存
        
        :return: 是否成功
        """
        try:
            logger.info("开始刷新文档缓存...")
            self._loaded = False
            self.load_all_documents(force_reload=True)
            logger.info("文档缓存刷新成功")
            return True
        except Exception as e:
            logger.error(f"文档缓存刷新失败: {e}")
            return False
    
    def is_loaded(self) -> bool:
        """检查文档是否已加载"""
        return self._loaded
    
    def get_load_time(self) -> float:
        """获取文档加载耗时"""
        return self._load_time
    
    def clear_cache(self):
        """清空文档缓存"""
        self._docs_cache = {}
        self._loaded = False
        self._load_time = 0.0
        logger.info("文档缓存已清空")
