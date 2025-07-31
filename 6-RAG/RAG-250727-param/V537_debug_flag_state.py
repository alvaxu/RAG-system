'''
程序说明：
## 1. 调试memory_cleared_flag状态
## 2. 检查问答过程中的标志位变化
## 3. 验证记忆保存逻辑
'''

import requests
import json

def debug_flag_state():
    """调试标志位状态"""
    
    base_url = "http://localhost:5000/api"
    
    print("=== 调试标志位状态 ===")
    
    # 1. 检查初始状态
    print("\n1. 检查初始记忆状态:")
    try:
        response = requests.get(f"{base_url}/memory/stats?user_id=default_user")
        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print(f"   初始会话记忆: {stats.get('session_memory_count', 0)}")
    except Exception as e:
        print(f"   ❌ 检查初始状态失败: {e}")
    
    # 2. 清除记忆
    print("\n2. 清除记忆:")
    try:
        response = requests.post(f"{base_url}/memory/clear", json={
            "user_id": None,
            "memory_type": "all"
        })
        if response.status_code == 200:
            print("   ✓ 记忆清除成功")
        else:
            print(f"   ❌ 记忆清除失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 清除记忆异常: {e}")
    
    # 3. 检查清除后的状态
    print("\n3. 检查清除后的状态:")
    try:
        response = requests.get(f"{base_url}/memory/stats?user_id=default_user")
        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print(f"   清除后会话记忆: {stats.get('session_memory_count', 0)}")
    except Exception as e:
        print(f"   ❌ 检查清除后状态失败: {e}")
    
    # 4. 进行问答测试（第一次）
    print("\n4. 进行第一次问答测试:")
    try:
        response = requests.post(f"{base_url}/qa/ask", json={
            "question": "测试问题1",
            "user_id": "default_user",
            "use_memory": True,
            "k": 5
        })
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✓ 第一次问答成功")
                print(f"   回答长度: {len(data.get('answer', ''))}")
            else:
                print(f"   ❌ 第一次问答失败: {data.get('error')}")
        else:
            print(f"   ❌ 第一次问答请求失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 第一次问答异常: {e}")
    
    # 5. 检查第一次问答后的状态
    print("\n5. 检查第一次问答后的状态:")
    try:
        response = requests.get(f"{base_url}/memory/stats?user_id=default_user")
        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print(f"   第一次问答后会话记忆: {stats.get('session_memory_count', 0)}")
            
            if stats.get('session_memory_count', 0) > 0:
                print("   ✓ 第一次记忆保存成功")
            else:
                print("   ❌ 第一次记忆保存失败")
        else:
            print(f"   ❌ 检查第一次问答后状态失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 检查第一次问答后状态异常: {e}")
    
    # 6. 进行问答测试（第二次）
    print("\n6. 进行第二次问答测试:")
    try:
        response = requests.post(f"{base_url}/qa/ask", json={
            "question": "测试问题2",
            "user_id": "default_user",
            "use_memory": True,
            "k": 5
        })
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✓ 第二次问答成功")
                print(f"   回答长度: {len(data.get('answer', ''))}")
            else:
                print(f"   ❌ 第二次问答失败: {data.get('error')}")
        else:
            print(f"   ❌ 第二次问答请求失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 第二次问答异常: {e}")
    
    # 7. 检查第二次问答后的状态
    print("\n7. 检查第二次问答后的状态:")
    try:
        response = requests.get(f"{base_url}/memory/stats?user_id=default_user")
        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print(f"   第二次问答后会话记忆: {stats.get('session_memory_count', 0)}")
            
            if stats.get('session_memory_count', 0) > 0:
                print("   ✓ 第二次记忆保存成功")
            else:
                print("   ❌ 第二次记忆保存失败")
        else:
            print(f"   ❌ 检查第二次问答后状态失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 检查第二次问答后状态异常: {e}")
    
    print("\n=== 调试完成 ===")

if __name__ == "__main__":
    debug_flag_state() 