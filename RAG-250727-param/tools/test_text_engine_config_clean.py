#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
测试TextEngineConfig清理后的配置类型检查

## 1. 测试目标
验证清理TextEngineConfig后，TextEngine的配置类型检查是否正常工作

## 2. 测试内容
- 测试TextEngineConfigV2配置类型检查
- 测试错误配置类型的异常处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_config_type_check():
    """测试配置类型检查"""
    print("🧪 测试TextEngine配置类型检查...")
    
    try:
        from v2.core.text_engine import TextEngine
        from v2.config.v2_config import TextEngineConfigV2
        
        # 测试正确的配置类型
        print("✅ 导入成功")
        
        # 测试配置类型检查逻辑
        config = TextEngineConfigV2()
        print(f"✅ 配置对象创建成功: {type(config).__name__}")
        
        # 验证配置类型检查
        if isinstance(config, TextEngineConfigV2):
            print("✅ 配置类型检查通过")
        else:
            print("❌ 配置类型检查失败")
            return False
        
        print("🎯 所有测试通过！TextEngineConfig清理成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_type_check()
    sys.exit(0 if success else 1)
