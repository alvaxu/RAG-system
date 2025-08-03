'''
程序说明：
## 1. 检查向量数据库统计信息
## 2. 分析图片添加成功和失败的情况
## 3. 显示详细的类型分布
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processing.vector_generator import VectorGenerator
from config.settings import Settings

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
        print("向量数据库统计信息")
        print("="*60)
        
        # 基本信息
        print(f"总文档数: {stats['total_documents']}")
        print(f"向量维度: {stats['vector_dimension']}")
        
        # 类型分布
        print("\n类型分布:")
        for chunk_type, count in stats['type_distribution'].items():
            print(f"  {chunk_type}: {count}")
        
        # 图片统计
        if stats['image_statistics']:
            print("\n图片统计:")
            img_stats = stats['image_statistics']
            print(f"  总图片数: {img_stats['total_images']}")
            print(f"  有caption的图片: {img_stats['images_with_caption']}")
            print(f"  有footnote的图片: {img_stats['images_with_footnote']}")
            print(f"  有增强描述的图片: {img_stats['images_with_enhanced_description']}")
            
            if img_stats['image_types']:
                print("  图片类型分布:")
                for img_type, count in img_stats['image_types'].items():
                    print(f"    {img_type}: {count}")
        
        # 表格统计
        if stats['table_types']:
            print("\n表格类型分布:")
            for table_type, count in stats['table_types'].items():
                print(f"  {table_type}: {count}")
        
        print("="*60)
        
        # 分析增量处理结果
        print("\n增量处理分析:")
        total_docs = stats['total_documents']
        text_docs = stats['type_distribution'].get('text', 0)
        table_docs = stats['type_distribution'].get('table', 0)
        image_docs = stats['type_distribution'].get('image', 0)
        
        print(f"文本分块: {text_docs}")
        print(f"表格分块: {table_docs}")
        print(f"图片分块: {image_docs}")
        
        # 计算增量添加的内容
        # 原始数据库应该有43个条目（38个文档+5张图片）
        original_count = 43
        incremental_count = total_docs - original_count
        
        print(f"\n增量添加的内容:")
        print(f"  原始条目数: {original_count}")
        print(f"  当前条目数: {total_docs}")
        print(f"  增量添加数: {incremental_count}")
        
        # 分析图片添加情况
        if image_docs > 0:
            original_images = 5  # 原始数据库中的图片数
            new_images = image_docs - original_images
            print(f"\n图片添加情况:")
            print(f"  原始图片数: {original_images}")
            print(f"  当前图片数: {image_docs}")
            print(f"  新增图片数: {new_images}")
            
            # 从日志中我们知道有30张图片需要处理，但只有22张成功
            expected_images = 30
            successful_images = new_images
            failed_images = expected_images - successful_images
            
            print(f"  预期处理图片: {expected_images}")
            print(f"  成功添加图片: {successful_images}")
            print(f"  失败图片数: {failed_images}")
            
            if failed_images > 0:
                print(f"  失败原因: API频率限制")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    main() 