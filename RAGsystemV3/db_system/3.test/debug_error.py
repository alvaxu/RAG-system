#!/usr/bin/env python3
"""
调试错误定位脚本

定位'str' object has no attribute 'get'错误的具体位置
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from core.model_caller import LangChainModelCaller

# 配置日志
logging.basicConfig(level=logging.INFO)

def debug_model_caller():
    """调试ModelCaller"""
    print("🔍 调试ModelCaller...")
    
    try:
        # 初始化ModelCaller
        from config.config_manager import ConfigManager
        config_manager = ConfigManager()
        model_caller = LangChainModelCaller(config_manager)
        
        print("✅ ModelCaller初始化成功")
        
        # 测试调用不存在的图片
        print("\n🔄 测试调用不存在的图片...")
        result = model_caller.call_image_embedding('/fake/path/test.jpg')
        
        print(f"📊 返回结果类型: {type(result)}")
        print(f"📊 返回结果内容: {result}")
        
        if isinstance(result, dict):
            print(f"📊 success字段: {result.get('success')}")
            print(f"📊 error字段: {result.get('error')}")
        else:
            print(f"❌ 返回结果不是字典类型")
            
    except Exception as e:
        print(f"❌ 调试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_model_caller()
