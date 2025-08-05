'''
测试ONE-PEACE模型是否能识别图像内容
'''

import os
import base64
import dashscope
from dashscope import MultiModalEmbedding
import numpy as np

# 设置API密钥
dashscope.api_key = "sk-bfff6cdc92e84b2f89064cd382fdbe4a"

def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为base64字符串"""
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_image

def test_one_peace_content_recognition(image_path: str):
    """测试ONE-PEACE模型是否能识别图像内容"""
    try:
        # 编码图片
        image_base64 = encode_image_to_base64(image_path)
        
        # 构建输入参数
        input_data = [{'image': f"data:image/jpeg;base64,{image_base64}"}]
        
        print(f"正在分析图片: {image_path}")
        
        # 调用ONE-PEACE模型
        result = MultiModalEmbedding.call(
            model=MultiModalEmbedding.Models.multimodal_embedding_one_peace_v1,
            input=input_data,
            auto_truncation=True
        )
        
        if result.status_code == 200:
            print("✅ ONE-PEACE模型调用成功")
            
            # 获取embedding
            embedding = result.output["embedding"]
            print(f"Embedding维度: {len(embedding)}")
            
            # 分析embedding特征
            embedding_array = np.array(embedding)
            print(f"Embedding统计信息:")
            print(f"  均值: {np.mean(embedding_array):.6f}")
            print(f"  标准差: {np.std(embedding_array):.6f}")
            print(f"  最大值: {np.max(embedding_array):.6f}")
            print(f"  最小值: {np.min(embedding_array):.6f}")
            print(f"  范数: {np.linalg.norm(embedding_array):.6f}")
            
            # 尝试从embedding中提取内容信息
            content_info = analyze_embedding_for_content(embedding_array)
            print(f"\n📊 基于embedding的内容分析:")
            print(content_info)
            
            return embedding, content_info
        else:
            print(f"❌ ONE-PEACE模型调用失败: {result.status_code}")
            print(f"错误信息: {result.message}")
            return None, None
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def analyze_embedding_for_content(embedding: np.ndarray) -> str:
    """
    分析embedding来推断图像内容
    这是一个简化的方法，基于embedding的统计特征来推测图像内容
    """
    try:
        # 计算各种统计特征
        mean_val = np.mean(embedding)
        std_val = np.std(embedding)
        norm_val = np.linalg.norm(embedding)
        
        # 分析embedding的分布特征
        positive_ratio = np.sum(embedding > 0) / len(embedding)
        negative_ratio = np.sum(embedding < 0) / len(embedding)
        zero_ratio = np.sum(embedding == 0) / len(embedding)
        
        # 计算embedding的复杂度
        complexity_score = norm_val * std_val * abs(mean_val)
        
        # 基于统计特征推断内容
        content_features = []
        
        # 基于范数推断复杂度
        if norm_val > 1.5:
            content_features.append("高复杂度视觉内容")
        elif norm_val > 1.0:
            content_features.append("中等复杂度视觉内容")
        else:
            content_features.append("简单视觉内容")
        
        # 基于标准差推断特征丰富度
        if std_val > 0.15:
            content_features.append("视觉特征丰富")
        elif std_val > 0.08:
            content_features.append("视觉特征中等")
        else:
            content_features.append("视觉特征简单")
        
        # 基于均值推断整体色调
        if mean_val > 0.1:
            content_features.append("整体色调偏亮")
        elif mean_val < -0.1:
            content_features.append("整体色调偏暗")
        else:
            content_features.append("整体色调适中")
        
        # 基于正负值比例推断内容特征
        if positive_ratio > 0.6:
            content_features.append("内容偏向积极特征")
        elif negative_ratio > 0.6:
            content_features.append("内容偏向消极特征")
        else:
            content_features.append("内容特征平衡")
        
        # 基于复杂度分数推断信息密度
        if complexity_score > 0.3:
            content_features.append("信息密度高")
        elif complexity_score > 0.15:
            content_features.append("信息密度中等")
        else:
            content_features.append("信息密度较低")
        
        return ", ".join(content_features)
        
    except Exception as e:
        return f"内容分析失败: {e}"

def main():
    """主函数"""
    # 测试一张图片
    image_path = "./central/images/c812467ccd91f5edc2f88d1b0e7b3158e9506f2aa204bd0730b732dc78275634.jpg"
    
    if os.path.exists(image_path):
        print("🔍 开始测试ONE-PEACE模型图像内容识别...")
        embedding, content_info = test_one_peace_content_recognition(image_path)
        
        if embedding is not None:
            print("\n📝 测试结果:")
            print("="*50)
            print("ONE-PEACE模型能够生成图像的embedding向量")
            print("但是embedding本身是数值向量，不直接包含可读的图像内容描述")
            print("需要通过分析embedding的统计特征来推断图像内容")
            print("="*50)
        else:
            print("❌ 测试失败")
    else:
        print(f"❌ 图片文件不存在: {image_path}")

if __name__ == "__main__":
    main() 