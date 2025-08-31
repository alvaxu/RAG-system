'''
程序说明：
## 1. 测试文档名标准化功能的脚本
## 2. 验证从文件名到标准化文档名的转换
## 3. 测试不同版本后缀的文档名是否能正确标准化
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.v3_main_processor import V3MainProcessor

def test_document_name_normalization():
    """测试文档名标准化功能"""
    print("🧪 测试文档名标准化功能")
    print("=" * 50)
    
    # 创建处理器实例（不需要完整初始化）
    processor = V3MainProcessor.__new__(V3MainProcessor)
    
    # 测试用例
    test_cases = [
        # 测试用例：(原始文件名, 期望的标准化文档名)
        (
            "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改.pdf",
            "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改",
            "PDF文件，无版本后缀"
        ),
        (
            "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改_1.json",
            "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改",
            "JSON文件，带_1后缀"
        ),
        (
            "【华泰证券】中芯国际（688981）：上调港股目标价到63港币，看好DeepSeek推动代工需求强劲增长_2.md",
            "【华泰证券】中芯国际（688981）：上调港股目标价到63港币，看好DeepSeek推动代工需求强劲增长",
            "MD文件，带_2后缀"
        ),
        (
            "report_v1.pdf",
            "report",
            "带v1版本后缀"
        ),
        (
            "document_version2.docx",
            "document",
            "带version2版本后缀"
        ),
        (
            "annual_report_2024.pdf",
            "annual_report_2024",
            "带年份后缀（不应被标准化）"
        ),
        (
            "quarterly_report_2025_Q1.pdf",
            "quarterly_report_2025_Q1",
            "带年份和季度后缀（不应被标准化）"
        )
    ]
    
    print("📋 测试用例:")
    for i, (original_name, expected_normalized, description) in enumerate(test_cases, 1):
        print(f"  {i}. {description}")
        print(f"     原始文件名: {original_name}")
        print(f"     期望标准化: {expected_normalized}")
        print()
    
    print("🔍 测试结果:")
    print("-" * 50)
    
    all_passed = True
    for i, (original_name, expected_normalized, description) in enumerate(test_cases, 1):
        try:
            # 模拟文件名处理流程
            raw_doc_name = os.path.splitext(original_name)[0]
            normalized_name = processor._normalize_document_name(raw_doc_name)
            
            # 检查结果
            if normalized_name == expected_normalized:
                print(f"✅ 测试 {i} 通过: {description}")
                print(f"   原始: {raw_doc_name}")
                print(f"   标准化: {normalized_name}")
            else:
                print(f"❌ 测试 {i} 失败: {description}")
                print(f"   原始: {raw_doc_name}")
                print(f"   期望: {expected_normalized}")
                print(f"   实际: {normalized_name}")
                all_passed = False
            
            print()
            
        except Exception as e:
            print(f"❌ 测试 {i} 异常: {description}")
            print(f"   错误: {e}")
            all_passed = False
            print()
    
    # 总结
    print("📊 测试总结:")
    print("-" * 50)
    if all_passed:
        print("🎉 所有测试通过！文档名标准化功能工作正常。")
    else:
        print("⚠️  部分测试失败，需要检查文档名标准化逻辑。")
    
    return all_passed

def test_incremental_document_matching():
    """测试增量模式文档匹配功能"""
    print("\n🔄 测试增量模式文档匹配功能")
    print("=" * 50)
    
    # 创建处理器实例（不需要完整初始化）
    processor = V3MainProcessor.__new__(V3MainProcessor)
    
    # 模拟数据库中的现有文档名
    existing_docs = [
        "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改_1",
        "【华泰证券】中芯国际（688981）：上调港股目标价到63港币，看好DeepSeek推动代工需求强劲增长_2"
    ]
    
    # 测试新输入的文档
    new_files = [
        "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改.pdf",
        "【华泰证券】中芯国际（688981）：上调港股目标价到63港币，看好DeepSeek推动代工需求强劲增长.pdf",
        "【新文档】完全不同的内容.pdf"
    ]
    
    print("📚 现有数据库文档:")
    for doc in existing_docs:
        print(f"  - {doc}")
    
    print("\n📄 新输入文档:")
    for file_path in new_files:
        file_name = os.path.basename(file_path)
        print(f"  - {file_name}")
    
    print("\n🔍 文档匹配结果:")
    print("-" * 50)
    
    for file_path in new_files:
        file_name = os.path.basename(file_path)
        print(f"\n📄 检查文档: {file_name}")
        
        # 检查是否与现有文档重复
        is_new = True
        for existing_doc in existing_docs:
            if processor._is_same_document(file_name, existing_doc):
                print(f"  🔍 检测到重复文档: {file_name} <-> {existing_doc}")
                is_new = False
                break
        
        if is_new:
            print(f"  ✅ 新文档: {file_name}")
        else:
            print(f"  ⚠️  跳过重复文档: {file_name}")

if __name__ == "__main__":
    print("🚀 开始测试文档名标准化功能")
    print("=" * 60)
    
    # 测试1: 文档名标准化
    test1_passed = test_document_name_normalization()
    
    # 测试2: 增量模式文档匹配
    test2_passed = test_incremental_document_matching()
    
    # 最终总结
    print("\n" + "=" * 60)
    print("🏁 最终测试总结")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！文档名标准化和增量匹配功能工作正常。")
        print("\n✅ 修复效果:")
        print("  1. 文档名标准化：正确去除版本后缀")
        print("  2. 增量模式匹配：正确识别重复文档")
        print("  3. 避免重复处理：相同文档的不同版本被正确识别")
    else:
        print("⚠️  部分测试失败，需要进一步检查。")
    
    print("\n" + "=" * 60)
