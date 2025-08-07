'''
程序说明：
## 1. 检查向量数据库元数据中的字段结构
## 2. 分析content和enhanced_description字段的存在情况
## 3. 验证两个字段的内容是否相同
'''

import pickle
import os
import json

def check_metadata_fields():
    """检查元数据中的字段结构"""
    
    # 加载元数据
    metadata_file = 'central/vector_db/metadata.pkl'
    
    if not os.path.exists(metadata_file):
        print("❌ 元数据文件不存在")
        return
    
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"📊 总记录数: {len(metadata)}")
        
        # 统计不同类型
        image_data = [item for item in metadata if item.get('chunk_type') == 'image']
        text_data = [item for item in metadata if item.get('chunk_type') == 'text']
        table_data = [item for item in metadata if item.get('chunk_type') == 'table']
        
        print(f"🖼️  图片记录数: {len(image_data)}")
        print(f"📄 文本记录数: {len(text_data)}")
        print(f"📊 表格记录数: {len(table_data)}")
        
        if not image_data:
            print("❌ 没有找到图片记录")
            return
        
        # 检查第一个图片记录的字段结构
        first_image = image_data[0]
        print(f"\n🔍 第一个图片记录的字段结构:")
        print("=" * 60)
        
        for key, value in first_image.items():
            if key in ['content', 'enhanced_description']:
                print(f"  {key}: {repr(value)}")
            elif isinstance(value, list) and len(value) > 0:
                print(f"  {key}: {value[:3]}... (共{len(value)}项)")
            else:
                print(f"  {key}: {value}")
        
        # 检查所有图片记录的content和enhanced_description字段
        print(f"\n🔍 检查所有图片记录的字段情况:")
        print("=" * 60)
        
        has_content_count = 0
        has_enhanced_description_count = 0
        both_fields_count = 0
        same_content_count = 0
        
        for i, item in enumerate(image_data):
            has_content = 'content' in item
            has_enhanced_description = 'enhanced_description' in item
            
            if has_content:
                has_content_count += 1
            if has_enhanced_description:
                has_enhanced_description_count += 1
            if has_content and has_enhanced_description:
                both_fields_count += 1
                
                # 检查内容是否相同
                content = item.get('content', '')
                enhanced_desc = item.get('enhanced_description', '')
                if content == enhanced_desc:
                    same_content_count += 1
                
                # 显示前3个记录的详细对比
                if i < 3:
                    print(f"\n📷 图片 {i+1}:")
                    print(f"  图片ID: {item.get('image_id', 'No ID')}")
                    print(f"  文档: {item.get('document_name', 'Unknown')}")
                    print(f"  content字段: {repr(content)}")
                    print(f"  enhanced_description字段: {repr(enhanced_desc)}")
                    print(f"  内容相同: {content == enhanced_desc}")
        
        print(f"\n📊 字段统计:")
        print(f"  有content字段的记录: {has_content_count}")
        print(f"  有enhanced_description字段的记录: {has_enhanced_description_count}")
        print(f"  同时有两个字段的记录: {both_fields_count}")
        print(f"  两个字段内容相同的记录: {same_content_count}")
        
        # 检查是否有记录缺少某个字段
        missing_content = has_enhanced_description_count - both_fields_count
        missing_enhanced_description = has_content_count - both_fields_count
        
        if missing_content > 0:
            print(f"  ⚠️  有 {missing_content} 个记录缺少content字段")
        if missing_enhanced_description > 0:
            print(f"  ⚠️  有 {missing_enhanced_description} 个记录缺少enhanced_description字段")
        
        if both_fields_count > 0 and same_content_count == both_fields_count:
            print(f"  ✅ 所有同时有两个字段的记录，内容都相同")
        elif both_fields_count > 0:
            print(f"  ⚠️  有 {both_fields_count - same_content_count} 个记录的两个字段内容不同")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_metadata_fields()
