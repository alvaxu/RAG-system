'''
程序说明：
## 1. 调试Pipeline配置传递问题
## 2. 检查pipeline_config.__dict__的实际内容
## 3. 验证配置是否正确传递到UnifiedPipeline
'''

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def debug_pipeline_config():
    """调试Pipeline配置传递问题"""
    
    logger.info("开始调试Pipeline配置传递问题")
    
    try:
        # 导入必要的模块
        from v2.config.v2_config import V2ConfigManager
        
        # 加载配置
        config_manager = V2ConfigManager()
        pipeline_config = config_manager.get_engine_config('unified_pipeline')
        
        if not pipeline_config:
            logger.error("❌ 无法获取unified_pipeline配置")
            return False
        
        logger.info("✅ 配置加载成功")
        logger.info(f"配置对象类型: {type(pipeline_config)}")
        logger.info(f"配置对象属性: {[attr for attr in dir(pipeline_config) if not attr.startswith('_')]}")
        
        # 检查关键字段
        logger.info(f"\n🔍 关键字段检查:")
        logger.info(f"  enable_llm_generation: {pipeline_config.enable_llm_generation}")
        logger.info(f"  enable_source_filtering: {pipeline_config.enable_source_filtering}")
        logger.info(f"  max_context_results: {pipeline_config.max_context_results}")
        logger.info(f"  max_content_length: {pipeline_config.max_content_length}")
        
        # 检查__dict__内容
        logger.info(f"\n🔍 __dict__内容检查:")
        config_dict = pipeline_config.__dict__
        logger.info(f"  __dict__类型: {type(config_dict)}")
        logger.info(f"  __dict__键: {list(config_dict.keys())}")
        
        for key, value in config_dict.items():
            logger.info(f"    {key}: {value} (类型: {type(value)})")
        
        # 检查enable_source_filtering字段
        if 'enable_source_filtering' in config_dict:
            logger.info(f"\n✅ enable_source_filtering字段存在: {config_dict['enable_source_filtering']}")
        else:
            logger.error(f"\n❌ enable_source_filtering字段不存在！")
            
        # 模拟UnifiedPipeline的config.get调用
        logger.info(f"\n🔍 模拟UnifiedPipeline的config.get调用:")
        test_config = config_dict.copy()
        
        # 模拟UnifiedPipeline的初始化
        enable_source_filtering = test_config.get('enable_source_filtering', True)
        logger.info(f"  config.get('enable_source_filtering', True) = {enable_source_filtering}")
        
        if enable_source_filtering:
            logger.warning(f"⚠️ 源过滤将被启用！")
        else:
            logger.info(f"✅ 源过滤将被禁用")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("=== Pipeline配置调试工具 ===")
    
    success = debug_pipeline_config()
    
    if success:
        logger.info("✅ 调试完成")
    else:
        logger.error("❌ 调试失败")

if __name__ == "__main__":
    main()
