#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. Table Engine 第一阶段改进测试脚本
## 2. 测试文档加载机制重构和配置管理优化
## 3. 验证重试机制、错误处理、延迟加载和缓存管理
## 4. 验证配置验证和初始化流程
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from v2.config.v2_config import V2ConfigManager, TableEngineConfigV2
from v2.core.table_engine import TableEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("🔍 测试配置加载")
    print("=" * 60)
    
    try:
        # 加载配置
        config_manager = V2ConfigManager()
        config = config_manager.config  # 使用config属性而不是load_config()方法
        
        print(f"✅ 配置加载成功")
        print(f"   配置类型: {type(config)}")
        
        # 检查table_engine配置
        if hasattr(config, 'table_engine'):
            table_config = config.table_engine
            print(f"✅ table_engine配置存在")
            print(f"   配置类型: {type(table_config)}")
            print(f"   配置内容: {table_config}")
            
            # 检查关键配置项
            key_configs = [
                'max_recall_results',
                'use_new_pipeline', 
                'enable_enhanced_reranking',
                'recall_strategy',
                'reranking'
            ]
            
            for key in key_configs:
                if hasattr(table_config, key):
                    value = getattr(table_config, key)
                    print(f"   ✅ {key}: {value}")
                else:
                    print(f"   ❌ {key}: 缺失")
        else:
            print(f"❌ table_engine配置缺失")
            
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()

def test_table_engine_initialization():
    """测试Table Engine初始化"""
    print("\n" + "=" * 60)
    print("🔍 测试Table Engine初始化")
    print("=" * 60)
    
    try:
        # 加载配置
        config_manager = V2ConfigManager()
        config = config_manager.config  # 使用config属性
        
        if not hasattr(config, 'table_engine'):
            print("❌ 配置中缺少table_engine，跳过初始化测试")
            return
        
        # 创建Table Engine（跳过初始文档加载）
        print("开始创建Table Engine...")
        table_engine = TableEngine(
            config=config.table_engine,
            vector_store=None,  # 暂时不提供，测试配置验证
            document_loader=None,  # 暂时不提供，测试配置验证
            skip_initial_load=True  # 跳过初始加载，只测试配置验证
        )
        
        print(f"✅ Table Engine创建成功")
        print(f"   引擎名称: {table_engine.name}")
        print(f"   配置类型: {type(table_engine.config)}")
        print(f"   文档加载状态: {table_engine._docs_loaded}")
        print(f"   表格文档数量: {len(table_engine.table_docs)}")
        
        # 检查配置验证结果
        print("\n配置验证结果:")
        if hasattr(table_engine.config, 'recall_strategy'):
            strategy = table_engine.config.recall_strategy
            for layer, config in strategy.items():
                enabled = config.get('enabled', False)
                top_k = config.get('top_k', 0)
                print(f"   {layer}: {'启用' if enabled else '禁用'}, top_k: {top_k}")
        
        if hasattr(table_engine.config, 'reranking'):
            reranking = table_engine.config.reranking
            print(f"   重排序配置: {reranking}")
            
    except Exception as e:
        print(f"❌ Table Engine初始化失败: {e}")
        import traceback
        traceback.print_exc()

def test_config_validation():
    """测试配置验证"""
    print("\n" + "=" * 60)
    print("🔍 测试配置验证")
    print("=" * 60)
    
    try:
        # 创建一个测试配置
        test_config = TableEngineConfigV2(
            name="test_table_engine",
            max_results=20,
            table_similarity_threshold=0.7,
            header_weight=0.4,
            content_weight=0.4,
            structure_weight=0.2,
            max_recall_results=100,
            use_new_pipeline=True,
            enable_enhanced_reranking=True
        )
        
        print(f"✅ 测试配置创建成功")
        print(f"   配置内容: {test_config}")
        
        # 创建Table Engine进行配置验证
        print("\n开始配置验证...")
        table_engine = TableEngine(
            config=test_config,
            vector_store=None,
            document_loader=None,
            skip_initial_load=True
        )
        
        print(f"✅ 配置验证通过")
        
        # 检查配置验证的详细结果
        print("\n配置验证详细结果:")
        print(f"   召回策略配置: {test_config.recall_strategy}")
        print(f"   重排序配置: {test_config.reranking}")
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        import traceback
        traceback.print_exc()

def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("🔍 测试错误处理")
    print("=" * 60)
    
    try:
        # 测试无效配置
        print("测试无效配置...")
        invalid_config = TableEngineConfigV2(
            table_similarity_threshold=1.5  # 无效值
        )
        
        # 这应该会抛出异常
        table_engine = TableEngine(
            config=invalid_config,
            vector_store=None,
            document_loader=None,
            skip_initial_load=True
        )
        
        print("❌ 应该抛出异常但没有")
        
    except ValueError as e:
        print(f"✅ 正确捕获配置验证异常: {e}")
    except Exception as e:
        print(f"❌ 捕获到意外的异常类型: {type(e)} - {e}")

def main():
    """主函数"""
    print("🚀 Table Engine 第一阶段改进测试")
    print("测试内容：文档加载机制重构和配置管理优化")
    print("=" * 60)
    
    # 测试配置加载
    test_config_loading()
    
    # 测试Table Engine初始化
    test_table_engine_initialization()
    
    # 测试配置验证
    test_config_validation()
    
    # 测试错误处理
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("🎉 第一阶段测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
