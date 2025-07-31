'''
程序说明：
## 1. 测试记忆API脚本
## 2. 验证记忆统计API是否正常工作
## 3. 检查前端和后端数据一致性
'''

import requests
import json

def test_memory_api():
    """
    测试记忆API
    """
    base_url = "http://localhost:5000/api"
    
    print("=== 记忆API测试 ===")
    
    # 1. 测试记忆统计API
    print("\n1. 测试记忆统计API:")
    try:
        response = requests.get(f"{base_url}/memory/stats?user_id=default_user")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            if data.get('success'):
                stats = data.get('stats', {})
                print(f"会话记忆数量: {stats.get('session_memory_count', 0)}")
                print(f"用户记忆数量: {stats.get('user_memory_count', 0)}")
                print(f"总记忆数量: {stats.get('total_memory_count', 0)}")
            else:
                print(f"API返回错误: {data.get('error')}")
        else:
            print(f"HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 2. 测试系统状态API
    print("\n2. 测试系统状态API:")
    try:
        response = requests.get(f"{base_url}/system/status")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"系统状态: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 3. 测试健康检查API
    print("\n3. 测试健康检查API:")
    try:
        response = requests.get(f"{base_url.replace('/api', '')}/health")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"健康状态: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n=== API测试完成 ===")

if __name__ == "__main__":
    test_memory_api() 