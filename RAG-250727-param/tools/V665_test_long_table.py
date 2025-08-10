#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 测试超长表格的截断处理
## 2. 验证反馈信息的完整性
## 3. 模拟真实业务场景

"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processing.enhanced_chunker import EnhancedSemanticChunker

def test_long_table_processing():
    """测试超长表格处理"""
    print("🧪 开始测试超长表格处理...")
    print("=" * 60)
    
    # 创建分块器实例
    chunker = EnhancedSemanticChunker(chunk_size=1000, chunk_overlap=100)
    
    # 创建一个超长的表格内容（模拟真实业务场景）
    print("📊 创建超长表格内容...")
    
    # 表头
    table_header = """表格类型: 财务数据表
表格ID: table_financial_001
行数: 100
列数: 8
列标题（字段定义）: 年份,季度,营业收入(万元),净利润(万元),毛利率(%),净利率(%),总资产(万元),净资产(万元)
数据记录:"""
    
    # 生成100行数据
    data_rows = []
    for i in range(100):
        year = 2015 + (i // 4)
        quarter = (i % 4) + 1
        revenue = 1000 + i * 50
        profit = 100 + i * 5
        gross_margin = 25 + (i % 10)
        net_margin = 10 + (i % 5)
        total_assets = 5000 + i * 100
        net_assets = 2000 + i * 50
        
        row = f"  记录{i+1}: {year},{quarter},{revenue},{profit},{gross_margin}%,{net_margin}%,{total_assets},{net_assets}"
        data_rows.append(row)
    
    # 组合完整表格
    long_table = table_header + "\n" + "\n".join(data_rows)
    
    print(f"📋 表格信息:")
    print(f"   - 总长度: {len(long_table)} 字符")
    print(f"   - 数据行数: {len(data_rows)} 行")
    print(f"   - 最大分块长度: {chunker.max_chunk_length} 字符")
    print(f"   - 格式优化阈值: {chunker.max_chunk_length * 1.5} 字符")
    
    print("\n" + "=" * 60)
    print("🔧 开始处理超长表格...")
    print("=" * 60)
    
    # 处理表格
    result = chunker._validate_and_truncate_chunk(long_table, "表格")
    
    print("\n" + "=" * 60)
    print("📊 处理结果分析:")
    print("=" * 60)
    print(f"原始长度: {len(long_table)} 字符")
    print(f"处理后长度: {len(result)} 字符")
    print(f"压缩比例: {((len(long_table) - len(result)) / len(long_table) * 100):.1f}%")
    
    # 检查结果中是否包含截断标记
    if "中间" in result and "行数据省略" in result:
        print("✅ 截断标记正确添加")
    else:
        print("❌ 截断标记缺失")
    
    if "表格内容已截断处理" in result:
        print("✅ 最终截断标记正确添加")
    else:
        print("❌ 最终截断标记缺失")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    
    return result

if __name__ == "__main__":
    test_long_table_processing()
