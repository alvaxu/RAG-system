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

def check_new_doc_chunks():
    """检查新增文档的具体分块内容"""
    
    print("=" * 60)
    print("新增文档分块内容检查")
    print("=" * 60)
    
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
        new_doc_chunks = []
        old_doc_chunks = []
        
        print(f"总文档数: {len(vector_store.docstore._dict)}")
        
        for doc_id, doc in vector_store.docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                source = doc.metadata.get('source', '')
                print(f"文档ID: {doc_id}, 来源: {source}")
                
                if '上海证券' in source:
                    new_doc_chunks.append({
                        'id': doc_id,
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    })
                elif '中原证券' in source:
                    old_doc_chunks.append({
                        'id': doc_id,
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    })
        
        print(f"\n📊 分块统计:")
        print(f"   - 新增文档块数: {len(new_doc_chunks)}")
        print(f"   - 原始文档块数: {len(old_doc_chunks)}")
        
        # 检查新增文档的前几个块
        print(f"\n📋 新增文档前5个块的内容:")
        for i, chunk in enumerate(new_doc_chunks[:5]):
            print(f"\n--- 块 {i+1} ---")
            print(f"ID: {chunk['id']}")
            print(f"内容长度: {len(chunk['content'])} 字符")
            print(f"内容预览: {chunk['content'][:200]}...")
            print(f"元数据: {chunk['metadata']}")
        
        # 检查原始文档的前几个块作为对比
        print(f"\n📋 原始文档前3个块的内容:")
        for i, chunk in enumerate(old_doc_chunks[:3]):
            print(f"\n--- 块 {i+1} ---")
            print(f"ID: {chunk['id']}")
            print(f"内容长度: {len(chunk['content'])} 字符")
            print(f"内容预览: {chunk['content'][:200]}...")
            print(f"元数据: {chunk['metadata']}")
        
        # 检查关键词匹配
        test_keywords = ['中芯国际', '晶圆制造', '三大行业特征', '深度研究']
        print(f"\n🔍 关键词匹配检查:")
        for keyword in test_keywords:
            new_matches = sum(1 for chunk in new_doc_chunks if keyword in chunk['content'])
            old_matches = sum(1 for chunk in old_doc_chunks if keyword in chunk['content'])
            print(f"   - '{keyword}': 新增文档 {new_matches} 个块, 原始文档 {old_matches} 个块")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == "__main__":
    check_new_doc_chunks() 