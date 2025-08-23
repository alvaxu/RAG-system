#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
测试表格数据流，验证TableEngine返回的数据结构和v2_routes.py的数据处理逻辑

## 1. 模拟TableEngine返回的数据结构
## 2. 测试v2_routes.py中的_extract_actual_doc_and_score函数
## 3. 验证表格ID和HTML内容的提取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.api.v2_routes import _extract_actual_doc_and_score

def test_table_data_extraction():
    """测试表格数据提取逻辑"""
    print("🔍 测试表格数据提取逻辑")
    print("=" * 50)
    
    # 模拟TableEngine返回的统一Pipeline格式
    mock_table_result = {
        'content': '这是表格的语义化内容',
        'metadata': {
            'document_name': '测试文档',
            'page_number': 1,
            'chunk_type': 'table'
        },
        'original_result': {
            'doc': {
                'doc': {
                    'page_content': '<table><tr><td>测试表格</td></tr></table>',
                    'document_name': '测试文档',  # 🔑 修复：直接在inner_doc中添加document_name
                    'page_number': 1,
                    'table_id': 'table_001',
                    'chunk_type': 'table',
                    'metadata': {
                        'document_name': '测试文档',
                        'page_number': 1,
                        'table_id': 'table_001',
                        'chunk_type': 'table'
                    }
                },
                'score': 0.85
            }
        }
    }
    
    print("📊 模拟数据:")
    print(f"  - 类型: {type(mock_table_result)}")
    print(f"  - 结构: {mock_table_result}")
    print()
    
    # 测试数据提取
    actual_doc, score = _extract_actual_doc_and_score(mock_table_result)
    
    print("🔍 提取结果:")
    if actual_doc:
        print(f"  - actual_doc类型: {type(actual_doc)}")
        print(f"  - 是否有metadata: {hasattr(actual_doc, 'metadata')}")
        if hasattr(actual_doc, 'metadata'):
            print(f"  - metadata: {actual_doc.metadata}")
            print(f"  - table_id: {actual_doc.metadata.get('table_id', '未找到')}")
            print(f"  - document_name: {actual_doc.metadata.get('document_name', '未找到')}")
            print(f"  - page_number: {actual_doc.metadata.get('page_number', '未找到')}")
        print(f"  - 是否有page_content: {hasattr(actual_doc, 'page_content')}")
        if hasattr(actual_doc, 'page_content'):
            print(f"  - page_content类型: {type(actual_doc.page_content)}")
            print(f"  - page_content长度: {len(actual_doc.page_content)}")
            print(f"  - page_content前100字符: '{actual_doc.page_content[:100]}...'")
        print(f"  - score: {score}")
    else:
        print("  - 提取失败，actual_doc为None")
    
    print()
    
    # 测试表格结果构建逻辑
    print("🔍 测试表格结果构建逻辑:")
    if actual_doc and hasattr(actual_doc, 'metadata'):
        # 模拟v2_routes.py中的表格结果构建
        table_result = {
            'id': actual_doc.metadata.get('table_id', 'unknown') or f"table_1",
            'table_html': actual_doc.metadata.get('page_content', '') or getattr(actual_doc, 'page_content', ''),
            'document_name': actual_doc.metadata.get('document_name', '未知文档'),
            'page_number': actual_doc.metadata.get('page_number', 'N/A'),
            'score': score
        }
        
        print(f"  - 构建的table_result: {table_result}")
        print(f"  - id字段: '{table_result['id']}'")
        print(f"  - table_html字段: '{table_result['table_html'][:100]}...'")
        print(f"  - document_name字段: '{table_result['document_name']}'")
        print(f"  - page_number字段: '{table_result['page_number']}'")
    
    print("=" * 50)

def test_flat_structure():
    """测试扁平化结构的数据提取"""
    print("🔍 测试扁平化结构的数据提取")
    print("=" * 50)
    
    # 模拟扁平化结构（来自TableEngine的formatted_result）
    mock_flat_result = {
        'id': 'table_001',
        'content': '这是表格的语义化内容',
        'page_content': '<table><tr><td>测试表格</td></tr></table>',
        'document_name': '测试文档',
        'page_number': 1,
        'chunk_type': 'table',
        'table_type': '数据表格',
        'score': 0.85,
        'metadata': {
            'document_name': '测试文档',
            'page_number': 1,
            'table_type': '数据表格'
        }
    }
    
    print("📊 模拟扁平化数据:")
    print(f"  - 类型: {type(mock_flat_result)}")
    print(f"  - 结构: {mock_flat_result}")
    print()
    
    # 测试数据提取
    actual_doc, score = _extract_actual_doc_and_score(mock_flat_result)
    
    print("🔍 提取结果:")
    if actual_doc:
        print(f"  - actual_doc类型: {type(actual_doc)}")
        print(f"  - 是否有metadata: {hasattr(actual_doc, 'metadata')}")
        if hasattr(actual_doc, 'metadata'):
            print(f"  - metadata: {actual_doc.metadata}")
        print(f"  - 是否有page_content: {hasattr(actual_doc, 'page_content')}")
        if hasattr(actual_doc, 'page_content'):
            print(f"  - page_content: '{actual_doc.page_content[:100]}...'")
        print(f"  - score: {score}")
    else:
        print("  - 提取失败，actual_doc为None")
    
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 开始测试表格数据流")
    print()
    
    test_table_data_extraction()
    print()
    test_flat_structure()
    
    print("✅ 测试完成")
