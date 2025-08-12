#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：

## 1. API密钥管理模块测试工具
## 2. 验证配置文件和环境变量的优先级
## 3. 测试各种配置场景
## 4. 简单直接的API密钥可用性测试
## 5. 作为tools目录下的测试工具
'''

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.api_key_manager import APIKeyManager, get_dashscope_api_key, get_mineru_api_key


def simple_api_key_test():
    """简单直接的API密钥可用性测试"""
    print("🔍 简单直接的API密钥可用性测试")
    print("=" * 50)

    # 1. 直接检查环境变量
    print("\n1. 环境变量检查:")
    dashscope_env = os.getenv('MY_DASHSCOPE_API_KEY', '')
    mineru_env = os.getenv('MINERU_API_KEY', '')

    print(f"MY_DASHSCOPE_API_KEY: {'✅ 已设置' if dashscope_env else '❌ 未设置'}")
    if dashscope_env:
        print(f"  值: {dashscope_env[:10]}...{dashscope_env[-4:]}")

    print(f"MINERU_API_KEY: {'✅ 已设置' if mineru_env else '❌ 未设置'}")
    if mineru_env:
        print(f"  值: {mineru_env[:10]}...{mineru_env[-4:]}")

    # 2. 测试我们的API密钥管理模块
    print("\n2. API密钥管理模块测试:")
    try:
        # 测试空配置时是否能从环境变量获取
        dashscope_key = get_dashscope_api_key("")
        mineru_key = get_mineru_api_key("")
        
        print(f"DashScope API密钥: {'✅ 已获取' if dashscope_key else '❌ 未获取'}")
        if dashscope_key:
            print(f"  值: {dashscope_key[:10]}...{dashscope_key[-4:]}")
        
        print(f"minerU API密钥: {'✅ 已获取' if mineru_key else '❌ 未获取'}")
        if mineru_key:
            print(f"  值: {mineru_key[:10]}...{mineru_key[-4:]}")
            
    except Exception as e:
        print(f"❌ API密钥管理模块测试失败: {e}")

    # 3. 测试Settings类
    print("\n3. Settings类测试:")
    try:
        from config.settings import Settings
        
        settings = Settings.load_from_file('config.json')
        print(f"配置文件中的dashscope_api_key: '{settings.dashscope_api_key}'")
        print(f"配置文件中的mineru_api_key: '{settings.mineru_api_key}'")
        
        if settings.dashscope_api_key:
            print("✅ Settings类成功加载了DashScope API密钥")
        else:
            print("❌ Settings类没有加载到DashScope API密钥")
            
        if settings.mineru_api_key:
            print("✅ Settings类成功加载了minerU API密钥")
        else:
            print("❌ Settings类没有加载到minerU API密钥")
            
    except Exception as e:
        print(f"❌ Settings类测试失败: {e}")

    print("\n" + "=" * 50)
    print("简单测试完成！")


def test_api_key_manager():
    """测试API密钥管理模块"""
    print("🔑 测试API密钥管理模块")
    print("=" * 60)
    
    # 测试1：空配置，环境变量未设置
    print("\n📋 测试1：空配置，环境变量未设置")
    print("-" * 40)
    
    # 临时清除环境变量
    old_dashscope_env = os.environ.pop('MY_DASHSCOPE_API_KEY', None)
    old_mineru_env = os.environ.pop('MINERU_API_KEY', None)
    
    try:
        dashscope_key = get_dashscope_api_key("")
        mineru_key = get_mineru_api_key("")
        
        print(f"DashScope API密钥: {'✅ 已获取' if dashscope_key else '❌ 未获取'}")
        print(f"minerU API密钥: {'✅ 已获取' if mineru_key else '❌ 未获取'}")
        
        if not dashscope_key and not mineru_key:
            print("✅ 测试通过：空配置时正确返回空字符串")
        else:
            print("❌ 测试失败：空配置时应该返回空字符串")
    
    finally:
        # 恢复环境变量
        if old_dashscope_env:
            os.environ['MY_DASHSCOPE_API_KEY'] = old_dashscope_env
        if old_mineru_env:
            os.environ['MINERU_API_KEY'] = old_mineru_env
    
    # 测试2：占位符配置，环境变量未设置
    print("\n📋 测试2：占位符配置，环境变量未设置")
    print("-" * 40)
    
    # 确保环境变量被清除
    os.environ.pop('MY_DASHSCOPE_API_KEY', None)
    os.environ.pop('MINERU_API_KEY', None)
    
    dashscope_key = get_dashscope_api_key("你的DashScope API密钥")
    mineru_key = get_mineru_api_key("你的minerU API密钥")
    
    print(f"DashScope API密钥: {'✅ 已获取' if dashscope_key else '❌ 未获取'}")
    print(f"minerU API密钥: {'✅ 已获取' if mineru_key else '❌ 未获取'}")
    
    if not dashscope_key and not mineru_key:
        print("✅ 测试通过：占位符配置时正确返回空字符串")
    else:
        print("❌ 测试失败：占位符配置时应该返回空字符串")
    
    # 测试3：有效配置
    print("\n📋 测试3：有效配置")
    print("-" * 40)
    
    test_dashscope_key = "test_dashscope_key_12345"
    test_mineru_key = "test_mineru_key_67890"
    
    dashscope_key = get_dashscope_api_key(test_dashscope_key)
    mineru_key = get_mineru_api_key(test_mineru_key)
    
    print(f"DashScope API密钥: {'✅ 已获取' if dashscope_key else '❌ 未获取'}")
    print(f"minerU API密钥: {'✅ 已获取' if mineru_key else '❌ 未获取'}")
    
    if dashscope_key == test_dashscope_key and mineru_key == test_mineru_key:
        print("✅ 测试通过：有效配置时正确返回配置值")
    else:
        print("❌ 测试失败：有效配置时应该返回配置值")
    
    # 测试4：环境变量优先级
    print("\n📋 测试4：环境变量优先级")
    print("-" * 40)
    
    # 设置环境变量
    os.environ['MY_DASHSCOPE_API_KEY'] = 'env_dashscope_key_12345'
    os.environ['MINERU_API_KEY'] = 'env_mineru_key_67890'
    
    try:
        # 空配置，应该从环境变量获取
        dashscope_key = get_dashscope_api_key("")
        mineru_key = get_mineru_api_key("")
        
        print(f"DashScope API密钥: {'✅ 已获取' if dashscope_key else '❌ 未获取'}")
        print(f"minerU API密钥: {'✅ 已获取' if mineru_key else '❌ 未获取'}")
        
        if dashscope_key == 'env_dashscope_key_12345' and mineru_key == 'env_mineru_key_67890':
            print("✅ 测试通过：环境变量优先级正确")
        else:
            print("❌ 测试失败：环境变量优先级不正确")
    
    finally:
        # 清除环境变量
        os.environ.pop('MY_DASHSCOPE_API_KEY', None)
        os.environ.pop('MINERU_API_KEY', None)
    
    # 测试5：API密钥管理器类方法
    print("\n📋 测试5：API密钥管理器类方法")
    print("-" * 40)
    
    # 测试一次性获取所有API密钥
    dashscope_key, mineru_key = APIKeyManager.get_all_api_keys("", "")
    print(f"一次性获取 - DashScope: {'✅ 已获取' if dashscope_key else '❌ 未获取'}")
    print(f"一次性获取 - minerU: {'✅ 已获取' if mineru_key else '❌ 未获取'}")
    
    # 测试状态获取
    status = APIKeyManager.get_api_keys_status("", "")
    print(f"状态信息: {status}")
    
    print("\n🎉 所有测试完成！")


def test_real_config():
    """测试真实配置文件"""
    print("\n🔍 测试真实配置文件")
    print("=" * 60)
    
    try:
        from config.settings import Settings
        
        # 加载配置文件
        settings = Settings.load_from_file('config.json')
        
        print(f"配置文件路径: config.json")
        print(f"DashScope API密钥配置: {'已设置' if settings.dashscope_api_key else '未设置'}")
        print(f"minerU API密钥配置: {'已设置' if settings.mineru_api_key else '未设置'}")
        
        # 显示Settings对象的实际值
        print(f"\nSettings对象中的实际值:")
        print(f"  dashscope_api_key: '{settings.dashscope_api_key}'")
        print(f"  mineru_api_key: '{settings.mineru_api_key}'")
        
        # 检查环境变量
        env_dashscope = os.getenv('MY_DASHSCOPE_API_KEY', '')
        env_mineru = os.getenv('MINERU_API_KEY', '')
        print(f"\n环境变量中的值:")
        print(f"  MY_DASHSCOPE_API_KEY: {'已设置' if env_dashscope else '未设置'}")
        print(f"  MINERU_API_KEY: {'已设置' if env_mineru else '未设置'}")
        
        # 使用API密钥管理器获取
        dashscope_key = get_dashscope_api_key(settings.dashscope_api_key)
        mineru_key = get_mineru_api_key(settings.mineru_api_key)
        
        print(f"\n实际获取结果:")
        print(f"DashScope API密钥: {'✅ 已获取' if dashscope_key else '❌ 未获取'}")
        print(f"minerU API密钥: {'✅ 已获取' if mineru_key else '❌ 未获取'}")
        
        # 显示来源信息
        status = APIKeyManager.get_api_keys_status(settings.dashscope_api_key, settings.mineru_api_key)
        print(f"\n来源信息:")
        print(f"DashScope: {status['dashscope']['source']}")
        print(f"minerU: {status['mineru']['source']}")
        
    except Exception as e:
        print(f"❌ 测试真实配置失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🚀 API密钥管理模块测试工具")
    print("=" * 80)
    
    print("\n选择测试模式:")
    print("1. 简单测试 - 快速检查API密钥是否可用")
    print("2. 完整测试 - 详细的模块功能测试")
    print("3. 真实配置测试 - 检查实际配置文件")
    print("4. 全部测试 - 运行所有测试")
    
    try:
        choice = input("\n请输入选择 (1-4，默认1): ").strip()
        if not choice:
            choice = "1"
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
        return
    
    print("\n" + "=" * 80)
    
    if choice == "1":
        simple_api_key_test()
    elif choice == "2":
        test_api_key_manager()
    elif choice == "3":
        test_real_config()
    elif choice == "4":
        simple_api_key_test()
        test_api_key_manager()
        test_real_config()
    else:
        print("❌ 无效选择，运行简单测试")
        simple_api_key_test()
    
    print("\n" + "=" * 80)
    print("🎯 测试完成！")
    print("\n使用说明:")
    print("1. 简单测试：快速检查API密钥是否可用")
    print("2. 完整测试：验证配置文件和环境变量的优先级")
    print("3. 真实配置测试：检查实际配置文件的状态")
    print("4. 建议在修改API密钥相关代码后运行此测试")


if __name__ == "__main__":
    main()
