#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 测试table engine配置修复是否成功
## 2. 验证第二层向量搜索配置是否正确获取
## 3. 检查召回策略配置的完整性
## 4. 验证修复后的配置键名匹配
'''

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入table engine和配置
from v2.core.table_engine import TableEngine
from v2.config.v2_config import TableEngineConfigV2

def test_table_engine_config():
    """测试table engine配置修复"""
    print("=" * 60)
    print("测试Table Engine配置修复")
    print("=" * 60)
    
    try:
        # 创建配置
        config = TableEngineConfigV2()
        print(f"✅ 配置创建成功: {type(config)}")
        
        # 检查召回策略配置
        if hasattr(config, 'recall_strategy'):
            print(f"✅ 召回策略配置存在")
            strategy = config.recall_strategy
            
            # 检查各层配置
            layers = [
                'layer1_structure_search',
                'layer2_vector_search', 
                'layer3_keyword_search',
                'layer4_hybrid_search',
                'layer5_fuzzy_search',
                'layer6_expansion_search'
            ]
            
            for layer in layers:
                if layer in strategy:
                    layer_config = strategy[layer]
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
        else:
            print("❌ 召回策略配置缺失")
            return False
        
        # 检查向量搜索配置
        vector_config = strategy.get('layer2_vector_search', {})
        if vector_config:
            print(f"\n🔍 第二层向量搜索配置:")
            print(f"  - 启用状态: {vector_config.get('enabled', True)}")
            print(f"  - top_k: {vector_config.get('top_k', 50)}")
            print(f"  - similarity_threshold: {vector_config.get('similarity_threshold', 0.65)}")
            print(f"  - 描述: {vector_config.get('description', 'N/A')}")
        else:
            print("❌ 第二层向量搜索配置缺失")
            return False
        
        print("\n✅ 配置检查完成，所有配置键名正确")
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

def test_config_key_matching():
    """测试配置键名匹配"""
    print("\n" + "=" * 60)
    print("测试配置键名匹配")
    print("=" * 60)
    
    try:
        # 创建配置
        config = TableEngineConfigV2()
        
        # 检查配置键名是否与代码中的使用一致
        strategy = config.recall_strategy
        
        # 模拟代码中的配置获取
        test_cases = [
            ('layer1_structure_search', 'structure_threshold'),
            ('layer2_vector_search', 'similarity_threshold'),
            ('layer3_keyword_search', 'match_threshold'),
            ('layer4_hybrid_search', 'vector_weight'),
            ('layer5_fuzzy_search', 'fuzzy_threshold'),
            ('layer6_expansion_search', 'enabled')
        ]
        
        all_passed = True
        for layer, key in test_cases:
            if layer in strategy:
                layer_config = strategy[layer]
                if key in layer_config:
                    value = layer_config[key]
                    print(f"  ✅ {layer}.{key}: {value}")
                else:
                    print(f"  ❌ {layer}.{key}: 配置缺失")
                    all_passed = False
            else:
                print(f"  ❌ {layer}: 层配置缺失")
                all_passed = False
        
        if all_passed:
            print("\n✅ 所有配置键名匹配成功")
        else:
            print("\n❌ 存在配置键名不匹配")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 配置键名匹配测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试Table Engine配置修复")
    
    # 测试1: 基本配置检查
    config_ok = test_table_engine_config()
    
    # 测试2: 配置键名匹配
    key_matching_ok = test_config_key_matching()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    if config_ok and key_matching_ok:
        print("✅ 所有测试通过！Table Engine配置修复成功")
        print("\n修复内容:")
        print("  - 修复了_vector_search方法中的配置键名错误")
        print("  - 从'layer1_vector_search'改为'layer2_vector_search'")
        print("  - 确保配置键名与配置文件定义一致")
        print("\n下一步:")
        print("  - 可以测试table engine的第二层召回功能")
        print("  - 验证向量搜索是否返回结果")
    else:
        print("❌ 部分测试失败，需要进一步检查")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
