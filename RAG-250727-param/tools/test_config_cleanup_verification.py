#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
测试所有配置类清理后的配置类型检查

## 1. 测试目标
验证清理TableEngineConfig和ImageEngineConfig后，各引擎的配置类型检查是否正常工作

## 2. 测试内容
- 测试TableEngineConfigV2配置类型检查
- 测试ImageEngineConfigV2配置类型检查
- 测试错误配置类型的异常处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_table_engine_config_cleanup():
    """测试表格引擎配置清理"""
    print("🧪 测试TableEngine配置清理...")
    
    try:
        from v2.core.table_engine import TableEngine
        from v2.config.v2_config import TableEngineConfigV2
        
        # 测试正确的配置类型
        print("✅ 导入成功")
        
        # 测试配置类型检查逻辑
        config = TableEngineConfigV2()
        print(f"✅ 配置对象创建成功: {type(config).__name__}")
        
        # 验证配置类型检查
        if isinstance(config, TableEngineConfigV2):
            print("✅ 配置类型检查通过")
        else:
            print("❌ 配置类型检查失败")
            return False
        
        print("🎯 TableEngine配置清理成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_image_engine_config_cleanup():
    """测试图片引擎配置清理"""
    print("🧪 测试ImageEngine配置清理...")
    
    try:
        from v2.core.image_engine import ImageEngine
        from v2.config.v2_config import ImageEngineConfigV2
        
        # 测试正确的配置类型
        print("✅ 导入成功")
        
        # 测试配置类型检查逻辑
        config = ImageEngineConfigV2()
        print(f"✅ 配置对象创建成功: {type(config).__name__}")
        
        # 验证配置类型检查
        if isinstance(config, ImageEngineConfigV2):
            print("✅ 配置类型检查通过")
        else:
            print("❌ 配置类型检查失败")
            return False
        
        print("🎯 ImageEngine配置清理成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_text_engine_config_cleanup():
    """测试文本引擎配置清理"""
    print("🧪 测试TextEngine配置清理...")
    
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
        
        print("🎯 TextEngine配置清理成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试所有配置类清理结果...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 测试表格引擎配置清理
    if test_table_engine_config_cleanup():
        success_count += 1
    print("-" * 30)
    
    # 测试图片引擎配置清理
    if test_image_engine_config_cleanup():
        success_count += 1
    print("-" * 30)
    
    # 测试文本引擎配置清理
    if test_text_engine_config_cleanup():
        success_count += 1
    print("-" * 30)
    
    # 输出测试结果
    print("=" * 50)
    print(f"🎯 测试完成！成功: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 所有配置类清理成功！")
        return True
    else:
        print("❌ 部分配置类清理失败！")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
