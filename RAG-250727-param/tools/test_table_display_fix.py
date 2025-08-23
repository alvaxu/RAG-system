#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试表格显示修复是否成功
## 2. 模拟完整的表格结果数据结构
"""

import sys
import os
from pathlib import Path

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_mock_table_response():
    """创建模拟的表格响应数据"""
    mock_response = {
        'success': True,
        'question': '中芯国际的营业收入从2017年到2024年的变化趋势如何？',
        'query_type': 'table',
        'answer': '根据提供的上下文信息，中芯国际的营业收入从2023年到2024年的数据如下...',
        'table_results': [
            {
                'id': 'table_752140',
                'table_type': '数据表格',
                'table_title': '数据表格 table_752140',
                'table_html': '<table><tr><td></td><td>2023A</td><td>2024A</td><td>2025E</td><td>2026E</td><td>2027E</td></tr><tr><td>营业收入 (百万元)</td><td>45,250</td><td>57,796</td><td>68,204</td><td>79,507</td><td>91,110</td></tr><tr><td>增长比率 (%)</td><td>-8.61</td><td>27.72</td><td>18.01</td><td>16.57</td><td>14.59</td></tr></table>',
                'table_content': ' | 2023A | 2024A | 2025E | 2026E | 2027E\n营业收入 (百万元) | 45,250 | 57,796 | 68,204 | 79,507 | 91,110\n增长比率 (%) | -8.61 | 27.72 | 18.01 | 16.57 | 14.59',
                'document_name': '【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评',
                'page_number': 2,
                'score': 0.7267832199475612,
                'chunk_type': 'table',
                'table_headers': ['', '2023A', '2024A', '2025E', '2026E', '2027E'],
                'table_row_count': 6,
                'column_count': 6,
                'table_summary': '表头: 2023A | 2024A | 2025E | 2026E | 2027E'
            },
            {
                'id': 'table_883313',
                'table_type': '数据表格',
                'table_title': '单位：百万元',
                'table_html': '<table><tr><td>单位：百万元</td><td>2024A</td><td>2025E</td><td>2026E</td><td>2027E</td></tr><tr><td>营业收入</td><td>57796</td><td>70652</td><td>78639</td><td>87584</td></tr><tr><td>年增长率</td><td>27.7%</td><td>22.2%</td><td>11.3%</td><td>11.4%</td></tr></table>',
                'table_content': '单位：百万元 | 2024A | 2025E | 2026E | 2027E\n营业收入 | 57796 | 70652 | 78639 | 87584\n年增长率 | 27.7% | 22.2% | 11.3% | 11.4%',
                'document_name': '【上海证券】中芯国际深度研究报告：晶圆制造龙头，领航国产芯片新征程',
                'page_number': 1,
                'score': 0.6836512945031366,
                'chunk_type': 'table',
                'table_headers': ['单位：百万元', '2024A', '2025E', '2026E', '2027E'],
                'table_row_count': 6,
                'column_count': 5,
                'table_summary': '表头: 单位：百万元 | 2024A | 2025E | 2026E | 2027E'
            }
        ],
        'sources': [
            {
                'title': '【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评 - 第2页',
                'page_number': 2,
                'document_name': '【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评',
                'source_type': '表格',
                'score': 0.7267832199475612,
                'formatted_source': '中原证券产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评 - 数据表格 table_752140 - 第2页 (表格)'
            },
            {
                'title': '【上海证券】中芯国际深度研究报告：晶圆制造龙头，领航国产芯片新征程 - 第1页',
                'page_number': 1,
                'document_name': '【上海证券】中芯国际深度研究报告：晶圆制造龙头，领航国产芯片新征程',
                'source_type': '表格',
                'score': 0.6836512945031366,
                'formatted_source': '上海证券中芯国际深度研究报告：晶圆制造龙头，领航国产芯片新征程 - 单位：百万元 - 第1页 (表格)'
            }
        ]
    }
    
    return mock_response

def test_table_display_logic():
    """测试表格显示逻辑"""
    print("🔍 测试表格显示修复是否成功")
    print("=" * 60)
    
    try:
        # 创建模拟数据
        mock_response = create_mock_table_response()
        print("1. 创建模拟数据成功")
        print(f"   表格结果数量: {len(mock_response['table_results'])}")
        print(f"   来源信息数量: {len(mock_response['sources'])}")
        
        # 检查表格结果数据结构
        print("\n2. 检查表格结果数据结构...")
        for i, table_result in enumerate(mock_response['table_results']):
            print(f"   表格 {i+1}:")
            print(f"     ID: {table_result.get('id', 'N/A')}")
            print(f"     类型: {table_result.get('table_type', 'N/A')}")
            print(f"     文档名称: {table_result.get('document_name', 'N/A')}")
            print(f"     页码: {table_result.get('page_number', 'N/A')}")
            print(f"     分数: {table_result.get('score', 'N/A')}")
            print(f"     HTML内容长度: {len(table_result.get('table_html', ''))}")
            print(f"     文本内容长度: {len(table_result.get('table_content', ''))}")
        
        # 检查来源信息数据结构
        print("\n3. 检查来源信息数据结构...")
        for i, source in enumerate(mock_response['sources']):
            print(f"   来源 {i+1}:")
            print(f"     标题: {source.get('title', 'N/A')}")
            print(f"     文档名称: {source.get('document_name', 'N/A')}")
            print(f"     页码: {source.get('page_number', 'N/A')}")
            print(f"     类型: {source.get('source_type', 'N/A')}")
            print(f"     格式化来源: {source.get('formatted_source', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✅ 数据结构检查完成")
        
        # 模拟前端显示逻辑
        print("\n4. 模拟前端显示逻辑...")
        for i, table_result in enumerate(mock_response['table_results']):
            table_id = table_result.get('id', 'unknown')
            table_type = table_result.get('table_type', '数据表格')
            document_name = table_result.get('document_name', '未知文档')
            page_number = table_result.get('page_number', 'N/A')
            score = table_result.get('score', 0)
            
            print(f"   表格 {i+1}: {table_id}")
            print(f"     📄 {document_name}")
            if page_number and page_number != 'N/A':
                print(f"     📖 第{page_number}页")
            print(f"     ⭐ {score:.2f}")
            
            # 检查HTML内容
            if table_result.get('table_html') and table_result['table_html'].strip().startswith('<table'):
                print(f"     ✅ 有有效的HTML表格内容")
            else:
                print(f"     ⚠️ 没有有效的HTML表格内容，使用文本格式")
        
        print("\n" + "=" * 60)
        print("✅ 前端显示逻辑测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_table_display_logic()
