#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试API返回结构
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.api_key_manager import get_dashscope_api_key
from config.settings import Settings

def debug_api_response():
    """调试API返回结构"""
    try:
        # 获取API密钥
        config = Settings.load_from_file('config.json')
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return
        
        print("✅ API密钥获取成功")
        
        # 设置API密钥
        import dashscope
        dashscope.api_key = api_key
        
        # 调用API
        from dashscope import MultiModalEmbedding
        print("🚀 调用API...")
        
        result = MultiModalEmbedding.call(
            model='multimodal-embedding-v1',
            input=[{'text': '测试查询'}]
        )
        
        print(f"✅ API调用成功，状态码: {result.status_code}")
        print(f"📊 结果类型: {type(result)}")
        print(f"🔍 结果属性: {dir(result)}")
        
        # 检查status_code
        if hasattr(result, 'status_code'):
            print(f"📡 状态码: {result.status_code}")
        
        # 检查output
        if hasattr(result, 'output'):
            print(f"📤 输出类型: {type(result.output)}")
            print(f"📤 输出属性: {dir(result.output)}")
            print(f"📤 输出内容: {result.output}")
        else:
            print("❌ 没有output属性")
        
        # 检查其他可能的属性
        for attr in ['data', 'result', 'embedding', 'embeddings']:
            if hasattr(result, attr):
                print(f"✅ 找到属性 {attr}: {getattr(result, attr)}")
        
        # 尝试访问常见的属性
        try:
            if hasattr(result, 'output') and hasattr(result.output, 'embedding'):
                print(f"🎯 通过result.output.embedding访问: {result.output.embedding}")
        except Exception as e:
            print(f"❌ 访问result.output.embedding失败: {e}")
        
        try:
            if hasattr(result, 'output') and hasattr(result.output, 'embeddings'):
                print(f"🎯 通过result.output.embeddings访问: {result.output.embeddings}")
        except Exception as e:
            print(f"❌ 访问result.output.embeddings失败: {e}")
        
        # 打印完整的result内容
        print(f"\n📋 完整结果内容:")
        print(result)
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_response()
