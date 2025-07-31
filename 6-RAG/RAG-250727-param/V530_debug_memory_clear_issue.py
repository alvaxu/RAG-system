'''
程序说明：
## 1. 调试记忆清除问题
## 2. 分析记忆管理器的工作流程
## 3. 验证清除功能是否正确执行
## 4. 检查文件读写操作
'''

import os
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.memory_manager import MemoryManager
from config.settings import Settings

def debug_memory_clear_issue():
    """
    调试记忆清除问题
    """
    print("🔍 开始调试记忆清除问题...")
    
    # 1. 检查文件状态
    config = Settings()
    memory_dir = config.memory_db_dir
    session_file = os.path.join(memory_dir, 'session_memory.json')
    user_file = os.path.join(memory_dir, 'user_memory.json')
    
    print(f"\n📁 文件路径:")
    print(f"  记忆目录: {memory_dir}")
    print(f"  会话记忆文件: {session_file}")
    print(f"  用户记忆文件: {user_file}")
    
    # 2. 检查文件是否存在
    print(f"\n📋 文件状态:")
    print(f"  会话记忆文件存在: {os.path.exists(session_file)}")
    print(f"  用户记忆文件存在: {os.path.exists(user_file)}")
    
    if os.path.exists(session_file):
        file_size = os.path.getsize(session_file)
        print(f"  会话记忆文件大小: {file_size} 字节")
        
        # 读取文件内容
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
                user_count = len(data.keys())
                total_memories = sum(len(memories) for memories in data.values())
                print(f"  用户数量: {user_count}")
                print(f"  总记忆数: {total_memories}")
                
                # 显示每个用户的记忆数量
                for user_id, memories in data.items():
                    print(f"    用户 {user_id}: {len(memories)} 条记忆")
        except Exception as e:
            print(f"  读取文件失败: {e}")
    
    # 3. 初始化记忆管理器
    print(f"\n🧠 初始化记忆管理器...")
    memory_manager = MemoryManager(memory_dir)
    
    # 4. 检查内存状态
    print(f"\n💾 内存状态:")
    session_users = len(memory_manager.session_memory.keys())
    user_users = len(memory_manager.user_memory.keys())
    total_session = sum(len(items) for items in memory_manager.session_memory.values())
    total_user = sum(len(items) for items in memory_manager.user_memory.values())
    
    print(f"  会话记忆用户数: {session_users}")
    print(f"  用户记忆用户数: {user_users}")
    print(f"  会话记忆总数: {total_session}")
    print(f"  用户记忆总数: {total_user}")
    
    # 5. 测试清除功能
    print(f"\n🧹 测试清除功能...")
    
    # 清除所有记忆
    print("  清除所有记忆...")
    memory_manager.clear_session_memory(None)  # 清除所有会话记忆
    memory_manager.clear_user_memory(None)     # 清除所有用户记忆
    
    # 检查清除后的状态
    print(f"\n✅ 清除后状态:")
    session_users_after = len(memory_manager.session_memory.keys())
    user_users_after = len(memory_manager.user_memory.keys())
    total_session_after = sum(len(items) for items in memory_manager.session_memory.values())
    total_user_after = sum(len(items) for items in memory_manager.user_memory.values())
    
    print(f"  会话记忆用户数: {session_users_after}")
    print(f"  用户记忆用户数: {user_users_after}")
    print(f"  会话记忆总数: {total_session_after}")
    print(f"  用户记忆总数: {total_user_after}")
    
    # 6. 检查文件是否被清除
    print(f"\n📄 检查文件状态:")
    if os.path.exists(session_file):
        file_size_after = os.path.getsize(session_file)
        print(f"  会话记忆文件大小: {file_size_after} 字节")
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                content_after = f.read()
                if content_after.strip() == '{}':
                    print("  ✅ 会话记忆文件已正确清除")
                else:
                    print("  ❌ 会话记忆文件未正确清除")
                    print(f"  文件内容: {content_after[:200]}...")
        except Exception as e:
            print(f"  读取文件失败: {e}")
    
    # 7. 模拟添加新记忆
    print(f"\n➕ 模拟添加新记忆...")
    memory_manager.add_to_session(
        user_id="default_user",
        question="测试问题",
        answer="测试回答",
        context={"test": "data"}
    )
    
    # 检查添加后的状态
    print(f"\n📊 添加记忆后状态:")
    session_users_final = len(memory_manager.session_memory.keys())
    total_session_final = sum(len(items) for items in memory_manager.session_memory.values())
    
    print(f"  会话记忆用户数: {session_users_final}")
    print(f"  会话记忆总数: {total_session_final}")
    
    # 8. 检查文件是否被重新创建
    print(f"\n📄 最终文件状态:")
    if os.path.exists(session_file):
        file_size_final = os.path.getsize(session_file)
        print(f"  会话记忆文件大小: {file_size_final} 字节")
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                content_final = f.read()
                data_final = json.loads(content_final)
                print(f"  文件内容用户数: {len(data_final.keys())}")
                for user_id, memories in data_final.items():
                    print(f"    用户 {user_id}: {len(memories)} 条记忆")
        except Exception as e:
            print(f"  读取文件失败: {e}")
    
    print(f"\n🎯 调试完成！")

if __name__ == '__main__':
    debug_memory_clear_issue() 