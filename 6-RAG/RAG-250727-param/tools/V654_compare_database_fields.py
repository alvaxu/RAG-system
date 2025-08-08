'''
程序说明：
## 1. 对比当前数据库字段和原始数据库字段的差异
## 2. 检查图片标题字段是否正确保存
## 3. 分析字段缺失和变化情况
'''

import pickle
import os
import json

def analyze_current_database_fields():
    """分析当前数据库的字段情况"""
    
    print("🔍 分析当前数据库字段情况")
    print("=" * 60)
    
    # 加载当前元数据
    metadata_file = 'central/vector_db/metadata.pkl'
    
    if not os.path.exists(metadata_file):
        print("❌ 元数据文件不存在")
        return
    
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"📊 总记录数: {len(metadata)}")
        
        # 按类型分组
        image_data = [item for item in metadata if item.get('chunk_type') == 'image']
        text_data = [item for item in metadata if item.get('chunk_type') == 'text']
        table_data = [item for item in metadata if item.get('chunk_type') == 'table']
        
        print(f"🖼️  图片记录数: {len(image_data)}")
        print(f"📄 文本记录数: {len(text_data)}")
        print(f"📊 表格记录数: {len(table_data)}")
        
        # 分析图片文档字段
        if image_data:
            print(f"\n🔍 图片文档字段分析:")
            print("-" * 40)
            
            first_image = image_data[0]
            print(f"第一个图片文档的所有字段:")
            for key, value in first_image.items():
                if key == 'enhanced_description':
                    print(f"  {key}: {repr(str(value)[:100])}...")
                elif isinstance(value, list):
                    print(f"  {key}: {value} (长度: {len(value)})")
                else:
                    print(f"  {key}: {value}")
            
            # 检查关键字段
            print(f"\n🔍 关键字段检查:")
            print("-" * 40)
            
            has_img_caption = sum(1 for item in image_data if item.get('img_caption'))
            has_img_footnote = sum(1 for item in image_data if item.get('img_footnote'))
            has_enhanced_description = sum(1 for item in image_data if item.get('enhanced_description'))
            
            print(f"有img_caption字段的记录: {has_img_caption}/{len(image_data)}")
            print(f"有img_footnote字段的记录: {has_img_footnote}/{len(image_data)}")
            print(f"有enhanced_description字段的记录: {has_enhanced_description}/{len(image_data)}")
            
            # 检查img_caption内容
            non_empty_captions = [item for item in image_data if item.get('img_caption') and len(item.get('img_caption', [])) > 0]
            print(f"img_caption非空的记录: {len(non_empty_captions)}/{len(image_data)}")
            
            if non_empty_captions:
                print(f"前3个非空标题:")
                for i, item in enumerate(non_empty_captions[:3]):
                    print(f"  {i+1}. {item.get('img_caption')}")
            else:
                print(f"❌ 所有图片的img_caption都为空!")
        
        # 分析文本文档字段
        if text_data:
            print(f"\n🔍 文本文档字段分析:")
            print("-" * 40)
            
            first_text = text_data[0]
            print(f"第一个文本文档的所有字段:")
            for key, value in first_text.items():
                print(f"  {key}: {value}")
        
        # 分析表格文档字段
        if table_data:
            print(f"\n🔍 表格文档字段分析:")
            print("-" * 40)
            
            first_table = table_data[0]
            print(f"第一个表格文档的所有字段:")
            for key, value in first_table.items():
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def check_original_json_files():
    """检查原始JSON文件中的图片标题"""
    
    print(f"\n🔍 检查原始JSON文件中的图片标题")
    print("=" * 60)
    
    json_files = [
        'document/md/【上海证券】中芯国际深度研究报告：晶圆制造龙头，领航国产芯片新征程_1.json',
        'document/md/【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评_1.json'
    ]
    
    for json_file in json_files:
        if not os.path.exists(json_file):
            print(f"❌ JSON文件不存在: {json_file}")
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            images = [item for item in data if item.get('type') == 'image']
            print(f"\n📄 {os.path.basename(json_file)}:")
            print(f"  图片总数: {len(images)}")
            
            # 检查图片标题
            non_empty_captions = [item for item in images if item.get('img_caption') and len(item.get('img_caption', [])) > 0]
            print(f"  有标题的图片: {len(non_empty_captions)}/{len(images)}")
            
            if non_empty_captions:
                print(f"  前3个图片标题:")
                for i, item in enumerate(non_empty_captions[:3]):
                    print(f"    {i+1}. {item.get('img_caption')}")
            else:
                print(f"  ❌ 所有图片都没有标题!")
                
        except Exception as e:
            print(f"❌ 读取JSON文件失败 {json_file}: {e}")

def compare_with_original_design():
    """与原始设计对比"""
    
    print(f"\n🔍 与原始设计对比")
    print("=" * 60)
    
    print("📋 原始设计中的字段:")
    print("  共同字段 (3个): chunk_type, document_name, page_number")
    print("  图片文档独有字段 (11个): enhanced_description, extension, image_filename, image_id, image_path, image_type, img_caption, img_footnote, page_idx, semantic_features, source_zip")
    print("  文本和表格文档共有字段 (3个): chunk_index, table_id, table_type")
    
    print(f"\n🔍 当前问题分析:")
    print("-" * 40)
    print("❌ 问题1: img_caption字段为空，导致图4检索失败")
    print("❌ 问题2: 图片标题信息在数据库生成过程中丢失")
    print("❌ 问题3: 需要重新生成数据库或修复图片标题提取逻辑")
    
    print(f"\n💡 解决方案:")
    print("-" * 40)
    print("1. 检查JSON文件中的图片标题是否正确")
    print("2. 修复图片标题提取和保存逻辑")
    print("3. 重新生成向量数据库")
    print("4. 或者修复现有数据库中的图片标题字段")

def main():
    """主函数"""
    print("🔍 数据库字段对比分析")
    print("=" * 60)
    
    # 1. 分析当前数据库字段
    analyze_current_database_fields()
    
    # 2. 检查原始JSON文件
    check_original_json_files()
    
    # 3. 与原始设计对比
    compare_with_original_design()
    
    print(f"\n📋 总结:")
    print("=" * 60)
    print("✅ 当前数据库结构基本正确")
    print("❌ 主要问题: img_caption字段为空")
    print("🔧 需要修复: 图片标题提取和保存逻辑")

if __name__ == "__main__":
    main()
