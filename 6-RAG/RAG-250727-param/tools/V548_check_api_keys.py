'''
程序说明：
## 1. 检查API KEY配置
## 2. 验证配置加载是否正确
## 3. 调试API KEY问题
'''

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings


def check_api_keys():
    """检查API KEY配置"""
    print("=" * 60)
    print("🔍 检查API KEY配置")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        print("📋 配置信息:")
        print(f"  DashScope API KEY: {settings.dashscope_api_key}")
        print(f"  minerU API KEY: {settings.mineru_api_key}")
        
        # 检查环境变量
        env_dashscope = os.getenv('MY_DASHSCOPE_API_KEY', '')
        env_mineru = os.getenv('MINERU_API_KEY', '')
        
        print("\n🌍 环境变量:")
        print(f"  MY_DASHSCOPE_API_KEY: {env_dashscope}")
        print(f"  MINERU_API_KEY: {env_mineru}")
        
        # 检查配置文件
        with open('config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        print("\n📄 配置文件中的API KEY:")
        print(f"  dashscope_api_key: {config_data.get('api', {}).get('dashscope_api_key', '')}")
        print(f"  mineru_api_key: {config_data.get('api', {}).get('mineru_api_key', '')}")
        
        # 分析问题
        print("\n🔍 问题分析:")
        
        if not settings.dashscope_api_key:
            print("  ❌ DashScope API KEY为空")
        elif settings.dashscope_api_key in ['你的APIKEY', '你的DashScope API密钥']:
            print("  ❌ DashScope API KEY是占位符")
        else:
            print("  ✅ DashScope API KEY已配置")
        
        if not settings.mineru_api_key:
            print("  ❌ minerU API KEY为空")
        elif settings.mineru_api_key == '你的minerU API密钥':
            print("  ❌ minerU API KEY是占位符")
        else:
            print("  ✅ minerU API KEY已配置")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查API KEY失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始API KEY检查...")
    
    result = check_api_keys()
    
    if result:
        print("\n✅ API KEY检查完成")
    else:
        print("\n❌ API KEY检查失败")


if __name__ == "__main__":
    main() 