'''
程序说明：
## 1. 测试文档名匹配逻辑的脚本
## 2. 验证智能文档名去重功能
## 3. 测试不同版本的文档名是否能正确识别为同一文档
'''

import os
import re
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.v3_main_processor import V3MainProcessor

def test_document_name_matching():
    """测试文档名匹配功能"""
    print("🧪 测试文档名匹配功能")
    print("=" * 50)
    
    # 创建处理器实例（不需要完整初始化）
    processor = V3MainProcessor.__new__(V3MainProcessor)
    
    # 测试用例
    test_cases = [
        # 测试用例：(文档名1, 文档名2, 期望结果)
        (
            "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改.pdf",
            "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改_1",
            True,  # 应该是同一文档
            "PDF文件 vs 带_1后缀的JSON文件"
        ),
        (
            "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改_1",
            "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改_2",
            True,  # 应该是同一文档的不同版本
            "带_1后缀 vs 带_2后缀"
        ),
        (
            "【华泰证券】中芯国际（688981）：上调港股目标价到63港币，看好DeepSeek推动代工需求强劲增长.pdf",
            "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改.pdf",
            False,  # 应该是不同文档
            "华泰证券报告 vs 光大证券报告"
        ),
        (
            "document_v1.pdf",
            "document_v2.pdf",
            True,  # 应该是同一文档的不同版本
            "v1版本 vs v2版本"
        ),
        (
            "report_2024.pdf",
            "report_2025.pdf",
            False,  # 应该是不同文档（年份不同）
            "2024年报告 vs 2025年报告"
        ),
    ]
    
    print("📋 测试用例:")
    for i, (name1, name2, expected, description) in enumerate(test_cases, 1):
        print(f"\n{i}. {description}")
        print(f"   文档1: {name1}")
        print(f"   文档2: {name2}")
        
        # 测试标准化功能
        normalized1 = processor._normalize_document_name(name1)
        normalized2 = processor._normalize_document_name(name2)
        print(f"   标准化1: {normalized1}")
        print(f"   标准化2: {normalized2}")
        
        # 测试匹配功能
        result = processor._is_same_document(name1, name2)
        print(f"   匹配结果: {result}")
        print(f"   期望结果: {expected}")
        
        if result == expected:
            print("   ✅ 测试通过")
        else:
            print("   ❌ 测试失败")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成")

if __name__ == "__main__":
    test_document_name_matching()
