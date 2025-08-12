#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查InMemoryDocstore中的文档结构
"""

import pickle
from pathlib import Path

def check_docstore():
    """检查InMemoryDocstore中的文档结构"""
    index_path = Path('central/vector_db/index.pkl')
    
    if not index_path.exists():
        print(f"❌ 索引文件不存在: {index_path}")
        return
    
    try:
        with open(index_path, 'rb') as f:
            index_data = pickle.load(f)
        
        print(f"📊 InMemoryDocstore分析")
        print(f"文件路径: {index_path.absolute()}")
        print()
        
        # 第1个元素应该是InMemoryDocstore
        if len(index_data) >= 1:
            docstore = index_data[0]
            print(f"📋 第1个元素:")
            print(f"  类型: {type(docstore)}")
            print(f"  类型名: {type(docstore).__name__}")
            print()
            
            # 检查docstore的属性
            if hasattr(docstore, '_dict'):
                print(f"🔍 _dict属性:")
                docstore_dict = docstore._dict
                print(f"  类型: {type(docstore_dict)}")
                print(f"  长度: {len(docstore_dict)}")
                print(f"  键类型: {type(list(docstore_dict.keys())[0]) if docstore_dict else 'No keys'}")
                print()
                
                # 检查前几个文档
                print("📝 前3个文档:")
                for i, (doc_id, doc) in enumerate(list(docstore_dict.items())[:3]):
                    print(f"  文档 {i+1}:")
                    print(f"    ID: {doc_id}")
                    print(f"    类型: {type(doc)}")
                    if hasattr(doc, 'metadata'):
                        print(f"    元数据: {doc.metadata}")
                    if hasattr(doc, 'page_content'):
                        content_preview = doc.page_content[:100] + '...' if len(doc.page_content) > 100 else doc.page_content
                        print(f"    内容预览: {content_preview}")
                    print()
                
                # 统计chunk_type
                print("📊 Chunk类型分布:")
                chunk_types = {}
                for doc in docstore_dict.values():
                    if hasattr(doc, 'metadata') and 'chunk_type' in doc.metadata:
                        chunk_type = doc.metadata['chunk_type']
                        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                for chunk_type, count in sorted(chunk_types.items()):
                    print(f"  {chunk_type}: {count}")
                
                # 检查关键字段
                print("\n🎯 关键字段检查:")
                key_fields = ['document_name', 'page_number', 'chunk_type', 'source', 'title']
                for field in key_fields:
                    field_values = set()
                    for doc in docstore_dict.values():
                        if hasattr(doc, 'metadata') and field in doc.metadata:
                            field_values.add(doc.metadata[field])
                    
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
                for doc_id, doc in docstore_dict.items():
                    if sample_count >= 3:
                        break
                    if hasattr(doc, 'metadata') and 'document_name' in doc.metadata:
                        print(f"  [{doc_id}] {doc.metadata.get('chunk_type', 'N/A')}: {doc.metadata.get('document_name', 'N/A')} (p.{doc.metadata.get('page_number', 'N/A')})")
                        sample_count += 1
            else:
                print("❌ docstore没有_dict属性")
                print(f"可用属性: {[attr for attr in dir(docstore) if not attr.startswith('_')]}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    check_docstore()
