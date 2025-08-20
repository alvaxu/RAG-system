#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试multimodal-embedding-v1的不同调用方式和参数
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dashscope import MultiModalEmbedding
    import dashscope
    
    print("=" * 80)
    print("全面测试multimodal-embedding-v1的不同调用方式")
    print("=" * 80)
    
    # 设置API密钥
    from config.api_key_manager import APIKeyManager
    api_key_manager = APIKeyManager()
    dashscope_key, mineru_key = api_key_manager.get_all_api_keys()
    dashscope.api_key = dashscope_key
    
    print(f"✅ API密钥设置成功")
    
    # 测试不同的调用方式
    test_text = "中芯国际全球部署"
    print(f"\n测试文本: {test_text}")
    
    test_cases = [
        {
            "name": "纯文本输入 - 基础调用",
            "model": "multimodal-embedding-v1",
            "input": [{'text': test_text}],
            "params": {}
        },
        {
            "name": "纯文本输入 - 带auto_truncation",
            "model": "multimodal-embedding-v1", 
            "input": [{'text': test_text}],
            "params": {"auto_truncation": True}
        },
        {
            "name": "纯文本输入 - 带模态类型",
            "model": "multimodal-embedding-v1",
            "input": [{'text': test_text, 'modality': 'text'}],
            "params": {"auto_truncation": True}
        },
        {
            "name": "使用Models枚举",
            "model": MultiModalEmbedding.Models.multimodal_embedding_one_peace_v1,
            "input": [{'text': test_text}],
            "params": {"auto_truncation": True}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {test_case['name']} ---")
        
        try:
            result = MultiModalEmbedding.call(
                model=test_case['model'],
                input=test_case['input'],
                **test_case['params']
            )
            
            print(f"✅ API调用成功: {result.status_code}")
            
            if hasattr(result, 'output') and result.output:
                print(f"   输出结构: {list(result.output.keys())}")
                
                embedding = None
                if 'embeddings' in result.output:
                    embedding = result.output['embeddings'][0]['embedding']
                    print(f"   从embeddings[0]['embedding']获取")
                elif 'embedding' in result.output:
                    embedding = result.output['embedding']
                    print(f"   从embedding获取")
                
                if embedding:
                    print(f"   向量维度: {len(embedding)}")
                    print(f"   向量类型: {type(embedding)}")
                    print(f"   向量前3个值: {embedding[:3]}")
                    print(f"   向量范围: [{min(embedding):.6f}, {max(embedding):.6f}]")
                else:
                    print(f"   ❌ 无法获取embedding")
                    print(f"   完整输出: {result.output}")
            else:
                print(f"   ❌ 没有输出内容")
                print(f"   响应: {result}")
                
        except Exception as e:
            print(f"   ❌ API调用失败: {e}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    
except Exception as e:
    print(f"导入或执行失败: {e}")
    import traceback
    traceback.print_exc()
