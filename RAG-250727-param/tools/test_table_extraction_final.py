#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试修复后的表格数据提取是否成功
## 2. 验证_extract_actual_doc_and_score函数的工作
"""

import sys
import os
from pathlib import Path

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_mock_pipeline_result():
    """创建模拟的统一Pipeline结果"""
    from types import SimpleNamespace
    
    # 模拟Document对象
    mock_doc = SimpleNamespace()
    mock_doc.metadata = {
        'document_name': '【上海证券】中芯国际深度研究报告：晶圆制造龙头，领航国产芯片新征程',
        'page_number': 1,
        'chunk_index': 1,
        'chunk_type': 'table',
        'table_id': 'table_883313',
        'table_type': '数据表格',
        'table_title': '单位：百万元',
        'table_summary': '表头: 单位：百万元 | 2024A | 2025E | 2026E | 2027E',
        'table_headers': ['单位：百万元', '2024A', '2025E', '2026E', '2027E'],
        'processed_table_content': '单位：百万元 | 2024A | 2025E | 2026E | 2027E\n营业收入 | 57796 | 70652 | 78639 | 87584',
        'table_row_count': 6,
        'table_column_count': 5,
        'page_content': '<table><tr><td>单位：百万元</td><td>2024A</td><td>2025E</td><td>2026E</td><td>2027E</td></tr><tr><td>营业收入</td><td>57796</td><td>70652</td><td>78639</td><td>87584</td></tr></table>'
    }
    mock_doc.page_content = '单位：百万元 | 2024A | 2025E | 2026E | 2027E\n营业收入 | 57796 | 70652 | 78639 | 87584'
    
    # 构造统一Pipeline的结果格式
    pipeline_result = {
        'content': '',
        'metadata': {},
        'original_result': {
            'doc': {
                'doc': mock_doc,
                'page_content': '单位：百万元 | 2024A | 2025E | 2026E | 2027E\n营业收入 | 57796 | 70652 | 78639 | 87584',
                'score': 1.0
            }
        }
    }
    
    return pipeline_result

def test_extraction():
    """测试数据提取函数"""
    # 导入函数
    from v2.api.v2_routes import _extract_actual_doc_and_score
    
    # 创建测试数据
    pipeline_result = create_mock_pipeline_result()
    
    print("🔍 测试统一Pipeline结果格式提取...")
    print(f"📊 输入数据结构: {type(pipeline_result)}")
    print(f"📊 是否包含original_result: {'original_result' in pipeline_result}")
    print(f"📊 是否包含doc: {'doc' in pipeline_result['original_result']}")
    
    # 测试提取
    actual_doc, score = _extract_actual_doc_and_score(pipeline_result)
    
    if actual_doc is None:
        print("❌ 提取失败：actual_doc 为 None")
        return False
    
    print(f"\n✅ 提取成功！")
    print(f"📄 文档类型: {type(actual_doc)}")
    print(f"📄 是否有metadata: {hasattr(actual_doc, 'metadata')}")
    
    if hasattr(actual_doc, 'metadata'):
        metadata = actual_doc.metadata
        print(f"📄 文档名称: {metadata.get('document_name', '未知')}")
        print(f"📄 页码: {metadata.get('page_number', '未知')}")
        print(f"📄 表格ID: {metadata.get('table_id', '未知')}")
        print(f"📄 HTML内容长度: {len(metadata.get('page_content', ''))}")
        print(f"📄 HTML内容预览: {metadata.get('page_content', '')[:100]}...")
        print(f"📄 分数: {score}")
        
        # 模拟表格结果构建
        table_result = {
            'id': metadata.get('table_id', 'unknown'),
            'table_type': metadata.get('table_type', '数据表格'),
            'table_html': metadata.get('page_content', '') or getattr(actual_doc, 'page_content', ''),
            'document_name': metadata.get('document_name', '未知文档'),
            'page_number': metadata.get('page_number', 'N/A'),
            'score': score
        }
        
        print(f"\n🎯 表格结果构建测试:")
        print(f"  ID: {table_result['id']}")
        print(f"  类型: {table_result['table_type']}")
        print(f"  文档名称: {table_result['document_name']}")
        print(f"  页码: {table_result['page_number']}")
        print(f"  HTML长度: {len(table_result['table_html'])}")
        print(f"  分数: {table_result['score']}")
        
        return True
    else:
        print("❌ 提取的文档对象没有metadata属性")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 测试修复后的表格数据提取功能")
    print("=" * 60)
    
    success = test_extraction()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！表格数据提取功能已修复")
    else:
        print("❌ 测试失败！需要进一步调试")
    print("=" * 60)
