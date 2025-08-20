#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试multimodal-embedding-v1对纯文本输入的实际向量维度
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dashscope import MultiModalEmbedding
    import dashscope
    
    print("=" * 80)
    print("测试multimodal-embedding-v1对纯文本输入的向量维度")
    print("=" * 80)
    
    # 设置API密钥
    from config.api_key_manager import APIKeyManager
    api_key_manager = APIKeyManager()
    dashscope_key, mineru_key = api_key_manager.get_all_api_keys()
    dashscope.api_key = dashscope_key
    
    print(f"✅ API密钥设置成功")
    
    # 测试纯文本输入
    test_text = "中芯国际全球部署"
    print(f"\n测试文本: {test_text}")
    
    try:
        result = MultiModalEmbedding.call(
            model='multimodal-embedding-v1',
            input=[{'text': test_text}],
            auto_truncation=True
        )
        
        print(f"✅ API调用成功: {result.status_code}")
        
        if hasattr(result, 'output') and result.output:
            print(f"输出结构: {list(result.output.keys())}")
            
            if 'embeddings' in result.output:
                embedding = result.output['embeddings'][0]['embedding']
                print(f"   向量维度: {len(embedding)}")
                print(f"   向量类型: {type(embedding)}")
                print(f"   向量前5个值: {embedding[:5]}")
            elif 'embedding' in result.output:
                embedding = result.output['embedding']
                print(f"   向量维度: {len(embedding)}")
                print(f"   向量类型: {type(embedding)}")
                print(f"   向量前5个值: {embedding[:5]}")
            else:
                print(f"   完整输出: {result.output}")
        else:
            print(f"❌ 没有输出内容")
            
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    
except Exception as e:
    print(f"导入或执行失败: {e}")
    import traceback
    traceback.print_exc()
