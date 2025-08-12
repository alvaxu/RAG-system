#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试来源信息显示功能
"""

import requests
import json

def test_source_display():
    """测试来源信息显示功能"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 测试来源信息显示功能")
    print("=" * 50)
    
    # 发送测试问题
    test_question = "中芯国际的主要业务和核心技术是什么？"
    
    try:
        response = requests.post(
            f"{base_url}/api/v2/qa/ask",
            json={
                "question": test_question,
                "user_id": "test_user",
                "use_memory": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 问题回答成功")
            print(f"📝 答案长度: {len(result.get('answer', ''))} 字符")
            print(f"🔍 问题: {test_question}")
            
            # 检查来源信息
            sources = result.get('sources', [])
            print(f"\n📊 来源信息:")
            print(f"  总数: {len(sources)} 个来源")
            
            if sources:
                print(f"\n📋 来源详情:")
                for i, source in enumerate(sources[:5]):  # 只显示前5个
                    print(f"  {i+1}. 文档名: {source.get('document_name', 'N/A')}")
                    print(f"     页码: {source.get('page_number', 'N/A')}")
                    print(f"     类型: {source.get('source_type', 'N/A')}")
                    print(f"     格式化来源: {source.get('formatted_source', 'N/A')}")
                    print(f"     内容预览: {source.get('content_preview', 'N/A')[:100]}...")
                    print()
                
                # 检查是否有formatted_source字段
                has_formatted = any('formatted_source' in source for source in sources)
                if has_formatted:
                    print("✅ 格式化来源信息字段存在")
                else:
                    print("❌ 格式化来源信息字段缺失")
            else:
                print("❌ 没有来源信息")
                
        else:
            print(f"❌ 问题回答失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_source_display()
