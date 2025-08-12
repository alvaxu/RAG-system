#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API密钥管理器调试脚本
用于测试API密钥是否正确获取
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.api_key_manager import APIKeyManager, get_dashscope_api_key

def test_api_key_manager():
    """测试API密钥管理器"""
    print("🔍 测试API密钥管理器...")
    
    # 检查环境变量
    print(f"\n📋 环境变量检查:")
    print(f"  MY_DASHSCOPE_API_KEY: {'已设置' if os.getenv('MY_DASHSCOPE_API_KEY') else '未设置'}")
    if os.getenv('MY_DASHSCOPE_API_KEY'):
        key = os.getenv('MY_DASHSCOPE_API_KEY')
        print(f"  值: {key[:10]}...{key[-10:] if len(key) > 20 else ''}")
    
    # 测试APIKeyManager类方法
    print(f"\n🔧 测试APIKeyManager类方法:")
    api_key_manager = APIKeyManager()
    
    # 测试get_dashscope_api_key()
    dashscope_key = api_key_manager.get_dashscope_api_key()
    print(f"  get_dashscope_api_key(): {'✅ 成功' if dashscope_key else '❌ 失败'}")
    if dashscope_key:
        print(f"  密钥长度: {len(dashscope_key)}")
        print(f"  密钥前10位: {dashscope_key[:10]}...")
    else:
        print("  未获取到API密钥")
    
    # 测试便捷函数
    print(f"\n🚀 测试便捷函数:")
    dashscope_key_func = get_dashscope_api_key()
    print(f"  get_dashscope_api_key(): {'✅ 成功' if dashscope_key_func else '❌ 失败'}")
    if dashscope_key_func:
        print(f"  密钥长度: {len(dashscope_key_func)}")
        print(f"  密钥前10位: {dashscope_key_func[:10]}...")
    
    # 测试验证方法
    print(f"\n✅ 测试验证方法:")
    is_valid = APIKeyManager.validate_dashscope_key(dashscope_key)
    print(f"  validate_dashscope_key(): {'✅ 有效' if is_valid else '❌ 无效'}")
    
    # 测试状态获取
    print(f"\n📊 测试状态获取:")
    status = APIKeyManager.get_api_keys_status()
    print(f"  DashScope状态: {status['dashscope']}")
    print(f"  MinerU状态: {status['mineru']}")
    
    return dashscope_key

if __name__ == "__main__":
    print("🚀 开始API密钥管理器调试...")
    api_key = test_api_key_manager()
    
    if api_key:
        print(f"\n🎉 API密钥获取成功！")
        print(f"密钥长度: {len(api_key)}")
    else:
        print(f"\n❌ API密钥获取失败！")
        print("请检查:")
        print("1. 环境变量 MY_DASHSCOPE_API_KEY 是否设置")
        print("2. 环境变量值是否有效")
        print("3. 配置文件 config.json 中的 dashscope_api_key 是否设置")
