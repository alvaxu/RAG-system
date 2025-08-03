'''
程序说明：
## 1. 将图片添加到现有的向量数据库中
## 2. 使用配置管理确保嵌入模型一致性
## 3. 处理图片的批处理以避免API限制
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from document_processing.enhanced_vector_generator import EnhancedVectorGenerator
from document_processing.enhanced_image_processor import EnhancedImageProcessor
from langchain_community.vectorstores import FAISS
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_images_to_vector_db():
    """将图片添加到向量数据库"""
    print("="*60)
    print("🔍 将图片添加到向量数据库")
    print("="*60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        config_dict = config.to_dict()
        print(f"✅ 配置加载成功")
        
        # 检查图片目录
        images_dir = "central/images"
        if not os.path.exists(images_dir):
            print(f"❌ 图片目录不存在: {images_dir}")
            return False
        
        # 获取图片文件列表
        image_files = []
        for file in os.listdir(images_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                image_path = os.path.join(images_dir, file)
                image_files.append({
                    'image_path': image_path,
                    'image_id': file.split('.')[0],
                    'document_name': '中芯国际相关文档',
                    'page_number': 1
                })
        
        print(f"✅ 找到 {len(image_files)} 个图片文件")
        
        if not image_files:
            print("❌ 没有找到图片文件")
            return False
        
        # 初始化向量生成器
        vector_generator = EnhancedVectorGenerator(config_dict)
        
        # 加载现有的向量存储
        vector_db_path = config.vector_db_dir
        vector_store = vector_generator.load_vector_store(vector_db_path)
        
        if not vector_store:
            print("❌ 无法加载向量存储")
            return False
        
        print(f"✅ 向量存储加载成功，包含 {vector_store.index.ntotal} 个文档")
        
        # 分批处理图片，避免API限制
        batch_size = 5  # 每批处理5个图片
        total_processed = 0
        
        for i in range(0, len(image_files), batch_size):
            batch = image_files[i:i + batch_size]
            print(f"\n🔍 处理第 {i//batch_size + 1} 批图片 ({len(batch)} 个)...")
            
            try:
                # 添加图片到向量存储
                success = vector_generator.add_images_to_store(
                    vector_store=vector_store,
                    image_files=batch,
                    save_path=vector_db_path
                )
                
                if success:
                    total_processed += len(batch)
                    print(f"   ✅ 第 {i//batch_size + 1} 批图片处理成功")
                else:
                    print(f"   ❌ 第 {i//batch_size + 1} 批图片处理失败")
                    
            except Exception as e:
                print(f"   ❌ 处理第 {i//batch_size + 1} 批图片时出错: {e}")
        
        print(f"\n📊 处理结果:")
        print(f"   - 总图片数量: {len(image_files)}")
        print(f"   - 成功处理: {total_processed}")
        print(f"   - 失败数量: {len(image_files) - total_processed}")
        
        if total_processed > 0:
            print(f"✅ 成功将 {total_processed} 个图片添加到向量数据库")
            return True
        else:
            print(f"❌ 没有图片被成功添加到向量数据库")
            return False
            
    except Exception as e:
        print(f"❌ 添加图片到向量数据库失败: {e}")
        return False

if __name__ == "__main__":
    add_images_to_vector_db() 