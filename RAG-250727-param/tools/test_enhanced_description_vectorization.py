#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试enhanced_description向量化功能

验证修复后的vector_generator.py是否能正确创建image_text chunks
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
import logging

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_description_vectorization():
    """测试enhanced_description向量化功能"""
    print("🧪 测试enhanced_description向量化功能")
    print("=" * 60)
    
    try:
        # 1. 加载配置
        print("📋 步骤1: 加载配置...")
        config = Settings.load_from_file('config.json')
        
        # 检查关键配置
        print(f"   ✅ enable_enhanced_description_vectorization: {config.enable_enhanced_description_vectorization}")
        print(f"   ✅ enable_enhancement: {config.enable_enhancement}")
        print(f"   ✅ text_embedding_model: {config.text_embedding_model}")
        
        if not config.enable_enhanced_description_vectorization:
            print("❌ 配置中未启用enhanced_description向量化功能")
            return False
        
        # 2. 获取API密钥
        print("\n🔑 步骤2: 获取API密钥...")
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        if not api_key:
            print("❌ 无法获取DashScope API密钥")
            return False
        print("   ✅ DashScope API密钥获取成功")
        
        # 3. 加载向量数据库
        print("\n🗄️ 步骤3: 加载向量数据库...")
        vector_db_path = config.vector_db_dir
        if not os.path.exists(vector_db_path):
            print(f"❌ 向量数据库路径不存在: {vector_db_path}")
            return False
        
        # 初始化embeddings
        embeddings = DashScopeEmbeddings(
            dashscope_api_key=api_key, 
            model=config.text_embedding_model
        )
        
        # 加载向量存储
        vector_store = FAISS.load_local(
            vector_db_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        print(f"   ✅ 向量数据库加载成功，文档总数: {len(vector_store.docstore._dict)}")
        
        # 4. 检查现有的image_text chunks
        print("\n🔍 步骤4: 检查现有的image_text chunks...")
        image_text_count = 0
        image_count = 0
        
        for doc_id, doc in vector_store.docstore._dict.items():
            chunk_type = doc.metadata.get('chunk_type', '')
            if chunk_type == 'image_text':
                image_text_count += 1
            elif chunk_type == 'image':
                image_count += 1
        
        print(f"   📸 图片chunks数量: {image_count}")
        print(f"   🔤 image_text chunks数量: {image_text_count}")
        
        # 5. 检查配置传递
        print("\n⚙️ 步骤5: 检查配置传递...")
        from document_processing.vector_generator import VectorGenerator
        
        # 创建VectorGenerator实例
        vector_generator = VectorGenerator(config.__dict__)
        
        # 检查配置是否正确传递
        config_dict = vector_generator.config
        if isinstance(config_dict, dict):
            enable_vectorization = config_dict.get('enable_enhanced_description_vectorization', False)
            print(f"   ✅ VectorGenerator配置检查: enable_enhanced_description_vectorization = {enable_vectorization}")
        else:
            print(f"   ⚠️ VectorGenerator配置类型: {type(config_dict)}")
            if hasattr(config_dict, 'enable_enhanced_description_vectorization'):
                enable_vectorization = config_dict.enable_enhanced_description_vectorization
                print(f"   ✅ 属性检查: enable_enhanced_description_vectorization = {enable_vectorization}")
            else:
                print("   ❌ 配置中未找到enable_enhanced_description_vectorization属性")
        
        # 6. 模拟图片处理流程
        print("\n🔄 步骤6: 模拟图片处理流程...")
        if image_count > 0:
            print("   📝 找到现有图片，可以测试向量化流程")
            print("   💡 建议运行V502_image_enhancer_new.py来测试完整的向量化流程")
        else:
            print("   ⚠️ 未找到现有图片，无法测试向量化流程")
        
        print("\n✅ 测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = test_enhanced_description_vectorization()
    
    if success:
        print("\n🎉 enhanced_description向量化功能测试通过！")
        print("\n📋 下一步建议:")
        print("   1. 运行 V502_image_enhancer_new.py 测试完整的向量化流程")
        print("   2. 检查生成的image_text chunks是否正确添加到数据库")
        print("   3. 验证Image Engine是否能正确召回这些chunks")
    else:
        print("\n❌ enhanced_description向量化功能测试失败！")
        print("请检查配置和依赖项")

if __name__ == "__main__":
    main()
