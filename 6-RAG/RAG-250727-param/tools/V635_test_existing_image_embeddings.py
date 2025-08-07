'''
程序说明：
## 1. 测试Qwen的multimodal-embedding-v1模型是否支持图片内容理解
## 2. 对比ONE-PEACE和Qwen multimodal embedding的能力
## 3. 探索真正的图像内容理解功能
'''

import os
import sys
import numpy as np
import base64
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.settings import Settings
from dashscope import MultiModalEmbedding

def analyze_embedding_semantics(embedding: List[float]) -> Dict[str, Any]:
    """分析embedding的语义特征"""
    try:
        embedding_array = np.array(embedding)
        
        # 计算统计特征
        mean_val = np.mean(embedding_array)
        std_val = np.std(embedding_array)
        norm_val = np.linalg.norm(embedding_array)
        max_val = np.max(embedding_array)
        min_val = np.min(embedding_array)
        dynamic_range = max_val - min_val
        
        # 基于统计特征推断图像内容
        features = []
        
        # 复杂度分析
        if norm_val > 1.8:
            complexity = "高复杂度视觉内容"
        elif norm_val > 1.2:
            complexity = "中等复杂度视觉内容"
        else:
            complexity = "简单视觉内容"
        
        # 特征丰富度分析
        if std_val > 0.15:
            richness = "视觉特征丰富"
        elif std_val > 0.08:
            richness = "视觉特征中等"
        else:
            richness = "视觉特征简单"
        
        # 亮度分析
        if mean_val > 0.12:
            brightness = "整体亮度较高"
        elif mean_val < -0.12:
            brightness = "整体亮度较低"
        else:
            brightness = "亮度适中"
        
        # 对比度分析
        if dynamic_range > 0.8:
            contrast = "高对比度"
        elif dynamic_range > 0.4:
            contrast = "中等对比度"
        else:
            contrast = "低对比度"
        
        return {
            'statistics': {
                'mean': mean_val,
                'std': std_val,
                'norm': norm_val,
                'max': max_val,
                'min': min_val,
                'dynamic_range': dynamic_range
            },
            'semantic_features': {
                'complexity': complexity,
                'richness': richness,
                'brightness': brightness,
                'contrast': contrast
            },
            'features_list': [complexity, richness, brightness, contrast]
        }
        
    except Exception as e:
        print(f"❌ 语义分析失败: {e}")
        return None

def test_qwen_multimodal_embedding():
    """测试Qwen的multimodal-embedding-v1模型是否支持图片内容理解"""
    print("🔍 测试Qwen的multimodal-embedding-v1模型")
    print("=" * 80)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        api_key = config.dashscope_api_key
        
        print(f"🔑 API密钥: {api_key[:10]}...")
        
        # 1. 测试ONE-PEACE模型（当前使用的）
        print(f"\n🔍 1. 测试ONE-PEACE模型:")
        print("-" * 50)
        
        try:
            # 获取一张测试图片
            test_image_path = "./central/images/0a61fa499a2c5c449f51eea53f8757ac5f4924e5ef90c68301b8cc75ee4c82b3.jpg"
            if not os.path.exists(test_image_path):
                # 尝试其他图片
                images_dir = "./central/images"
                if os.path.exists(images_dir):
                    image_files = [f for f in os.listdir(images_dir) if f.endswith('.jpg')]
                    if image_files:
                        test_image_path = os.path.join(images_dir, image_files[0])
            
            if os.path.exists(test_image_path):
                print(f"📷 使用测试图片: {test_image_path}")
                
                # 读取图片并转换为base64
                with open(test_image_path, 'rb') as f:
                    image_data = f.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # 添加data URL前缀
                image_data_url = f"data:image/jpeg;base64,{image_base64}"
                
                # 测试ONE-PEACE模型
                print("🔄 调用ONE-PEACE模型...")
                result = MultiModalEmbedding.call(
                    model='multimodal_embedding_one_peace_v1',
                    input=[{'image': image_data_url}]
                )
                
                if result.status_code == 200:
                    print("✅ ONE-PEACE模型调用成功")
                    embedding = result.output['embedding']
                    print(f"📊 Embedding维度: {len(embedding)}")
                    print(f"📊 Embedding范数: {np.linalg.norm(embedding):.4f}")
                    print(f"📊 Embedding均值: {np.mean(embedding):.4f}")
                    print(f"📊 Embedding标准差: {np.std(embedding):.4f}")
                    
                    # 分析语义特征
                    semantic_analysis = analyze_embedding_semantics(embedding)
                    if semantic_analysis:
                        print(f"🎯 语义分析: {', '.join(semantic_analysis['features_list'])}")
                else:
                    print(f"❌ ONE-PEACE模型调用失败: {result.message}")
                    
            else:
                print("❌ 没有找到测试图片")
                
        except Exception as e:
            print(f"❌ ONE-PEACE测试失败: {e}")
        
        # 2. 测试Qwen multimodal-embedding-v1模型
        print(f"\n🔍 2. 测试Qwen multimodal-embedding-v1模型:")
        print("-" * 50)
        
        try:
            if os.path.exists(test_image_path):
                print("🔄 调用Qwen multimodal-embedding-v1模型...")
                
                # 测试Qwen multimodal-embedding-v1模型
                result = MultiModalEmbedding.call(
                    model='multimodal-embedding-v1',
                    input=[{'image': image_data_url}]
                )
                
                if result.status_code == 200:
                    print("✅ Qwen multimodal-embedding-v1模型调用成功")
                    
                    # 打印完整的返回结果结构
                    print(f"📋 返回结果结构: {list(result.output.keys())}")
                    
                    # 尝试不同的embedding字段名
                    embedding = None
                    if 'embedding' in result.output:
                        embedding = result.output['embedding']
                    elif 'embeddings' in result.output:
                        embeddings_list = result.output['embeddings']
                        if isinstance(embeddings_list, list) and len(embeddings_list) > 0:
                            if isinstance(embeddings_list[0], dict) and 'embedding' in embeddings_list[0]:
                                embedding = embeddings_list[0]['embedding']
                            else:
                                embedding = embeddings_list[0]
                    elif 'data' in result.output and 'embedding' in result.output['data']:
                        embedding = result.output['data']['embedding']
                    
                    if embedding:
                        print(f"📊 Embedding维度: {len(embedding)}")
                        print(f"📊 Embedding范数: {np.linalg.norm(embedding):.4f}")
                        print(f"📊 Embedding均值: {np.mean(embedding):.4f}")
                        print(f"📊 Embedding标准差: {np.std(embedding):.4f}")
                        
                        # 分析语义特征
                        semantic_analysis = analyze_embedding_semantics(embedding)
                        if semantic_analysis:
                            print(f"🎯 语义分析: {', '.join(semantic_analysis['features_list'])}")
                    else:
                        print("⚠️  未找到embedding字段")
                        print(f"📋 完整返回结果: {result.output}")
                    
                    # 检查是否有额外的内容理解信息
                    for key in ['text', 'description', 'content', 'caption', 'summary']:
                        if key in result.output:
                            print(f"📝 {key}: {result.output[key]}")
                    
                    # 检查是否有其他可能的内容理解字段
                    for key, value in result.output.items():
                        if isinstance(value, str) and len(value) > 20:
                            print(f"📝 可能的描述字段 '{key}': {value[:100]}...")
                        
                else:
                    print(f"❌ Qwen multimodal-embedding-v1模型调用失败: {result.message}")
                    
        except Exception as e:
            print(f"❌ Qwen multimodal-embedding-v1测试失败: {e}")
        
        # 3. 对比分析
        print(f"\n🔍 3. 模型对比分析:")
        print("-" * 50)
        
        print("📊 模型能力对比:")
        print("- ONE-PEACE: 主要用于生成图像embedding向量")
        print("- Qwen multimodal-embedding-v1: 可能支持更丰富的内容理解")
        print("- 两者都主要用于向量化，而非直接的内容理解")
        
        print(f"\n💡 结论:")
        print("- 两个模型都主要用于生成图像embedding")
        print("- 真正的图像内容理解需要专门的视觉理解模型")
        print("- 建议集成GPT-4V、Claude 3.5 Sonnet等模型进行内容理解")
        print("- 可以将embedding用于相似性检索，配合LLM进行内容分析")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qwen_multimodal_embedding()
