#!/usr/bin/env python3
"""
测试图片补做程序

功能：
1. 测试ImageCompletion类的初始化
2. 测试向量数据库连接
3. 测试未完成图片查询
4. 测试智能检测逻辑
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.image_completion import ImageCompletion

def test_image_completion():
    """测试图片补做程序"""
    print("🧪 开始测试图片补做程序")
    print("="*50)
    
    try:
        # 1. 测试初始化
        print("1️⃣ 测试初始化...")
        completion = ImageCompletion()
        print("✅ 初始化成功")
        
        # 2. 测试向量数据库连接
        print("\n2️⃣ 测试向量数据库连接...")
        if completion.vector_store_manager.load():
            print("✅ 向量数据库连接成功")
            
            # 3. 测试状态获取
            print("\n3️⃣ 测试状态获取...")
            status = completion.vector_store_manager.get_status()
            print(f"   数据库状态: {status}")
            
            # 4. 测试未完成图片查询
            print("\n4️⃣ 测试未完成图片查询...")
            unfinished_images = completion.vector_store_manager.get_unfinished_images()
            print(f"   发现未完成图片: {len(unfinished_images)} 张")
            
            if unfinished_images:
                print("   前3张图片信息:")
                for i, img in enumerate(unfinished_images[:3]):
                    print(f"     {i+1}. {img['image_id']} - {img['document_name']}")
                    print(f"        路径: {img['image_path']}")
                    print(f"        需要增强: {img['needs_enhancement']}")
                    print(f"        需要向量化: {img['needs_vectorization']}")
            
            # 5. 测试智能检测逻辑
            print("\n5️⃣ 测试智能检测逻辑...")
            if unfinished_images:
                test_image = unfinished_images[0]
                needs_vectorization = completion._should_revectorize(test_image)
                print(f"   测试图片 {test_image['image_id']} 是否需要重新向量化: {needs_vectorization}")
            
            print("\n🎉 所有测试通过！")
            
        else:
            print("❌ 向量数据库连接失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_completion()
