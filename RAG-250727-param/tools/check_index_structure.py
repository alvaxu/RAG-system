#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查index.pkl的详细结构
"""

import pickle
from pathlib import Path

def check_index_structure():
    """检查index.pkl的详细结构"""
    index_path = Path('central/vector_db/index.pkl')
    
    if not index_path.exists():
        print(f"❌ 索引文件不存在: {index_path}")
        return
    
    try:
        with open(index_path, 'rb') as f:
            index_data = pickle.load(f)
        
        print(f"📊 index.pkl 结构分析")
        print(f"文件路径: {index_path.absolute()}")
        print(f"数据类型: {type(index_data)}")
        print(f"数据长度: {len(index_data)}")
        print()
        
        for i, item in enumerate(index_data):
            print(f"📋 第{i+1}个元素:")
            print(f"  类型: {type(item)}")
            print(f"  长度: {len(item) if hasattr(item, '__len__') else 'No length'}")
            
            if isinstance(item, list):
                print(f"  列表元素数量: {len(item)}")
                if len(item) > 0:
                    print(f"  第一个元素类型: {type(item[0])}")
                    if isinstance(item[0], dict):
                        print(f"  第一个元素键: {list(item[0].keys())}")
                        # 显示前几个文档的元数据
                        print(f"  前3个文档的document_name:")
                        for j, doc in enumerate(item[:3]):
                            if isinstance(doc, dict):
                                doc_name = doc.get('document_name', 'N/A')
                                chunk_type = doc.get('chunk_type', 'N/A')
                                print(f"    [{j+1}] {chunk_type}: {doc_name}")
            
            elif isinstance(item, dict):
                print(f"  字典键: {list(item.keys())}")
            
            print()
        
        # 检查是否包含元数据
        print("🔍 查找元数据:")
        for i, item in enumerate(index_data):
            if isinstance(item, list) and len(item) > 0:
                # 检查第一个元素是否有document_name字段
                if isinstance(item[0], dict) and 'document_name' in item[0]:
                    print(f"  第{i+1}个元素包含元数据，文档数量: {len(item)}")
                    # 统计chunk_type
                    chunk_types = {}
                    for doc in item:
                        if isinstance(doc, dict):
                            chunk_type = doc.get('chunk_type', 'unknown')
                            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                    print(f"  Chunk类型分布: {chunk_types}")
                    
                    # 显示一些示例
                    print(f"  示例文档:")
                    for j, doc in enumerate(item[:2]):
                        if isinstance(doc, dict):
                            print(f"    [{j+1}] {doc.get('chunk_type', 'N/A')}: {doc.get('document_name', 'N/A')} (p.{doc.get('page_number', 'N/A')})")
                    break
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    check_index_structure()
