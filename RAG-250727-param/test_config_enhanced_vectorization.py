#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试enhanced_description_vectorization配置项是否正确加载
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from config.settings import Settings
    print("✅ 成功导入Settings类")
except ImportError as e:
    print(f"❌ 导入Settings类失败: {e}")
    sys.exit(1)

def test_config_loading():
    """测试配置加载"""
    print("\n🔍 测试配置加载...")
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        print("✅ 成功加载config.json")
        
        # 检查新字段
        print(f"\n📊 配置字段检查:")
        print(f"   enable_enhancement: {config.enable_enhancement}")
        print(f"   enable_enhanced_description_vectorization: {config.enable_enhanced_description_vectorization}")
        print(f"   enhancement_model: {config.enhancement_model}")
        
        # 转换为字典并检查
        config_dict = config.to_dict()
        if 'image_processing' in config_dict:
            image_config = config_dict['image_processing']
            print(f"\n🔧 图像处理配置:")
            for key, value in image_config.items():
                print(f"   {key}: {value}")
        
        # 验证新字段是否正确加载
        if hasattr(config, 'enable_enhanced_description_vectorization'):
            print(f"\n✅ 新字段enable_enhanced_description_vectorization已正确加载")
            print(f"   值: {config.enable_enhanced_description_vectorization}")
        else:
            print(f"\n❌ 新字段enable_enhanced_description_vectorization未找到")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_saving():
    """测试配置保存"""
    print("\n💾 测试配置保存...")
    
    try:
        # 创建新配置
        config = Settings()
        config.enable_enhancement = True
        config.enable_enhanced_description_vectorization = True
        config.enhancement_model = 'qwen-vl-plus'
        
        # 保存到临时文件
        temp_file = 'test_config_temp.json'
        config.save_to_file(temp_file)
        print(f"✅ 配置已保存到临时文件: {temp_file}")
        
        # 重新加载验证
        loaded_config = Settings.load_from_file(temp_file)
        print(f"✅ 重新加载配置成功")
        print(f"   enable_enhanced_description_vectorization: {loaded_config.enable_enhanced_description_vectorization}")
        
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"🧹 临时文件已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置保存测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始测试enhanced_description_vectorization配置项")
    print("="*60)
    
    # 测试配置加载
    load_success = test_config_loading()
    
    # 测试配置保存
    save_success = test_config_saving()
    
    print("\n" + "="*60)
    if load_success and save_success:
        print("🎉 所有测试通过！enhanced_description_vectorization配置项工作正常")
    else:
        print("❌ 部分测试失败，请检查配置")
