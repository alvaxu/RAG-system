'''
程序说明：
## 1. 检查图片处理的具体情况
## 2. 分析成功和失败的图片
## 3. 为重新处理失败的图片做准备
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processing.vector_generator import VectorGenerator
from config.settings import Settings
import pickle
from pathlib import Path

def main():
    """主函数"""
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        vg = VectorGenerator(config.to_dict())
        
        # 加载向量数据库
        vs = vg.load_vector_store('./central/vector_db')
        if not vs:
            print("❌ 无法加载向量数据库")
            return
        
        # 获取统计信息
        stats = vg.get_vector_store_statistics(vs)
        
        print("="*60)
        print("图片处理详细分析")
        print("="*60)
        
        # 检查图片统计
        if stats['image_statistics']:
            img_stats = stats['image_statistics']
            print(f"总图片数: {img_stats['total_images']}")
            print(f"有caption的图片: {img_stats['images_with_caption']}")
            print(f"有footnote的图片: {img_stats['images_with_footnote']}")
            print(f"有增强描述的图片: {img_stats['images_with_enhanced_description']}")
        
        # 检查metadata.pkl文件
        metadata_file = Path("central/vector_db/metadata.pkl")
        if metadata_file.exists():
            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)
            
            print(f"\n元数据文件包含 {len(metadata)} 个条目")
            
            # 统计图片类型的条目
            image_entries = [m for m in metadata if m.get('chunk_type') == 'image']
            print(f"图片条目数: {len(image_entries)}")
            
            # 显示图片信息
            print("\n图片条目详情:")
            for i, entry in enumerate(image_entries):
                print(f"  {i+1}. {entry.get('image_filename', 'unknown')}")
                print(f"     路径: {entry.get('image_path', 'unknown')}")
                print(f"     文档: {entry.get('document_name', 'unknown')}")
                print(f"     页码: {entry.get('page_number', 'unknown')}")
                print()
        
        # 检查central/images目录
        images_dir = Path("central/images")
        if images_dir.exists():
            image_files = list(images_dir.glob("*.jpg"))
            print(f"\ncentral/images目录包含 {len(image_files)} 个图片文件")
            
            # 检查哪些图片在向量数据库中
            if 'image_statistics' in stats and stats['image_statistics']['total_images'] > 0:
                print("\n图片文件与向量数据库对比:")
                for img_file in image_files:
                    img_name = img_file.name
                    # 检查是否在向量数据库中
                    in_db = any(entry.get('image_filename') == img_name for entry in image_entries) if 'image_entries' in locals() else False
                    status = "✅ 已添加" if in_db else "❌ 未添加"
                    print(f"  {img_name}: {status}")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    main() 