#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 调试table_engine的返回格式问题
## 2. 验证策略1和策略2返回的processed_doc格式
## 3. 检查metadata传递是否正确
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.config.v2_config import V2ConfigManager
from v2.core.table_engine import TableEngine
from core.vector_store import VectorStoreManager

def test_table_engine_return_format():
    """测试table_engine的返回格式"""
    
    print("🔍 开始测试table_engine的返回格式")
    
    try:
        # 加载配置
        config_manager = V2ConfigManager()
        config = config_manager.get_engine_config('table_engine')
        
        if not config:
            print("❌ 无法加载table_engine配置")
            return
        
        print(f"✅ 成功加载配置: {type(config)}")
        
        # 加载向量数据库
        vector_store = VectorStoreManager()
        if not vector_store:
            print("❌ 无法加载向量数据库")
            return
        
        print(f"✅ 成功加载向量数据库: {type(vector_store)}")
        
        # 创建table_engine实例
        table_engine = TableEngine(config=config, vector_store=vector_store)
        print(f"✅ 成功创建TableEngine实例: {type(table_engine)}")
        
        # 测试查询
        test_query = "中芯国际"
        print(f"\n🔍 测试查询: {test_query}")
        
        # 直接调用第二层向量搜索
        print("\n📋 测试第二层向量搜索...")
        layer2_results = table_engine._vector_semantic_search(test_query, top_k=5)
        
        if not layer2_results:
            print("❌ 第二层向量搜索返回空结果")
            return
        
        print(f"✅ 第二层向量搜索成功，返回 {len(layer2_results)} 个结果")
        
        # 分析返回结果的格式
        print("\n📊 分析返回结果格式:")
        for i, result in enumerate(layer2_results):
            print(f"\n--- 结果 {i+1} ---")
            print(f"类型: {type(result)}")
            print(f"键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            if isinstance(result, dict):
                # 检查关键字段
                if 'doc' in result:
                    doc = result['doc']
                    print(f"doc类型: {type(doc)}")
                    if hasattr(doc, 'metadata'):
                        print(f"doc.metadata: {doc.metadata}")
                        print(f"document_name: {doc.metadata.get('document_name', '未找到')}")
                        print(f"page_number: {doc.metadata.get('page_number', '未找到')}")
                    if hasattr(doc, 'page_content'):
                        print(f"page_content长度: {len(doc.page_content)}")
                        print(f"page_content预览: {doc.page_content[:100]}...")
                
                if 'content' in result:
                    print(f"content长度: {len(result['content'])}")
                
                if 'metadata' in result:
                    print(f"metadata: {result['metadata']}")
                    print(f"metadata.document_name: {result['metadata'].get('document_name', '未找到')}")
                    print(f"metadata.page_number: {result['metadata'].get('page_number', '未找到')}")
                
                if 'score' in result:
                    print(f"score: {result['score']}")
        
        # 测试process_query方法
        print("\n📋 测试process_query方法...")
        query_result = table_engine.process_query(test_query)
        
        if not query_result.success:
            print(f"❌ process_query失败: {query_result.error_message}")
            return
        
        print(f"✅ process_query成功，返回 {len(query_result.results)} 个结果")
        
        # 分析最终结果的格式
        print("\n📊 分析最终结果格式:")
        for i, result in enumerate(query_result.results[:3]):  # 只显示前3个
            print(f"\n--- 最终结果 {i+1} ---")
            print(f"类型: {type(result)}")
            print(f"键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            if isinstance(result, dict):
                # 检查关键字段
                if 'document_name' in result:
                    print(f"document_name: {result['document_name']}")
                if 'page_number' in result:
                    print(f"page_number: {result['page_number']}")
                if 'content' in result:
                    print(f"content长度: {len(result['content'])}")
                if 'metadata' in result:
                    print(f"metadata: {result['metadata']}")
        
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_table_engine_return_format()
