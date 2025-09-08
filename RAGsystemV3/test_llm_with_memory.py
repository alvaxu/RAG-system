#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM是否能理解包含历史记忆的prompt
"""

import requests
import json
import time

def test_llm_with_memory():
    """测试LLM是否能理解包含历史记忆的prompt"""
    print("🧠 测试LLM理解能力")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # 第1步：创建会话并询问中芯国际
    print("📝 第1步：询问中芯国际是什么公司")
    try:
        response1 = requests.post(f"{base_url}/api/v3/rag/query", json={
            "query": "中芯国际是什么公司？",
            "query_type": "text",
            "user_id": "test_user"
        }, timeout=30)
        
        if response1.status_code == 200:
            data1 = response1.json()
            session_id = data1.get('session_id')
            print(f"✅ 创建会话: {session_id}")
            print(f"🤖 第1轮回答: {data1.get('answer', '')[:200]}...")
        else:
            print(f"❌ 第1轮请求失败: {response1.status_code}")
            return
    except Exception as e:
        print(f"❌ 第1轮请求异常: {e}")
        return
    
    time.sleep(2)
    
    # 第2步：询问"它的主要业务是什么？"
    print("\n📝 第2步：询问它的主要业务是什么？")
    try:
        response2 = requests.post(f"{base_url}/api/v3/rag/query", json={
            "query": "它的主要业务是什么？",
            "query_type": "text",
            "user_id": "test_user",
            "session_id": session_id
        }, timeout=30)
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"🤖 第2轮回答: {data2.get('answer', '')}")
            print(f"🧠 记忆增强: {'使用历史记忆' if data2.get('processing_metadata', {}).get('memory_enhanced') else '未使用历史记忆'}")
            
            # 检查回答是否理解"它"指中芯国际
            answer = data2.get('answer', '')
            if '中芯国际' in answer or 'SMIC' in answer:
                print("✅ LLM正确理解了'它'指中芯国际")
            else:
                print("❌ LLM没有理解'它'指中芯国际")
        else:
            print(f"❌ 第2轮请求失败: {response2.status_code}")
    except Exception as e:
        print(f"❌ 第2轮请求异常: {e}")

if __name__ == "__main__":
    test_llm_with_memory()
