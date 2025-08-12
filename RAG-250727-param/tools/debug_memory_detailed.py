#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试记忆管理器状态
"""

import requests
import json
import time

def debug_memory_detailed():
    """详细调试记忆管理器状态"""
    
    base_url = "http://127.0.0.1:5000"
    test_user_id = "test_user"
    
    print("🔍 详细调试记忆管理器状态")
    print("=" * 60)
    
    # 1. 获取系统状态
    print("📊 获取系统状态...")
    try:
        response = requests.get(f"{base_url}/api/v2/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 系统状态: {status.get('status', 'unknown')}")
            print(f"🧠 记忆管理器状态: {status.get('memory_manager_status', 'unknown')}")
        else:
            print(f"❌ 获取系统状态失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 2. 获取test_user的记忆统计
    print(f"\n📊 获取 {test_user_id} 的记忆统计...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats?user_id={test_user_id}")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 记忆统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 3. 获取default_user的记忆统计作为对比
    print(f"\n📊 获取 default_user 的记忆统计作为对比...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats?user_id=default_user")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 记忆统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 4. 发送测试问题
    print(f"\n🔍 发送测试问题到 {test_user_id}...")
    test_question = f"详细调试记忆功能 - {int(time.time())}"
    
    try:
        response = requests.post(
            f"{base_url}/api/v2/qa/ask",
            json={
                "question": test_question,
                "user_id": test_user_id,
                "use_memory": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 问题回答成功")
            print(f"📝 答案长度: {len(result.get('answer', ''))} 字符")
            print(f"🔍 问题: {test_question}")
        else:
            print(f"❌ 问题回答失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 5. 等待系统处理
    print("\n⏳ 等待系统处理...")
    time.sleep(3)
    
    # 6. 再次获取test_user的记忆统计
    print(f"\n📊 再次获取 {test_user_id} 的记忆统计...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats?user_id={test_user_id}")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 记忆统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 7. 检查记忆文件内容
    print(f"\n📁 检查记忆文件内容...")
    try:
        # 获取所有用户的记忆统计
        response = requests.get(f"{base_url}/api/v2/memory/stats")
        if response.status_code == 200:
            all_stats = response.json()
            print(f"✅ 所有用户记忆统计: {json.dumps(all_stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取所有用户记忆统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    debug_memory_detailed()
