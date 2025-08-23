#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试V501_incremental_processor的图片增强功能
## 2. 验证配置是否正确传递
"""

import sys
import os
from pathlib import Path

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V501_incremental_processor import IncrementalDocumentProcessor

def test_incremental_processor():
    """测试增量处理器"""
    print("🔍 测试V501_incremental_processor的图片增强功能")
    print("=" * 60)
    
    try:
        # 1. 创建增量处理器
        print("1. 创建增量处理器...")
        processor = IncrementalDocumentProcessor('config.json')
        print(f"   ✅ 增量处理器创建成功")
        
        # 2. 检查配置
        print("\n2. 检查配置...")
        print(f"   enable_enhancement: {processor.config.enable_enhancement}")
        print(f"   enable_enhanced_description_vectorization: {processor.config.enable_enhanced_description_vectorization}")
        
        # 3. 检查pipeline配置
        print("\n3. 检查pipeline配置...")
        pipeline = processor.pipeline
        print(f"   ✅ pipeline已初始化")
        
        # 4. 检查vector_generator配置
        print("\n4. 检查vector_generator配置...")
        vector_gen = pipeline.vector_generator
        print(f"   ✅ vector_generator已初始化")
        
        # 5. 检查ImageProcessor配置
        print("\n5. 检查ImageProcessor配置...")
        if vector_gen.image_processor:
            print(f"   ✅ ImageProcessor已初始化")
            print(f"   enhancement_enabled: {vector_gen.image_processor.enhancement_enabled}")
            print(f"   enhancement_config: {vector_gen.image_processor.enhancement_config}")
            
            # 检查是否有image_enhancer
            if hasattr(vector_gen.image_processor, 'image_enhancer'):
                print(f"   ✅ image_enhancer已初始化")
            else:
                print(f"   ❌ image_enhancer未初始化")
        else:
            print(f"   ❌ ImageProcessor未初始化")
        
        # 6. 检查配置传递路径
        print("\n6. 检查配置传递路径...")
        config_dict = processor.config.to_dict()
        print(f"   config.to_dict()包含image_processing: {'image_processing' in config_dict}")
        if 'image_processing' in config_dict:
            img_config = config_dict['image_processing']
            print(f"   enable_enhancement: {img_config.get('enable_enhancement')}")
            print(f"   enable_enhanced_description_vectorization: {img_config.get('enable_enhanced_description_vectorization')}")
        
        print("\n" + "=" * 60)
        print("✅ 增量处理器测试完成")
        
        # 7. 总结
        print("\n📋 总结:")
        if vector_gen.image_processor and vector_gen.image_processor.enhancement_enabled:
            print("   ✅ 图片增强功能已启用")
        else:
            print("   ❌ 图片增强功能未启用")
            
        if vector_gen.image_processor and hasattr(vector_gen.image_processor, 'image_enhancer'):
            print("   ✅ 图像增强器已初始化")
        else:
            print("   ❌ 图像增强器未初始化")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_incremental_processor()
