'''
程序说明：
## 1. 彻底清理记忆数据脚本
## 2. 只保留default_user的数据，删除所有其他用户数据
## 3. 确保清理彻底，包括test_user等所有其他用户
'''

import json
import os
from pathlib import Path

def clean_memory_data_complete():
    """
    彻底清理记忆数据，只保留default_user的数据
    """
    memory_dir = Path("memory_db")
    session_file = memory_dir / "session_memory.json"
    user_file = memory_dir / "user_memory.json"
    
    print("开始彻底清理记忆数据...")
    
    # 清理会话记忆
    if session_file.exists():
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            print(f"清理前用户数量: {len(session_data.keys())}")
            print(f"清理前用户列表: {list(session_data.keys())}")
            
            # 只保留default_user的数据
            cleaned_session_data = {}
            if "default_user" in session_data:
                cleaned_session_data["default_user"] = session_data["default_user"]
                print(f"保留default_user的会话记忆: {len(session_data['default_user'])}条")
            else:
                print("警告: 没有找到default_user的数据")
            
            # 删除其他所有用户数据
            removed_users = [user for user in session_data.keys() if user != "default_user"]
            print(f"删除其他用户数据: {len(removed_users)}个用户")
            print(f"删除的用户列表: {removed_users}")
            
            # 保存清理后的数据
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_session_data, f, ensure_ascii=False, indent=2)
            
            print("会话记忆清理完成")
            
        except Exception as e:
            print(f"清理会话记忆失败: {e}")
    
    # 清理用户记忆
    if user_file.exists():
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            print(f"清理前用户记忆用户数量: {len(user_data.keys())}")
            print(f"清理前用户记忆用户列表: {list(user_data.keys())}")
            
            # 只保留default_user的数据
            cleaned_user_data = {}
            if "default_user" in user_data:
                cleaned_user_data["default_user"] = user_data["default_user"]
                print(f"保留default_user的用户记忆: {len(user_data['default_user'])}条")
            else:
                print("警告: 没有找到default_user的用户记忆数据")
            
            # 删除其他所有用户数据
            removed_users = [user for user in user_data.keys() if user != "default_user"]
            print(f"删除其他用户记忆数据: {len(removed_users)}个用户")
            print(f"删除的用户记忆用户列表: {removed_users}")
            
            # 保存清理后的数据
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_user_data, f, ensure_ascii=False, indent=2)
            
            print("用户记忆清理完成")
            
        except Exception as e:
            print(f"清理用户记忆失败: {e}")
    
    print("记忆数据彻底清理完成！")
    
    # 验证清理结果
    print("\n验证清理结果:")
    if session_file.exists():
        with open(session_file, 'r', encoding='utf-8') as f:
            final_session_data = json.load(f)
        print(f"清理后会话记忆用户数量: {len(final_session_data.keys())}")
        print(f"清理后会话记忆用户列表: {list(final_session_data.keys())}")
    
    if user_file.exists():
        with open(user_file, 'r', encoding='utf-8') as f:
            final_user_data = json.load(f)
        print(f"清理后用户记忆用户数量: {len(final_user_data.keys())}")
        print(f"清理后用户记忆用户列表: {list(final_user_data.keys())}")

if __name__ == "__main__":
    clean_memory_data_complete() 