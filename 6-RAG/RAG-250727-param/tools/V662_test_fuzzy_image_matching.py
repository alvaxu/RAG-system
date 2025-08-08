"""
程序说明：

## 1. 测试模糊图片匹配功能
测试当用户输入完整图片标题时，系统是否能正确选择最匹配的图片

## 2. 验证词汇重叠度算法
确保算法能正确计算用户输入与图片标题的词汇重叠度
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_qa_system import load_enhanced_qa_system
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fuzzy_image_matching():
    """
    测试模糊图片匹配功能
    """
    print("=== 测试模糊图片匹配功能 ===")
    
    # 加载QA系统
    qa_system = load_enhanced_qa_system("central/vector_db")
    if not qa_system:
        print("❌ 加载QA系统失败")
        return
    
    print("✅ QA系统加载成功")
    
    # 测试用例
    test_cases = [
        {
            "question": "请显示图4：公司25Q1下游应用领域结构情况",
            "expected": "应该只返回一个图4，且标题包含'公司25Q1下游应用领域结构情况'"
        },
        {
            "question": "图4：中芯国际归母净利润情况概览",
            "expected": "应该只返回一个图4，且标题包含'中芯国际归母净利润情况概览'"
        },
        {
            "question": "显示图4",
            "expected": "应该返回所有图4（因为没有完整标题）"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i} ---")
        print(f"问题: {test_case['question']}")
        print(f"期望: {test_case['expected']}")
        
        try:
            # 调用QA系统
            result = qa_system.answer_question(test_case['question'])
            
            # 分析结果
            sources = result.get('sources', [])
            image_sources = [s for s in sources if s.get('type') == 'image']
            
            print(f"找到 {len(image_sources)} 个图片源")
            
            for j, img_source in enumerate(image_sources, 1):
                caption = img_source.get('caption', '')
                print(f"  图片{j}: {caption}")
            
            # 验证结果
            if '：' in test_case['question'] and len(image_sources) > 1:
                print("⚠️  警告: 用户输入了完整标题，但返回了多个图片")
            elif '：' in test_case['question'] and len(image_sources) == 1:
                print("✅ 成功: 用户输入了完整标题，只返回了一个图片")
            elif '：' not in test_case['question'] and len(image_sources) >= 1:
                print("✅ 成功: 用户只输入了图号，返回了相应的图片")
            else:
                print("❌ 失败: 没有找到相关图片")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")

def test_overlap_score():
    """
    测试词汇重叠度计算功能
    """
    print("\n=== 测试词汇重叠度计算功能 ===")
    
    # 加载QA系统
    qa_system = load_enhanced_qa_system("central/vector_db")
    if not qa_system:
        print("❌ 加载QA系统失败")
        return
    
    # 测试用例
    test_cases = [
        {
            "user_input": "图4：公司25Q1下游应用领域结构情况",
            "caption": ["图4：公司25Q1下游应用领域结构情况"],
            "expected_score": "高分数（完全匹配）"
        },
        {
            "user_input": "图4：公司25Q1下游应用领域结构情况",
            "caption": ["图4：中芯国际归母净利润情况概览"],
            "expected_score": "低分数（部分匹配）"
        },
        {
            "user_input": "图4：公司25Q1下游应用",
            "caption": ["图4：公司25Q1下游应用领域结构情况"],
            "expected_score": "中等分数（部分匹配）"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 重叠度测试 {i} ---")
        print(f"用户输入: {test_case['user_input']}")
        print(f"图片标题: {test_case['caption']}")
        print(f"期望分数: {test_case['expected_score']}")
        
        try:
            score = qa_system._calculate_overlap_score(test_case['user_input'], test_case['caption'])
            print(f"实际分数: {score}")
            
            if score > 0:
                print("✅ 成功: 计算出了重叠度分数")
            else:
                print("⚠️  警告: 没有找到重叠词汇")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("开始测试模糊图片匹配功能...")
    
    # 测试词汇重叠度计算
    test_overlap_score()
    
    # 测试模糊图片匹配
    test_fuzzy_image_matching()
    
    print("\n=== 测试完成 ===")
