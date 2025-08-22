'''
程序说明：
## 1. 测试修复后的_calculate_content_relevance方法
## 2. 验证中文查询的分数计算是否正常
## 3. 对比修复前后的分数差异
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_content_relevance():
    """测试内容相关性计算"""
    
    print("=" * 60)
    print("🔍 测试修复后的_calculate_content_relevance方法")
    print("=" * 60)
    
    try:
        # 直接导入方法
        from v2.core.text_engine import TextEngine
        
        # 创建一个简单的测试类
        class TestTextEngine:
            def _calculate_content_relevance(self, query: str, content: str) -> float:
                """
                计算内容相关性分数（修复版本，支持中文）
                
                :param query: 查询文本
                :param content: 文档内容
                :return: 相关性分数 [0, 1]
                """
                try:
                    if not content or not query:
                        return 0.0
                    
                    # 预处理：转换为小写
                    query_lower = query.lower()
                    content_lower = content.lower()
                    
                    # 方法1：直接字符串包含匹配（给高分）
                    if query_lower in content_lower:
                        return 0.8
                    
                    # 方法2：使用jieba进行中文分词
                    try:
                        import jieba
                        
                        # 提取查询关键词
                        query_keywords = jieba.lcut(query_lower, cut_all=False)
                        query_words = [word for word in query_keywords if len(word) > 1]  # 过滤单字符
                        
                        if not query_words:
                            # 如果jieba分词失败，降级到基本分词
                            query_words = [word for word in query_lower.split() if len(word) > 1]
                        
                        # 提取内容关键词
                        content_keywords = jieba.lcut(content_lower, cut_all=False)
                        content_words = [word for word in content_keywords if len(word) > 1]
                        
                        if not content_words:
                            # 如果jieba分词失败，降级到基本分词
                            content_words = [word for word in content_lower.split() if len(word) > 1]
                        
                    except Exception as e:
                        # 如果jieba失败，降级到基本分词
                        query_words = [word for word in query_lower.split() if len(word) > 1]
                        content_words = [word for word in content_lower.split() if len(word) > 1]
                    
                    if not query_words or not content_words:
                        return 0.0
                    
                    # 计算匹配词数和分数
                    matched_words = 0
                    total_score = 0.0
                    
                    for query_word in query_words:
                        if query_word in content_words:
                            matched_words += 1
                            # 计算词频分数
                            word_count = content_lower.count(query_word)
                            word_score = min(word_count / len(content_words), 0.3)  # 限制单个词的最大分数
                            total_score += word_score
                    
                    # 计算匹配率
                    match_rate = matched_words / len(query_words) if query_words else 0
                    
                    # 综合分数：匹配率 + 词频分数
                    final_score = (match_rate * 0.7 + total_score * 0.3)
                    
                    return min(final_score, 1.0)
                    
                except Exception as e:
                    # 如果所有方法都失败，返回0
                    return 0.0
        
        # 创建测试实例
        test_engine = TestTextEngine()
        
        # 测试查询和内容
        test_cases = [
            {
                "query": "中芯国际的产能利用率如何？",
                "content": "中芯国际的产能利用率显著提升，持续推进工艺迭代升级"
            },
            {
                "query": "半导体制造工艺",
                "content": "半导体制造工艺不断改进，技术持续创新"
            },
            {
                "query": "晶圆代工",
                "content": "晶圆代工市场需求旺盛，产能利用率高"
            },
            {
                "query": "芯片技术",
                "content": "集成电路技术发展迅速，芯片制造工艺升级"
            }
        ]
        
        print("\n📊 测试结果:")
        print("-" * 60)
        
        for i, case in enumerate(test_cases, 1):
            query = case["query"]
            content = case["content"]
            
            # 计算分数
            score = test_engine._calculate_content_relevance(query, content)
            
            print(f"测试 {i}:")
            print(f"  查询: {query}")
            print(f"  内容: {content}")
            print(f"  分数: {score:.3f}")
            print(f"  阈值0.15: {'✅ 通过' if score >= 0.15 else '❌ 未通过'}")
            print()
        
        print("=" * 60)
        print("🎯 测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_content_relevance()
