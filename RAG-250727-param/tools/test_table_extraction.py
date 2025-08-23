#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试表格数据提取是否修复
## 2. 模拟统一Pipeline的结果格式
"""

import sys
import os
from pathlib import Path

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模拟统一Pipeline的结果格式
def create_mock_table_result():
    """创建模拟的表格结果"""
    from types import SimpleNamespace
    
    # 模拟Document对象
    mock_doc = SimpleNamespace()
    mock_doc.metadata = {
        'document_name': '【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评',
        'page_number': 2,
        'chunk_type': 'table',
        'table_id': 'table_752140',
        'table_type': '数据表格',
        'table_title': '数据表格 table_752140',
        'table_summary': '表头: 2023A | 2024A | 2025E | 2026E | 2027E',
        'table_headers': ['', '2023A', '2024A', '2025E', '2026E', '2027E'],
        'processed_table_content': ' | 2023A | 2024A | 2025E | 2026E | 2027E\n营业收入 (百万元) | 45,250 | 57,796 | 68,204 | 79,507 | 91,110',
        'table_row_count': 6,
        'table_column_count': 6,
        'page_content': '<table><tr><td></td><td>2023A</td><td>2024A</td><td>2025E</td><td>2026E</td><td>2027E</td></tr><tr><td>营业收入 (百万元)</td><td>45,250</td><td>57,796</td><td>68,204</td><td>79,507</td><td>91,110</td></tr></table>'
    }
    mock_doc.score = 0.7267832199475612
    
    # 模拟统一Pipeline格式
    mock_result = {
        'content': '',
        'metadata': {},
        'original_result': {
            'doc': {
                'doc': mock_doc,
                'page_content': ' | 2023A | 2024A | 2025E | 2026E | 2027E\n营业收入 (百万元) | 45,250 | 57,796 | 68,204 | 79,507 | 91,110',
                'score': 0.7267832199475612
            }
        }
    }
    
    return mock_result

def test_extract_actual_doc_and_score():
    """测试_extract_actual_doc_and_score函数"""
    print("🔍 测试表格数据提取是否修复")
    print("=" * 60)
    
    try:
        # 导入修复后的函数
        sys.path.append('v2/api')
        from v2_routes import _extract_actual_doc_and_score
        
        # 创建模拟数据
        mock_result = create_mock_table_result()
        print("1. 创建模拟数据成功")
        print(f"   模拟数据结构: {type(mock_result)}")
        print(f"   包含字段: {list(mock_result.keys())}")
        
        # 测试提取
        print("\n2. 测试数据提取...")
        actual_doc, score = _extract_actual_doc_and_score(mock_result)
        
        if actual_doc:
            print("   ✅ 成功提取文档对象")
            print(f"   文档类型: {type(actual_doc)}")
            print(f"   分数: {score}")
            
            # 检查元数据
            if hasattr(actual_doc, 'metadata') and actual_doc.metadata:
                metadata = actual_doc.metadata
                print(f"   ✅ 成功提取元数据")
                print(f"   文档名称: {metadata.get('document_name', 'N/A')}")
                print(f"   页码: {metadata.get('page_number', 'N/A')}")
                print(f"   表格ID: {metadata.get('table_id', 'N/A')}")
                print(f"   表格类型: {metadata.get('table_type', 'N/A')}")
                print(f"   HTML内容长度: {len(metadata.get('page_content', ''))}")
                print(f"   处理内容长度: {len(metadata.get('processed_table_content', ''))}")
            else:
                print("   ❌ 元数据提取失败")
        else:
            print("   ❌ 文档对象提取失败")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extract_actual_doc_and_score()
