#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接检查表格文档内容的脚本
"""

import os
import sys
import pickle
import faiss
from pathlib import Path

def check_table_content_direct():
    """直接检查向量数据库中的表格文档内容"""
    
    # 向量数据库路径
    vector_db_path = "central/vector_db"
    
    if not os.path.exists(vector_db_path):
        print(f"❌ 向量数据库路径不存在: {vector_db_path}")
        return
    
    # 加载FAISS索引
    try:
        index = faiss.read_index(os.path.join(vector_db_path, "index.faiss"))
        print(f"✅ FAISS索引加载成功，包含 {index.ntotal} 个向量")
    except Exception as e:
        print(f"❌ FAISS索引加载失败: {e}")
        return
    
    # 加载索引元数据
    try:
        with open(os.path.join(vector_db_path, "index.pkl"), "rb") as f:
            index_data = pickle.load(f)
        print(f"✅ 索引元数据加载成功")
    except Exception as e:
        print(f"❌ 索引元数据加载失败: {e}")
        return
    
    # 检查索引数据结构
    print(f"\n🔍 索引数据结构:")
    print(f"  类型: {type(index_data)}")
    print(f"  长度: {len(index_data)}")
    
    if len(index_data) >= 2:
        docstore = index_data[0]
        id_mapping = index_data[1]
        
        print(f"  文档存储类型: {type(docstore)}")
        print(f"  ID映射类型: {type(id_mapping)}")
        print(f"  ID映射长度: {len(id_mapping)}")
        
        # 查找表格文档
        table_docs = []
        for doc_id, doc in docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', '')
                if chunk_type == 'table':
                    table_docs.append((doc_id, doc))
        
        print(f"\n📊 找到 {len(table_docs)} 个表格文档")
        
        if table_docs:
            print(f"\n🔍 检查前3个表格文档:")
            for i, (doc_id, doc) in enumerate(table_docs[:3]):
                print(f"\n📄 表格文档 {i+1}:")
                print(f"  文档ID: {doc_id}")
                print(f"  文档类型: {type(doc)}")
                
                if hasattr(doc, 'metadata'):
                    metadata = doc.metadata
                    print(f"  元数据类型: {type(metadata)}")
                    print(f"  元数据键: {list(metadata.keys())}")
                    
                    # 检查关键字段
                    key_fields = ['document_name', 'page_number', 'chunk_type', 'table_id', 'table_type']
                    for field in key_fields:
                        value = metadata.get(field, 'NOT_FOUND')
                        print(f"    {field}: {value}")
                
                if hasattr(doc, 'page_content'):
                    page_content = doc.page_content
                    print(f"  page_content类型: {type(page_content)}")
                    print(f"  page_content长度: {len(str(page_content))}")
                    print(f"  page_content预览: {str(page_content)[:200]}...")
                
                # 检查是否有其他内容字段
                content_fields = ['content', 'processed_table_content', 'table_content']
                for field in content_fields:
                    if hasattr(doc, field):
                        value = getattr(doc, field)
                        print(f"  {field}: {type(value)}, 长度: {len(str(value))}")
                        print(f"  {field}预览: {str(value)[:100]}...")
    
    else:
        print(f"❌ 索引数据结构不正确，期望至少2个元素，实际: {len(index_data)}")

if __name__ == "__main__":
    check_table_content_direct()
