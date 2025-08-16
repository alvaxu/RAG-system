#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查图片文档的存储结构
"""

import pickle
from pathlib import Path

def check_image_doc_detail():
    """详细检查图片文档的存储结构"""
    index_path = Path('central/vector_db/index.pkl')
    
    if not index_path.exists():
        print(f"❌ 索引文件不存在: {index_path}")
        return
    
    try:
        with open(index_path, 'rb') as f:
            index_data = pickle.load(f)
        
        docstore = index_data[0]
        
        if not hasattr(docstore, '_dict'):
            print("❌ docstore没有_dict属性")
            return
        
        print("🔍 详细检查图片文档结构:")
        print("=" * 60)
        
        image_count = 0
        for doc_id, doc in docstore._dict.items():
            if (hasattr(doc, 'metadata') and 
                'chunk_type' in doc.metadata and 
                doc.metadata['chunk_type'] == 'image'):
                
                image_count += 1
                print(f"\n📷 图片文档 {image_count}:")
                print(f"  ID: {doc_id}")
                print(f"  文档名: {doc.metadata.get('document_name', 'N/A')}")
                print(f"  页码: {doc.metadata.get('page_number', 'N/A')}")
                
                # 检查page_content
                if hasattr(doc, 'page_content'):
                    print(f"  page_content长度: {len(doc.page_content)}")
                    print(f"  page_content内容: {doc.page_content[:200]}...")
                else:
                    print("  page_content: 不存在")
                
                # 检查metadata中的关键字段
                print(f"  完整metadata: {doc.metadata}")
                
                if image_count >= 3:  # 只显示前3个图片文档
                    break
        
        print(f"\n📊 总共找到 {image_count} 个图片文档")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    check_image_doc_detail()
