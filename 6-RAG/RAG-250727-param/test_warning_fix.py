'''
程序说明：
## 1. 测试警告修复
## 2. 验证API密钥配置是否正确识别
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings

def test_settings_warning():
    """测试Settings警告修复"""
    print("=" * 60)
    print("🔍 测试Settings警告修复")
    print("=" * 60)
    
    try:
        # 测试从配置文件加载
        settings = Settings.load_from_file('config.json')
        print("✅ 成功从config.json加载配置")
        print(f"  DashScope API Key: {settings.dashscope_api_key[:20]}...")
        print(f"  minerU API Key: {settings.mineru_api_key[:20]}...")
        
        # 检查是否还有警告
        print("\n📋 检查警告状态:")
        if settings.dashscope_api_key and settings.dashscope_api_key not in ['你的APIKEY', '你的DashScope API密钥']:
            print("  ✅ DashScope API密钥已正确配置")
        else:
            print("  ❌ DashScope API密钥未配置")
        
        if settings.mineru_api_key and settings.mineru_api_key != '你的minerU API密钥':
            print("  ✅ minerU API密钥已正确配置")
        else:
            print("  ❌ minerU API密钥未配置")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_settings_warning() 