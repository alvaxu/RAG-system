'''
程序说明：
## 1. 模拟Flask应用的记忆管理器初始化
## 2. 检查工作目录和路径解析
## 3. 验证记忆加载是否正确
'''

import os
import sys
import json
from pathlib import Path

# 模拟Flask应用的路径设置
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.settings import Settings
from core.memory_manager import MemoryManager

def test_flask_memory_init():
    """测试Flask应用的记忆管理器初始化"""
    
    print("=== 测试Flask应用记忆初始化 ===")
    
    # 1. 检查当前工作目录
    print("\n1. 当前工作目录:")
    print(f"   当前目录: {os.getcwd()}")
    print(f"   项目根目录: {project_root}")
    
    # 2. 创建Settings实例（模拟Flask应用）
    print("\n2. 创建Settings实例:")
    try:
        settings = Settings()
        print(f"   记忆目录: {settings.memory_db_dir}")
        print(f"   记忆目录绝对路径: {os.path.abspath(settings.memory_db_dir)}")
        
        # 检查记忆目录是否存在
        memory_dir = Path(settings.memory_db_dir)
        print(f"   记忆目录存在: {memory_dir.exists()}")
        if memory_dir.exists():
            print(f"   记忆目录内容: {list(memory_dir.iterdir())}")
        
    except Exception as e:
        print(f"   ❌ Settings创建失败: {e}")
        return
    
    # 3. 创建MemoryManager实例（模拟Flask应用）
    print("\n3. 创建MemoryManager实例:")
    try:
        memory_manager = MemoryManager(settings.memory_db_dir)
        print("   ✓ MemoryManager创建成功")
        
        # 检查记忆文件路径
        print(f"   会话记忆文件: {memory_manager.session_memory_file}")
        print(f"   用户记忆文件: {memory_manager.user_memory_file}")
        
        # 检查记忆文件是否存在
        print(f"   会话记忆文件存在: {memory_manager.session_memory_file.exists()}")
        print(f"   用户记忆文件存在: {memory_manager.user_memory_file.exists()}")
        
    except Exception as e:
        print(f"   ❌ MemoryManager创建失败: {e}")
        return
    
    # 4. 检查加载的记忆
    print("\n4. 检查加载的记忆:")
    session_memories = memory_manager.session_memory.get("default_user", [])
    user_memories = memory_manager.user_memory.get("default_user", [])
    
    print(f"   内存中的会话记忆: {len(session_memories)} 条")
    print(f"   内存中的用户记忆: {len(user_memories)} 条")
    
    # 5. 测试记忆统计
    print("\n5. 测试记忆统计:")
    stats = memory_manager.get_memory_stats("default_user")
    print(f"   统计结果: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    # 6. 检查记忆文件内容
    print("\n6. 检查记忆文件内容:")
    if memory_manager.session_memory_file.exists():
        with open(memory_manager.session_memory_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            session_count = len(session_data.get("default_user", []))
            print(f"   文件中的会话记忆: {session_count} 条")
    
    if memory_manager.user_memory_file.exists():
        with open(memory_manager.user_memory_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
            user_count = len(user_data.get("default_user", []))
            print(f"   文件中的用户记忆: {user_count} 条")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_flask_memory_init() 