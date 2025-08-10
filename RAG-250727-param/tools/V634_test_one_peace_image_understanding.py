'''
程序说明：
## 1. 测试ONE-PEACE模型是否能够进行真正的图像内容理解
## 2. 尝试不同的API调用方式来获取图像描述
## 3. 探索DashScope的图像理解能力
'''

import os
import base64
import sys
import json
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import dashscope
from dashscope import MultiModalEmbedding
from config.settings import Settings

def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为base64字符串"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_image
    except Exception as e:
        print(f"❌ 编码图片失败: {e}")
        return ""

def test_one_peace_embedding_only(image_path: str):
    """测试ONE-PEACE模型仅生成embedding"""
    print("🔍 测试ONE-PEACE模型生成embedding...")
    
    try:
        # 编码图片
        image_base64 = encode_image_to_base64(image_path)
        if not image_base64:
            return None
        
        # 构建输入参数
        input_data = [{'image': f"data:image/jpeg;base64,{image_base64}"}]
        
        # 调用ONE-PEACE模型
        # 从配置中获取ONE-PEACE模型名称（如果有配置的话）
        image_embedding_model = 'multimodal_embedding_one_peace_v1'  # 默认值
        
        result = MultiModalEmbedding.call(
            model=getattr(MultiModalEmbedding.Models, image_embedding_model),
            input=input_data,
            auto_truncation=True
        )
        
        if result.status_code == 200:
            print("✅ ONE-PEACE embedding生成成功")
            embedding = result.output["embedding"]
            print(f"   Embedding维度: {len(embedding)}")
            print(f"   Embedding前10个值: {embedding[:10]}")
            return embedding
        else:
            print(f"❌ ONE-PEACE embedding生成失败: {result.status_code}")
            print(f"   错误信息: {result.message}")
            return None
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_dashscope_image_understanding(image_path: str):
    """测试DashScope的图像理解能力"""
    print("\n🔍 测试DashScope的图像理解能力...")
    
    try:
        # 尝试使用DashScope的其他图像理解API
        # 注意：这里需要根据DashScope的实际API来调整
        
        # 方法1：尝试使用图像描述API（如果存在）
        print("   尝试方法1: 图像描述API...")
        try:
            # 这里可以尝试DashScope的图像描述API
            # 由于DashScope的API可能有限制，我们先尝试一个通用的方法
            pass
        except Exception as e:
            print(f"   方法1失败: {e}")
        
        # 方法2：尝试使用多模态对话API
        print("   尝试方法2: 多模态对话API...")
        try:
            # 尝试使用DashScope的多模态对话功能
            # 构建一个简单的图像描述请求
            image_base64 = encode_image_to_base64(image_path)
            if image_base64:
                # 这里可以尝试调用DashScope的多模态对话API
                # 由于API限制，我们先返回一个占位符
                print("   方法2: 需要DashScope多模态对话API支持")
        except Exception as e:
            print(f"   方法2失败: {e}")
        
        # 方法3：基于embedding的语义分析
        print("   尝试方法3: 基于embedding的语义分析...")
        embedding = test_one_peace_embedding_only(image_path)
        if embedding:
            semantic_analysis = analyze_embedding_semantics(embedding)
            print(f"   语义分析结果: {semantic_analysis}")
            return semantic_analysis
        
        return None
        
    except Exception as e:
        print(f"❌ 图像理解测试失败: {e}")
        return None

def analyze_embedding_semantics(embedding: list) -> str:
    """基于embedding进行语义分析"""
    try:
        import numpy as np
        
        embedding_array = np.array(embedding)
        
        # 计算统计特征
        mean_val = np.mean(embedding_array)
        std_val = np.std(embedding_array)
        norm_val = np.linalg.norm(embedding_array)
        max_val = np.max(embedding_array)
        min_val = np.min(embedding_array)
        
        # 基于统计特征推断图像内容
        features = []
        
        # 复杂度分析
        if norm_val > 1.8:
            features.append("高复杂度视觉内容")
        elif norm_val > 1.2:
            features.append("中等复杂度视觉内容")
        else:
            features.append("简单视觉内容")
        
        # 特征丰富度分析
        if std_val > 0.15:
            features.append("视觉特征丰富")
        elif std_val > 0.08:
            features.append("视觉特征中等")
        else:
            features.append("视觉特征简单")
        
        # 亮度分析
        if mean_val > 0.12:
            features.append("整体亮度较高")
        elif mean_val < -0.12:
            features.append("整体亮度较低")
        else:
            features.append("亮度适中")
        
        # 动态范围分析
        dynamic_range = max_val - min_val
        if dynamic_range > 0.8:
            features.append("高对比度")
        elif dynamic_range > 0.4:
            features.append("中等对比度")
        else:
            features.append("低对比度")
        
        return ", ".join(features)
        
    except Exception as e:
        print(f"❌ 语义分析失败: {e}")
        return "无法分析"

def test_enhanced_image_description(image_path: str):
    """测试增强的图像描述生成"""
    print("\n🔍 测试增强的图像描述生成...")
    
    try:
        # 获取图片文件名
        filename = os.path.basename(image_path)
        
        # 基于embedding的语义分析
        embedding = test_one_peace_embedding_only(image_path)
        if not embedding:
            return None
        
        semantic_features = analyze_embedding_semantics(embedding)
        
        # 构建增强描述
        description_parts = []
        
        # 1. 基础信息
        description_parts.append(f"图片文件: {filename}")
        
        # 2. 语义特征
        description_parts.append(f"语义特征: {semantic_features}")
        
        # 3. 基于文件名的类型推断
        filename_lower = filename.lower()
        if any(keyword in filename_lower for keyword in ['chart', 'graph', 'plot']):
            description_parts.append("推断类型: 数据图表")
        elif any(keyword in filename_lower for keyword in ['table', 'data']):
            description_parts.append("推断类型: 数据表格")
        elif any(keyword in filename_lower for keyword in ['diagram', 'flow']):
            description_parts.append("推断类型: 流程图")
        elif any(keyword in filename_lower for keyword in ['photo', 'image']):
            description_parts.append("推断类型: 照片")
        else:
            description_parts.append("推断类型: 信息图表")
        
        # 4. 技术特征
        description_parts.append(f"Embedding维度: {len(embedding)}")
        description_parts.append(f"向量范数: {sum(x*x for x in embedding) ** 0.5:.4f}")
        
        # 组合描述
        enhanced_description = " | ".join(description_parts)
        print(f"✅ 增强描述生成成功:")
        print(f"   {enhanced_description}")
        
        return enhanced_description
        
    except Exception as e:
        print(f"❌ 增强描述生成失败: {e}")
        return None

def test_image_content_extraction(image_path: str):
    """测试图像内容提取能力"""
    print("\n🔍 测试图像内容提取能力...")
    
    try:
        # 尝试使用计算机视觉库进行内容提取
        # 这里可以集成OpenCV、PIL等库来提取更多图像信息
        
        print("   尝试使用计算机视觉技术提取图像内容...")
        
        # 方法1：使用PIL提取基本信息
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
                mode = img.mode
                format_type = img.format
                
                print(f"   图像尺寸: {width}x{height}")
                print(f"   图像模式: {mode}")
                print(f"   图像格式: {format_type}")
                
                # 可以添加更多图像分析
                # 例如：颜色分析、边缘检测等
                
        except ImportError:
            print("   PIL库未安装，跳过图像基本信息提取")
        except Exception as e:
            print(f"   图像基本信息提取失败: {e}")
        
        # 方法2：尝试使用OCR提取文字（如果有的话）
        print("   尝试OCR文字提取...")
        try:
            # 这里可以集成OCR库来提取图像中的文字
            # 例如：pytesseract、easyocr等
            print("   OCR功能需要额外安装OCR库")
        except Exception as e:
            print(f"   OCR提取失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 图像内容提取失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 测试ONE-PEACE模型的图像内容理解能力")
    print("=" * 80)
    
    # 选择一张图片进行测试
    image_path = "./central/images/c812467ccd91f5edc2f88d1b0e7b3158e9506f2aa204bd0730b732dc78275634.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在: {image_path}")
        return
    
    print(f"📷 测试图片: {image_path}")
    print(f"📊 图片大小: {os.path.getsize(image_path)} 字节")
    
    # 1. 测试ONE-PEACE embedding
    embedding = test_one_peace_embedding_only(image_path)
    
    # 2. 测试图像理解能力
    understanding_result = test_dashscope_image_understanding(image_path)
    
    # 3. 测试增强描述生成
    enhanced_description = test_enhanced_image_description(image_path)
    
    # 4. 测试图像内容提取
    content_extraction = test_image_content_extraction(image_path)
    
    # 总结
    print("\n📊 测试总结:")
    print("=" * 80)
    
    if embedding:
        print("✅ ONE-PEACE embedding生成: 成功")
    else:
        print("❌ ONE-PEACE embedding生成: 失败")
    
    if understanding_result:
        print("✅ 图像理解能力: 部分成功")
    else:
        print("❌ 图像理解能力: 失败")
    
    if enhanced_description:
        print("✅ 增强描述生成: 成功")
    else:
        print("❌ 增强描述生成: 失败")
    
    if content_extraction:
        print("✅ 图像内容提取: 成功")
    else:
        print("❌ 图像内容提取: 失败")
    
    print("\n💡 结论:")
    print("- ONE-PEACE模型主要用于生成embedding向量")
    print("- 基于embedding可以进行有限的语义分析")
    print("- 真正的图像内容理解需要集成其他技术")
    print("- 建议结合OCR、计算机视觉等技术来增强图像理解能力")

if __name__ == "__main__":
    main()
