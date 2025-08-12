#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重排序引擎修复后的功能
"""

import requests
import json

def test_reranking():
    """测试重排序引擎是否正常工作"""
    
    url = "http://127.0.0.1:5000/api/v2/qa/ask"
    
    # 测试数据
    data = {
        "question": "中芯国际的主要业务和核心技术是什么？",
        "user_id": "test_user"
    }
    
    try:
        print("🔍 发送测试查询...")
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 查询成功!")
            
            # 检查是否有LLM答案
            if 'answer' in result and result['answer']:
                print(f"🤖 LLM答案长度: {len(result['answer'])} 字符")
                print(f"📝 答案预览: {result['answer'][:200]}...")
            else:
                print("❌ 没有找到LLM答案")
            
            # 检查来源信息
            if 'sources' in result and result['sources']:
                print(f"📚 找到 {len(result['sources'])} 个来源")
                for i, source in enumerate(result['sources'][:3]):  # 只显示前3个
                    print(f"  来源 {i+1}: {source.get('document_name', 'N/A')} - 第{source.get('page_number', 'N/A')}页")
            else:
                print("❌ 没有找到来源信息")
                
        else:
            print(f"❌ 查询失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    print("🧪 测试重排序引擎修复后的功能")
    print("=" * 50)
    test_reranking()
