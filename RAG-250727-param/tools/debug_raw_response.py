#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示API的原始响应，查看完整的数据结构
"""

import requests
import json

def debug_raw_response():
    """显示API的原始响应"""
    
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
            
            # 显示完整的响应结构
            print("\n📋 完整响应结构:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
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
    print("🧪 显示API原始响应")
    print("=" * 60)
    debug_raw_response()
