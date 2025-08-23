#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
找出向量数据库中缺少HTML内容的表格
"""

import os
import sys
import pickle
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def find_missing_html_tables(vector_db_path):
    """
    找出向量数据库中缺少HTML内容的表格
    
    :param vector_db_path: 向量数据库路径
    :return: 缺少HTML内容的表格列表
    """
    try:
        # 加载元数据
        metadata_path = Path(vector_db_path) / "metadata.pkl"
        if not metadata_path.exists():
            print(f"❌ 元数据文件不存在: {metadata_path}")
            return []
        
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"📊 加载了 {len(metadata)} 个文档的元数据")
        
        # 找出所有表格文档
        table_docs = []
        missing_html_tables = []
        
        for i, doc_metadata in enumerate(metadata):
            if doc_metadata.get('chunk_type') == 'table':
                table_docs.append({
                    'index': i,
                    'metadata': doc_metadata
                })
                
                # 检查是否缺少HTML内容
                page_content = doc_metadata.get('page_content', '')
                if not page_content or page_content.strip() == '':
                    missing_html_tables.append({
                        'index': i,
                        'metadata': doc_metadata,
                        'reason': 'page_content为空或不存在'
                    })
                elif not page_content.strip().startswith('<table'):
                    missing_html_tables.append({
                        'index': i,
                        'metadata': doc_metadata,
                        'reason': 'page_content不是HTML格式',
                        'content_preview': page_content[:100]
                    })
        
        print(f"📋 找到 {len(table_docs)} 个表格文档")
        print(f"❌ 其中 {len(missing_html_tables)} 个缺少HTML内容")
        
        # 显示缺少HTML内容的表格详情
        if missing_html_tables:
            print("\n🔍 缺少HTML内容的表格详情:")
            for i, missing_table in enumerate(missing_html_tables, 1):
                metadata = missing_table['metadata']
                print(f"\n表格 {i}:")
                print(f"  索引: {missing_table['index']}")
                print(f"  表格ID: {metadata.get('table_id', 'N/A')}")
                print(f"  表格类型: {metadata.get('table_type', 'N/A')}")
                print(f"  文档名称: {metadata.get('document_name', 'N/A')}")
                print(f"  页码: {metadata.get('page_number', 'N/A')}")
                print(f"  分块索引: {metadata.get('chunk_index', 'N/A')}")
                print(f"  行数: {metadata.get('table_row_count', 'N/A')}")
                print(f"  列数: {metadata.get('table_column_count', 'N/A')}")
                print(f"  原因: {missing_table['reason']}")
                
                if 'content_preview' in missing_table:
                    print(f"  内容预览: {missing_table['content_preview']}")
                
                # 检查processed_table_content
                processed_content = metadata.get('processed_table_content', '')
                if processed_content:
                    print(f"  处理后内容: {processed_content[:100]}...")
                else:
                    print(f"  处理后内容: 无")
        
        # 分析分表情况
        print(f"\n📊 分表分析:")
        chunk_indices = [doc['metadata'].get('chunk_index', -1) for doc in table_docs]
        chunk_indices.sort()
        print(f"  分块索引范围: {min(chunk_indices)} - {max(chunk_indices)}")
        print(f"  分块索引列表: {chunk_indices}")
        
        # 按分块索引分组
        chunk_groups = {}
        for doc in table_docs:
            chunk_index = doc['metadata'].get('chunk_index', -1)
            if chunk_index not in chunk_groups:
                chunk_groups[chunk_index] = []
            chunk_groups[chunk_index].append(doc)
        
        print(f"\n📋 按分块索引分组的表格:")
        for chunk_index in sorted(chunk_groups.keys()):
            docs = chunk_groups[chunk_index]
            has_html_count = sum(1 for doc in docs if doc['metadata'].get('page_content', '').strip().startswith('<table'))
            total_count = len(docs)
            print(f"  分块 {chunk_index}: {total_count} 个表格，{has_html_count} 个有HTML")
        
        return missing_html_tables
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return []

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python find_missing_html_tables.py <vector_db_path>")
        print("示例: python find_missing_html_tables.py ./central/vector_db")
        sys.exit(1)
    
    vector_db_path = sys.argv[1]
    
    if not os.path.exists(vector_db_path):
        print(f"❌ 向量数据库路径不存在: {vector_db_path}")
        sys.exit(1)
    
    print(f"🔍 开始分析向量数据库: {vector_db_path}")
    missing_tables = find_missing_html_tables(vector_db_path)
    
    if missing_tables:
        print(f"\n❌ 发现 {len(missing_tables)} 个缺少HTML内容的表格")
        print("建议检查表格分块和HTML内容保存逻辑")
    else:
        print("\n✅ 所有表格都有HTML内容")

if __name__ == "__main__":
    main()
