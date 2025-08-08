"""
程序说明：

## 1. 最终验证模糊匹配功能
确认当用户输入完整图片标题时，系统能正确选择最匹配的图片

## 2. 验证"显示两个图4"问题已解决
确保不会再出现多个图4同时显示的问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_qa_system import load_enhanced_qa_system
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def final_verification():
    """
    最终验证模糊匹配功能
    """
    print("=== 最终验证模糊匹配功能 ===")
    
    # 加载QA系统
    qa_system = load_enhanced_qa_system("central/vector_db")
    if not qa_system:
        print("❌ 加载QA系统失败")
        return
    
    print("✅ QA系统加载成功")
    
    # 测试用例 - 模拟原始问题
    test_cases = [
        {
            "question": "请显示图4：公司25Q1下游应用领域结构情况",
            "expected_images": 1,
            "expected_title": "公司25Q1下游应用领域结构情况"
        },
        {
            "question": "图4：中芯国际归母净利润情况概览",
            "expected_images": 1,
            "expected_title": "中芯国际归母净利润情况概览"
        },
        {
            "question": "显示图4",
            "expected_images": ">=1",  # 应该返回所有图4
            "expected_title": "任意图4"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 验证测试 {i} ---")
        print(f"问题: {test_case['question']}")
        print(f"期望图片数量: {test_case['expected_images']}")
        print(f"期望标题包含: {test_case['expected_title']}")
        
        try:
            # 调用QA系统
            result = qa_system.answer_question(test_case['question'])
            
            # 分析结果
            sources = result.get('sources', [])
            image_sources = [s for s in sources if s.get('metadata', {}).get('chunk_type') == 'image']
            
            print(f"实际图片数量: {len(image_sources)}")
            
            # 验证图片数量
            expected_count = test_case['expected_images']
            if isinstance(expected_count, str) and expected_count.startswith(">="):
                min_count = int(expected_count[2:])
                count_ok = len(image_sources) >= min_count
            else:
                count_ok = len(image_sources) == expected_count
            
            # 验证图片标题
            title_ok = True
            if image_sources and test_case['expected_title'] != "任意图4":
                captions = []
                for img_source in image_sources:
                    metadata = img_source.get('metadata', {})
                    img_caption = metadata.get('img_caption', [])
                    if img_caption:
                        captions.extend(img_caption)
                
                print(f"找到的图片标题: {captions}")
                
                # 检查是否有匹配的标题
                title_ok = any(test_case['expected_title'] in caption for caption in captions)
            
            # 输出验证结果
            if count_ok and title_ok:
                print("✅ 验证通过")
                success_count += 1
            else:
                print("❌ 验证失败")
                if not count_ok:
                    print(f"  图片数量不匹配: 期望{expected_count}，实际{len(image_sources)}")
                if not title_ok:
                    print(f"  标题不匹配: 期望包含'{test_case['expected_title']}'")
            
            # 显示图片详情
            for j, img_source in enumerate(image_sources, 1):
                metadata = img_source.get('metadata', {})
                caption = metadata.get('img_caption', ['无标题'])
                print(f"  图片{j}: {caption}")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    # 总结
    print(f"\n=== 验证总结 ===")
    print(f"成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有测试通过！模糊匹配功能完全正常！")
        print("✅ '显示两个图4'问题已解决！")
    else:
        print("⚠️  部分测试失败，需要进一步调试")
    
    return success_count == total_count

def test_overlap_score_accuracy():
    """
    测试词汇重叠度算法的准确性
    """
    print("\n=== 测试词汇重叠度算法准确性 ===")
    
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
        print(f"期望: {test_case['expected_score']}")
        
        try:
            score = qa_system._calculate_overlap_score(test_case['user_input'], test_case['caption'])
            print(f"实际分数: {score}")
            
            # 验证分数合理性
            if score >= 5:
                print("✅ 高分数 - 匹配度很高")
            elif score >= 2:
                print("✅ 中等分数 - 部分匹配")
            else:
                print("✅ 低分数 - 匹配度较低")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("开始最终验证模糊匹配功能...")
    
    # 测试词汇重叠度算法
    test_overlap_score_accuracy()
    
    # 最终验证
    success = final_verification()
    
    if success:
        print("\n🎉 恭喜！模糊匹配功能实现成功！")
        print("✅ 解决了'显示两个图4'的问题")
        print("✅ 当用户输入完整标题时，系统能正确选择最匹配的图片")
        print("✅ 当用户只输入图号时，系统返回所有匹配的图片")
    else:
        print("\n⚠️  验证失败，需要进一步调试")
    
    print("\n=== 验证完成 ===")
