'''
程序说明：
## 1. 调试字段映射问题
## 2. 分析为什么_extract_actual_doc_and_score返回None
## 3. 验证数据结构的一致性
'''

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
from v2.api.v2_routes import _extract_actual_doc_and_score, _build_unified_image_result, _build_unified_table_result, _build_unified_text_result

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_document_extraction():
    """测试文档提取函数"""
    print("🧪 开始测试文档提取函数...")
    
    # 测试1: 标准Document对象
    print("\n1. 测试标准Document对象...")
    try:
        from langchain.schema import Document
        
        # 创建模拟的Document对象
        mock_doc = Document(
            page_content="这是测试内容",
            metadata={
                'chunk_type': 'text',
                'document_name': '测试文档.pdf',
                'page_number': 1,
                'chunk_index': 0
            }
        )
        
        # 测试提取
        actual_doc, score = _extract_actual_doc_and_score(mock_doc)
        
        if actual_doc is not None:
            print(f"✅ 标准Document对象提取成功")
            print(f"   实际文档类型: {type(actual_doc)}")
            print(f"   元数据: {actual_doc.metadata}")
            print(f"   分数: {score}")
        else:
            print(f"❌ 标准Document对象提取失败")
            
    except Exception as e:
        print(f"❌ 测试标准Document对象时出错: {e}")
    
    # 测试2: 嵌套结构
    print("\n2. 测试嵌套结构...")
    try:
        nested_doc = {
            'doc': mock_doc,
            'score': 0.95
        }
        
        actual_doc, score = _extract_actual_doc_and_score(nested_doc)
        
        if actual_doc is not None:
            print(f"✅ 嵌套结构提取成功")
            print(f"   实际文档类型: {type(actual_doc)}")
            print(f"   分数: {score}")
        else:
            print(f"❌ 嵌套结构提取失败")
            
    except Exception as e:
        print(f"❌ 测试嵌套结构时出错: {e}")
    
    # 测试3: 空对象
    print("\n3. 测试空对象...")
    try:
        actual_doc, score = _extract_actual_doc_and_score(None)
        
        if actual_doc is None:
            print(f"✅ 空对象处理正确，返回None")
        else:
            print(f"❌ 空对象处理错误，应该返回None")
            
    except Exception as e:
        print(f"❌ 测试空对象时出错: {e}")

def test_field_building():
    """测试字段构建函数"""
    print("\n🧪 开始测试字段构建函数...")
    
    try:
        from langchain.schema import Document
        
        # 测试图片字段构建
        print("\n1. 测试图片字段构建...")
        image_doc = Document(
            page_content="图片描述",
            metadata={
                'chunk_type': 'image',
                'document_name': '测试图片.pdf',
                'page_number': 5,
                'img_caption': ['测试图片标题'],
                'img_footnote': ['测试脚注'],
                'enhanced_description': '这是增强描述',
                'image_id': 'img_001',
                'image_path': '/path/to/image.jpg',
                'image_filename': 'test.jpg',
                'image_type': 'jpg',
                'extension': '.jpg'
            }
        )
        
        image_result = _build_unified_image_result(image_doc, 0.95)
        print(f"✅ 图片字段构建成功")
        print(f"   caption: {image_result['caption']}")
        print(f"   image_id: {image_result['image_id']}")
        print(f"   image_path: {image_result['image_path']}")
        
        # 测试表格字段构建
        print("\n2. 测试表格字段构建...")
        table_doc = Document(
            page_content="<table>...</table>",
            metadata={
                'chunk_type': 'table',
                'document_name': '测试表格.pdf',
                'page_number': 10,
                'table_id': 'table_001',
                'table_type': '数据表格',
                'table_title': '测试表格',
                'table_summary': '表格摘要',
                'table_headers': ['列1', '列2'],
                'table_row_count': 5,
                'table_column_count': 2,
                'processed_table_content': '处理后的内容'
            }
        )
        
        table_result = _build_unified_table_result(table_doc, 0.88)
        print(f"✅ 表格字段构建成功")
        print(f"   table_id: {table_result['id']}")
        print(f"   table_title: {table_result['table_title']}")
        print(f"   table_html: {table_result['table_html'][:50]}...")
        
        # 测试文本字段构建
        print("\n3. 测试文本字段构建...")
        text_doc = Document(
            page_content="这是测试文本内容，用于验证字段提取功能。",
            metadata={
                'chunk_type': 'text',
                'document_name': '测试文本.pdf',
                'page_number': 3,
                'chunk_index': 15
            }
        )
        
        text_result = _build_unified_text_result(text_doc, 0.92)
        print(f"✅ 文本字段构建成功")
        print(f"   content: {text_result['content'][:30]}...")
        print(f"   chunk_index: {text_result['chunk_index']}")
        
    except Exception as e:
        print(f"❌ 测试字段构建时出错: {e}")

def test_hybrid_engine_result_structure():
    """测试混合引擎返回结果的结构"""
    print("\n🧪 开始测试混合引擎结果结构...")
    
    try:
        # 模拟hybrid_engine返回的QueryResult结构
        from v2.core.base_engine import QueryResult, QueryType
        
        # 创建模拟的QueryResult
        mock_results = [
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
            }
        ]
        
        query_result = QueryResult(
            success=True,
            query="测试查询",
            query_type=QueryType.TEXT,
            results=mock_results,
            total_count=len(mock_results),
            processing_time=0.5,
            engine_name="TestEngine",
            metadata={}
        )
        
        print(f"✅ QueryResult创建成功")
        print(f"   结果数量: {query_result.total_count}")
        print(f"   结果类型: {type(query_result.results)}")
        print(f"   第一个结果: {query_result.results[0]}")
        
        # 测试从QueryResult中提取文档
        if hasattr(query_result, 'results') and query_result.results:
            print(f"\n🔍 测试从QueryResult提取文档...")
            
            for i, doc in enumerate(query_result.results):
                print(f"   文档 {i}: {type(doc)}")
                actual_doc, score = _extract_actual_doc_and_score(doc)
                
                if actual_doc is not None:
                    print(f"   ✅ 提取成功: {type(actual_doc)}")
                    print(f"   分数: {score}")
                else:
                    print(f"   ❌ 提取失败")
        
    except Exception as e:
        print(f"❌ 测试混合引擎结果结构时出错: {e}")

def main():
    """主函数"""
    print("🚀 开始调试字段映射问题...")
    
    # 测试1: 文档提取
    test_document_extraction()
    
    # 测试2: 字段构建
    test_field_building()
    
    # 测试3: 混合引擎结果结构
    test_hybrid_engine_result_structure()
    
    print("\n🎉 调试测试完成!")

if __name__ == "__main__":
    main()
