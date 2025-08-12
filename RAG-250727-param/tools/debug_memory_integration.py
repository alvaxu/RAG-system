#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试记忆管理器集成状态
"""

import requests
import json

def debug_memory_integration():
    """调试记忆管理器的集成状态"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 调试记忆管理器集成状态")
    print("=" * 50)
    
    # 1. 检查系统状态
    print("📊 检查系统状态...")
    try:
        response = requests.get(f"{base_url}/api/v2/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
            # 检查记忆管理器状态
            memory_ready = status.get('memory_manager_ready', False)
            print(f"\n🧠 记忆管理器状态: {'✅ 就绪' if memory_ready else '❌ 未就绪'}")
            
        else:
            print(f"❌ 获取系统状态失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 2. 检查记忆统计
    print("\n📊 检查记忆统计...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 记忆统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 3. 检查混合引擎状态
    print("\n🔧 检查混合引擎状态...")
    try:
        response = requests.get(f"{base_url}/api/v2/status")
        if response.status_code == 200:
            status = response.json()
            hybrid_engine = status.get('hybrid_engine', {})
            print(f"✅ 混合引擎状态: {json.dumps(hybrid_engine, indent=2, ensure_ascii=False)}")
            
            # 检查是否有记忆管理器
            has_memory_manager = 'memory_manager' in hybrid_engine
            print(f"\n🧠 混合引擎是否有记忆管理器: {'✅ 是' if has_memory_manager else '❌ 否'}")
            
        else:
            print(f"❌ 获取状态失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 4. 测试记忆更新
    print("\n🧪 测试记忆更新...")
    try:
        response = requests.post(
            f"{base_url}/api/v2/qa/ask",
            json={
                "question": "测试记忆集成",
                "user_id": "debug_user",
                "use_memory": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 问题回答成功")
            print(f"📝 答案: {result.get('answer', '')[:100]}...")
            
            # 检查响应中是否有记忆相关信息
            has_memory_info = 'memory_updated' in result or 'memory_count' in result
            print(f"🧠 响应中是否有记忆信息: {'✅ 是' if has_memory_info else '❌ 否'}")
            
        else:
            print(f"❌ 问题回答失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 5. 再次检查记忆统计
    print("\n📊 再次检查记忆统计...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats")
        if response.status_code == 200:
            updated_stats = response.json()
            print(f"✅ 更新后记忆统计: {json.dumps(updated_stats, indent=2, ensure_ascii=False)}")
            
            # 检查是否有变化
            if stats['stats']['session_memory_count'] != updated_stats['stats']['session_memory_count']:
                print("✅ 会话记忆数量有变化")
            else:
                print("❌ 会话记忆数量没有变化")
                
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    debug_memory_integration()
