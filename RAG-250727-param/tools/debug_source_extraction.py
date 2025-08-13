#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试来源提取问题的脚本
用于深入分析 _extract_sources_from_result 函数中的文档结构处理
"""

import sys
import os
import json
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.config.v2_config import V2ConfigManager
from v2.core.hybrid_engine import HybridEngine
from v2.core.base_engine import QueryType

def debug_document_structure():
    """调试文档结构"""
    print("🔍 开始调试文档结构...")
    
    try:
        # 初始化配置管理器
        config_manager = V2ConfigManager()
        v2_config = config_manager.config
        
        # 初始化混合引擎
        hybrid_engine = HybridEngine(v2_config.hybrid_engine)
        
        # 执行一个混合查询
        query = "中芯国际的产能利用率如何？"
        print(f"📝 执行查询: {query}")
        
        start_time = time.time()
        result = hybrid_engine.process_query(
            query,
            query_type=QueryType.HYBRID,
            max_results=5
        )
        processing_time = time.time() - start_time
        
        print(f"⏱️  查询耗时: {processing_time:.2f}秒")
        print(f"✅ 查询成功: {result.success}")
        print(f"📊 结果数量: {len(result.results) if result.results else 0}")
        
        if result.success and result.results:
            print("\n🔍 分析每个结果的结构:")
            for i, doc in enumerate(result.results):
                print(f"\n--- 结果 {i+1} ---")
                print(f"类型: {type(doc)}")
                
                if isinstance(doc, dict):
                    print(f"字典键: {list(doc.keys())}")
                    
                    # 检查是否是 dict_keys(['doc_id', 'doc', 'score', 'match_type']) 结构
                    if set(doc.keys()) == {'doc_id', 'doc', 'score', 'match_type'}:
                        print("🎯 发现目标结构: dict_keys(['doc_id', 'doc', 'score', 'match_type'])")
                        
                        # 检查 doc 字段
                        if 'doc' in doc and isinstance(doc['doc'], dict):
                            print("✅ doc 字段存在且是字典")
                            actual_doc = doc['doc']
                            print(f"   actual_doc 类型: {type(actual_doc)}")
                            print(f"   actual_doc 键: {list(actual_doc.keys()) if isinstance(actual_doc, dict) else 'N/A'}")
                            
                            # 检查关键字段
                            chunk_type = actual_doc.get('chunk_type', 'N/A')
                            document_name = actual_doc.get('document_name', 'N/A')
                            page_number = actual_doc.get('page_number', 'N/A')
                            
                            print(f"   chunk_type: {chunk_type}")
                            print(f"   document_name: {document_name}")
                            print(f"   page_number: {page_number}")
                            
                            # 检查是否有内容字段
                            if 'page_content' in actual_doc:
                                print(f"   page_content 存在，长度: {len(actual_doc['page_content'])}")
                            elif 'content' in actual_doc:
                                print(f"   content 存在，长度: {len(actual_doc['content'])}")
                            else:
                                print("   ❌ 没有找到内容字段")
                        else:
                            print("❌ doc 字段不存在或不是字典")
                            print(f"   doc 字段值: {doc.get('doc')}")
                            print(f"   doc 字段类型: {type(doc.get('doc'))}")
                    else:
                        print("📋 其他字典结构")
                        # 显示前几个键值对
                        for key, value in list(doc.items())[:3]:
                            if isinstance(value, str) and len(value) > 100:
                                print(f"   {key}: {value[:100]}...")
                            else:
                                print(f"   {key}: {value}")
                
                elif hasattr(doc, 'metadata'):
                    print("📄 Document 对象")
                    metadata = doc.metadata
                    print(f"   metadata 键: {list(metadata.keys())}")
                    print(f"   chunk_type: {metadata.get('chunk_type', 'N/A')}")
                    print(f"   document_name: {metadata.get('document_name', 'N/A')}")
                    print(f"   page_number: {metadata.get('page_number', 'N/A')}")
                
                else:
                    print("❓ 未知对象类型")
                    print(f"   属性: {dir(doc)}")
        
        # 检查是否有 LLM 答案
        if hasattr(result, 'metadata') and result.metadata:
            print(f"\n🤖 LLM 答案元数据: {list(result.metadata.keys())}")
            if 'llm_answer' in result.metadata:
                llm_answer = result.metadata['llm_answer']
                print(f"   LLM 答案长度: {len(llm_answer) if llm_answer else 0}")
        
    except Exception as e:
        print(f"❌ 调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 开始调试来源提取问题...")
    print("=" * 60)
    
    debug_document_structure()
    
    print("\n" + "=" * 60)
    print("🏁 调试完成")

if __name__ == "__main__":
    main()
