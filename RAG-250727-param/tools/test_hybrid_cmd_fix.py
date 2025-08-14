#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试混合查询命令行修复的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V800_v2_main import V2RAGSystem

def test_hybrid_query():
    """
    测试混合查询功能
    """
    print("🚀 开始测试混合查询功能...")
    
    try:
        # 初始化系统
        print("📋 初始化V2 RAG系统...")
        system = V2RAGSystem()
        print("✅ 系统初始化成功")
        
        # 测试混合查询
        question = "请帮我分析一下这个图片中的表格数据"
        print(f"🔍 测试问题: {question}")
        
        # 执行混合查询
        result = system.ask_question(question, query_type='hybrid')
        
        print("📊 查询结果:")
        print(f"状态: {result.get('status', 'N/A')}")
        print(f"答案: {result.get('answer', 'N/A')}")
        print(f"来源: {result.get('sources', 'N/A')}")
        
        print("✅ 混合查询测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hybrid_query()
