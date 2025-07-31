'''
程序说明：
## 1. 直接测试记忆管理器脚本
## 2. 模拟API调用，检查记忆管理器状态
## 3. 验证数据加载和API响应的一致性
'''

import json
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.memory_manager import MemoryManager

def test_memory_manager_direct():
    """
    直接测试记忆管理器
    """
    print("=== 直接测试记忆管理器 ===")
    
    # 1. 初始化记忆管理器
    print("\n1. 初始化记忆管理器:")
    memory_manager = MemoryManager("memory_db")
    
    # 2. 检查内存状态
    print("\n2. 内存状态:")
    print(f"会话记忆用户数量: {len(memory_manager.session_memory.keys())}")
    print(f"会话记忆用户列表: {list(memory_manager.session_memory.keys())}")
    for user_id, items in memory_manager.session_memory.items():
        print(f"  - {user_id}: {len(items)}条记忆")
    
    print(f"用户记忆用户数量: {len(memory_manager.user_memory.keys())}")
    print(f"用户记忆用户列表: {list(memory_manager.user_memory.keys())}")
    for user_id, items in memory_manager.user_memory.items():
        print(f"  - {user_id}: {len(items)}条记忆")
    
    # 3. 模拟API调用 - 获取default_user的统计
    print("\n3. 模拟API调用 - 获取default_user统计:")
    try:
        stats = memory_manager.get_memory_stats("default_user")
        print(f"API响应: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
        # 验证数据一致性
        session_count = len(memory_manager.session_memory.get("default_user", []))
        user_count = len(memory_manager.user_memory.get("default_user", []))
        total_count = session_count + user_count
        
        print(f"直接计算 - 会话记忆: {session_count}")
        print(f"直接计算 - 用户记忆: {user_count}")
        print(f"直接计算 - 总记忆: {total_count}")
        
        print(f"API返回 - 会话记忆: {stats.get('session_memory_count', 0)}")
        print(f"API返回 - 用户记忆: {stats.get('user_memory_count', 0)}")
        print(f"API返回 - 总记忆: {stats.get('total_memory_count', 0)}")
        
        # 检查一致性
        if (session_count == stats.get('session_memory_count', 0) and 
            user_count == stats.get('user_memory_count', 0) and
            total_count == stats.get('total_memory_count', 0)):
            print("✓ 数据一致性检查通过")
        else:
            print("✗ 数据一致性检查失败")
            
    except Exception as e:
        print(f"获取统计失败: {e}")
    
    # 4. 模拟API调用 - 获取全局统计
    print("\n4. 模拟API调用 - 获取全局统计:")
    try:
        all_stats = memory_manager.get_memory_stats()
        print(f"全局统计: {json.dumps(all_stats, ensure_ascii=False, indent=2)}")
        
        # 验证全局数据一致性
        total_session = sum(len(items) for items in memory_manager.session_memory.values())
        total_user = sum(len(items) for items in memory_manager.user_memory.values())
        total_users = len(set(list(memory_manager.session_memory.keys()) + list(memory_manager.user_memory.keys())))
        
        print(f"直接计算 - 总会话记忆: {total_session}")
        print(f"直接计算 - 总用户记忆: {total_user}")
        print(f"直接计算 - 总用户数: {total_users}")
        
        print(f"API返回 - 总会话记忆: {all_stats.get('total_session_memory', 0)}")
        print(f"API返回 - 总用户记忆: {all_stats.get('total_user_memory', 0)}")
        print(f"API返回 - 总用户数: {all_stats.get('total_users', 0)}")
        
        # 检查一致性
        if (total_session == all_stats.get('total_session_memory', 0) and 
            total_user == all_stats.get('total_user_memory', 0) and
            total_users == all_stats.get('total_users', 0)):
            print("✓ 全局数据一致性检查通过")
        else:
            print("✗ 全局数据一致性检查失败")
            
    except Exception as e:
        print(f"获取全局统计失败: {e}")
    
    # 5. 检查文件状态
    print("\n5. 文件状态检查:")
    session_file = Path("memory_db/session_memory.json")
    user_file = Path("memory_db/user_memory.json")
    
    if session_file.exists():
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            print(f"文件中的会话记忆用户: {list(session_data.keys())}")
            for user_id, items in session_data.items():
                print(f"  - {user_id}: {len(items)}条记忆")
    
    if user_file.exists():
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            print(f"文件中的用户记忆用户: {list(user_data.keys())}")
            for user_id, items in user_data.items():
                print(f"  - {user_id}: {len(items)}条记忆")
    
    print("\n=== 直接测试完成 ===")

if __name__ == "__main__":
    test_memory_manager_direct() 