#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单对话测试 - 只测试前两个问题
"""

import requests
import json
import time

def test_simple_conversation():
    """测试简单对话功能"""
    print("🧠 测试简单对话功能")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    session_id = None
    
    # 第1轮对话
    print("\n📝 第1轮对话")
    print("问题: 中芯国际是什么公司？")
    print("期望: 首次询问，应该没有历史记忆")
    print("-" * 40)
    
    try:
        response = requests.post(f"{base_url}/api/v3/rag/query", json={
            "query": "中芯国际是什么公司？",
            "query_type": "text",
            "user_id": "test_user"
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"✅ 创建会话: {session_id}")
            print(f"🤖 系统回答: {data.get('answer', '')[:200]}...")
            print(f"🧠 记忆增强: {'使用历史记忆' if data.get('processing_metadata', {}).get('memory_enhanced') else '未使用历史记忆'}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return
    
    time.sleep(2)
    
    # 第2轮对话
    print("\n📝 第2轮对话")
    print("问题: 它的主要业务是什么？")
    print("期望: 应该记住之前关于中芯国际的对话")
    print("-" * 40)
    
    try:
        response = requests.post(f"{base_url}/api/v3/rag/query", json={
            "query": "它的主要业务是什么？",
            "query_type": "text",
            "user_id": "test_user",
            "session_id": session_id
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 系统回答: {data.get('answer', '')[:200]}...")
            print(f"🧠 记忆增强: {'使用历史记忆' if data.get('processing_metadata', {}).get('memory_enhanced') else '未使用历史记忆'}")
            
            # 检查回答是否理解"它"指中芯国际
            answer = data.get('answer', '')
            if '中芯国际' in answer or 'SMIC' in answer:
                print("✅ 系统正确理解了'它'指中芯国际")
            else:
                print("❌ 系统没有理解'它'指中芯国际")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 简单对话测试完成")

if __name__ == "__main__":
    test_simple_conversation()
