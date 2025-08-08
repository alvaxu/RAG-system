"""
图像增强功能测试脚本
"""

import os
import sys
import json
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_config_loading():
    """测试配置加载功能"""
    print("🔍 测试配置加载功能")
    
    try:
        if not os.path.exists("config.json"):
            print("❌ config.json文件不存在")
            return False
        
        with open("config.json", 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        if 'image_processing' not in config_data:
            print("❌ 缺少image_processing配置项")
            return False
        
        image_config = config_data['image_processing']
        print("✅ 配置加载成功")
        print(f"  - 增强功能启用: {image_config.get('enable_enhancement')}")
        print(f"  - 模型: {image_config.get('enhancement_model')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_image_enhancer():
    """测试ImageEnhancer"""
    print("\n🔍 测试ImageEnhancer")
    
    try:
        from document_processing.image_enhancer import ImageEnhancer
        from config.settings import Settings
        
        settings = Settings.load_from_file("config.json")
        api_key = settings.dashscope_api_key
        image_config = getattr(settings, 'image_processing', {})
        
        enhancer = ImageEnhancer(api_key, image_config)
        print("✅ ImageEnhancer初始化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ ImageEnhancer测试失败: {e}")
        return False

def test_image_processor():
    """测试ImageProcessor集成"""
    print("\n🔍 测试ImageProcessor集成")
    
    try:
        from document_processing.image_processor import ImageProcessor
        from config.settings import Settings
        
        settings = Settings.load_from_file("config.json")
        api_key = settings.dashscope_api_key
        
        processor = ImageProcessor(api_key)
        print("✅ ImageProcessor初始化成功")
        print(f"  - 增强功能启用: {processor.enhancement_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ ImageProcessor测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始图像增强功能测试")
    print("=" * 60)
    
    results = []
    results.append(("配置加载", test_config_loading()))
    results.append(("ImageEnhancer", test_image_enhancer()))
    results.append(("ImageProcessor", test_image_processor()))
    
    print("\n📊 测试结果:")
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 {passed}/{len(results)} 测试通过")
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
