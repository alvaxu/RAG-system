"""
测试配置修复是否有效

## 1. 功能特点
- 测试配置管理器是否正确加载引擎配置
- 验证引擎配置是否为dataclass对象
- 测试get_engine_config_for_initialization方法

## 2. 与其他版本的不同点
- 新增的配置测试脚本
- 专门测试配置对象类型问题
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.config.v2_config import V2ConfigManager

def test_config_loading():
    """测试配置加载"""
    print("🔍 测试配置加载...")
    
    try:
        # 初始化配置管理器
        config_manager = V2ConfigManager()
        print("✅ 配置管理器初始化成功")
        
        # 检查各个引擎配置
        engine_types = ['smart_filter', 'source_filter', 'reranking', 'llm']
        
        for engine_type in engine_types:
            print(f"\n📋 检查 {engine_type} 引擎配置:")
            
            # 获取配置
            config = config_manager.get_engine_config(engine_type)
            if config:
                print(f"  - 配置类型: {type(config)}")
                print(f"  - 是否为dataclass: {hasattr(config, '__dataclass_fields__')}")
                
                # 测试get_engine_config_for_initialization
                init_config = config_manager.get_engine_config_for_initialization(engine_type)
                if init_config:
                    print(f"  - 初始化配置类型: {type(init_config)}")
                    print(f"  - 是否为dataclass: {hasattr(init_config, '__dataclass_fields__')}")
                    
                    # 测试访问enable_filtering属性
                    if hasattr(init_config, 'enable_filtering'):
                        print(f"  - enable_filtering: {init_config.enable_filtering}")
                    elif hasattr(init_config, 'enable_reranking'):
                        print(f"  - enable_reranking: {init_config.enable_reranking}")
                    elif hasattr(init_config, 'enable_llm'):
                        print(f"  - enable_llm: {init_config.enable_llm}")
                else:
                    print(f"  ❌ 初始化配置获取失败")
            else:
                print(f"  ❌ 配置不存在")
        
        # 检查hybrid_engine配置
        print(f"\n📋 检查 hybrid_engine 配置:")
        hybrid_config = config_manager.get_engine_config('hybrid')
        if hybrid_config:
            print(f"  - 配置类型: {type(hybrid_config)}")
            print(f"  - 是否为dataclass: {hasattr(hybrid_config, '__dataclass_fields__')}")
            
            if hasattr(hybrid_config, 'optimization_pipeline'):
                pipeline_config = hybrid_config.optimization_pipeline
                print(f"  - optimization_pipeline类型: {type(pipeline_config)}")
                print(f"  - 是否为dataclass: {hasattr(pipeline_config, '__dataclass_fields__')}")
                
                if hasattr(pipeline_config, 'enable_smart_filtering'):
                    print(f"  - enable_smart_filtering: {pipeline_config.enable_smart_filtering}")
                if hasattr(pipeline_config, 'enable_source_filtering'):
                    print(f"  - enable_source_filtering: {pipeline_config.enable_source_filtering}")
        
        print("\n🎉 配置测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config_loading()
