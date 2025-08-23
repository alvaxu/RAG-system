#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查表格HTML内容的脚本
"""

import os
import sys
import pickle
import faiss
from pathlib import Path

def check_table_html_content():
    """检查表格文档中的HTML内容"""
    
    # 向量数据库路径
    vector_db_path = "central/vector_db"
    
    if not os.path.exists(vector_db_path):
        print(f"❌ 向量数据库路径不存在: {vector_db_path}")
        return
    
    # 加载索引元数据
    try:
        with open(os.path.join(vector_db_path, "index.pkl"), "rb") as f:
            index_data = pickle.load(f)
        print(f"✅ 索引元数据加载成功")
    except Exception as e:
        print(f"❌ 索引元数据加载失败: {e}")
        return
    
    if len(index_data) >= 2:
        docstore = index_data[0]
        
        # 查找表格文档
        table_docs = []
        for doc_id, doc in docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', '')
                if chunk_type == 'table':
                    table_docs.append((doc_id, doc))
        
        print(f"\n📊 找到 {len(table_docs)} 个表格文档")
        
        if table_docs:
            print(f"\n🔍 检查表格文档的HTML内容:")
            
            html_count = 0
            text_count = 0
            
            for i, (doc_id, doc) in enumerate(table_docs[:5]):  # 只检查前5个
                print(f"\n📄 表格文档 {i+1}:")
                print(f"  文档ID: {doc_id}")
                
                if hasattr(doc, 'metadata'):
                    metadata = doc.metadata
                    document_name = metadata.get('document_name', '未知文档')
                    page_number = metadata.get('page_number', '未知页')
                    print(f"  文档: {document_name}")
                    print(f"  页码: {page_number}")
                
                if hasattr(doc, 'page_content'):
                    page_content = doc.page_content
                    print(f"  page_content类型: {type(page_content)}")
                    print(f"  page_content长度: {len(str(page_content))}")
                    
                    # 检查是否是HTML格式
                    if '<table' in str(page_content) or '<tr' in str(page_content) or '<td' in str(page_content):
                        print(f"  ✅ 包含HTML标签")
                        html_count += 1
                        print(f"  HTML内容预览: {str(page_content)[:300]}...")
                    else:
                        print(f"  ⚠️ 不包含HTML标签")
                        text_count += 1
                        print(f"  文本内容预览: {str(page_content)[:300]}...")
                
                # 检查其他可能的内容字段
                content_fields = ['content', 'processed_table_content', 'table_content']
                for field in content_fields:
                    if hasattr(doc, field):
                        value = getattr(doc, field)
                        if value:
                            print(f"  {field}: 长度 {len(str(value))}")
                            if '<table' in str(value) or '<tr' in str(value) or '<td' in str(value):
                                print(f"    ✅ {field} 包含HTML标签")
                            else:
                                print(f"    ⚠️ {field} 不包含HTML标签")
            
            print(f"\n📊 HTML内容统计:")
            print(f"  包含HTML标签的表格: {html_count}")
            print(f"  纯文本格式的表格: {text_count}")
            print(f"  总计检查: {min(5, len(table_docs))}")
    
    else:
        print(f"❌ 索引数据结构不正确")

if __name__ == "__main__":
    check_table_html_content()
