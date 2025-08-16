#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 专门调试向量搜索问题
## 2. 测试不同的过滤条件和搜索参数
## 3. 验证图片文档的向量搜索功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from v2.core.document_loader import DocumentLoader
from core.vector_store import VectorStoreManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_vector_search():
    """调试向量搜索功能"""
    print("🔍 开始调试向量搜索...")
    print("=" * 60)
    
    try:
        # 1. 加载向量数据库
        print("📚 加载向量数据库...")
        vector_store_manager = VectorStoreManager()
        vector_store = vector_store_manager.load_vector_store("central/vector_db")
        
        if not vector_store:
            print("❌ 向量数据库加载失败")
            return
        
        print(f"✅ 向量数据库加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
        
        # 2. 检查文档类型分布
        print("\n📊 检查文档类型分布...")
        type_counts = {}
        for doc_id, doc in vector_store.docstore._dict.items():
            chunk_type = doc.metadata.get('chunk_type', 'unknown')
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
        
        print("文档类型分布:")
        for doc_type, count in type_counts.items():
            print(f"  {doc_type}: {count}")
        
        # 3. 测试无过滤条件搜索
        print("\n🔍 测试无过滤条件搜索...")
        query = "图4：中芯国际归母净利润情况概览"
        
        try:
            raw_results = vector_store.similarity_search(query, k=20)
            print(f"✅ 无过滤条件搜索成功，返回 {len(raw_results)} 个结果")
            
            # 检查结果的类型分布
            result_types = {}
            for doc in raw_results:
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                result_types[chunk_type] = result_types.get(chunk_type, 0) + 1
            
            print("搜索结果类型分布:")
            for doc_type, count in result_types.items():
                print(f"  {doc_type}: {count}")
                
        except Exception as e:
            print(f"❌ 无过滤条件搜索失败: {e}")
        
        # 4. 测试带过滤条件搜索
        print("\n🔍 测试带过滤条件搜索...")
        
        # 测试不同的过滤条件
        filter_conditions = [
            {'chunk_type': 'image'},
            {'chunk_type': 'text'},
            {'chunk_type': 'table'},
            {'type': 'image'},  # 错误的字段名
            {'document_name': '【上海证券】中芯国际深度研究报告：晶圆制造龙头，领航国产芯片新征程'}
        ]
        
        for i, filter_cond in enumerate(filter_conditions, 1):
            try:
                print(f"\n  测试过滤条件 {i}: {filter_cond}")
                filtered_results = vector_store.similarity_search(query, k=20, filter=filter_cond)
                print(f"    ✅ 搜索成功，返回 {len(filtered_results)} 个结果")
                
                # 检查过滤后的结果类型
                if filtered_results:
                    first_doc = filtered_results[0]
                    print(f"    第一个结果类型: {first_doc.metadata.get('chunk_type', 'unknown')}")
                    print(f"    第一个结果文档名: {first_doc.metadata.get('document_name', 'unknown')}")
                
            except Exception as e:
                print(f"    ❌ 搜索失败: {e}")
        
        # 5. 检查图片文档的元数据
        print("\n🔍 检查图片文档的元数据...")
        image_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            if doc.metadata.get('chunk_type') == 'image':
                image_docs.append(doc)
        
        print(f"找到 {len(image_docs)} 个图片文档")
        
        if image_docs:
            # 显示前3个图片文档的元数据
            for i, doc in enumerate(image_docs[:3], 1):
                print(f"\n  图片文档 {i}:")
                print(f"    文档ID: {doc.metadata.get('image_id', 'unknown')}")
                print(f"    文档名: {doc.metadata.get('document_name', 'unknown')}")
                print(f"    页码: {doc.metadata.get('page_number', 'unknown')}")
                print(f"    图片标题: {doc.metadata.get('img_caption', [])}")
                print(f"    增强描述: {doc.metadata.get('enhanced_description', '')[:100]}...")
        
        # 6. 测试特定图片查询
        print("\n🔍 测试特定图片查询...")
        if image_docs:
            # 使用第一个图片文档的标题作为查询
            first_image_caption = image_docs[0].metadata.get('img_caption', [''])
            if first_image_caption:
                test_query = first_image_caption[0]
                print(f"测试查询: {test_query}")
                
                try:
                    # 无过滤条件
                    raw_results = vector_store.similarity_search(test_query, k=10)
                    print(f"  无过滤条件: {len(raw_results)} 个结果")
                    
                    # 图片过滤条件
                    filtered_results = vector_store.similarity_search(test_query, k=10, filter={'chunk_type': 'image'})
                    print(f"  图片过滤条件: {len(filtered_results)} 个结果")
                    
                except Exception as e:
                    print(f"  ❌ 测试查询失败: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 向量搜索调试完成！")
        
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_vector_search()
