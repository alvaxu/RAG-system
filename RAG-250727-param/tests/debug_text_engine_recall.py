'''
程序说明：
## 1. 调试text_engine第一层召回返回0的问题
## 2. 测试不同的阈值设置
## 3. 分析分数分布情况
## 4. 验证搜索策略是否正常工作
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.text_engine import TextEngine
from v2.config.v2_config import TextEngineConfigV2
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_text_engine_recall():
    """测试text_engine的第一层召回"""
    
    print("=" * 60)
    print("🔍 开始调试text_engine第一层召回问题")
    print("=" * 60)
    
    try:
        # 1. 创建配置
        print("\n1️⃣ 创建配置...")
        text_config = TextEngineConfigV2()
        
        print(f"✅ 配置创建成功")
        print(f"   第一层阈值: {text_config.recall_strategy['layer1_vector_search']['similarity_threshold']}")
        
        # 2. 创建text_engine（不依赖vector_store）
        print("\n2️⃣ 创建text_engine...")
        text_engine = TextEngine(text_config, vector_store=None, skip_initial_load=True)
        print("✅ text_engine创建成功")
        
        # 3. 测试查询
        test_query = "中芯国际的产能利用率如何？"
        print(f"\n3️⃣ 测试查询: {test_query}")
        
        # 4. 测试不同的阈值
        test_thresholds = [0.05, 0.1, 0.15, 0.2, 0.3]
        
        for threshold in test_thresholds:
            print(f"\n🔍 测试阈值: {threshold}")
            
            # 临时修改阈值
            text_config.recall_strategy['layer1_vector_search']['similarity_threshold'] = threshold
            
            # 测试第一层召回
            try:
                # 直接调用第一层方法
                layer1_results = text_engine._vector_similarity_search(test_query, top_k=10)
                print(f"   阈值 {threshold}: 返回 {len(layer1_results)} 个结果")
                
                if layer1_results:
                    # 显示前3个结果的分数
                    for i, result in enumerate(layer1_results[:3]):
                        score = result.get('vector_score', 0)
                        print(f"   结果 {i+1}: 分数={score:.3f}, 策略={result.get('search_strategy', 'N/A')}")
                        
            except Exception as e:
                print(f"   阈值 {threshold}: 错误 - {e}")
        
        # 5. 测试分数计算方法
        print(f"\n4️⃣ 测试分数计算方法...")
        test_content = "中芯国际的产能利用率显著提升，持续推进工艺迭代升级"
        score = text_engine._calculate_content_relevance(test_query, test_content)
        print(f"   查询: {test_query}")
        print(f"   内容: {test_content}")
        print(f"   计算分数: {score:.3f}")
        
        # 6. 分析分数分布
        print(f"\n5️⃣ 分析分数分布...")
        sample_contents = [
            "中芯国际的产能利用率显著提升",
            "半导体制造工艺不断改进",
            "晶圆代工市场需求旺盛",
            "集成电路技术发展迅速",
            "芯片制造工艺升级"
        ]
        
        scores = []
        for content in sample_contents:
            score = text_engine._calculate_content_relevance(test_query, content)
            scores.append(score)
            print(f"   '{content}': {score:.3f}")
        
        if scores:
            print(f"   分数统计:")
            print(f"     最高分: {max(scores):.3f}")
            print(f"     最低分: {min(scores):.3f}")
            print(f"     平均分: {sum(scores)/len(scores):.3f}")
            print(f"     超过0.15的数量: {sum(1 for s in scores if s >= 0.15)}")
            print(f"     超过0.1的数量: {sum(1 for s in scores if s >= 0.1)}")
            print(f"     超过0.05的数量: {sum(1 for s in scores if s >= 0.05)}")
        
        print("\n" + "=" * 60)
        print("🎯 调试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_text_engine_recall()
