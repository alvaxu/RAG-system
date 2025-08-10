#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 测试增强分块器的优化功能
## 2. 验证表格截断处理的反馈信息
## 3. 测试不同长度的表格内容处理

"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processing.enhanced_chunker import EnhancedSemanticChunker

def test_enhanced_chunker():
    """测试增强分块器的功能"""
    print("🧪 开始测试增强分块器...")
    print("=" * 60)
    
    # 创建分块器实例
    chunker = EnhancedSemanticChunker(chunk_size=1000, chunk_overlap=100)
    
    # 测试1：短表格（无需处理）
    print("\n📋 测试1：短表格（无需处理）")
    print("-" * 40)
    short_table = """
表格类型: 财务数据表
表格ID: table_001
行数: 5
列数: 4
列标题（字段定义）: 年份,营业收入,净利润,增长率
数据记录:
  记录1: 2020,1000,100,10%
  记录2: 2021,1100,120,20%
  记录3: 2022,1200,150,25%
  记录4: 2023,1300,180,20%
  记录5: 2024,1400,200,11%
"""
    
    result1 = chunker._validate_and_truncate_chunk(short_table, "表格")
    print(f"处理结果长度: {len(result1)}字符")
    
    # 测试2：中等长度表格（格式优化）
    print("\n📋 测试2：中等长度表格（格式优化）")
    print("-" * 40)
    medium_table = short_table * 3  # 重复3次，增加长度
    
    result2 = chunker._validate_and_truncate_chunk(medium_table, "表格")
    print(f"处理结果长度: {len(result2)}字符")
    
    # 测试3：超长表格（截断处理）
    print("\n📋 测试3：超长表格（截断处理）")
    print("-" * 40)
    long_table = short_table * 10  # 重复10次，大幅增加长度
    
    result3 = chunker._validate_and_truncate_chunk(long_table, "表格")
    print(f"处理结果长度: {len(result3)}字符")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    
    return result1, result2, result3

if __name__ == "__main__":
    test_enhanced_chunker()
