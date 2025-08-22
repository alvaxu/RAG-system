#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 调试table_engine的web端返回格式
## 2. 模拟process_query的完整流程
## 3. 检查最终结果的document_name和page_number
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_table_web_format():
    """测试table_engine的web端格式"""
    
    print("🔍 开始测试table_engine的web端格式")
    
    # 模拟策略1返回的结果格式
    print("\n📋 模拟策略1返回的结果:")
    
    # 模拟一个doc对象
    class MockDoc:
        def __init__(self):
            self.page_content = "港股（0981.HK）指标 | 2023 | 2024 | 2025E..."
            self.metadata = {
                'document_name': '【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题',
                'page_number': 1,
                'table_id': 'table_333611',
                'table_type': '数据表格',
                'chunk_type': 'table'
            }
    
    mock_doc = MockDoc()
    
    # 策略1的processed_doc格式
    strategy1_result = {
        'doc': mock_doc,
        'content': mock_doc.page_content,
        'metadata': mock_doc.metadata,
        'score': 0.85,
        'source': 'vector_search',
        'layer': 2,
        'search_method': 'content_semantic_similarity_filter',
        'vector_score': 0.85,
        'match_details': 'processed_table_content语义匹配(filter)'
    }
    
    print("策略1返回的processed_doc:")
    print(f"  doc类型: {type(strategy1_result['doc'])}")
    print(f"  doc.metadata: {strategy1_result['doc'].metadata}")
    print(f"  content长度: {len(strategy1_result['content'])}")
    print(f"  metadata: {strategy1_result['metadata']}")
    print(f"  score: {strategy1_result['score']}")
    
    # 模拟process_query中的格式化过程
    print("\n🔧 模拟process_query中的格式化:")
    
    result = strategy1_result
    doc = result['doc']
    metadata = getattr(doc, 'metadata', {})
    structure_analysis = result.get('structure_analysis', {})
    
    # 这是table_engine中process_query的格式化逻辑
    formatted_result = {
        'id': metadata.get('table_id', 'unknown'),
        'content': getattr(doc, 'page_content', ''),
        'score': result['score'],
        'source': result.get('source', 'unknown'),
        'layer': result.get('layer', 1),
        
        # 关键的顶层字段映射
        'page_content': getattr(doc, 'page_content', ''),
        'document_name': metadata.get('document_name', '未知文档'),
        'page_number': metadata.get('page_number', '未知页'),
        'chunk_type': 'table',
        'table_type': structure_analysis.get('table_type', 'unknown'),
        'doc_id': metadata.get('table_id') or metadata.get('doc_id') or metadata.get('id', 'unknown'),
        
        'metadata': {
            'document_name': metadata.get('document_name', '未知文档'),
            'page_number': metadata.get('page_number', '未知页'),
            'table_type': structure_analysis.get('table_type', 'unknown'),
            'business_domain': structure_analysis.get('business_domain', 'unknown'),
            'quality_score': structure_analysis.get('quality_score', 0.0),
            'is_truncated': structure_analysis.get('is_truncated', False),
            'truncation_type': structure_analysis.get('truncation_type', 'none'),
            'truncated_rows': structure_analysis.get('truncated_rows', 0),
            'current_rows': structure_analysis.get('row_count', 0),
            'original_rows': structure_analysis.get('original_row_count', 0)
        }
    }
    
    print("格式化后的结果:")
    print(f"  id: {formatted_result['id']}")
    print(f"  document_name: '{formatted_result['document_name']}'")
    print(f"  page_number: {formatted_result['page_number']}")
    print(f"  chunk_type: {formatted_result['chunk_type']}")
    print(f"  metadata.document_name: '{formatted_result['metadata']['document_name']}'")
    print(f"  metadata.page_number: {formatted_result['metadata']['page_number']}")
    
    # 检查是否会显示"未知文档"
    if formatted_result['document_name'] == '未知文档':
        print("❌ 会显示'未知文档'！")
    else:
        print("✅ document_name正常")
    
    if formatted_result['page_number'] == '未知页':
        print("❌ 会显示'未知页'！")
    else:
        print("✅ page_number正常")
    
    # 现在检查是否是structure_analysis的问题
    print(f"\n🔍 检查structure_analysis:")
    print(f"  structure_analysis: {structure_analysis}")
    print(f"  table_type从哪里来: metadata.get('table_type'): '{metadata.get('table_type', 'N/A')}'")
    print(f"  structure_analysis.get('table_type'): '{structure_analysis.get('table_type', 'N/A')}'")
    
    # 模拟正确的格式化（应该从metadata获取table_type）
    print(f"\n🔧 修正的格式化:")
    corrected_formatted_result = {
        'id': metadata.get('table_id', 'unknown'),
        'content': getattr(doc, 'page_content', ''),
        'score': result['score'],
        'source': result.get('source', 'unknown'),
        'layer': result.get('layer', 1),
        
        # 关键的顶层字段映射
        'page_content': getattr(doc, 'page_content', ''),
        'document_name': metadata.get('document_name', '未知文档'),
        'page_number': metadata.get('page_number', '未知页'),
        'chunk_type': 'table',
        'table_type': metadata.get('table_type', 'unknown'),  # 应该从metadata获取，不是structure_analysis
        'doc_id': metadata.get('table_id') or metadata.get('doc_id') or metadata.get('id', 'unknown'),
        
        'metadata': {
            'document_name': metadata.get('document_name', '未知文档'),
            'page_number': metadata.get('page_number', '未知页'),
            'table_type': metadata.get('table_type', 'unknown'),  # 从metadata获取
            'chunk_type': 'table'
        }
    }
    
    print("修正后的结果:")
    print(f"  table_type: '{corrected_formatted_result['table_type']}'")
    print(f"  metadata.table_type: '{corrected_formatted_result['metadata']['table_type']}'")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    test_table_web_format()
