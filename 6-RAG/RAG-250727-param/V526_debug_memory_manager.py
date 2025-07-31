'''
程序说明：
## 1. 记忆管理器调试脚本
## 2. 检查记忆管理器的状态和问题
## 3. 验证数据加载和保存是否正确
'''

import json
import os
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.memory_manager import MemoryManager

def debug_memory_manager():
    """
    调试记忆管理器
    """
    print("=== 记忆管理器调试 ===")
    
    # 1. 检查文件状态
    memory_dir = Path("memory_db")
    session_file = memory_dir / "session_memory.json"
    user_file = memory_dir / "user_memory.json"
    
    print(f"\n1. 文件状态检查:")
    print(f"记忆目录: {memory_dir}")
    print(f"会话记忆文件: {session_file} (存在: {session_file.exists()})")
    print(f"用户记忆文件: {user_file} (存在: {user_file.exists()})")
    
    if session_file.exists():
        print(f"会话记忆文件大小: {session_file.stat().st_size} 字节")
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            print(f"会话记忆用户数量: {len(session_data.keys())}")
            print(f"会话记忆用户列表: {list(session_data.keys())}")
            for user_id, items in session_data.items():
                print(f"  - {user_id}: {len(items)}条记忆")
    
    if user_file.exists():
        print(f"用户记忆文件大小: {user_file.stat().st_size} 字节")
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            print(f"用户记忆用户数量: {len(user_data.keys())}")
            print(f"用户记忆用户列表: {list(user_data.keys())}")
            for user_id, items in user_data.items():
                print(f"  - {user_id}: {len(items)}条记忆")
    
    # 2. 初始化记忆管理器
    print(f"\n2. 初始化记忆管理器:")
    memory_manager = MemoryManager("memory_db")
    
    # 3. 检查内存状态
    print(f"\n3. 内存状态检查:")
    print(f"会话记忆用户数量: {len(memory_manager.session_memory.keys())}")
    print(f"会话记忆用户列表: {list(memory_manager.session_memory.keys())}")
    for user_id, items in memory_manager.session_memory.items():
        print(f"  - {user_id}: {len(items)}条记忆")
    
    print(f"用户记忆用户数量: {len(memory_manager.user_memory.keys())}")
    print(f"用户记忆用户列表: {list(memory_manager.user_memory.keys())}")
    for user_id, items in memory_manager.user_memory.items():
        print(f"  - {user_id}: {len(items)}条记忆")
    
    # 4. 测试统计功能
    print(f"\n4. 统计功能测试:")
    default_user_stats = memory_manager.get_memory_stats("default_user")
    print(f"default_user统计: {default_user_stats}")
    
    all_stats = memory_manager.get_memory_stats()
    print(f"全局统计: {all_stats}")
    
    # 5. 测试清理功能
    print(f"\n5. 清理功能测试:")
    print("清理前状态:")
    print(f"  - 会话记忆: {len(memory_manager.session_memory.keys())}个用户")
    print(f"  - 用户记忆: {len(memory_manager.user_memory.keys())}个用户")
    
    # 清理非default_user的数据
    users_to_remove = [user for user in memory_manager.session_memory.keys() if user != "default_user"]
    for user_id in users_to_remove:
        memory_manager.clear_session_memory(user_id)
        print(f"  - 已清理用户 {user_id} 的会话记忆")
    
    users_to_remove = [user for user in memory_manager.user_memory.keys() if user != "default_user"]
    for user_id in users_to_remove:
        memory_manager.clear_user_memory(user_id)
        print(f"  - 已清理用户 {user_id} 的用户记忆")
    
    print("清理后状态:")
    print(f"  - 会话记忆: {len(memory_manager.session_memory.keys())}个用户")
    print(f"  - 用户记忆: {len(memory_manager.user_memory.keys())}个用户")
    
    # 6. 验证文件状态
    print(f"\n6. 清理后文件状态:")
    if session_file.exists():
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            print(f"会话记忆文件用户数量: {len(session_data.keys())}")
            print(f"会话记忆文件用户列表: {list(session_data.keys())}")
    
    if user_file.exists():
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            print(f"用户记忆文件用户数量: {len(user_data.keys())}")
            print(f"用户记忆文件用户列表: {list(user_data.keys())}")
    
    print("\n=== 调试完成 ===")

if __name__ == "__main__":
    debug_memory_manager() 