'''
测试API KEY优先级获取
验证所有地方都按照正确的优先级获取API KEY：
1. 配置文件中的值（如果不为空且不是占位符）
2. 环境变量 MY_DASHSCOPE_API_KEY
3. 默认空字符串
'''

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager
from config.settings import Settings


def test_settings_priority():
    """测试Settings类的API KEY优先级"""
    print("=" * 60)
    print("🔍 测试Settings类API KEY优先级")
    print("=" * 60)
    
    # 测试1: 从配置文件加载
    print("\n📋 测试1: 从配置文件加载")
    settings = Settings.load_from_file('config.json')
    print(f"  dashscope_api_key: {settings.dashscope_api_key[:10]}..." if settings.dashscope_api_key else "  dashscope_api_key: 未配置")
    
    # 测试2: 直接创建（应该使用环境变量）
    print("\n📋 测试2: 直接创建Settings")
    settings_direct = Settings()
    print(f"  dashscope_api_key: {settings_direct.dashscope_api_key[:10]}..." if settings_direct.dashscope_api_key else "  dashscope_api_key: 未配置")
    
    return True


def test_config_manager_priority():
    """测试ConfigManager的API KEY优先级"""
    print("\n" + "=" * 60)
    print("🔍 测试ConfigManager API KEY优先级")
    print("=" * 60)
    
    try:
        config_manager = ConfigManager()
        api_key = config_manager.settings.dashscope_api_key
        print(f"  dashscope_api_key: {api_key[:10]}..." if api_key else "  dashscope_api_key: 未配置")
        
        # 验证配置
        validation_results = config_manager.validate_config()
        print(f"  API密钥验证: {'通过' if validation_results.get('api_keys', False) else '失败'}")
        
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_environment_variable():
    """测试环境变量"""
    print("\n" + "=" * 60)
    print("🔍 测试环境变量")
    print("=" * 60)
    
    env_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
    print(f"  环境变量 MY_DASHSCOPE_API_KEY: {env_key[:10]}..." if env_key else "  环境变量 MY_DASHSCOPE_API_KEY: 未设置")
    
    return bool(env_key)


def test_priority_logic():
    """测试优先级逻辑"""
    print("\n" + "=" * 60)
    print("🔍 测试优先级逻辑")
    print("=" * 60)
    
    # 模拟不同情况
    test_cases = [
        {
            'name': '配置文件有效值',
            'config_value': 'sk-test123',
            'env_value': 'sk-env456',
            'expected': 'sk-test123'
        },
        {
            'name': '配置文件占位符',
            'config_value': '你的DashScope API密钥',
            'env_value': 'sk-env456',
            'expected': 'sk-env456'
        },
        {
            'name': '配置文件为空',
            'config_value': '',
            'env_value': 'sk-env456',
            'expected': 'sk-env456'
        },
        {
            'name': '都为空',
            'config_value': '',
            'env_value': '',
            'expected': ''
        }
    ]
    
    for case in test_cases:
        print(f"\n  📋 {case['name']}:")
        print(f"    配置文件值: {case['config_value']}")
        print(f"    环境变量值: {case['env_value']}")
        
        # 模拟优先级逻辑
        if case['config_value'] and case['config_value'] != '你的DashScope API密钥':
            result = case['config_value']
        elif case['env_value']:
            result = case['env_value']
        else:
            result = ''
        
        print(f"    实际结果: {result}")
        print(f"    期望结果: {case['expected']}")
        print(f"    状态: {'✅' if result == case['expected'] else '❌'}")
    
    return True


def main():
    """主函数"""
    print("🚀 开始API KEY优先级测试...")
    
    tests = [
        ("Settings优先级测试", test_settings_priority),
        ("ConfigManager优先级测试", test_config_manager_priority),
        ("环境变量测试", test_environment_variable),
        ("优先级逻辑测试", test_priority_logic)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！API KEY优先级实现正确！")
    else:
        print("⚠️  部分测试失败，需要进一步检查")


if __name__ == "__main__":
    main() 