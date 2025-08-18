#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 诊断数据库中的表格文档结构
## 2. 检查文档对象的实际属性和类型
## 3. 帮助理解为什么表格引擎无法正确加载文档
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.document_loader import DocumentLoader
from document_processing.vector_generator import VectorGenerator
from config.config_manager import ConfigManager
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_table_docs_structure():
    """检查表格文档结构"""
    try:
        logger.info("🔍 开始检查表格文档结构...")
        
        # 1. 检查统一文档加载器
        logger.info("=" * 60)
        logger.info("1. 检查统一文档加载器")
        logger.info("=" * 60)
        
        try:
            # 加载配置
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # 初始化向量生成器
            vector_generator = VectorGenerator(config)
            
            # 初始化文档加载器
            document_loader = DocumentLoader(vector_generator.vector_store)
            table_docs = document_loader.get_documents_by_type('table')
            logger.info(f"统一文档加载器返回表格文档数量: {len(table_docs)}")
            
            if table_docs:
                # 检查前3个文档的结构
                for i, doc in enumerate(table_docs[:3]):
                    logger.info(f"\n📄 文档 {i} 结构分析:")
                    logger.info(f"  类型: {type(doc)}")
                    logger.info(f"  所有属性: {dir(doc)}")
                    
                    # 检查是否有metadata属性
                    if hasattr(doc, 'metadata'):
                        logger.info(f"  metadata类型: {type(doc.metadata)}")
                        logger.info(f"  metadata内容: {doc.metadata}")
                    else:
                        logger.info("  ❌ 没有metadata属性")
                    
                    # 检查是否有page_content属性
                    if hasattr(doc, 'page_content'):
                        logger.info(f"  page_content类型: {type(doc.page_content)}")
                        logger.info(f"  page_content长度: {len(doc.page_content)}")
                        logger.info(f"  page_content前100字符: {doc.page_content[:100]}...")
                    else:
                        logger.info("  ❌ 没有page_content属性")
                    
                    # 检查其他可能的属性
                    for attr in ['content', 'text', 'data', 'table_data']:
                        if hasattr(doc, attr):
                            logger.info(f"  {attr}属性: {getattr(doc, attr)}")
                    
                    # 如果是字典类型，显示所有键
                    if isinstance(doc, dict):
                        logger.info(f"  字典键: {list(doc.keys())}")
                        for key, value in doc.items():
                            logger.info(f"    {key}: {type(value)} = {str(value)[:100]}...")
                    
            else:
                logger.warning("⚠️ 统一文档加载器未返回任何表格文档")
                
        except Exception as e:
            logger.error(f"检查统一文档加载器失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
        
        # 2. 检查向量数据库
        logger.info("\n" + "=" * 60)
        logger.info("2. 检查向量数据库")
        logger.info("=" * 60)
        
        try:
            if hasattr(vector_generator, 'vector_store') and hasattr(vector_generator.vector_store, 'docstore') and hasattr(vector_generator.vector_store.docstore, '_dict'):
                docstore_dict = vector_generator.vector_store.docstore._dict
                logger.info(f"向量数据库docstore._dict长度: {len(docstore_dict)}")
                
                # 查找表格类型的文档
                table_docs_in_vector = []
                for doc_id, doc in docstore_dict.items():
                    if hasattr(doc, 'metadata'):
                        chunk_type = doc.metadata.get('chunk_type', '')
                        if chunk_type == 'table':
                            table_docs_in_vector.append((doc_id, doc))
                
                logger.info(f"向量数据库中找到 {len(table_docs_in_vector)} 个chunk_type='table'的文档")
                
                if table_docs_in_vector:
                    # 检查前3个表格文档
                    for i, (doc_id, doc) in enumerate(table_docs_in_vector[:3]):
                        logger.info(f"\n📊 向量数据库表格文档 {i} (ID: {doc_id}):")
                        logger.info(f"  类型: {type(doc)}")
                        logger.info(f"  所有属性: {dir(doc)}")
                        
                        if hasattr(doc, 'metadata'):
                            logger.info(f"  metadata: {doc.metadata}")
                        if hasattr(doc, 'page_content'):
                            logger.info(f"  page_content长度: {len(doc.page_content)}")
                            logger.info(f"  page_content前100字符: {doc.page_content[:100]}...")
                
                # 检查所有文档的chunk_type分布
                chunk_type_distribution = {}
                for doc_id, doc in docstore_dict.items():
                    if hasattr(doc, 'metadata'):
                        chunk_type = doc.metadata.get('chunk_type', 'unknown')
                        chunk_type_distribution[chunk_type] = chunk_type_distribution.get(chunk_type, 0) + 1
                
                logger.info(f"\n📊 chunk_type分布:")
                for chunk_type, count in chunk_type_distribution.items():
                    logger.info(f"  {chunk_type}: {count} 个")
                    
            else:
                logger.warning("⚠️ 向量数据库没有docstore._dict属性")
                
        except Exception as e:
            logger.error(f"检查向量数据库失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
        
        # 3. 总结和建议
        logger.info("\n" + "=" * 60)
        logger.info("3. 总结和建议")
        logger.info("=" * 60)
        
        logger.info("基于以上检查，表格引擎的问题可能是:")
        logger.info("1. 统一文档加载器返回的文档对象结构与预期不符")
        logger.info("2. 文档对象缺少必要的metadata或page_content属性")
        logger.info("3. 需要检查DocumentLoader.get_documents_by_type('table')的实现")
        
        logger.info("\n建议:")
        logger.info("1. 检查DocumentLoader.get_documents_by_type方法的实现")
        logger.info("2. 确认表格文档在数据库中的实际存储格式")
        logger.info("3. 根据实际文档结构调整表格引擎的加载逻辑")
        
    except Exception as e:
        logger.error(f"诊断脚本执行失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    check_table_docs_structure()
