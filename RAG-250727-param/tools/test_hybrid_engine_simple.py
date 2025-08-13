#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试混合引擎的脚本
用于诊断混合引擎的问题
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.config.v2_config import V2ConfigManager
from v2.core.hybrid_engine import HybridEngine
from v2.core.base_engine import QueryType

def test_hybrid_engine():
    """测试混合引擎"""
    print("🔍 开始测试混合引擎...")
    
    try:
        # 初始化配置管理器
        config_manager = V2ConfigManager()
        v2_config = config_manager.config
        
        print(f"✅ 配置管理器初始化成功")
        print(f"   混合引擎配置: {type(v2_config.hybrid_engine)}")
        
        # 检查混合引擎配置
        if hasattr(v2_config.hybrid_engine, 'optimization_pipeline'):
            pipeline_config = v2_config.hybrid_engine.optimization_pipeline
            print(f"   优化管道配置: {type(pipeline_config)}")
            print(f"   - 重排序: {pipeline_config.enable_reranking}")
            print(f"   - LLM生成: {pipeline_config.enable_llm_generation}")
            print(f"   - 智能过滤: {pipeline_config.enable_smart_filtering}")
            print(f"   - 源过滤: {pipeline_config.enable_source_filtering}")
        else:
            print("   ❌ 没有找到优化管道配置")
        
        # 初始化混合引擎
        print("\n🔧 初始化混合引擎...")
        hybrid_engine = HybridEngine(v2_config.hybrid_engine)
        print(f"✅ 混合引擎初始化成功")
        
        # 检查引擎状态
        print(f"\n📊 引擎状态:")
        print(f"   - 图片引擎: {'✅' if hybrid_engine.image_engine else '❌'}")
        print(f"   - 文本引擎: {'✅' if hybrid_engine.text_engine else '❌'}")
        print(f"   - 表格引擎: {'✅' if hybrid_engine.table_engine else '❌'}")
        print(f"   - 重排序引擎: {'✅' if hybrid_engine.reranking_engine else '❌'}")
        print(f"   - LLM引擎: {'✅' if hybrid_engine.llm_engine else '❌'}")
        print(f"   - 智能过滤引擎: {'✅' if hybrid_engine.smart_filter_engine else '❌'}")
        print(f"   - 源过滤引擎: {'✅' if hybrid_engine.source_filter_engine else '❌'}")
        print(f"   - 优化管道: {'✅' if hybrid_engine.optimization_pipeline else '❌'}")
        
        # 执行一个简单的查询
        print(f"\n🔍 执行简单查询...")
        query = "中芯国际"
        
        start_time = time.time()
        result = hybrid_engine.process_query(
            query,
            query_type=QueryType.TEXT,
            max_results=3
        )
        processing_time = time.time() - start_time
        
        print(f"⏱️  查询耗时: {processing_time:.2f}秒")
        print(f"✅ 查询成功: {result.success}")
        print(f"📊 结果数量: {len(result.results) if result.results else 0}")
        
        if result.success and result.results:
            print(f"\n📄 前3个结果:")
            for i, doc in enumerate(result.results[:3]):
                print(f"   结果{i+1}:")
                if isinstance(doc, dict):
                    print(f"     类型: {type(doc)}")
                    print(f"     键: {list(doc.keys())}")
                    if 'doc' in doc and isinstance(doc['doc'], dict):
                        actual_doc = doc['doc']
                        print(f"     实际文档类型: {type(actual_doc)}")
                        print(f"     实际文档键: {list(actual_doc.keys())}")
                        print(f"     chunk_type: {actual_doc.get('chunk_type', 'N/A')}")
                        print(f"     document_name: {actual_doc.get('document_name', 'N/A')}")
                elif hasattr(doc, 'metadata'):
                    print(f"     Document对象")
                    print(f"     chunk_type: {doc.metadata.get('chunk_type', 'N/A')}")
                    print(f"     document_name: {doc.metadata.get('document_name', 'N/A')}")
                else:
                    print(f"     其他类型: {type(doc)}")
        
        # 检查元数据
        if hasattr(result, 'metadata') and result.metadata:
            print(f"\n🤖 结果元数据:")
            for key, value in result.metadata.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"   {key}: {value[:100]}...")
                else:
                    print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 开始简单测试混合引擎...")
    print("=" * 60)
    
    test_hybrid_engine()
    
    print("\n" + "=" * 60)
    print("🏁 测试完成")

if __name__ == "__main__":
    main()
