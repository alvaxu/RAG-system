#!/usr/bin/env python3
'''
程序说明：
## 1. 专门用于调试图片处理问题的简化测试脚本
## 2. 只测试图片增强和向量化的关键步骤
## 3. 输出更清晰，便于定位问题
'''

import os
import sys
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from document_processing.vector_generator import VectorGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_image_processing():
    """测试图片处理功能"""
    print("🔍 开始测试图片处理功能...")
    
    # 1. 加载配置
    print("\n1️⃣ 加载配置...")
    try:
        config = Settings()
        print(f"✅ 配置加载成功")
        print(f"🔍 配置类型: {type(config)}")
        print(f"🔍 enable_enhanced_description_vectorization: {config.enable_enhanced_description_vectorization}")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return
    
    # 2. 初始化VectorGenerator
    print("\n2️⃣ 初始化VectorGenerator...")
    try:
        vector_generator = VectorGenerator(config)
        print(f"✅ VectorGenerator初始化成功")
        print(f"🔍 image_processor类型: {type(vector_generator.image_processor)}")
    except Exception as e:
        print(f"❌ VectorGenerator初始化失败: {e}")
        return
    
    # 3. 检查配置传递
    print("\n3️⃣ 检查配置传递...")
    try:
        # 模拟一个图片文件信息
        test_image_info = {
            'image_path': 'test_path',
            'image_hash': 'test_hash',
            'document_name': 'test_doc',
            'page_number': 1,
            'img_caption': ['测试图片'],
            'img_footnote': []
        }
        
        # 检查配置获取
        enable_vectorization = vector_generator.config.get('enable_enhanced_description_vectorization', False)
        print(f"🔍 从config获取的enable_vectorization: {enable_vectorization}")
        print(f"🔍 config内容预览: {str(config)[:200]}...")
        
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    test_image_processing()
