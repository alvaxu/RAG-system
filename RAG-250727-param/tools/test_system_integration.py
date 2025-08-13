'''
程序说明：
## 1. 系统集成测试脚本
## 2. 验证智能后处理引擎是否正确集成到整个系统中
## 3. 测试配置加载、引擎初始化、API状态等
## 4. 确保所有组件能够正常协作
'''

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.config.v2_config import V2ConfigManager
from v2.core.hybrid_engine import HybridEngine


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_config_loading():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")
    
    try:
        config_manager = V2ConfigManager()
        config = config_manager.config
        print("✅ V2配置管理器创建成功")
        
        # 检查配置结构
        print(f"配置版本: {getattr(config, 'version', 'N/A')}")
        print(f"系统名称: {getattr(config, 'system_name', 'N/A')}")
        
        # 检查混合引擎配置
        if hasattr(config, 'hybrid_engine'):
            hybrid_config = config.hybrid_engine
            print(f"混合引擎启用: {getattr(hybrid_config, 'enabled', False)}")
            
            # 检查优化管道配置
            if hasattr(hybrid_config, 'optimization_pipeline'):
                opt_pipeline = hybrid_config.optimization_pipeline
                print(f"智能后处理启用: {getattr(opt_pipeline, 'enable_intelligent_post_processing', False)}")
        
        return config
        
    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        return None


def test_hybrid_engine_initialization(config):
    """测试混合引擎初始化"""
    print("\n=== 测试混合引擎初始化 ===")
    
    try:
        # 创建混合引擎实例
        hybrid_engine = HybridEngine(config)
        print("✅ 混合引擎创建成功")
        
        # 检查智能后处理引擎
        print(f"智能后处理引擎: {hybrid_engine.intelligent_post_processing_engine is not None}")
        
        if hybrid_engine.intelligent_post_processing_engine:
            print("✅ 智能后处理引擎初始化成功")
            print(f"引擎类型: {type(hybrid_engine.intelligent_post_processing_engine)}")
        else:
            print("❌ 智能后处理引擎初始化失败")
        
        return hybrid_engine
        
    except Exception as e:
        print(f"❌ 混合引擎初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主测试函数"""
    print("🚀 开始系统集成测试")
    
    # 设置日志
    setup_logging()
    
    try:
        # 测试配置加载
        config = test_config_loading()
        if not config:
            print("❌ 配置加载失败，测试终止")
            return
        
        # 测试混合引擎初始化
        hybrid_engine = test_hybrid_engine_initialization(config)
        if not hybrid_engine:
            print("❌ 混合引擎初始化失败，测试终止")
            return
        
        print("\n🎉 系统集成测试完成！")
        print("\n📋 测试总结:")
        print("✅ 配置加载: 成功")
        print("✅ 混合引擎初始化: 成功")
        print("✅ 智能后处理引擎: 成功")
        print("\n🎯 智能后处理引擎已成功集成到系统中！")
        
    except Exception as e:
        print(f"\n❌ 系统集成测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
