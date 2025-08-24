'''
程序说明：
## 1. 调试实际数据结构问题
## 2. 分析为什么result.results中的doc是空字典{}
## 3. 找出数据流断裂点
'''

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
from v2.api.v2_routes import _extract_actual_doc_and_score

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_document_structure(doc, level=0):
    """递归分析文档结构"""
    indent = "  " * level
    
    if doc is None:
        print(f"{indent}❌ 文档为None")
        return
    
    print(f"{indent}📄 文档类型: {type(doc)}")
    
    if isinstance(doc, dict):
        print(f"{indent}📋 字典内容:")
        for key, value in doc.items():
            print(f"{indent}   {key}: {type(value)} = {value}")
            
            # 递归分析嵌套结构
            if isinstance(value, (dict, list)) and level < 3:
                analyze_document_structure(value, level + 1)
                
    elif hasattr(doc, '__dict__'):
        print(f"{indent}🔧 对象属性:")
        for attr_name, attr_value in doc.__dict__.items():
            print(f"{indent}   {attr_name}: {type(attr_value)} = {attr_value}")
            
            # 递归分析嵌套结构
            if isinstance(attr_value, (dict, list)) and level < 3:
                analyze_document_structure(attr_value, level + 1)
                
    elif hasattr(doc, 'metadata'):
        print(f"{indent}📊 元数据: {doc.metadata}")
        if hasattr(doc, 'page_content'):
            print(f"{indent}📝 页面内容: {doc.page_content[:100]}...")
    else:
        print(f"{indent}❓ 未知结构: {doc}")

def test_empty_dict_case():
    """测试空字典的情况"""
    print("🧪 测试空字典情况...")
    
    # 模拟空字典
    empty_doc = {}
    
    print(f"📄 输入: {empty_doc}")
    print(f"📄 类型: {type(empty_doc)}")
    
    # 测试提取
    actual_doc, score = _extract_actual_doc_and_score(empty_doc)
    
    print(f"🔍 提取结果:")
    print(f"   实际文档: {actual_doc}")
    print(f"   分数: {score}")
    
    if actual_doc is None:
        print("✅ 空字典正确处理，返回None")
    else:
        print("❌ 空字典处理错误")

def test_nested_structure():
    """测试嵌套结构"""
    print("\n🧪 测试嵌套结构...")
    
    # 模拟复杂的嵌套结构
    nested_doc = {
        'doc': {
            'doc': {
                'metadata': {
                    'chunk_type': 'text',
                    'document_name': '测试文档.pdf'
                },
                'page_content': '测试内容'
            }
        },
        'score': 0.95
    }
    
    print(f"📄 输入嵌套结构:")
    analyze_document_structure(nested_doc)
    
    # 测试提取
    actual_doc, score = _extract_actual_doc_and_score(nested_doc)
    
    print(f"\n🔍 提取结果:")
    print(f"   实际文档: {actual_doc}")
    print(f"   分数: {score}")
    
    if actual_doc is not None:
        print("✅ 嵌套结构提取成功")
        print(f"   元数据: {actual_doc.metadata}")
    else:
        print("❌ 嵌套结构提取失败")

def test_real_hybrid_engine_structure():
    """测试真实的混合引擎结构"""
    print("\n🧪 测试真实混合引擎结构...")
    
    try:
        from v2.core.base_engine import QueryResult, QueryType
        from langchain_core.documents.base import Document
        
        # 创建真实的QueryResult结构
        mock_docs = [
            {
                'doc': Document(
                    page_content="测试内容",
                    metadata={
                        'chunk_type': 'text',
                        'document_name': '测试文档.pdf',
                        'page_number': 1
                    }
                ),
                'score': 0.95
            },
            {
                'doc': Document(
                    page_content="表格内容",
                    metadata={
                        'chunk_type': 'table',
                        'document_name': '测试表格.pdf',
                        'page_number': 2,
                        'table_id': 'table_001'
                    }
                ),
                'score': 0.88
            }
        ]
        
        query_result = QueryResult(
            success=True,
            query="测试查询",
            query_type=QueryType.TEXT,
            results=mock_docs,
            total_count=len(mock_docs),
            processing_time=0.5,
            engine_name="TestEngine",
            metadata={}
        )
        
        print(f"✅ QueryResult创建成功")
        print(f"   结果数量: {query_result.total_count}")
        print(f"   结果类型: {type(query_result.results)}")
        
        # 分析每个结果
        for i, doc in enumerate(query_result.results):
            print(f"\n🔍 分析结果 {i}:")
            analyze_document_structure(doc)
            
            # 测试提取
            actual_doc, score = _extract_actual_doc_and_score(doc)
            
            if actual_doc is not None:
                print(f"   ✅ 提取成功: {type(actual_doc)}")
                print(f"   分数: {score}")
                print(f"   元数据: {actual_doc.metadata}")
            else:
                print(f"   ❌ 提取失败")
        
    except Exception as e:
        print(f"❌ 测试真实混合引擎结构时出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 开始调试实际数据结构问题...")
    
    # 测试1: 空字典情况
    test_empty_dict_case()
    
    # 测试2: 嵌套结构
    test_nested_structure()
    
    # 测试3: 真实混合引擎结构
    test_real_hybrid_engine_structure()
    
    print("\n🎉 调试测试完成!")

if __name__ == "__main__":
    main()
