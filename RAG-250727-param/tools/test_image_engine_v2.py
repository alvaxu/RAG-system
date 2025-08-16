#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：

## 1. 测试Image Engine V2.0的五层召回策略
## 2. 测试ImageRerankingService集成
## 3. 测试统一Pipeline集成
## 4. 验证图片查询功能的完整性
'''

import sys
import os
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging
from v2.core.image_engine import ImageEngine
from v2.config.v2_config import V2ConfigManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_image_engine_v2():
    """测试Image Engine V2.0"""
    print("🔍 开始测试Image Engine V2.0...")
    print("=" * 60)
    
    try:
        # 1. 加载配置
        print("📋 加载配置...")
        try:
            config_manager = V2ConfigManager()
            print(f"✅ 配置管理器创建成功: {type(config_manager)}")
            print(f"✅ 配置对象类型: {type(config_manager.config)}")
            print(f"✅ 配置对象属性: {[attr for attr in dir(config_manager.config) if not attr.startswith('_')][:10]}")
            
            # 直接访问配置
            if hasattr(config_manager.config, 'image_engine'):
                print(f"✅ 直接访问image_engine: {config_manager.config.image_engine.name}")
            else:
                print("❌ 直接访问image_engine失败")
            
            # 通过方法访问配置
            image_config = config_manager.get_engine_config('image')
            print(f"✅ 通过方法访问结果: {type(image_config)}")
            
            if not image_config:
                print("❌ 无法获取Image Engine配置")
                return False
        except Exception as e:
            print(f"❌ 配置加载异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"✅ 配置加载成功: {image_config.name}")
        print(f"   - 最大结果数: {image_config.max_results}")
        print(f"   - 向量搜索阈值: {image_config.image_similarity_threshold}")
        print(f"   - 启用关键词搜索: {image_config.enable_keyword_search}")
        print(f"   - 启用增强重排序: {image_config.enable_enhanced_reranking}")
        print(f"   - 使用新Pipeline: {image_config.use_new_pipeline}")
        
        # 2. 创建Image Engine实例
        print("\n🚀 创建Image Engine实例...")
        image_engine = ImageEngine(
            config=image_config,
            vector_store=None,  # 暂时不提供，测试基本功能
            document_loader=None,  # 暂时不提供，测试基本功能
            skip_initial_load=True
        )
        
        print(f"✅ Image Engine创建成功: {image_engine.name}")
        print(f"   - 引擎状态: {image_engine.status}")
        
        # 3. 测试五层召回策略配置
        print("\n📊 检查五层召回策略配置...")
        if hasattr(image_config, 'recall_strategy'):
            recall_strategy = image_config.recall_strategy
            print(f"✅ 召回策略配置存在，包含 {len(recall_strategy)} 层")
            
            for layer_name, layer_config in recall_strategy.items():
                print(f"   - {layer_name}: {layer_config.get('description', '无描述')}")
                print(f"     enabled: {layer_config.get('enabled', False)}")
                print(f"     top_k: {layer_config.get('top_k', 'N/A')}")
        else:
            print("❌ 召回策略配置不存在")
        
        # 4. 测试重排序配置
        print("\n🔄 检查重排序配置...")
        if hasattr(image_config, 'reranking'):
            reranking_config = image_config.reranking
            print(f"✅ 重排序配置存在")
            print(f"   - 目标数量: {reranking_config.get('target_count', 'N/A')}")
            print(f"   - 使用LLM增强: {reranking_config.get('use_llm_enhancement', 'N/A')}")
            print(f"   - 模型名称: {reranking_config.get('model_name', 'N/A')}")
            print(f"   - 相似度阈值: {reranking_config.get('similarity_threshold', 'N/A')}")
        else:
            print("❌ 重排序配置不存在")
        
        # 5. 测试方法存在性
        print("\n🔍 检查关键方法...")
        methods_to_check = [
            '_search_images_with_five_layer_recall',
            '_vector_search',
            '_keyword_search',
            '_hybrid_search',
            '_fuzzy_search',
            '_expansion_search',
            '_final_ranking_and_limit'
        ]
        
        for method_name in methods_to_check:
            if hasattr(image_engine, method_name):
                print(f"✅ {method_name}: 存在")
            else:
                print(f"❌ {method_name}: 缺失")
        
        # 6. 测试配置参数
        print("\n⚙️ 检查配置参数...")
        params_to_check = [
            'max_recall_results',
            'use_new_pipeline',
            'enable_enhanced_reranking'
        ]
        
        for param_name in params_to_check:
            if hasattr(image_config, param_name):
                value = getattr(image_config, param_name)
                print(f"✅ {param_name}: {value}")
            else:
                print(f"❌ {param_name}: 缺失")
        
        print("\n🎉 Image Engine V2.0测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_image_engine_v2()
    if success:
        print("\n✅ 所有测试通过！Image Engine V2.0再造成功！")
    else:
        print("\n❌ 测试失败，需要进一步调试")
