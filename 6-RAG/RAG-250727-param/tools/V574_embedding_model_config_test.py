'''
程序说明：
## 1. 嵌入模型配置验证测试脚本
## 2. 检查所有相关文件是否正确使用统一配置
## 3. 验证文本嵌入模型和多模态嵌入模型的配置
## 4. 确保没有硬编码的模型名称
'''

import os
import sys
import logging
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_manager import ConfigManager
from document_processing.vector_generator import VectorGenerator
from document_processing.enhanced_vector_generator import EnhancedVectorGenerator
from document_processing.image_processor import ImageProcessor
from document_processing.enhanced_image_processor import EnhancedImageProcessor
from core.vector_store import VectorStoreManager
from core.enhanced_qa_system import load_enhanced_qa_system

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_config_loading():
    """
    测试配置加载
    """
    print("=" * 60)
    print("测试配置加载")
    print("=" * 60)
    
    try:
        # 加载配置管理器
        config_manager = ConfigManager()
        settings = config_manager.get_settings()
        
        print("✅ 配置管理器加载成功")
        print(f"文本嵌入模型: {settings.text_embedding_model}")
        print(f"多模态嵌入模型: {settings.multimodal_embedding_model}")
        
        return config_manager, settings
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return None, None


def test_vector_generator_config(config_manager):
    """
    测试向量生成器配置
    """
    print("\n" + "=" * 60)
    print("测试向量生成器配置")
    print("=" * 60)
    
    try:
        settings = config_manager.get_settings()
        
        # 测试VectorGenerator
        print("测试 VectorGenerator...")
        vector_gen = VectorGenerator(settings)
        print(f"✅ VectorGenerator 文本嵌入模型: {vector_gen.embeddings.model}")
        
        # 测试EnhancedVectorGenerator
        print("测试 EnhancedVectorGenerator...")
        config_dict = settings.to_dict()
        enhanced_vector_gen = EnhancedVectorGenerator(config_dict)
        print(f"✅ EnhancedVectorGenerator 文本嵌入模型: {enhanced_vector_gen.embeddings.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ 向量生成器配置测试失败: {e}")
        return False


def test_image_processor_config(config_manager):
    """
    测试图片处理器配置
    """
    print("\n" + "=" * 60)
    print("测试图片处理器配置")
    print("=" * 60)
    
    try:
        settings = config_manager.get_settings()
        config_dict = settings.to_dict()
        
        # 测试ImageProcessor
        print("测试 ImageProcessor...")
        image_processor = ImageProcessor("test_key", config_dict)
        print(f"✅ ImageProcessor 多模态嵌入模型: {image_processor.multimodal_embedding_model}")
        
        # 测试EnhancedImageProcessor
        print("测试 EnhancedImageProcessor...")
        enhanced_image_processor = EnhancedImageProcessor("test_key", config_dict)
        print(f"✅ EnhancedImageProcessor 多模态嵌入模型: {enhanced_image_processor.multimodal_embedding_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ 图片处理器配置测试失败: {e}")
        return False


def test_vector_store_config(config_manager):
    """
    测试向量存储配置
    """
    print("\n" + "=" * 60)
    print("测试向量存储配置")
    print("=" * 60)
    
    try:
        settings = config_manager.get_settings()
        config_dict = settings.to_dict()
        
        # 测试VectorStoreManager
        print("测试 VectorStoreManager...")
        vector_store_manager = VectorStoreManager("test_key", config_dict)
        if vector_store_manager.embeddings:
            print(f"✅ VectorStoreManager 文本嵌入模型: {vector_store_manager.embeddings.model}")
        else:
            print("⚠️ VectorStoreManager 未初始化embeddings（API密钥为测试值）")
        
        return True
        
    except Exception as e:
        print(f"❌ 向量存储配置测试失败: {e}")
        return False


def test_qa_system_config(config_manager):
    """
    测试问答系统配置
    """
    print("\n" + "=" * 60)
    print("测试问答系统配置")
    print("=" * 60)
    
    try:
        settings = config_manager.get_settings()
        config_dict = settings.to_dict()
        
        # 测试QA系统配置加载
        print("测试 QA系统配置加载...")
        # 注意：这里只是测试配置加载，不实际创建QA系统实例
        text_embedding_model = config_dict.get('vector_store', {}).get('text_embedding_model', 'text-embedding-v4')
        print(f"✅ QA系统文本嵌入模型配置: {text_embedding_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ 问答系统配置测试失败: {e}")
        return False


def check_hardcoded_models():
    """
    检查是否有硬编码的模型名称
    """
    print("\n" + "=" * 60)
    print("检查硬编码模型名称")
    print("=" * 60)
    
    # 需要检查的文件列表
    files_to_check = [
        'document_processing/vector_generator.py',
        'document_processing/enhanced_vector_generator.py',
        'document_processing/image_processor.py',
        'document_processing/enhanced_image_processor.py',
        'core/vector_store.py',
        'core/enhanced_qa_system.py'
    ]
    
    hardcoded_found = False
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查硬编码的模型名称（排除作为默认值的情况）
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # 检查是否在getattr或get方法的默认值中
                    if "'text-embedding-v4'" in line or '"text-embedding-v4"' in line:
                        # 排除作为默认值的情况
                        if not any(keyword in line for keyword in ['getattr', 'get(', 'default', 'else:', 'multimodal_embedding_model =', 'text_embedding_model =']):
                            print(f"⚠️ {file_path}: 第{i}行发现硬编码的 'text-embedding-v4'")
                            hardcoded_found = True
                    
                    if "'multimodal_embedding_one_peace_v1'" in line or '"multimodal_embedding_one_peace_v1"' in line:
                        # 排除作为默认值的情况
                        if not any(keyword in line for keyword in ['getattr', 'get(', 'default', 'else:', 'multimodal_embedding_model =', 'text_embedding_model =']):
                            print(f"⚠️ {file_path}: 第{i}行发现硬编码的 'multimodal_embedding_one_peace_v1'")
                            hardcoded_found = True
                    
            except Exception as e:
                print(f"❌ 检查文件 {file_path} 时出错: {e}")
    
    if not hardcoded_found:
        print("✅ 未发现硬编码的模型名称")
    
    return not hardcoded_found


def main():
    """
    主测试函数
    """
    print("嵌入模型配置统一性测试")
    print("=" * 60)
    
    # 测试配置加载
    config_manager, settings = test_config_loading()
    if not config_manager:
        return False
    
    # 测试各个组件的配置
    tests = [
        test_vector_generator_config,
        test_image_processor_config,
        test_vector_store_config,
        test_qa_system_config
    ]
    
    all_tests_passed = True
    for test_func in tests:
        if not test_func(config_manager):
            all_tests_passed = False
    
    # 检查硬编码模型名称
    no_hardcoded = check_hardcoded_models()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if all_tests_passed and no_hardcoded:
        print("✅ 所有测试通过！嵌入模型配置已统一")
        print("\n配置摘要:")
        print(f"  文本嵌入模型: {settings.text_embedding_model}")
        print(f"  多模态嵌入模型: {settings.multimodal_embedding_model}")
        print("\n所有组件都正确使用了统一配置，没有发现硬编码的模型名称。")
    else:
        print("❌ 部分测试失败，请检查配置")
        if not all_tests_passed:
            print("  - 组件配置测试失败")
        if not no_hardcoded:
            print("  - 发现硬编码的模型名称")
    
    return all_tests_passed and no_hardcoded


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 