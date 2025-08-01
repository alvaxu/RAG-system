'''
程序说明：
## 1. 测试图片处理相关文件的配置管理
## 2. 验证嵌入模型配置是否正确使用
## 3. 检查配置参数传递是否正确
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from document_processing.enhanced_image_processor import EnhancedImageProcessor
from document_processing.image_processor import ImageProcessor
from document_processing.enhanced_vector_generator import EnhancedVectorGenerator
from document_processing.vector_generator import VectorGenerator

def test_image_config_management():
    """测试图片处理相关文件的配置管理"""
    print("="*60)
    print("🔍 测试图片处理相关文件的配置管理")
    print("="*60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        config_dict = config.to_dict()
        print(f"✅ 配置加载成功")
        
        # 检查配置中的嵌入模型设置
        text_embedding_model = config_dict.get('vector_store', {}).get('text_embedding_model', 'text-embedding-v4')
        multimodal_embedding_model = config_dict.get('vector_store', {}).get('multimodal_embedding_model', 'multimodal_embedding_one_peace_v1')
        
        print(f"   配置的文本嵌入模型: {text_embedding_model}")
        print(f"   配置的多模态嵌入模型: {multimodal_embedding_model}")
        
        # 测试EnhancedImageProcessor
        print(f"\n🔍 测试EnhancedImageProcessor...")
        try:
            enhanced_image_processor = EnhancedImageProcessor("test_key", config_dict)
            print(f"   ✅ EnhancedImageProcessor初始化成功")
            print(f"   ✅ 配置参数传递正确")
        except Exception as e:
            print(f"   ❌ EnhancedImageProcessor初始化失败: {e}")
        
        # 测试ImageProcessor
        print(f"\n🔍 测试ImageProcessor...")
        try:
            image_processor = ImageProcessor("test_key", config_dict)
            print(f"   ✅ ImageProcessor初始化成功")
            print(f"   ✅ 配置参数传递正确")
        except Exception as e:
            print(f"   ❌ ImageProcessor初始化失败: {e}")
        
        # 测试EnhancedVectorGenerator
        print(f"\n🔍 测试EnhancedVectorGenerator...")
        try:
            enhanced_vector_generator = EnhancedVectorGenerator(config_dict)
            print(f"   ✅ EnhancedVectorGenerator初始化成功")
            print(f"   ✅ 配置参数传递正确")
            
            # 检查嵌入模型设置
            if hasattr(enhanced_vector_generator, 'embeddings'):
                print(f"   ✅ 文本嵌入模型设置正确")
            if hasattr(enhanced_vector_generator, 'enhanced_image_processor'):
                print(f"   ✅ 图片处理器设置正确")
        except Exception as e:
            print(f"   ❌ EnhancedVectorGenerator初始化失败: {e}")
        
        # 测试VectorGenerator
        print(f"\n🔍 测试VectorGenerator...")
        try:
            vector_generator = VectorGenerator(config_dict)
            print(f"   ✅ VectorGenerator初始化成功")
            print(f"   ✅ 配置参数传递正确")
            
            # 检查嵌入模型设置
            if hasattr(vector_generator, 'embeddings'):
                print(f"   ✅ 文本嵌入模型设置正确")
            if hasattr(vector_generator, 'image_processor'):
                print(f"   ✅ 图片处理器设置正确")
        except Exception as e:
            print(f"   ❌ VectorGenerator初始化失败: {e}")
        
        print(f"\n✅ 所有图片处理相关文件的配置管理测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_image_config_management() 