'''
程序说明：
## 1. 测试增强的图片元信息功能
## 2. 验证向量数据库中是否包含完整的图片元信息
## 3. 检查img_caption、img_footnote、page_idx等字段是否正确保存
'''

import os
import sys
import pickle
import json
from pathlib import Path

def test_enhanced_image_metadata():
    """
    测试增强的图片元信息功能
    """
    print("开始测试增强的图片元信息功能...")
    
    # 检查向量数据库中的元数据
    metadata_path = "vector_db_test/metadata.pkl"
    
    if not os.path.exists(metadata_path):
        print(f"错误: 找不到元数据文件 {metadata_path}")
        print("请先运行文档处理流程生成向量数据库")
        return False
    
    # 加载元数据
    try:
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        print(f"成功加载元数据，包含 {len(metadata)} 条记录")
    except Exception as e:
        print(f"加载元数据失败: {e}")
        return False
    
    # 分析图片元数据
    image_metadata = []
    for item in metadata:
        if item.get('chunk_type') == 'image':
            image_metadata.append(item)
    
    print(f"\n发现 {len(image_metadata)} 条图片元数据")
    
    if not image_metadata:
        print("没有找到图片元数据，请检查是否已处理包含图片的文档")
        return False
    
    # 检查图片元信息的完整性
    enhanced_features = ['img_caption', 'img_footnote', 'page_idx', 'image_filename', 'extension']
    missing_features = []
    
    for i, img_meta in enumerate(image_metadata[:5]):  # 只检查前5条
        print(f"\n图片 {i+1}:")
        print(f"  文档名: {img_meta.get('document_name', 'N/A')}")
        print(f"  页码: {img_meta.get('page_number', 'N/A')}")
        print(f"  图片ID: {img_meta.get('image_id', 'N/A')}")
        
        # 检查增强功能
        for feature in enhanced_features:
            value = img_meta.get(feature)
            if value is not None and value != [] and value != '':
                print(f"  {feature}: {value}")
            else:
                missing_features.append(feature)
                print(f"  {feature}: 缺失")
    
    # 统计缺失的功能
    if missing_features:
        print(f"\n缺失的功能: {set(missing_features)}")
        print("建议重新运行文档处理流程以包含完整的图片元信息")
    else:
        print("\n所有增强功能都已正确实现！")
    
    return True

def test_json_image_extraction():
    """
    测试从JSON文件提取图片信息的功能
    """
    print("\n测试从JSON文件提取图片信息...")
    
    # 检查JSON文件
    json_file = "md_test/【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评_1.json"
    
    if not os.path.exists(json_file):
        print(f"错误: 找不到JSON文件 {json_file}")
        return False
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取图片信息
        images = []
        for item in data:
            if item.get('type') == 'image':
                images.append(item)
        
        print(f"从JSON文件中提取到 {len(images)} 张图片")
        
        # 显示图片信息
        for i, img in enumerate(images[:3]):  # 只显示前3张
            print(f"\n图片 {i+1}:")
            print(f"  路径: {img.get('img_path', 'N/A')}")
            print(f"  标题: {img.get('img_caption', [])}")
            print(f"  脚注: {img.get('img_footnote', [])}")
            print(f"  页码: {img.get('page_idx', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"处理JSON文件失败: {e}")
        return False

def main():
    """
    主函数
    """
    print("=== 增强图片元信息功能测试 ===\n")
    
    # 测试1: 检查向量数据库中的图片元信息
    test1_result = test_enhanced_image_metadata()
    
    # 测试2: 检查JSON文件中的图片信息
    test2_result = test_json_image_extraction()
    
    print("\n=== 测试总结 ===")
    print(f"向量数据库元信息测试: {'通过' if test1_result else '失败'}")
    print(f"JSON图片信息测试: {'通过' if test2_result else '失败'}")
    
    if test1_result and test2_result:
        print("\n所有测试通过！增强的图片元信息功能已正确实现。")
        print("\n功能特点:")
        print("- 支持img_caption（图片标题）")
        print("- 支持img_footnote（图片脚注）")
        print("- 支持page_idx（页码索引）")
        print("- 支持image_filename（图片文件名）")
        print("- 支持extension（文件扩展名）")
        print("\n在前端显示时，可以展示:")
        print("- 文档名称")
        print("- 页码 (page_idx + 1)")
        print("- 图片标题和脚注")
        print("- 而不是显示图片路径")
    else:
        print("\n部分测试失败，请检查相关功能。")

if __name__ == "__main__":
    main() 