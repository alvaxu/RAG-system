'''
程序说明：
## 1. 清理记忆数据脚本
## 2. 只保留default_user的数据
## 3. 删除其他所有用户的历史数据
'''

import json
import os
from pathlib import Path

def clean_memory_data():
    """
    清理记忆数据，只保留default_user的数据
    """
    memory_dir = Path("memory_db")
    session_file = memory_dir / "session_memory.json"
    user_file = memory_dir / "user_memory.json"
    
    print("开始清理记忆数据...")
    
    # 清理会话记忆
    if session_file.exists():
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # 只保留default_user的数据
            cleaned_session_data = {}
            if "default_user" in session_data:
                cleaned_session_data["default_user"] = session_data["default_user"]
                print(f"保留default_user的会话记忆: {len(session_data['default_user'])}条")
            
            # 删除其他用户数据
            removed_users = [user for user in session_data.keys() if user != "default_user"]
            print(f"删除其他用户数据: {len(removed_users)}个用户")
            
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
            
            # 只保留default_user的数据
            cleaned_user_data = {}
            if "default_user" in user_data:
                cleaned_user_data["default_user"] = user_data["default_user"]
                print(f"保留default_user的用户记忆: {len(user_data['default_user'])}条")
            
            # 删除其他用户数据
            removed_users = [user for user in user_data.keys() if user != "default_user"]
            print(f"删除其他用户数据: {len(removed_users)}个用户")
            
            # 保存清理后的数据
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_user_data, f, ensure_ascii=False, indent=2)
            
            print("用户记忆清理完成")
            
        except Exception as e:
            print(f"清理用户记忆失败: {e}")
    
    print("记忆数据清理完成！")

if __name__ == "__main__":
    clean_memory_data() 