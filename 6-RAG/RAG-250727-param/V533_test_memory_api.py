'''
程序说明：
## 1. 测试记忆API响应
## 2. 检查记忆统计是否正确
## 3. 验证API返回的数据
'''

import requests
import json

def test_memory_api():
    """测试记忆API"""
    
    base_url = "http://localhost:5000/api"
    
    print("=== 测试记忆API ===")
    
    # 1. 测试记忆统计API
    print("\n1. 测试记忆统计API:")
    try:
        response = requests.get(f"{base_url}/memory/stats?user_id=default_user")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            if 'stats' in data:
                stats = data['stats']
                print(f"   会话记忆: {stats.get('session_memory_count', 0)}")
                print(f"   历史记忆: {stats.get('user_memory_count', 0)}")
                print(f"   总记忆数: {stats.get('total_memory_count', 0)}")
            else:
                print("   ❌ 响应中没有stats字段")
        else:
            print(f"   ❌ API请求失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
    
    # 2. 测试系统状态API
    print("\n2. 测试系统状态API:")
    try:
        response = requests.get(f"{base_url}/system/status")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"   ❌ API请求失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_memory_api() 