'''
程序说明：
## 1. 测试V2配置管理器的配置加载功能
## 2. 验证optimization_pipeline配置是否正确转换为OptimizationPipelineConfig对象
## 3. 检查配置对象的类型和属性访问
'''

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.config.v2_config import V2ConfigManager

def test_config_loading():
    """测试配置加载功能"""
    print("🔍 开始测试配置加载...")
    try:
        # 初始化配置管理器
        config_manager = V2ConfigManager()
        v2_config = config_manager.config
        
        print(f"✅ 配置管理器初始化成功")
        print(f"   系统名称: {v2_config.system_name}")
        print(f"   版本: {v2_config.version}")
        
        # 检查hybrid_engine配置
        if hasattr(v2_config, 'hybrid_engine') and v2_config.hybrid_engine:
            hybrid_config = v2_config.hybrid_engine
            print(f"\n🔧 混合引擎配置:")
            print(f"   类型: {type(hybrid_config)}")
            print(f"   名称: {hybrid_config.name}")
            print(f"   启用: {hybrid_config.enabled}")
            
            # 检查optimization_pipeline配置
            if hasattr(hybrid_config, 'optimization_pipeline') and hybrid_config.optimization_pipeline:
                pipeline_config = hybrid_config.optimization_pipeline
                print(f"\n📊 优化管道配置:")
                print(f"   类型: {type(pipeline_config)}")
                print(f"   重排序启用: {pipeline_config.enable_reranking}")
                print(f"   LLM生成启用: {pipeline_config.enable_llm_generation}")
                print(f"   智能过滤启用: {pipeline_config.enable_smart_filtering}")
                print(f"   源过滤启用: {pipeline_config.enable_source_filtering}")
                
                # 尝试访问属性，这应该不会出错
                try:
                    reranking_enabled = pipeline_config.enable_reranking
                    llm_enabled = pipeline_config.enable_llm_generation
                    smart_filter_enabled = pipeline_config.enable_smart_filtering
                    source_filter_enabled = pipeline_config.enable_source_filtering
                    
                    print(f"\n✅ 属性访问测试成功:")
                    print(f"   enable_reranking: {reranking_enabled}")
                    print(f"   enable_llm_generation: {llm_enabled}")
                    print(f"   enable_smart_filtering: {smart_filter_enabled}")
                    print(f"   enable_source_filtering: {source_filter_enabled}")
                    
                except AttributeError as e:
                    print(f"❌ 属性访问失败: {e}")
                    return False
                
            else:
                print("   ❌ 没有找到优化管道配置")
                return False
        else:
            print("   ❌ 没有找到混合引擎配置")
            return False
        
        # 检查其他引擎配置
        print(f"\n📋 其他引擎配置:")
        engine_types = ['image_engine', 'text_engine', 'table_engine', 'reranking_engine', 'llm_engine', 'smart_filter_engine', 'source_filter_engine']
        for engine_type in engine_types:
            if hasattr(v2_config, engine_type) and getattr(v2_config, engine_type):
                engine_config = getattr(v2_config, engine_type)
                print(f"   {engine_type}: {type(engine_config).__name__} - {'✅' if engine_config.enabled else '❌'}")
            else:
                print(f"   {engine_type}: 未配置")
        
        print(f"\n✅ 配置加载测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 开始测试V2配置管理器...")
    print("=" * 60)
    
    success = test_config_loading()
    
    print("\n" + "=" * 60)
    if success:
        print("🏁 测试成功 - 配置加载正常")
    else:
        print("💥 测试失败 - 配置加载有问题")
    
    return success

if __name__ == "__main__":
    main()
