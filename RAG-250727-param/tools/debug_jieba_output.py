#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
调试jieba分词的具体输出
'''

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from v2.core.image_engine import ImageEngine
from v2.config.v2_config import V2ConfigManager

def debug_jieba_output():
    """调试jieba分词的具体输出"""
    print("🔍 调试jieba分词的具体输出...")
    print("=" * 60)
    
    # 创建Image Engine实例
    config_manager = V2ConfigManager()
    image_config = config_manager.config.image_engine
    image_engine = ImageEngine(config=image_config, skip_initial_load=True)
    
    # 测试用例
    test_cases = [
        {
            'query': '中芯国际净利润图表',
            'text': '中芯国际2024年净利润表现良好'
        },
        {
            'query': '芯片制造良率数据',
            'text': '半导体芯片制造工艺'
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📊 测试用例 {i+1}:")
        print(f"  查询: {test_case['query']}")
        print(f"  目标文本: {test_case['text']}")
        
        # 提取查询关键词
        query_keywords = image_engine._extract_semantic_keywords_from_query(test_case['query'])
        print(f"  查询关键词: {query_keywords}")
        
        # 提取文本关键词
        text_keywords = image_engine._extract_semantic_keywords_from_text(test_case['text'], set())
        print(f"  文本关键词: {text_keywords}")
        
        # 计算Jaccard相似度
        query_words_set = set(query_keywords)
        text_words_set = set(text_keywords)
        
        intersection = query_words_set.intersection(text_words_set)
        union = query_words_set.union(text_words_set)
        
        if union:
            jaccard_score = len(intersection) / len(union)
            print(f"  Jaccard相似度: {jaccard_score:.3f}")
            print(f"  交集: {intersection}")
            print(f"  并集: {union}")
        else:
            print(f"  Jaccard相似度: 0.000")
        
        # 调用实际方法
        actual_score = image_engine._calculate_text_match_score(
            query_words_set, test_case['text'], 0.8
        )
        print(f"  实际方法返回分数: {actual_score:.3f}")

if __name__ == "__main__":
    debug_jieba_output()
