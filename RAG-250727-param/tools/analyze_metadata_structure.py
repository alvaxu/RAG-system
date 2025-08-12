#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元数据结构分析脚本
用于分析vector_db中存储的元数据字段结构
"""

import pickle
import json
from collections import defaultdict
from pathlib import Path

def analyze_metadata_structure():
    """分析元数据结构"""
    metadata_path = Path('central/vector_db/metadata.pkl')
    
    if not metadata_path.exists():
        print(f"❌ 元数据文件不存在: {metadata_path}")
        return
    
    try:
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"📊 元数据分析结果")
        print(f"文件路径: {metadata_path.absolute()}")
        print(f"数据类型: {type(metadata)}")
        print(f"数据长度: {len(metadata)}")
        print()
        
        # 分析字段结构
        field_types = defaultdict(set)
        field_examples = defaultdict(list)
        chunk_type_fields = defaultdict(set)
        
        for i, item in enumerate(metadata):
            if isinstance(item, dict):
                chunk_type = item.get('chunk_type', 'unknown')
                
                for field, value in item.items():
                    field_types[field].add(type(value).__name__)
                    chunk_type_fields[chunk_type].add(field)
                    
                    # 保存前3个示例
                    if len(field_examples[field]) < 3:
                        field_examples[field].append({
                            'chunk_type': chunk_type,
                            'value': str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                        })
        
        print("🔍 字段类型分析:")
        for field, types in sorted(field_types.items()):
            print(f"  {field}: {', '.join(sorted(types))}")
        
        print("\n📋 按chunk_type分组的字段:")
        for chunk_type, fields in sorted(chunk_type_fields.items()):
            print(f"  {chunk_type}: {', '.join(sorted(fields))}")
        
        print("\n📝 字段示例:")
        for field, examples in sorted(field_examples.items()):
            print(f"  {field}:")
            for example in examples:
                print(f"    [{example['chunk_type']}] {example['value']}")
        
        # 分析特定字段
        print("\n🎯 关键字段分析:")
        key_fields = ['document_name', 'page_number', 'chunk_type', 'source', 'title']
        for field in key_fields:
            if field in field_types:
                values = [item.get(field, 'N/A') for item in metadata if isinstance(item, dict)]
                unique_values = set(values)
                print(f"  {field}: {len(unique_values)} 个唯一值")
                if len(unique_values) <= 5:
                    print(f"    值: {list(unique_values)}")
                else:
                    print(f"    前5个值: {list(unique_values)[:5]}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    analyze_metadata_structure()
