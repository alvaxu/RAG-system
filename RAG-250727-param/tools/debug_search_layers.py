#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 诊断TableEngine中各个搜索层的问题
## 2. 检查为什么前两层搜索返回0个结果
## 3. 分析搜索算法的具体问题
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_search_layers():
    """诊断搜索层问题"""
    print("=" * 60)
    print("诊断TableEngine中各个搜索层的问题")
    print("=" * 60)
    
    try:
        # 导入TableEngine
        print("🔍 导入TableEngine...")
        from v2.core.table_engine import TableEngine
        from v2.config.v2_config import load_v2_config
        print("✅ TableEngine导入成功")
        
        # 获取配置
        print("\n🔍 获取配置...")
        config_manager = load_v2_config('v2/config/v2_config.json')
        table_config = config_manager.get_engine_config('table')
        print("✅ 配置获取成功")
        
        # 创建TableEngine（正确加载文档）
        print("\n🔍 创建TableEngine...")
        table_engine = TableEngine(table_config, skip_initial_load=False)  # 改为False，正确加载文档
        print("✅ TableEngine创建成功")
        
        # 检查配置
        print("\n🔍 检查搜索层配置...")
        if hasattr(table_config, 'recall_strategy'):
            strategy = table_config.recall_strategy
            print(f"✅ 召回策略配置存在，包含 {len(strategy)} 层")
            
            for layer_name, layer_config in strategy.items():
                enabled = layer_config.get('enabled', True)
                threshold = layer_config.get('similarity_threshold', layer_config.get('structure_threshold', layer_config.get('match_threshold', 'N/A')))
                top_k = layer_config.get('top_k', 'N/A')
                print(f"  - {layer_name}: 启用={enabled}, 阈值={threshold}, top_k={top_k}")
        else:
            print("❌ 召回策略配置不存在")
        
        # 检查文档状态
        print("\n🔍 检查文档状态...")
        print(f"  - table_docs数量: {len(table_engine.table_docs)}")
        print(f"  - vector_store状态: {table_engine.vector_store is not None}")
        print(f"  - document_loader状态: {table_engine.document_loader is not None}")
        
        # 检查搜索方法
        print("\n🔍 检查搜索方法...")
        search_methods = [
            '_table_structure_search',
            '_vector_search', 
            '_keyword_search',
            '_hybrid_search',
            '_fuzzy_search',
            '_expansion_search'
        ]
        
        for method_name in search_methods:
            if hasattr(table_engine, method_name):
                method = getattr(table_engine, method_name)
                print(f"  - {method_name}: 存在，类型={type(method)}")
            else:
                print(f"  - {method_name}: ❌ 不存在")
        
        # 测试查询
        print("\n🔍 测试查询...")
        test_query = "中芯国际的营业收入从2017年到2024年的变化趋势如何？"
        print(f"测试查询: {test_query}")
        
        # 检查各个搜索层的结果
        print("\n🔍 检查各个搜索层的结果...")
        
        # 第一层：结构搜索
        if hasattr(table_engine, '_table_structure_search'):
            print("🔍 测试第一层：结构搜索...")
            try:
                structure_results = table_engine._table_structure_search(test_query, 50)
                print(f"  - 结构搜索结果数量: {len(structure_results)}")
                if structure_results:
                    print(f"  - 第一个结果分数: {structure_results[0].get('score', 'N/A')}")
            except Exception as e:
                print(f"  - 结构搜索失败: {e}")
        
        # 第二层：向量搜索
        if hasattr(table_engine, '_vector_search'):
            print("🔍 测试第二层：向量搜索...")
            try:
                vector_results = table_engine._vector_search(test_query, 50)
                print(f"  - 向量搜索结果数量: {len(vector_results)}")
                if vector_results:
                    print(f"  - 第一个结果分数: {vector_results[0].get('score', 'N/A')}")
            except Exception as e:
                print(f"  - 向量搜索失败: {e}")
        
        # 第三层：关键词搜索
        if hasattr(table_engine, '_keyword_search'):
            print("🔍 测试第三层：关键词搜索...")
            try:
                keyword_results = table_engine._keyword_search(test_query, 50)
                print(f"  - 关键词搜索结果数量: {len(keyword_results)}")
                if keyword_results:
                    print(f"  - 第一个结果分数: {keyword_results[0].get('score', 'N/A')}")
            except Exception as e:
                print(f"  - 关键词搜索失败: {e}")
        
        print("\n🎉 搜索层诊断完成！")
        return True
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

def main():
    """主诊断函数"""
    print("🚀 开始诊断TableEngine搜索层问题")
    
    success = debug_search_layers()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 诊断完成！")
    else:
        print("❌ 诊断失败，请检查问题")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
