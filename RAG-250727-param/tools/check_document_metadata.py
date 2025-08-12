#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查index.pkl中存储的文档元数据
"""

import pickle
from pathlib import Path

def check_document_metadata():
    """检查index.pkl中的文档元数据"""
    index_path = Path('central/vector_db/index.pkl')
    
    if not index_path.exists():
        print(f"❌ 索引文件不存在: {index_path}")
        return
    
    try:
        with open(index_path, 'rb') as f:
            index_data = pickle.load(f)
        
        print(f"📊 文档元数据分析")
        print(f"文件路径: {index_path.absolute()}")
        print(f"数据类型: {type(index_data)}")
        print(f"数据长度: {len(index_data)}")
        print()
        
        # 第2个元素应该是文档元数据字典
        if len(index_data) >= 2 and isinstance(index_data[1], dict):
            metadata_dict = index_data[1]
            print(f"📋 文档元数据字典:")
            print(f"  键数量: {len(metadata_dict)}")
            print(f"  键范围: {min(metadata_dict.keys())} - {max(metadata_dict.keys())}")
            print()
            
            # 检查前几个文档的元数据
            print("🔍 前5个文档的元数据:")
            for i in range(min(5, len(metadata_dict))):
                if i in metadata_dict:
                    doc = metadata_dict[i]
                    print(f"  文档 {i}:")
                    if isinstance(doc, dict):
                        for key, value in doc.items():
                            if key == 'page_content':
                                content_preview = str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                                print(f"    {key}: {content_preview}")
                            else:
                                print(f"    {key}: {value}")
                    else:
                        print(f"    类型: {type(doc)}")
                    print()
            
            # 统计chunk_type分布
            print("📊 Chunk类型分布:")
            chunk_types = {}
            for i, doc in metadata_dict.items():
                if isinstance(doc, dict) and 'chunk_type' in doc:
                    chunk_type = doc['chunk_type']
                    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            for chunk_type, count in sorted(chunk_types.items()):
                print(f"  {chunk_type}: {count}")
            
            # 检查关键字段
            print("\n🎯 关键字段检查:")
            key_fields = ['document_name', 'page_number', 'chunk_type', 'source', 'title']
            for field in key_fields:
                field_values = set()
                for doc in metadata_dict.values():
                    if isinstance(doc, dict) and field in doc:
                        field_values.add(doc[field])
                
                if field_values:
                    print(f"  {field}: {len(field_values)} 个唯一值")
                    if len(field_values) <= 3:
                        print(f"    值: {list(field_values)}")
                    else:
                        print(f"    前3个值: {list(field_values)[:3]}")
                else:
                    print(f"  {field}: 未找到")
            
            # 显示一些示例文档
            print("\n📝 示例文档:")
            sample_count = 0
            for i, doc in metadata_dict.items():
                if sample_count >= 3:
                    break
                if isinstance(doc, dict) and 'document_name' in doc:
                    print(f"  [{i}] {doc.get('chunk_type', 'N/A')}: {doc.get('document_name', 'N/A')} (p.{doc.get('page_number', 'N/A')})")
                    sample_count += 1
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    check_document_metadata()
