#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 调试table engine的向量搜索问题
## 2. 验证第二层召回是否正常工作
## 3. 检查向量搜索的详细执行过程
## 4. 诊断为什么第二层召回为0
'''

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入必要的模块
try:
    from v2.config.v2_config import TableEngineConfigV2
    from v2.core.table_engine import TableEngine
    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

def test_table_engine_vector_search():
    """测试table engine的向量搜索功能"""
    print("=" * 60)
    print("测试Table Engine向量搜索功能")
    print("=" * 60)
    
    try:
        # 创建配置
        config = TableEngineConfigV2()
        print(f"✅ 配置创建成功")
        
        # 检查第二层向量搜索配置
        vector_config = config.recall_strategy.get('layer2_vector_search', {})
        print(f"🔍 第二层向量搜索配置:")
        print(f"  - 启用状态: {vector_config.get('enabled', True)}")
        print(f"  - top_k: {vector_config.get('top_k', 50)}")
        print(f"  - similarity_threshold: {vector_config.get('similarity_threshold', 0.65)}")
        
        # 创建table engine（跳过初始加载）
        print("\n🔍 创建Table Engine...")
        table_engine = TableEngine(config, skip_initial_load=True)
        print(f"✅ Table Engine创建成功")
        
        # 检查向量数据库状态
        print(f"\n🔍 向量数据库状态: {table_engine.vector_store is not None}")
        
        # 测试查询
        test_query = "中芯国际财务数据"
        print(f"\n🔍 测试查询: {test_query}")
        
        # 直接测试向量搜索
        if hasattr(table_engine, '_vector_search'):
            print("🔍 开始测试向量搜索...")
            try:
                vector_results = table_engine._vector_search(test_query, 50)
                print(f"✅ 向量搜索完成，返回 {len(vector_results)} 个结果")
                
                if vector_results:
                    print("🔍 前3个结果:")
                    for i, result in enumerate(vector_results[:3]):
                        print(f"  结果 {i+1}: score={result['score']}, source={result['source']}, layer={result['layer']}")
                else:
                    print("⚠️ 向量搜索没有返回结果")
                    
            except Exception as e:
                print(f"❌ 向量搜索测试失败: {e}")
                import traceback
                print(f"详细错误信息: {traceback.format_exc()}")
        else:
            print("❌ Table Engine没有_vector_search方法")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

def test_config_consistency():
    """测试配置一致性"""
    print("\n" + "=" * 60)
    print("测试配置一致性")
    print("=" * 60)
    
    try:
        config = TableEngineConfigV2()
        
        # 检查所有层的配置
        layers = [
            'layer1_structure_search',
            'layer2_vector_search', 
            'layer3_keyword_search',
            'layer4_hybrid_search',
            'layer5_fuzzy_search',
            'layer6_expansion_search'
        ]
        
        for layer in layers:
            if layer in config.recall_strategy:
                layer_config = config.recall_strategy[layer]
                enabled = layer_config.get('enabled', True)
                print(f"  ✅ {layer}: {'启用' if enabled else '禁用'}")
                
                # 检查特定配置项
                if layer == 'layer2_vector_search':
                    top_k = layer_config.get('top_k', 50)
                    similarity_threshold = layer_config.get('similarity_threshold', 0.65)
                    print(f"    - top_k: {top_k}")
                    print(f"    - similarity_threshold: {similarity_threshold}")
            else:
                print(f"  ❌ {layer}: 配置缺失")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置一致性测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始调试Table Engine向量搜索问题")
    
    # 测试1: 配置一致性
    config_ok = test_config_consistency()
    
    # 测试2: 向量搜索功能
    vector_search_ok = test_table_engine_vector_search()
    
    # 总结
    print("\n" + "=" * 60)
    print("调试结果总结")
    print("=" * 60)
    
    if config_ok and vector_search_ok:
        print("✅ 所有测试通过！")
        print("\n可能的问题:")
        print("  1. 向量数据库中没有表格文档")
        print("  2. 向量搜索的filter参数不正确")
        print("  3. 相似度阈值设置过高")
        print("  4. 向量数据库的embedding模型问题")
    else:
        print("❌ 部分测试失败，需要进一步检查")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
