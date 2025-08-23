#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试配置传递是否正确
## 2. 验证图片增强和向量化参数是否生效
"""

import sys
import os
from pathlib import Path

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from document_processing.vector_generator import VectorGenerator
from document_processing.image_processor import ImageProcessor

def test_config_passing():
    """测试配置传递"""
    print("🔍 测试配置传递是否正确")
    print("=" * 60)
    
    try:
        # 1. 加载配置
        print("1. 加载配置文件...")
        config = Settings.load_from_file('config.json')
        print(f"   ✅ 配置加载成功")
        
        # 2. 检查配置值
        print("\n2. 检查配置值...")
        print(f"   enable_enhancement: {config.enable_enhancement}")
        print(f"   enable_enhanced_description_vectorization: {config.enable_enhanced_description_vectorization}")
        
        # 3. 转换为字典
        print("\n3. 转换为字典...")
        config_dict = config.to_dict()
        print(f"   image_processing.enable_enhancement: {config_dict.get('image_processing', {}).get('enable_enhancement')}")
        print(f"   image_processing.enable_enhanced_description_vectorization: {config_dict.get('image_processing', {}).get('enable_enhanced_description_vectorization')}")
        
        # 4. 测试VectorGenerator初始化
        print("\n4. 测试VectorGenerator初始化...")
        vector_gen = VectorGenerator(config_dict)
        print(f"   ✅ VectorGenerator初始化成功")
        
        # 5. 检查ImageProcessor配置
        print("\n5. 检查ImageProcessor配置...")
        if vector_gen.image_processor:
            print(f"   ✅ ImageProcessor已初始化")
            print(f"   enhancement_enabled: {vector_gen.image_processor.enhancement_enabled}")
            print(f"   enhancement_config: {vector_gen.image_processor.enhancement_config}")
        else:
            print(f"   ❌ ImageProcessor未初始化")
        
        # 6. 测试ImageProcessor直接初始化
        print("\n6. 测试ImageProcessor直接初始化...")
        image_proc = ImageProcessor("test_key", config_dict)
        print(f"   ✅ ImageProcessor直接初始化成功")
        print(f"   enhancement_enabled: {image_proc.enhancement_enabled}")
        print(f"   enhancement_config: {image_proc.enhancement_config}")
        
        # 7. 测试Settings对象传递
        print("\n7. 测试Settings对象传递...")
        image_proc2 = ImageProcessor("test_key", config)
        print(f"   ✅ ImageProcessor with Settings对象初始化成功")
        print(f"   enhancement_enabled: {image_proc2.enhancement_enabled}")
        print(f"   enhancement_config: {image_proc2.enhancement_config}")
        
        print("\n" + "=" * 60)
        print("✅ 配置传递测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config_passing()
