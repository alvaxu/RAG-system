#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片处理器实际是如何生成1536维向量的
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dashscope import MultiModalEmbedding
    import dashscope
    
    print("=" * 80)
    print("测试图片处理器实际是如何生成1536维向量的")
    print("=" * 80)
    
    # 设置API密钥
    from config.api_key_manager import APIKeyManager
    api_key_manager = APIKeyManager()
    dashscope_key, mineru_key = api_key_manager.get_all_api_keys()
    dashscope.api_key = dashscope_key
    
    print(f"✅ API密钥设置成功")
    
    # 测试1：检查MultiModalEmbedding.Models中是否有multimodal_embedding_v1
    print(f"\n--- 测试1：检查Models属性 ---")
    print(f"MultiModalEmbedding.Models的所有属性:")
    for attr_name in dir(MultiModalEmbedding.Models):
        if not attr_name.startswith('_'):
            attr_value = getattr(MultiModalEmbedding.Models, attr_name)
            print(f"  {attr_name} = {attr_value}")
    
    # 测试2：模拟图片处理器的getattr调用
    print(f"\n--- 测试2：模拟图片处理器的getattr调用 ---")
    image_embedding_model = "multimodal-embedding-v1"
    print(f"配置的模型名称: {image_embedding_model}")
    
    try:
        model_attr = getattr(MultiModalEmbedding.Models, image_embedding_model)
        print(f"✅ getattr成功: {model_attr}")
    except AttributeError as e:
        print(f"❌ getattr失败: {e}")
        print(f"这说明图片处理器中的getattr调用会失败！")
    
    # 测试3：检查是否有异常处理逻辑
    print(f"\n--- 测试3：检查异常处理逻辑 ---")
    try:
        # 模拟图片处理器的逻辑
        image_embedding_model = "multimodal-embedding-v1"
        model_attr = getattr(MultiModalEmbedding.Models, image_embedding_model)
        print(f"✅ 直接调用成功: {model_attr}")
    except AttributeError:
        print(f"❌ 直接调用失败，尝试使用默认值")
        # 检查是否有默认值处理
        if hasattr(MultiModalEmbedding.Models, 'multimodal_embedding_one_peace_v1'):
            default_model = MultiModalEmbedding.Models.multimodal_embedding_one_peace_v1
            print(f"✅ 使用默认模型: {default_model}")
        else:
            print(f"❌ 没有可用的默认模型")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    
except Exception as e:
    print(f"导入或执行失败: {e}")
    import traceback
    traceback.print_exc()
