#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查文档的实际内容结构
"""

import pickle
from pathlib import Path

def check_document_content():
    """检查文档的实际内容结构"""
    index_path = Path('central/vector_db/index.pkl')
    
    if not index_path.exists():
        print(f"❌ 索引文件不存在: {index_path}")
        return
    
    try:
        with open(index_path, 'rb') as f:
            index_data = pickle.load(f)
        
        print(f"📊 文档内容分析")
        print(f"文件路径: {index_path.absolute()}")
        print()
        
        # 第2个元素应该是文档字典
        if len(index_data) >= 2 and isinstance(index_data[1], dict):
            metadata_dict = index_data[1]
            print(f"📋 文档字典:")
            print(f"  键数量: {len(metadata_dict)}")
            print(f"  键范围: {min(metadata_dict.keys())} - {max(metadata_dict.keys())}")
            print()
            
            # 检查前几个文档的内容
            print("🔍 前5个文档的内容:")
            for i in range(min(5, len(metadata_dict))):
                if i in metadata_dict:
                    doc = metadata_dict[i]
                    print(f"  文档 {i}:")
                    print(f"    类型: {type(doc)}")
                    if isinstance(doc, str):
                        print(f"    内容长度: {len(doc)}")
                        print(f"    内容预览: {doc[:200]}...")
                    elif isinstance(doc, dict):
                        print(f"    键: {list(doc.keys())}")
                        for key, value in doc.items():
                            if key == 'page_content':
                                content_preview = str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                                print(f"    {key}: {content_preview}")
                            else:
                                print(f"    {key}: {value}")
                    else:
                        print(f"    值: {doc}")
                    print()
            
            # 检查是否有包含元数据的文档
            print("🔍 查找包含元数据的文档:")
            metadata_docs = []
            for i, doc in metadata_dict.items():
                if isinstance(doc, dict) and 'document_name' in doc:
                    metadata_docs.append((i, doc))
                    if len(metadata_docs) >= 3:
                        break
            
            if metadata_docs:
                print(f"  找到 {len(metadata_docs)} 个包含元数据的文档:")
                for i, doc in metadata_docs:
                    print(f"    [{i}] {doc.get('chunk_type', 'N/A')}: {doc.get('document_name', 'N/A')} (p.{doc.get('page_number', 'N/A')})")
            else:
                print("  未找到包含元数据的文档")
                
                # 检查是否有其他结构
                print("  检查其他可能的文档结构:")
                sample_docs = list(metadata_dict.items())[:5]
                for i, doc in sample_docs:
                    if isinstance(doc, dict):
                        print(f"    文档 {i} 的键: {list(doc.keys())}")
                    else:
                        print(f"    文档 {i} 类型: {type(doc)}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    check_document_content()
