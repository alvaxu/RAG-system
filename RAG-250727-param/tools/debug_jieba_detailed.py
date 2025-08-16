#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
详细调试jieba分词的每个步骤
'''

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def debug_jieba_detailed():
    """详细调试jieba分词的每个步骤"""
    print("🔍 详细调试jieba分词的每个步骤...")
    print("=" * 60)
    
    try:
        import jieba
        import jieba.analyse
        
        # 添加领域专业词汇
        domain_words = [
            '中芯国际', 'SMIC', '晶圆代工', '半导体制造', '集成电路', 'IC', '微处理器',
            '良率', 'yield', '制程', '工艺', '封装', '测试', '晶圆', '硅片', '基板'
        ]
        for word in domain_words:
            jieba.add_word(word)
        
        # 测试文本
        text = "中芯国际2024年净利润表现良好"
        query = "中芯国际净利润图表"
        
        print(f"测试文本: {text}")
        print(f"查询文本: {query}")
        
        print("\n📊 详细分词过程:")
        
        # 1. 基本分词
        print("\n1. 基本分词 (jieba.lcut):")
        basic_words = jieba.lcut(text, cut_all=False)
        print(f"   结果: {basic_words}")
        
        # 2. TF-IDF关键词提取
        print("\n2. TF-IDF关键词提取 (jieba.analyse.extract_tags):")
        try:
            tfidf_keywords = jieba.analyse.extract_tags(text, topK=15, allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'an'))
            print(f"   结果: {tfidf_keywords}")
        except Exception as e:
            print(f"   失败: {e}")
        
        # 3. TextRank关键词提取
        print("\n3. TextRank关键词提取 (jieba.analyse.textrank):")
        try:
            textrank_keywords = jieba.analyse.textrank(text, topK=15, allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'an'))
            print(f"   结果: {textrank_keywords}")
        except Exception as e:
            print(f"   失败: {e}")
        
        # 4. 正则表达式提取
        print("\n4. 正则表达式提取:")
        import re
        regex_words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        print(f"   结果: {regex_words}")
        
        # 5. 检查"中芯国际"是否被正确识别
        print("\n5. 检查'中芯国际'识别:")
        if '中芯国际' in basic_words:
            print("   ✅ 在基本分词中被识别")
        else:
            print("   ❌ 在基本分词中未被识别")
        
        # 6. 手动测试添加词汇
        print("\n6. 手动测试添加词汇:")
        test_text = "中芯国际2024年净利润表现良好"
        print(f"   测试文本: {test_text}")
        
        # 重新添加词汇
        jieba.add_word('中芯国际')
        jieba.add_word('净利润')
        
        # 再次分词
        test_words = jieba.lcut(test_text, cut_all=False)
        print(f"   重新分词结果: {test_words}")
        
        if '中芯国际' in test_words:
            print("   ✅ '中芯国际'现在被正确识别")
        else:
            print("   ❌ '中芯国际'仍然未被识别")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_jieba_detailed()
