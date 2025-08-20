#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查MultiModalEmbedding.Models中实际可用的模型名称
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dashscope import MultiModalEmbedding
    import dashscope
    
    print("=" * 80)
    print("检查MultiModalEmbedding.Models中可用的模型")
    print("=" * 80)
    
    # 检查Models类的所有属性
    print("MultiModalEmbedding.Models的所有属性:")
    for attr_name in dir(MultiModalEmbedding.Models):
        if not attr_name.startswith('_'):
            attr_value = getattr(MultiModalEmbedding.Models, attr_name)
            print(f"  {attr_name} = {attr_value}")
    
    print("\n" + "=" * 80)
    print("测试直接调用multimodal-embedding-v1")
    print("=" * 80)
    
    # 设置API密钥
    from config.api_key_manager import APIKeyManager
    api_key_manager = APIKeyManager()
    api_keys = api_key_manager.get_all_api_keys()
    api_key = api_keys.get('dashscope')
    dashscope.api_key = api_key
    
    # 尝试直接调用
    try:
        result = MultiModalEmbedding.call(
            model='multimodal-embedding-v1',
            input=[{'text': '测试文本'}]
        )
        print(f"✅ 直接调用成功: {result.status_code}")
        if hasattr(result, 'output') and result.output:
            if 'embeddings' in result.output:
                embedding = result.output['embeddings'][0]['embedding']
                print(f"   向量维度: {len(embedding)}")
            elif 'embedding' in result.output:
                embedding = result.output['embedding']
                print(f"   向量维度: {len(embedding)}")
            else:
                print(f"   输出结构: {result.output}")
    except Exception as e:
        print(f"❌ 直接调用失败: {e}")
    
    print("\n" + "=" * 80)
    print("测试使用Models属性调用")
    print("=" * 80)
    
    # 尝试使用Models属性调用
    for attr_name in dir(MultiModalEmbedding.Models):
        if not attr_name.startswith('_'):
            attr_value = getattr(MultiModalEmbedding.Models, attr_name)
            print(f"\n尝试调用模型: {attr_name} = {attr_value}")
            try:
                result = MultiModalEmbedding.call(
                    model=attr_value,
                    input=[{'text': '测试文本'}]
                )
                print(f"✅ 调用成功: {result.status_code}")
                if hasattr(result, 'output') and result.output:
                    if 'embeddings' in result.output:
                        embedding = result.output['embeddings'][0]['embedding']
                        print(f"   向量维度: {len(embedding)}")
                    elif 'embedding' in result.output:
                        embedding = result.output['embedding']
                        print(f"   向量维度: {len(embedding)}")
                    else:
                        print(f"   输出结构: {result.output}")
            except Exception as e:
                print(f"❌ 调用失败: {e}")
    
except Exception as e:
    print(f"导入或执行失败: {e}")
    import traceback
    traceback.print_exc()
