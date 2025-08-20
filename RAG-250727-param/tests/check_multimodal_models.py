#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查MultiModalEmbedding.Models中可用的模型名称
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def check_multimodal_models():
    """检查可用的多模态模型"""
    try:
        from dashscope import MultiModalEmbedding
        
        print("可用的MultiModalEmbedding模型:")
        print("="*50)
        
        # 查看Models类的所有属性
        for attr_name in dir(MultiModalEmbedding.Models):
            if not attr_name.startswith('_'):
                attr_value = getattr(MultiModalEmbedding.Models, attr_name)
                print(f"  {attr_name}: {attr_value}")
        
        print("\n" + "="*50)
        print("检查是否支持 multimodal-embedding-v1:")
        
        # 直接测试 multimodal-embedding-v1
        try:
            # 尝试使用字符串直接调用
            print("测试1: 使用字符串 'multimodal-embedding-v1'")
            test_result = MultiModalEmbedding.call(
                model='multimodal-embedding-v1',
                input=[{'text': '测试文本'}]
            )
            print(f"  结果: {test_result.status_code}")
            if test_result.status_code == 200:
                embedding = test_result.output.get("embedding") or test_result.output.get("embeddings")
                if embedding:
                    if isinstance(embedding, list) and len(embedding) > 0:
                        if isinstance(embedding[0], dict):
                            dim = len(embedding[0].get('embedding', []))
                        else:
                            dim = len(embedding)
                        print(f"  成功！向量维度: {dim}")
                    else:
                        print(f"  成功！输出格式: {type(embedding)}")
        except Exception as e:
            print(f"  失败: {e}")
        
        print("\n" + "="*50)
        print("检查完成")
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_multimodal_models()
