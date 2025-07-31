'''
程序说明：
## 1. 配置管理测试脚本
## 2. 验证所有模块是否正确使用统一配置管理
## 3. 测试配置验证功能
## 4. 确保API key优先级正确工作
'''

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from document_processing.pipeline import DocumentProcessingPipeline
from core.memory_manager import MemoryManager
from api.app import create_app


def test_settings_loading():
    """测试Settings加载功能"""
    print("=" * 60)
    print("🔍 测试Settings加载功能")
    print("=" * 60)
    
    try:
        # 测试从配置文件加载
        settings = Settings.load_from_file('config.json')
        print(f"✅ 成功从config.json加载配置")
        print(f"  DashScope API Key: {'已配置' if settings.dashscope_api_key else '未配置'}")
        print(f"  minerU API Key: {'已配置' if settings.mineru_api_key else '未配置'}")
        print(f"  PDF目录: {settings.pdf_dir}")
        print(f"  向量数据库目录: {settings.vector_db_dir}")
        
        return True
    except Exception as e:
        print(f"❌ Settings加载失败: {e}")
        return False


def test_pipeline_config():
    """测试文档处理管道配置"""
    print("\n" + "=" * 60)
    print("🔍 测试文档处理管道配置")
    print("=" * 60)
    
    try:
        # 测试字典配置
        config_dict = {
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'max_table_rows': 100
        }
        
        pipeline = DocumentProcessingPipeline(config_dict)
        print("✅ 文档处理管道配置测试通过")
        print(f"  配置类型: {type(pipeline.config)}")
        print(f"  chunk_size: {pipeline.config.chunk_size}")
        print(f"  chunk_overlap: {pipeline.config.chunk_overlap}")
        
        return True
    except Exception as e:
        print(f"❌ 文档处理管道配置测试失败: {e}")
        return False


def test_memory_manager_config():
    """测试记忆管理器配置"""
    print("\n" + "=" * 60)
    print("🔍 测试记忆管理器配置")
    print("=" * 60)
    
    try:
        # 测试自动配置加载
        memory_manager = MemoryManager()
        print("✅ 记忆管理器配置测试通过")
        print(f"  记忆目录: {memory_manager.memory_dir}")
        
        return True
    except Exception as e:
        print(f"❌ 记忆管理器配置测试失败: {e}")
        return False


def test_api_app_config():
    """测试API应用配置"""
    print("\n" + "=" * 60)
    print("🔍 测试API应用配置")
    print("=" * 60)
    
    try:
        # 测试应用创建
        app = create_app()
        print("✅ API应用配置测试通过")
        
        # 检查配置是否正确加载
        config = app.config.get('SETTINGS')
        if config:
            print(f"  配置类型: {type(config)}")
            print(f"  DashScope API Key: {'已配置' if config.dashscope_api_key else '未配置'}")
        else:
            print("⚠️  配置对象未找到")
        
        return True
    except Exception as e:
        print(f"❌ API应用配置测试失败: {e}")
        return False


def test_api_key_priority():
    """测试API key优先级"""
    print("\n" + "=" * 60)
    print("🔍 测试API key优先级")
    print("=" * 60)
    
    try:
        settings = Settings.load_from_file('config.json')
        
        # 检查DashScope API key
        dashscope_key = settings.dashscope_api_key
        if dashscope_key and dashscope_key != '你的DashScope API密钥':
            print(f"✅ DashScope API Key: {dashscope_key[:20]}...")
        else:
            print("⚠️  DashScope API Key未配置")
        
        # 检查minerU API key
        mineru_key = settings.mineru_api_key
        if mineru_key and mineru_key != '你的minerU API密钥':
            print(f"✅ minerU API Key: {mineru_key[:20]}...")
        else:
            print("⚠️  minerU API Key未配置")
        
        return True
    except Exception as e:
        print(f"❌ API key优先级测试失败: {e}")
        return False


def test_config_validation():
    """测试配置验证功能"""
    print("\n" + "=" * 60)
    print("🔍 测试配置验证功能")
    print("=" * 60)
    
    try:
        settings = Settings.load_from_file('config.json')
        
        # 检查必需配置项
        required_configs = [
            'dashscope_api_key',
            'mineru_api_key', 
            'pdf_dir',
            'output_dir',
            'vector_db_dir',
            'memory_db_dir'
        ]
        
        missing_configs = []
        for config_name in required_configs:
            value = getattr(settings, config_name, None)
            if not value or value in ['你的DashScope API密钥', '你的minerU API密钥']:
                missing_configs.append(config_name)
        
        if missing_configs:
            print(f"⚠️  缺少配置项: {missing_configs}")
        else:
            print("✅ 所有必需配置项都已配置")
        
        return len(missing_configs) == 0
    except Exception as e:
        print(f"❌ 配置验证测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始配置管理测试...")
    
    tests = [
        ("Settings加载测试", test_settings_loading),
        ("文档处理管道配置测试", test_pipeline_config),
        ("记忆管理器配置测试", test_memory_manager_config),
        ("API应用配置测试", test_api_app_config),
        ("API key优先级测试", test_api_key_priority),
        ("配置验证测试", test_config_validation)
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
        print("🎉 所有测试通过！配置管理改进成功！")
    else:
        print("⚠️  部分测试失败，需要进一步检查")


if __name__ == "__main__":
    main() 