'''
程序说明：
## 1. 调试MemoryManager加载过程
## 2. 检查记忆文件状态
## 3. 验证记忆加载是否正确
'''

import json
import os
from pathlib import Path
from core.memory_manager import MemoryManager

def debug_memory_loading():
    """调试记忆加载过程"""
    
    print("=== 调试记忆加载过程 ===")
    
    # 1. 检查记忆文件状态
    print("\n1. 记忆文件状态:")
    session_file = Path("memory_db/session_memory.json")
    user_file = Path("memory_db/user_memory.json")
    
    if session_file.exists():
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            session_count = len(session_data.get("default_user", []))
            print(f"   会话记忆文件: 存在，{session_count} 条记录")
            print(f"   文件大小: {os.path.getsize(session_file)} 字节")
    else:
        print("   会话记忆文件: 不存在")
    
    if user_file.exists():
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            user_count = len(user_data.get("default_user", []))
            print(f"   用户记忆文件: 存在，{user_count} 条记录")
            print(f"   文件大小: {os.path.getsize(user_file)} 字节")
    else:
        print("   用户记忆文件: 不存在")
    
    # 2. 创建MemoryManager实例
    print("\n2. 创建MemoryManager实例:")
    try:
        memory_manager = MemoryManager()
        print("   ✓ MemoryManager创建成功")
        
        # 3. 检查加载的记忆
        print("\n3. 检查加载的记忆:")
        session_memories = memory_manager.session_memory.get("default_user", [])
        user_memories = memory_manager.user_memory.get("default_user", [])
        
        print(f"   内存中的会话记忆: {len(session_memories)} 条")
        print(f"   内存中的用户记忆: {len(user_memories)} 条")
        
        # 4. 测试记忆统计
        print("\n4. 测试记忆统计:")
        stats = memory_manager.get_memory_stats("default_user")
        print(f"   统计结果: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
        # 5. 测试记忆检索
        print("\n5. 测试记忆检索:")
        relevant_memories = memory_manager.retrieve_relevant_memory("default_user", "测试问题")
        print(f"   相关记忆数量: {len(relevant_memories)}")
        
    except Exception as e:
        print(f"   ❌ MemoryManager创建失败: {e}")
    
    print("\n=== 调试完成 ===")

if __name__ == "__main__":
    debug_memory_loading() 