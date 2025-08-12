#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试记忆功能修复
"""

import requests
import json
import time

def test_memory_functionality():
    """测试记忆功能是否正常工作"""
    
    base_url = "http://127.0.0.1:5000"
    test_user_id = "test_user"
    
    print("🧪 测试记忆功能修复")
    print("=" * 50)
    
    # 1. 获取初始记忆统计（指定test_user）
    print("📊 获取初始记忆统计...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats?user_id={test_user_id}")
        if response.status_code == 200:
            initial_stats = response.json()
            print(f"✅ 初始记忆统计: {json.dumps(initial_stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 2. 发送测试问题
    print("\n🔍 发送测试问题...")
    test_question = f"测试记忆功能是否正常工作 - {int(time.time())}"
    
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
    
    # 3. 等待一下让系统处理
    print("\n⏳ 等待系统处理...")
    time.sleep(2)
    
    # 4. 获取更新后的记忆统计（指定test_user）
    print("📊 获取更新后的记忆统计...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats?user_id={test_user_id}")
        if response.status_code == 200:
            updated_stats = response.json()
            print(f"✅ 更新后记忆统计: {json.dumps(updated_stats, indent=2, ensure_ascii=False)}")
            
            # 5. 比较记忆数量变化
            initial_session = initial_stats['stats']['session_memory_count']
            updated_session = updated_stats['stats']['session_memory_count']
            initial_user = initial_stats['stats']['user_memory_count']
            updated_user = updated_stats['stats']['user_memory_count']
            
            print(f"\n📈 记忆数量变化:")
            print(f"  会话记忆: {initial_session} → {updated_session}")
            print(f"  用户记忆: {initial_user} → {updated_user}")
            
            # 6. 检查记忆是否真的更新了（即使数量没有变化）
            print(f"\n🔍 检查记忆内容更新...")
            
            # 获取记忆文件内容，检查最新问题是否被记录
            try:
                with open('central/memory_db/conversation_contexts.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                test_user_context = data.get(test_user_id, {})
                last_question = test_user_context.get('last_question', '')
                conversation_history = test_user_context.get('conversation_history', [])
                
                print(f"  最新问题: {last_question}")
                print(f"  对话历史长度: {len(conversation_history)}")
                
                # 检查最新问题是否是我们刚才发送的
                if test_question in last_question:
                    print(f"  ✅ 最新问题已正确记录: {test_question}")
                    print(f"\n🎉 记忆功能正常工作！")
                else:
                    print(f"  ❌ 最新问题未正确记录")
                    print(f"     期望: {test_question}")
                    print(f"     实际: {last_question}")
                    
            except Exception as e:
                print(f"  ❌ 检查记忆文件失败: {e}")
                
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_memory_functionality()
