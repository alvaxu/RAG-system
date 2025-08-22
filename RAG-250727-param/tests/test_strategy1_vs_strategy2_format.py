#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 对比策略1和策略2的返回格式
## 2. 检查document_name和page_number字段差异
## 3. 找出导致web端显示问题的根本原因
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.config.v2_config import V2ConfigManager, TableEngineConfigV2
from v2.core.table_engine import TableEngine
from core.vector_store import VectorStoreManager

def test_strategy1_vs_strategy2():
    """对比策略1和策略2的返回格式"""
    
    print("🔍 开始对比策略1和策略2的返回格式")
    
    try:
        # 创建基本配置
        config = TableEngineConfigV2()
        
        # 加载向量数据库
        vector_store = VectorStoreManager()
        if not vector_store:
            print("❌ 无法加载向量数据库")
            return
        
        print(f"✅ 成功加载向量数据库: {type(vector_store)}")
        
        # 创建table_engine实例
        table_engine = TableEngine(config=config, vector_store=vector_store)
        print(f"✅ 成功创建TableEngine实例")
        
        # 测试查询
        test_query = "中芯国际"
        print(f"\n🔍 测试查询: {test_query}")
        
        # 临时修改阈值以确保策略1能返回结果
        original_threshold = getattr(config.recall_strategy.get('layer2_vector_search', {}), 'similarity_threshold', 0.15)
        print(f"原始阈值: {original_threshold}")
        
        # 降低阈值确保策略1有结果
        config.recall_strategy['layer2_vector_search']['similarity_threshold'] = 0.05
        
        # 直接调用第二层向量搜索，看策略1是否有结果
        print("\n📋 调用第二层向量搜索...")
        layer2_results = table_engine._vector_semantic_search(test_query, top_k=3)
        
        if not layer2_results:
            print("❌ 策略1+策略2都没有返回结果")
            # 恢复原始阈值
            config.recall_strategy['layer2_vector_search']['similarity_threshold'] = original_threshold
            return
        
        print(f"✅ 向量搜索成功，返回 {len(layer2_results)} 个结果")
        
        # 分析每个结果的格式和内容
        for i, result in enumerate(layer2_results):
            print(f"\n--- 结果 {i+1} ---")
            print(f"类型: {type(result)}")
            
            if isinstance(result, dict):
                print(f"所有键: {list(result.keys())}")
                
                # 检查关键字段
                print(f"score: {result.get('score', 'N/A')}")
                print(f"source: {result.get('source', 'N/A')}")
                print(f"layer: {result.get('layer', 'N/A')}")
                print(f"search_method: {result.get('search_method', 'N/A')}")
                
                # 检查doc对象
                if 'doc' in result:
                    doc = result['doc']
                    print(f"doc类型: {type(doc)}")
                    
                    if hasattr(doc, 'metadata'):
                        metadata = doc.metadata
                        print(f"doc.metadata类型: {type(metadata)}")
                        print(f"doc.metadata.document_name: '{metadata.get('document_name', '未找到')}'")
                        print(f"doc.metadata.page_number: {metadata.get('page_number', '未找到')}")
                        print(f"doc.metadata.chunk_type: '{metadata.get('chunk_type', '未找到')}'")
                        print(f"doc.metadata.table_id: '{metadata.get('table_id', '未找到')}'")
                    else:
                        print("❌ doc对象没有metadata属性")
                    
                    if hasattr(doc, 'page_content'):
                        print(f"doc.page_content长度: {len(doc.page_content)}")
                        print(f"doc.page_content预览: {doc.page_content[:100]}...")
                    else:
                        print("❌ doc对象没有page_content属性")
                else:
                    print("❌ 结果没有doc字段")
                
                # 检查顶层content和metadata字段
                if 'content' in result:
                    print(f"result['content']长度: {len(result['content'])}")
                    print(f"result['content']预览: {result['content'][:100]}...")
                else:
                    print("❌ 结果没有content字段")
                
                if 'metadata' in result:
                    metadata = result['metadata']
                    print(f"result['metadata']类型: {type(metadata)}")
                    print(f"result['metadata'].document_name: '{metadata.get('document_name', '未找到')}'")
                    print(f"result['metadata'].page_number: {metadata.get('page_number', '未找到')}")
                else:
                    print("❌ 结果没有metadata字段")
        
        # 恢复原始阈值
        config.recall_strategy['layer2_vector_search']['similarity_threshold'] = original_threshold
        
        print(f"\n✅ 对比测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strategy1_vs_strategy2()
