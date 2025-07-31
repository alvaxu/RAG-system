"""
程序说明：
## 1. 检查metadata.pkl中的图片信息
## 2. 验证图片元数据是否正确保存
## 3. 分析图片信息的结构
"""

import os
import pickle
import json
from typing import List, Dict, Any

def check_metadata_images():
    """
    检查metadata.pkl中的图片信息
    """
    print("=" * 60)
    print("🔍 检查metadata.pkl中的图片信息")
    print("=" * 60)
    
    metadata_file = "vector_db_test/metadata.pkl"
    if not os.path.exists(metadata_file):
        print(f"❌ metadata.pkl文件不存在: {metadata_file}")
        return
    
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"✅ 成功读取metadata.pkl，包含 {len(metadata)} 条记录")
        
        # 直接打印所有记录的结构
        print(f"\n📋 所有记录结构:")
        # 只显示前10条和后10条记录
        for i, meta in enumerate(metadata):
            if i < 10 or i >= len(metadata) - 10:
                if meta and isinstance(meta, dict):
                    print(f"   索引 {i}: {meta}")
                else:
                    print(f"   索引 {i}: {type(meta)} - {meta}")
        
        if len(metadata) > 20:
            print(f"   ... 省略了 {len(metadata) - 20} 条记录 ...")
        
        # 分析所有记录
        image_records = []
        text_records = []
        table_records = []
        other_records = []
        
        for i, meta in enumerate(metadata):
            if meta and isinstance(meta, dict):
                # 检查是否有图片相关信息
                if ('image_path' in meta or 
                    'image_id' in meta or 
                    meta.get('type') == 'image' or
                    meta.get('chunk_type') == 'image'):
                    image_records.append((i, meta))
                elif 'page_content' in meta or 'source' in meta:
                    chunk_type = meta.get('chunk_type', 'text')
                    if chunk_type == 'text':
                        text_records.append((i, meta))
                    elif chunk_type == 'table':
                        table_records.append((i, meta))
                    else:
                        other_records.append((i, meta))
                else:
                    # 如果不符合上述条件，归类为其他
                    other_records.append((i, meta))
            else:
                # 空记录或非字典记录
                other_records.append((i, meta))
        
        print(f"\n📊 记录分析:")
        print(f"   - 图片记录: {len(image_records)}")
        print(f"   - 文本记录: {len(text_records)}")
        print(f"   - 表格记录: {len(table_records)}")
        print(f"   - 其他记录: {len(other_records)}")
        
        # 显示图片记录详情
        if image_records:
            print(f"\n🖼️  图片记录详情:")
            for idx, meta in image_records:
                print(f"   索引 {idx}:")
                print(f"     - 文档名称: {meta.get('document_name', 'N/A')}")
                print(f"     - 页码: {meta.get('page_number', 'N/A')}")
                print(f"     - 图片路径: {meta.get('image_path', 'N/A')}")
                print(f"     - 图片ID: {meta.get('image_id', 'N/A')}")
                print(f"     - 类型: {meta.get('chunk_type', 'N/A')}")
                print(f"     - 完整metadata: {meta}")
                print()
        
        # 显示一些文本记录示例
        if text_records:
            print(f"\n📄 文本记录示例 (前3条):")
            for idx, meta in text_records[:3]:
                print(f"   索引 {idx}:")
                print(f"     - 文档名称: {meta.get('document_name', 'N/A')}")
                print(f"     - 页码: {meta.get('page_number', 'N/A')}")
                print(f"     - 类型: {meta.get('chunk_type', 'N/A')}")
                print(f"     - 内容预览: {meta.get('page_content', 'N/A')[:100]}...")
                print()
        
        # 检查是否有图片相关的文本描述
        print(f"\n🔍 检查是否有图片相关的文本描述:")
        image_related_text = []
        for idx, meta in text_records:
            content = meta.get('page_content', '')
            if any(keyword in content.lower() for keyword in ['图片', '图表', '图', 'image', 'chart', 'figure']):
                image_related_text.append((idx, meta))
        
        print(f"   找到 {len(image_related_text)} 条包含图片相关描述的文本记录")
        for idx, meta in image_related_text[:3]:
            print(f"   索引 {idx}: {meta.get('page_content', '')[:200]}...")
        
    except Exception as e:
        print(f"❌ 读取metadata.pkl失败: {e}")

if __name__ == "__main__":
    check_metadata_images() 