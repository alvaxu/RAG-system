#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
调试文本匹配分数计算问题
'''

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from v2.core.image_engine import ImageEngine
from v2.config.v2_config import V2ConfigManager

def debug_text_matching():
    """调试文本匹配分数计算"""
    print("🔍 调试文本匹配分数计算...")
    print("=" * 60)
    
    # 创建Image Engine实例
    config_manager = V2ConfigManager()
    image_config = config_manager.config.image_engine
    image_engine = ImageEngine(config=image_config, skip_initial_load=True)
    
    # 测试用例
    test_cases = [
        {
            'query_words': {'中芯国际', '净利润'},
            'text': '中芯国际2024年净利润表现良好',
            'base_score': 0.8,
            'expected_min': 0.4
        },
        {
            'query_words': {'芯片', '制造'},
            'text': '半导体芯片制造工艺',
            'base_score': 0.7,
            'expected_min': 0.35
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📊 测试用例 {i+1}:")
        print(f"  查询词: {test_case['query_words']}")
        print(f"  目标文本: {test_case['text']}")
        print(f"  基础分数: {test_case['base_score']}")
        
        # 分析查询词
        query_words = test_case['query_words']
        print(f"  查询词类型: {type(query_words)}")
        print(f"  查询词内容: {query_words}")
        
        # 分析目标文本
        text = test_case['text']
        print(f"  目标文本类型: {type(text)}")
        print(f"  目标文本内容: {text}")
        
        # 检查中文字符
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
        print(f"  包含中文字符: {has_chinese}")
        
        # 手动计算文本词集合
        text_lower = text.lower()
        if has_chinese:
            text_words = set(text_lower)
            print(f"  按字符分割的文本词: {text_words}")
        else:
            import re
            text_words = set(re.findall(r'\w+', text_lower))
            print(f"  按单词分割的文本词: {text_words}")
        
        # 计算重叠
        overlap = len(query_words & text_words)
        print(f"  重叠数量: {overlap}")
        print(f"  重叠内容: {query_words & text_words}")
        
        # 计算匹配比例
        total_query_words = len(query_words)
        match_ratio = overlap / total_query_words if total_query_words > 0 else 0
        print(f"  匹配比例: {match_ratio:.3f}")
        
        # 计算最终分数
        final_score = test_case['base_score'] * match_ratio
        print(f"  最终分数: {final_score:.3f}")
        
        # 调用实际方法
        actual_score = image_engine._calculate_text_match_score(
            query_words, text, test_case['base_score']
        )
        print(f"  实际方法返回分数: {actual_score:.3f}")
        
        if abs(actual_score - final_score) < 0.001:
            print("  ✅ 分数计算正确")
        else:
            print("  ❌ 分数计算错误")

if __name__ == "__main__":
    debug_text_matching()
