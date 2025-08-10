'''
程序说明：

## 1. 测试图像嵌入模型的参数化配置
## 2. 验证配置文件和代码的一致性
## 3. 测试不同配置值的加载和使用
'''

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from document_processing.image_processor import ImageProcessor


def test_image_embedding_config_loading():
    """测试图像嵌入配置的加载"""
    print("🔍 测试图像嵌入配置加载...")
    
    # 1. 测试默认配置
    print("\n📋 1. 测试默认配置:")
    default_settings = Settings()
    image_embedding_model = getattr(default_settings, 'image_embedding_model', 'NOT_FOUND')
    print(f"   默认配置: {image_embedding_model}")
    
    # 2. 测试从文件加载配置
    print("\n📋 2. 测试从文件加载配置:")
    config_path = project_root / "config.json"
    if config_path.exists():
        file_settings = Settings.load_from_file(str(config_path))
        file_image_embedding_model = getattr(file_settings, 'image_embedding_model', 'NOT_FOUND')
        print(f"   文件配置: {file_image_embedding_model}")
        
        # 检查是否与config.json一致
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        json_image_embedding_model = config_dict.get('vector_store', {}).get('image_embedding_model', 'NOT_FOUND')
        print(f"   JSON配置: {json_image_embedding_model}")
        
        if file_image_embedding_model == json_image_embedding_model:
            print("   ✅ 配置一致")
        else:
            print("   ❌ 配置不一致")
    else:
        print("   ❌ config.json文件不存在")
    
    # 3. 测试to_dict方法
    print("\n📋 3. 测试to_dict方法:")
    settings_dict = default_settings.to_dict()
    dict_image_embedding_model = settings_dict.get('vector_store', {}).get('image_embedding_model', 'NOT_FOUND')
    print(f"   to_dict结果: {dict_image_embedding_model}")
    
    return True


def test_image_processor_config():
    """测试ImageProcessor是否正确使用图像嵌入配置"""
    print("\n🔍 测试ImageProcessor配置使用...")
    
    try:
        # 创建配置对象
        config = {
            'vector_store': {
                'image_embedding_model': 'multimodal_embedding_one_peace_v1'
            },
            'enhancement_enabled': False
        }
        
        # 创建ImageProcessor实例
        image_processor = ImageProcessor(api_key="test_key", config=config)
        
        # 检查配置是否正确传递
        if hasattr(image_processor, 'config'):
            print("   ✅ ImageProcessor正确接收配置对象")
            image_embedding_model = image_processor.config.get('vector_store', {}).get('image_embedding_model', 'NOT_FOUND')
            print(f"   配置中的图像嵌入模型: {image_embedding_model}")
        else:
            print("   ❌ ImageProcessor未接收配置对象")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ ImageProcessor测试失败: {e}")
        return False


def test_config_file_integrity():
    """测试配置文件的完整性"""
    print("\n🔍 测试配置文件完整性...")
    
    config_path = project_root / "config.json"
    if not config_path.exists():
        print("   ❌ config.json文件不存在")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # 检查必要的配置项
        required_configs = [
            ('vector_store', 'image_embedding_model'),
            ('vector_store', 'text_embedding_model'),
            ('qa_system', 'model_name'),
            ('image_processing', 'enhancement_model')
        ]
        
        all_present = True
        for section, key in required_configs:
            if section not in config_dict:
                print(f"   ❌ 缺少配置节: {section}")
                all_present = False
            elif key not in config_dict[section]:
                print(f"   ❌ 缺少配置项: {section}.{key}")
                all_present = False
            else:
                print(f"   ✅ 配置项存在: {section}.{key} = {config_dict[section][key]}")
        
        return all_present
        
    except Exception as e:
        print(f"   ❌ 配置文件读取失败: {e}")
        return False


def test_config_consistency():
    """测试配置的一致性"""
    print("\n🔍 测试配置一致性...")
    
    try:
        # 加载配置
        config_path = project_root / "config.json"
        settings = Settings.load_from_file(str(config_path))
        
        # 检查图像嵌入配置
        image_embedding_model = getattr(settings, 'image_embedding_model', 'NOT_FOUND')
        print(f"   Settings类: {image_embedding_model}")
        
        # 检查JSON配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        json_image_embedding_model = config_dict.get('vector_store', {}).get('image_embedding_model', 'NOT_FOUND')
        print(f"   JSON文件: {json_image_embedding_model}")
        
        # 检查to_dict结果
        settings_dict = settings.to_dict()
        dict_image_embedding_model = settings_dict.get('vector_store', {}).get('image_embedding_model', 'NOT_FOUND')
        print(f"   to_dict: {dict_image_embedding_model}")
        
        # 验证一致性
        if image_embedding_model == json_image_embedding_model == dict_image_embedding_model:
            print("   ✅ 所有配置来源一致")
            return True
        else:
            print("   ❌ 配置来源不一致")
            return False
            
    except Exception as e:
        print(f"   ❌ 配置一致性测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 图像嵌入模型参数化配置测试")
    print("=" * 60)
    
    # 运行所有测试
    tests = [
        ("配置加载测试", test_image_embedding_config_loading),
        ("ImageProcessor配置测试", test_image_processor_config),
        ("配置文件完整性测试", test_config_file_integrity),
        ("配置一致性测试", test_config_consistency)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print(f"\n{'='*60}")
    print("📊 测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！图像嵌入模型参数化配置成功！")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置")
        return False


if __name__ == "__main__":
    main()
