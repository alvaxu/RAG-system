'''
程序说明：
## 1. 测试记忆清除功能
## 2. 验证记忆统计是否正确
## 3. 检查记忆清除后是否真正清空
'''

import json
import os
from pathlib import Path

def test_memory_clear():
    """测试记忆清除功能"""
    
    # 记忆文件路径
    session_memory_file = Path("memory_db/session_memory.json")
    user_memory_file = Path("memory_db/user_memory.json")
    
    print("=== 测试记忆清除功能 ===")
    
    # 1. 检查当前记忆状态
    print("\n1. 当前记忆状态:")
    if session_memory_file.exists():
        with open(session_memory_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            print(f"   会话记忆文件大小: {os.path.getsize(session_memory_file)} 字节")
            print(f"   会话记忆内容: {json.dumps(session_data, ensure_ascii=False, indent=2)[:200]}...")
    else:
        print("   会话记忆文件不存在")
    
    if user_memory_file.exists():
        with open(user_memory_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            print(f"   用户记忆文件大小: {os.path.getsize(user_memory_file)} 字节")
            print(f"   用户记忆内容: {json.dumps(user_data, ensure_ascii=False, indent=2)[:200]}...")
    else:
        print("   用户记忆文件不存在")
    
    # 2. 手动清除记忆
    print("\n2. 手动清除记忆:")
    
    # 清除会话记忆
    if session_memory_file.exists():
        empty_session = {"default_user": []}
        with open(session_memory_file, 'w', encoding='utf-8') as f:
            json.dump(empty_session, f, ensure_ascii=False, indent=2)
        print("   ✓ 已清除会话记忆")
    
    # 清除用户记忆
    if user_memory_file.exists():
        empty_user = {"default_user": []}
        with open(user_memory_file, 'w', encoding='utf-8') as f:
            json.dump(empty_user, f, ensure_ascii=False, indent=2)
        print("   ✓ 已清除用户记忆")
    
    # 3. 验证清除结果
    print("\n3. 验证清除结果:")
    if session_memory_file.exists():
        with open(session_memory_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            session_count = len(session_data.get("default_user", []))
            print(f"   会话记忆数量: {session_count}")
    else:
        print("   会话记忆文件不存在")
    
    if user_memory_file.exists():
        with open(user_memory_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            user_count = len(user_data.get("default_user", []))
            print(f"   用户记忆数量: {user_count}")
    else:
        print("   用户记忆文件不存在")
    
    print("\n=== 测试完成 ===")
    print("现在请重新启动应用并测试记忆清除功能")

if __name__ == "__main__":
    test_memory_clear() 