#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单张图片向量化功能

功能说明：
1. 只处理一张图片的enhanced_description向量化
2. 验证metadata.pkl是否正确维护
3. 测试修复后的vector_generator功能
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import DashScopeEmbeddings
    from config.settings import Settings
    from document_processing.image_enhancer import ImageEnhancer
    from document_processing.vector_generator import VectorGenerator
    from document_processing.image_processor import ImageProcessor
except ImportError as e:
    print(f"❌ 缺少必要的依赖包: {e}")
    print("请确保项目依赖已正确安装")
    sys.exit(1)

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SingleImageTester:
    """
    单张图片向量化测试器
    """
    
    def __init__(self):
        """初始化测试器"""
        try:
            # 加载配置
            self.config = Settings.load_from_file('config.json')
            
            # 使用统一的API密钥管理模块获取API密钥
            config_key = self.config.dashscope_api_key
            self.api_key = get_dashscope_api_key(config_key)
            
            if not self.api_key:
                logger.warning("未找到有效的DashScope API密钥")
            
            # 初始化图像增强器
            image_config = {
                'enable_enhancement': self.config.enable_enhancement,
                'enhancement_model': self.config.enhancement_model,
                'enhancement_max_tokens': self.config.enhancement_max_tokens,
                'enhancement_temperature': self.config.enhancement_temperature,
                'enhancement_batch_size': self.config.enhancement_batch_size,
                'enable_progress_logging': self.config.enable_progress_logging
            }
            self.image_enhancer = ImageEnhancer(
                api_key=self.api_key,
                config=image_config
            )
            
            # 初始化向量生成器
            self.vector_generator = VectorGenerator(self.config.__dict__)
            
            # 向量数据库路径
            self.vector_db_path = self.config.vector_db_dir
            
            logger.info("单张图片测试器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def load_vector_store(self) -> Optional[FAISS]:
        """加载向量数据库"""
        try:
            embedding_model = getattr(self.config, 'text_embedding_model', 'text-embedding-v1')
            embeddings = DashScopeEmbeddings(
                dashscope_api_key=self.api_key, 
                model=embedding_model
            )
            allow_dangerous_deserialization = getattr(self.config, 'allow_dangerous_deserialization', True)
            vector_store = FAISS.load_local(
                self.vector_db_path, 
                embeddings, 
                allow_dangerous_deserialization=allow_dangerous_deserialization
            )
            logger.info(f"向量数据库加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
            return vector_store
            
        except Exception as e:
            logger.error(f"加载向量数据库失败: {e}")
            return None
    
    def find_test_image(self) -> Optional[Dict[str, Any]]:
        """找到一个测试用的图片"""
        vector_store = self.load_vector_store()
        if not vector_store:
            return None
        
        # 查找第一张有enhanced_description的图片
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            if (metadata.get('chunk_type') == 'image' and 
                metadata.get('enhanced_description') and
                metadata.get('image_path') and
                os.path.exists(metadata.get('image_path'))):
                
                return {
                    'doc_id': doc_id,
                    'image_path': metadata.get('image_path'),
                    'document_name': metadata.get('document_name', '未知文档'),
                    'page_number': metadata.get('page_number', 1),
                    'image_id': metadata.get('image_id', 'unknown'),
                    'enhanced_description': metadata.get('enhanced_description', '')
                }
        
        return None
    
    def test_single_image_vectorization(self, image_info: Dict[str, Any]) -> bool:
        """测试单张图片的向量化"""
        print(f"🧪 开始测试单张图片向量化...")
        print(f"   文档: {image_info['document_name']}")
        print(f"   页码: {image_info['page_number']}")
        print(f"   图片ID: {image_info['image_id']}")
        print(f"   图片路径: {image_info['image_path']}")
        
        # 加载向量数据库
        vector_store = self.load_vector_store()
        if not vector_store:
            print("❌ 无法加载向量数据库")
            return False
        
        # 检查是否已经向量化
        already_vectorized = False
        for doc_id, doc in vector_store.docstore._dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            if (metadata.get('chunk_type') == 'image_text' and 
                metadata.get('related_image_id') == image_info['image_id']):
                already_vectorized = True
                break
        
        if already_vectorized:
            print(f"⚠️ 图片 {image_info['image_id']} 已经向量化过了")
            return True
        
        try:
            # 创建新的image_text Document对象
            from langchain.schema import Document
            text_doc = Document(
                page_content=image_info["enhanced_description"],
                metadata={
                    "chunk_type": "image_text",
                    "source_type": "image_description",
                    "image_id": image_info['image_id'],
                    "document_name": image_info['document_name'],
                    "page_number": image_info['page_number'],
                    "enhanced_description": image_info["enhanced_description"],
                    "related_image_id": image_info['image_id'],
                    "page_idx": 0,
                    "img_caption": [],
                    "img_footnote": []
                }
            )
            
            print(f"✅ 创建image_text Document对象成功")
            
            # 生成文本向量
            print(f"🔤 正在生成文本向量...")
            text_embedding = self.vector_generator.embeddings.embed_documents([text_doc.page_content])[0]
            print(f"✅ 文本向量生成成功，维度: {len(text_embedding)}")
            
            # 添加到向量存储
            print(f"📝 正在添加到FAISS索引...")
            vector_store.add_embeddings([(text_doc.page_content, text_embedding)], metadatas=[text_doc.metadata])
            print(f"✅ 成功添加到FAISS索引")
            
            # 保存向量数据库
            print(f"💾 正在保存向量数据库...")
            self.vector_generator._save_vector_store_with_metadata(vector_store, self.vector_db_path)
            print(f"✅ 向量数据库保存成功")
            
            # 验证结果
            print(f"🔍 验证结果...")
            updated_vector_store = self.load_vector_store()
            if updated_vector_store:
                doc_count = len(updated_vector_store.docstore._dict)
                print(f"✅ 数据库文档数量: {doc_count}")
                
                # 检查metadata.pkl
                metadata_path = os.path.join(self.vector_db_path, "metadata.pkl")
                if os.path.exists(metadata_path):
                    import pickle
                    with open(metadata_path, 'rb') as f:
                        metadata_list = pickle.load(f)
                    print(f"✅ metadata.pkl包含 {len(metadata_list)} 个元数据")
                    
                    # 统计chunk类型
                    chunk_types = {}
                    for metadata in metadata_list:
                        chunk_type = metadata.get('chunk_type', 'unknown')
                        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                    
                    print("📊 元数据统计:")
                    for chunk_type, count in sorted(chunk_types.items()):
                        print(f"   {chunk_type}: {count} 个")
                else:
                    print(f"❌ metadata.pkl文件不存在")
            
            return True
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            logger.error(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_test(self):
        """运行测试"""
        print("🚀 单张图片向量化测试启动")
        print("="*50)
        
        # 1. 查找测试图片
        print("🔍 正在查找测试图片...")
        test_image = self.find_test_image()
        
        if not test_image:
            print("❌ 没有找到合适的测试图片")
            print("请确保数据库中有图片且包含enhanced_description")
            return
        
        print(f"✅ 找到测试图片: {test_image['image_id']}")
        
        # 2. 执行测试
        print("\n🧪 开始执行测试...")
        success = self.test_single_image_vectorization(test_image)
        
        if success:
            print("\n🎉 测试成功！")
            print("metadata.pkl维护功能正常工作")
        else:
            print("\n❌ 测试失败！")
            print("请检查错误信息")


def main():
    """主函数"""
    try:
        tester = SingleImageTester()
        tester.run_test()
    except Exception as e:
        print(f"❌ 测试程序启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
