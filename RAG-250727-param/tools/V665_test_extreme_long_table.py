#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 测试极长表格的最终截断功能
## 2. 验证所有反馈信息的完整性
## 3. 测试边界情况处理

"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processing.enhanced_chunker import EnhancedSemanticChunker

def test_extreme_long_table():
    """测试极长表格处理"""
    print("🧪 开始测试极长表格处理...")
    print("=" * 60)
    
    # 创建分块器实例
    chunker = EnhancedSemanticChunker(chunk_size=1000, chunk_overlap=100)
    
    # 创建一个极长的表格内容（确保处理后仍超长）
    print("📊 创建极长表格内容...")
    
    # 表头
    table_header = """表格类型: 详细财务数据表
表格ID: table_extreme_financial_001
行数: 500
列数: 12
列标题（字段定义）: 年份,季度,月份,营业收入(万元),净利润(万元),毛利率(%),净利率(%),总资产(万元),净资产(万元),员工人数,研发投入(万元),市场份额(%)
数据记录:"""
    
    # 生成500行数据（确保处理后仍超长）
    data_rows = []
    for i in range(500):
        year = 2010 + (i // 12)
        quarter = ((i % 12) // 3) + 1
        month = (i % 12) + 1
        revenue = 1000 + i * 100
        profit = 100 + i * 10
        gross_margin = 25 + (i % 15)
        net_margin = 10 + (i % 8)
        total_assets = 5000 + i * 200
        net_assets = 2000 + i * 100
        employees = 100 + i * 5
        rd_investment = 200 + i * 20
        market_share = 5 + (i % 10)
        
        # 增加每行数据的长度，确保处理后仍超长
        additional_info = f"详细说明{i+1}: 这是一个非常详细的财务数据记录，包含了大量的业务信息和市场分析数据，用于支持决策制定和业务规划。"
        extra_details = f"补充信息{i+1}: 该记录还包含了市场趋势分析、竞争对手分析、风险评估、投资建议、战略规划建议、运营优化建议、成本控制建议、收入增长策略、市场份额扩张计划、技术创新方向等多个维度的深度分析内容。"
        
        row = f"  记录{i+1}: {year},{quarter},{month},{revenue},{profit},{gross_margin}%,{net_margin}%,{total_assets},{net_assets},{employees},{rd_investment},{market_share}% | {additional_info} | {extra_details}"
        data_rows.append(row)
    
    # 组合完整表格
    extreme_long_table = table_header + "\n" + "\n".join(data_rows)
    
    print(f"📋 表格信息:")
    print(f"   - 总长度: {len(extreme_long_table)} 字符")
    print(f"   - 数据行数: {len(data_rows)} 行")
    print(f"   - 最大分块长度: {chunker.max_chunk_length} 字符")
    print(f"   - 格式优化阈值: {chunker.max_chunk_length * 1.5} 字符")
    
    print("\n" + "=" * 60)
    print("🔧 开始处理极长表格...")
    print("=" * 60)
    
    # 处理表格
    result = chunker._validate_and_truncate_chunk(extreme_long_table, "表格")
    
    print("\n" + "=" * 60)
    print("📊 处理结果分析:")
    print("=" * 60)
    print(f"原始长度: {len(extreme_long_table)} 字符")
    print(f"处理后长度: {len(result)} 字符")
    print(f"压缩比例: {((len(extreme_long_table) - len(result)) / len(extreme_long_table) * 100):.1f}%")
    
    # 调试：显示处理后的结果内容（最后100个字符）
    print(f"\n🔍 处理后内容预览（最后100字符）:")
    print(f"'{result[-100:]}'")
    
    # 检查结果中是否包含各种标记
    checks = [
        ("表格数据行已截断处理", "行数截断标记"),
        ("表格内容已截断处理", "最终截断标记"),
        ("表格已进行智能截断处理", "处理信息标记")
    ]
    
    for check_text, check_name in checks:
        if check_text in result:
            print(f"✅ {check_name}正确添加")
        else:
            print(f"❌ {check_name}缺失")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    
    return result

if __name__ == "__main__":
    test_extreme_long_table()
