'''
程序说明：
## 1. 该脚本用于检查向量数据库metadata.pkl中是否包含图片相关的元数据
## 2. 验证系统是否使用ONE-PEACE模型处理图片
'''

import pickle
import os
import sys

def load_metadata(metadata_path):
    """
    加载向量数据库的元数据
    :param metadata_path: metadata.pkl文件路径
    :return: 元数据列表
    """
    try:
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        return metadata
    except Exception as e:
        print(f"加载元数据时出错: {e}")
        return None

def analyze_metadata(metadata):
    """
    分析元数据，检查是否包含图片相关信息
    :param metadata: 元数据列表
    :return: 分析结果
    """
    if not metadata:
        return "元数据为空"
    
    # 统计不同chunk_type的数量
    chunk_types = {}
    image_count = 0
    
    for item in metadata:
        chunk_type = item.get('chunk_type', 'unknown')
        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        if chunk_type == 'image':
            image_count += 1
    
    result = f"元数据统计:\n"
    for chunk_type, count in chunk_types.items():
        result += f"  {chunk_type}: {count}\n"
    
    result += f"\n图片相关元数据:\n"
    if image_count > 0:
        result += f"  发现 {image_count} 条图片相关的元数据\n"
        
        # 提取一些图片信息作为示例
        image_samples = []
        for item in metadata:
            if item.get('chunk_type') == 'image' and len(image_samples) < 3:
                image_samples.append({
                    'document_name': item.get('document_name', ''),
                    'image_id': item.get('image_id', ''),
                    'image_path': item.get('image_path', ''),
                })
        
        result += "  示例图片信息:\n"
        for i, sample in enumerate(image_samples, 1):
            result += f"    {i}. Document: {sample['document_name']}, Image ID: {sample['image_id']}, Path: {sample['image_path']}\n"
    else:
        result += "  未发现图片相关的元数据\n"
    
    return result

def check_one_peace_usage(image_processor_path):
    """检查是否使用ONE-PEACE模型
    :param image_processor_path: image_processor.py文件路径
    :return: 检查结果
    """
    try:
        with open(image_processor_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含ONE-PEACE相关代码
        if 'ONE-PEACE' in content or 'one_peace' in content or 'multimodal_embedding_one_peace' in content:
            return "系统使用ONE-PEACE模型处理图片"
        else:
            return "系统未使用ONE-PEACE模型处理图片"
    except Exception as e:
        return f"检查ONE-PEACE模型使用情况时出错: {e}"

def main():
    """
    主函数
    """
    # 定义文件路径
    metadata_path = "vector_db_test/metadata.pkl"
    image_processor_path = "document_processing/image_processor.py"
    
    print("开始检查向量数据库中的图片元数据...")
    
    # 检查文件是否存在
    if not os.path.exists(metadata_path):
        print(f"错误: 找不到元数据文件 {metadata_path}")
        sys.exit(1)
    
    if not os.path.exists(image_processor_path):
        print(f"错误: 找不到图片处理器文件 {image_processor_path}")
        sys.exit(1)
    
    # 加载元数据
    metadata = load_metadata(metadata_path)
    if metadata is None:
        print("错误: 无法加载元数据")
        sys.exit(1)
    
    # 分析元数据
    print(analyze_metadata(metadata))
    
    # 检查ONE-PEACE模型使用情况
    print("检查ONE-PEACE模型使用情况...")
    print(check_one_peace_usage(image_processor_path))

if __name__ == "__main__":
    main()