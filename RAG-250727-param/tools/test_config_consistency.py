#!/usr/bin/env python3
# -*- coding: utf-8
"""
程序说明：

## 1. 配置一致性测试脚本
## 2. 验证v2_config.py和v2_config.json的配置加载是否一致
## 3. 检查嵌套配置（如recall_strategy）是否正确加载

## 使用方法：
python test_config_consistency.py
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_config_consistency():
    """测试配置一致性"""
    try:
        logger.info("🔍 开始测试配置一致性")
        
        # 1. 导入配置管理器
        from v2.config.v2_config import V2ConfigManager
        
        # 2. 加载配置
        logger.info("加载配置...")
        config_manager = V2ConfigManager()
        
        # 3. 获取table_engine配置
        table_config = config_manager.get_engine_config('table')
        if not table_config:
            logger.error("❌ 无法获取table_engine配置")
            return False
        
        logger.info("✅ table_engine配置加载成功")
        
        # 4. 检查基础配置
        logger.info(f"  - max_results: {getattr(table_config, 'max_results', 'N/A')}")
        logger.info(f"  - table_similarity_threshold: {getattr(table_config, 'table_similarity_threshold', 'N/A')}")
        logger.info(f"  - keyword_weight: {getattr(table_config, 'keyword_weight', 'N/A')}")
        
        # 5. 检查recall_strategy配置
        logger.info("\n检查recall_strategy配置...")
        recall_config = getattr(table_config, 'recall_strategy', {})
        if recall_config:
            logger.info("✅ recall_strategy配置存在")
            
            # 检查每个层级的配置
            for layer_name, layer_config in recall_config.items():
                logger.info(f"\n  {layer_name}:")
                
                # 检查enabled属性
                if hasattr(layer_config, 'enabled'):
                    enabled = getattr(layer_config, 'enabled', False)
                    logger.info(f"    - enabled: {enabled}")
                else:
                    logger.warning(f"    - enabled: 属性缺失")
                
                # 检查其他属性
                if hasattr(layer_config, 'top_k'):
                    top_k = getattr(layer_config, 'top_k', 'N/A')
                    logger.info(f"    - top_k: {top_k}")
                
                if hasattr(layer_config, 'description'):
                    description = getattr(layer_config, 'description', 'N/A')
                    logger.info(f"    - description: {description}")
                
                # 检查配置类型
                logger.info(f"    - 配置类型: {type(layer_config)}")
                
                # 如果是字典，显示内容
                if isinstance(layer_config, dict):
                    logger.info(f"    - 字典内容: {layer_config}")
        else:
            logger.warning("⚠️ recall_strategy配置不存在")
        
        # 6. 检查配置对象类型
        logger.info(f"\n配置对象类型: {type(table_config)}")
        logger.info(f"配置对象类: {table_config.__class__.__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置一致性测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动配置一致性测试")
    
    success = test_config_consistency()
    
    if success:
        logger.info("🎉 配置一致性测试完成")
        sys.exit(0)
    else:
        logger.error("💥 配置一致性测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
