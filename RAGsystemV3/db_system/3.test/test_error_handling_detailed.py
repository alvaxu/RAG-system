#!/usr/bin/env python3
"""
详细的错误处理测试脚本

逐步测试每个环节，定位'str' object has no attribute 'get'错误
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from vectorization.image_vectorizer import ImageVectorizer
from config.config_manager import ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO)

def test_error_handling_step_by_step():
    """逐步测试错误处理"""
    print("🧪 逐步测试错误处理逻辑")
    print("="*50)
    
    try:
        # 1. 初始化配置管理器
        print("📋 初始化配置管理器...")
        config_manager = ConfigManager()
        print("✅ 配置管理器初始化成功")
        
        # 2. 初始化图片向量化器
        print("\n🔤 初始化图片向量化器...")
        image_vectorizer = ImageVectorizer(config_manager)
        print("✅ 图片向量化器初始化成功")
        
        # 3. 测试单个图片向量化（预期会失败，但不会崩溃）
        print("\n🔄 测试单个图片向量化...")
        try:
            result = image_vectorizer.vectorize_image('/fake/path/test.jpg', '测试描述', {})
            print(f"✅ 单个图片向量化完成")
            print(f"📊 状态: {result.get('vectorization_status')}")
            if result.get('vectorization_status') == 'failed':
                print(f"📝 错误信息: {result.get('error_message')}")
        except Exception as e:
            print(f"❌ 单个图片向量化过程中出现异常: {e}")
            print(f"❌ 异常类型: {type(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 4. 测试批量向量化（预期会失败，但不会崩溃）
        print("\n🔄 测试批量向量化...")
        test_images = [
            {
                'final_image_path': '/fake/path/image1.jpg',
                'enhanced_description': '这是第一张图片的描述'
            },
            {
                'final_image_path': '/fake/path/image2.jpg',
                'enhanced_description': '这是第二张图片的描述'
            }
        ]
        
        try:
            result = image_vectorizer.vectorize_images_batch(test_images)
            print(f"✅ 批量向量化完成，返回 {len(result)} 个结果")
            
            # 检查结果
            success_count = sum(1 for img in result if img.get('vectorization_status') == 'success')
            print(f"📊 成功: {success_count}, 失败: {len(result) - success_count}")
            
        except Exception as e:
            print(f"❌ 批量向量化过程中出现异常: {e}")
            print(f"❌ 异常类型: {type(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n🎉 所有测试通过！错误处理逻辑修复成功")
        return True
        
    except Exception as e:
        logging.error(f"测试失败: {e}")
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧪 详细错误处理测试")
    print("="*50)
    
    success = test_error_handling_step_by_step()
    
    if success:
        print("\n🎉 测试完成！")
    else:
        print("\n❌ 测试失败！")
    
    return success

if __name__ == "__main__":
    main()
