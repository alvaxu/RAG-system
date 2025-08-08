#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from document_processing.vector_generator import VectorGenerator
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_document_sources():
    """检查向量数据库中的文档来源分布"""
    try:
        # 加载配置
        settings = Settings.load_from_file("config.json")
        
        # 初始化向量生成器
        vector_generator = VectorGenerator(settings)
        
        # 加载向量存储
        vector_store = vector_generator.load_vector_store(settings.vector_db_dir)
        
        if vector_store is None:
            logger.error("无法加载向量存储")
            return
        
        # 获取所有文档的元数据
        metadatas = []
        for doc_id, doc in vector_store.docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                metadatas.append(doc.metadata)
        
        if not metadatas:
            logger.warning("向量存储中没有元数据")
            return
        
        # 统计文档来源
        document_sources = {}
        for metadata in metadatas:
            if metadata and 'document_name' in metadata:
                doc_name = metadata['document_name']
                if doc_name in document_sources:
                    document_sources[doc_name] += 1
                else:
                    document_sources[doc_name] = 1
        
        print("=" * 60)
        print("向量数据库中的文档来源分布")
        print("=" * 60)
        
        total_chunks = len(metadatas)
        print(f"总块数: {total_chunks}")
        print()
        
        for doc_name, count in document_sources.items():
            print(f"文档: {doc_name}")
            print(f"  块数: {count}")
            print()
        
        # 检查是否有新增文档的内容
        new_doc_keywords = ["上海证券", "深度研究报告", "晶圆制造龙头"]
        found_new_docs = []
        
        for doc_name in document_sources.keys():
            for keyword in new_doc_keywords:
                if keyword in doc_name:
                    found_new_docs.append(doc_name)
                    break
        
        print("=" * 60)
        print("新增文档检查结果")
        print("=" * 60)
        
        if found_new_docs:
            print("✅ 找到新增文档:")
            for doc_name in found_new_docs:
                print(f"  - {doc_name} (块数: {document_sources[doc_name]})")
        else:
            print("❌ 未找到新增文档")
            print("可能的原因:")
            print("  1. 新增文档未被正确添加到向量数据库")
            print("  2. 文档名称不包含预期的关键词")
            print("  3. 向量数据库元数据有问题")
        
        print()
        
        # 检查原始文档
        original_doc_keywords = ["中原证券", "季报点评"]
        found_original_docs = []
        
        for doc_name in document_sources.keys():
            for keyword in original_doc_keywords:
                if keyword in doc_name:
                    found_original_docs.append(doc_name)
                    break
        
        print("原始文档:")
        for doc_name in found_original_docs:
            print(f"  - {doc_name} (块数: {document_sources[doc_name]})")
        
    except Exception as e:
        logger.error(f"检查文档来源时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_document_sources() 