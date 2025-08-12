#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除记忆后测试记忆功能
"""

import requests
import json
import time

def test_memory_after_clear():
    """清除记忆后测试记忆功能"""
    
    base_url = "http://127.0.0.1:5000"
    test_user_id = "test_user"
    
    print("🧹 清除记忆后测试记忆功能")
    print("=" * 50)
    
    # 1. 清除test_user的记忆
    print(f"🗑️  清除 {test_user_id} 的记忆...")
    try:
        response = requests.post(
            f"{base_url}/api/v2/memory/clear",
            json={"user_id": test_user_id}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 记忆清除成功: {result.get('message', '')}")
        else:
            print(f"❌ 记忆清除失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 2. 获取清除后的记忆统计
    print(f"\n📊 获取清除后的记忆统计...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats?user_id={test_user_id}")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 清除后记忆统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 3. 发送测试问题
    print(f"\n🔍 发送测试问题到 {test_user_id}...")
    test_question = f"清除后测试记忆功能 - {int(time.time())}"
    
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
    
    # 4. 等待系统处理
    print("\n⏳ 等待系统处理...")
    time.sleep(2)
    
    # 5. 获取更新后的记忆统计
    print(f"\n📊 获取更新后的记忆统计...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats?user_id={test_user_id}")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 更新后记忆统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
            
            # 6. 比较记忆数量变化
            initial_session = 0  # 清除后应该是0
            updated_session = stats['stats']['session_memory_count']
            initial_user = 0     # 清除后应该是0
            updated_user = stats['stats']['user_memory_count']
            
            print(f"\n📈 记忆数量变化:")
            print(f"  会话记忆: {initial_session} → {updated_session} ({'✅ 增加' if updated_session > initial_session else '❌ 未变化'})")
            print(f"  用户记忆: {initial_user} → {updated_user} ({'✅ 增加' if updated_user > initial_user else '❌ 未变化'})")
            
            if updated_session > initial_session or updated_user > initial_user:
                print("\n🎉 记忆功能修复成功！")
            else:
                print("\n⚠️  记忆功能可能仍有问题")
                
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_memory_after_clear()
