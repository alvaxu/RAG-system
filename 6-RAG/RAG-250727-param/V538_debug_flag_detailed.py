'''
程序说明：
## 1. 详细调试memory_cleared_flag状态变化
## 2. 检查清除记忆和问答过程中的标志位
## 3. 验证记忆保存逻辑的每个步骤
'''

import requests
import json
import time

def debug_flag_detailed():
    """详细调试标志位状态"""
    
    base_url = "http://localhost:5000/api"
    
    print("=== 详细调试标志位状态 ===")
    
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
    
    # 2. 检查系统状态
    print("\n2. 检查系统状态:")
    try:
        response = requests.get(f"{base_url}/system/status")
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            memory_stats = status.get('memory_stats', {})
            vector_stats = status.get('vector_store_stats', {})
            print(f"   记忆管理器状态: {status.get('memory_manager', False)}")
            print(f"   记忆统计: {memory_stats}")
            print(f"   向量存储统计: {vector_stats}")
    except Exception as e:
        print(f"   ❌ 检查系统状态失败: {e}")
    
    # 3. 清除记忆
    print("\n3. 清除记忆:")
    try:
        response = requests.post(f"{base_url}/memory/clear", json={
            "user_id": None,
            "memory_type": "all"
        })
        if response.status_code == 200:
            print("   ✓ 记忆清除成功")
            clear_data = response.json()
            print(f"   清除响应: {json.dumps(clear_data, ensure_ascii=False, indent=2)}")
        else:
            print(f"   ❌ 记忆清除失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 清除记忆异常: {e}")
    
    # 4. 检查清除后的状态
    print("\n4. 检查清除后的状态:")
    try:
        response = requests.get(f"{base_url}/memory/stats?user_id=default_user")
        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print(f"   清除后会话记忆: {stats.get('session_memory_count', 0)}")
    except Exception as e:
        print(f"   ❌ 检查清除后状态失败: {e}")
    
    # 5. 进行问答测试
    print("\n5. 进行问答测试:")
    try:
        response = requests.post(f"{base_url}/qa/ask", json={
            "question": "这是一个测试问题",
            "user_id": "default_user",
            "use_memory": True,
            "k": 5
        })
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✓ 问答成功")
                print(f"   回答长度: {len(data.get('answer', ''))}")
                print(f"   回答内容: {data.get('answer', '')[:100]}...")
            else:
                print(f"   ❌ 问答失败: {data.get('error')}")
        else:
            print(f"   ❌ 问答请求失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 问答异常: {e}")
    
    # 6. 检查问答后的状态
    print("\n6. 检查问答后的状态:")
    try:
        response = requests.get(f"{base_url}/memory/stats?user_id=default_user")
        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print(f"   问答后会话记忆: {stats.get('session_memory_count', 0)}")
            print(f"   问答后总记忆数: {stats.get('total_memory_count', 0)}")
            
            if stats.get('session_memory_count', 0) > 0:
                print("   ✓ 记忆保存成功")
            else:
                print("   ❌ 记忆保存失败")
        else:
            print(f"   ❌ 检查问答后状态失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 检查问答后状态异常: {e}")
    
    # 7. 再次检查系统状态
    print("\n7. 再次检查系统状态:")
    try:
        response = requests.get(f"{base_url}/system/status")
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            memory_stats = status.get('memory_stats', {})
            vector_stats = status.get('vector_store_stats', {})
            print(f"   记忆统计: {memory_stats}")
            print(f"   向量存储统计: {vector_stats}")
    except Exception as e:
        print(f"   ❌ 检查系统状态失败: {e}")
    
    print("\n=== 详细调试完成 ===")

if __name__ == "__main__":
    debug_flag_detailed() 