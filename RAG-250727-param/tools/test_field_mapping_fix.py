'''
程序说明：
## 1. 测试字段映射修复效果
## 2. 验证_extract_actual_doc_and_score函数的增强处理
## 3. 模拟各种异常数据结构
'''

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
from v2.api.v2_routes import _extract_actual_doc_and_score

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_enhanced_extraction():
    """测试增强后的文档提取函数"""
    print("🧪 开始测试增强后的文档提取函数...")
    
    # 测试1: 空字典
    print("\n1. 测试空字典...")
    empty_doc = {}
    actual_doc, score = _extract_actual_doc_and_score(empty_doc)
    print(f"   结果: {actual_doc}, 分数: {score}")
    
    # 测试2: 包含空字典的列表
    print("\n2. 测试包含空字典的列表...")
    mixed_docs = [
        {'doc': 'valid_doc', 'score': 0.9},
        {},  # 空字典
        {'doc': 'another_valid_doc', 'score': 0.8},
        {}   # 另一个空字典
    ]
    
    for i, doc in enumerate(mixed_docs):
        print(f"   文档 {i}: {doc}")
        actual_doc, score = _extract_actual_doc_and_score(doc)
        if actual_doc is not None:
            print(f"   ✅ 提取成功: {actual_doc}")
        else:
            print(f"   ❌ 提取失败")
    
    # 测试3: 各种异常结构
    print("\n3. 测试各种异常结构...")
    
    test_cases = [
        None,                    # None
        {},                      # 空字典
        {'invalid': 'data'},     # 无效字典
        {'doc': None},           # doc为None
        {'doc': {}},             # doc为空字典
        {'doc': 'string'},       # doc为字符串
        {'doc': 123},            # doc为数字
        {'score': 0.9},          # 只有score
        {'metadata': {}},        # 只有metadata
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"   测试用例 {i}: {test_case}")
        actual_doc, score = _extract_actual_doc_and_score(test_case)
        if actual_doc is not None:
            print(f"   ✅ 提取成功: {type(actual_doc)}")
        else:
            print(f"   ❌ 提取失败")

def test_real_document_structures():
    """测试真实的文档结构"""
    print("\n🧪 测试真实的文档结构...")
    
    try:
        from langchain_core.documents.base import Document
        
        # 创建真实的Document对象
        valid_doc = Document(
            page_content="这是有效的内容",
            metadata={
                'chunk_type': 'text',
                'document_name': '测试文档.pdf',
                'page_number': 1
            }
        )
        
        # 测试各种包装结构
        test_structures = [
            # 标准Document对象
            valid_doc,
            
            # 标准嵌套结构
            {'doc': valid_doc, 'score': 0.95},
            
            # 多层嵌套
            {'doc': {'doc': valid_doc, 'score': 0.88}, 'score': 0.95},
            
            # 其他键名
            {'document': valid_doc, 'score': 0.92},
            {'result': valid_doc, 'score': 0.89},
            
            # 没有score
            {'doc': valid_doc},
            valid_doc,
        ]
        
        for i, structure in enumerate(test_structures):
            print(f"\n   测试结构 {i}: {type(structure)}")
            actual_doc, score = _extract_actual_doc_and_score(structure)
            
            if actual_doc is not None:
                print(f"   ✅ 提取成功: {type(actual_doc)}")
                print(f"   分数: {score}")
                print(f"   元数据: {actual_doc.metadata}")
            else:
                print(f"   ❌ 提取失败")
                
    except Exception as e:
        print(f"❌ 测试真实文档结构时出错: {e}")
        import traceback
        traceback.print_exc()

def test_edge_cases():
    """测试边界情况"""
    print("\n🧪 测试边界情况...")
    
    # 测试1: 循环引用
    print("\n1. 测试循环引用...")
    try:
        circular_dict = {}
        circular_dict['self'] = circular_dict
        
        actual_doc, score = _extract_actual_doc_and_score(circular_dict)
        print(f"   循环引用处理结果: {actual_doc}, 分数: {score}")
        
    except Exception as e:
        print(f"   循环引用处理异常: {e}")
    
    # 测试2: 超大字典
    print("\n2. 测试超大字典...")
    try:
        large_dict = {f'key_{i}': f'value_{i}' for i in range(1000)}
        large_dict['doc'] = 'large_doc'
        
        actual_doc, score = _extract_actual_doc_and_score(large_dict)
        print(f"   超大字典处理结果: {actual_doc}, 分数: {score}")
        
    except Exception as e:
        print(f"   超大字典处理异常: {e}")
    
    # 测试3: 特殊类型
    print("\n3. 测试特殊类型...")
    special_cases = [
        [],           # 空列表
        [1, 2, 3],   # 数字列表
        "string",     # 字符串
        123,          # 数字
        True,         # 布尔值
        False,        # 布尔值
        (),           # 空元组
        (1, 2, 3),   # 数字元组
    ]
    
    for case in special_cases:
        try:
            actual_doc, score = _extract_actual_doc_and_score(case)
            print(f"   特殊类型 {type(case)}: {actual_doc}, 分数: {score}")
        except Exception as e:
            print(f"   特殊类型 {type(case)} 处理异常: {e}")

def main():
    """主函数"""
    print("🚀 开始测试字段映射修复效果...")
    
    # 测试1: 增强后的提取函数
    test_enhanced_extraction()
    
    # 测试2: 真实文档结构
    test_real_document_structures()
    
    # 测试3: 边界情况
    test_edge_cases()
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main()
