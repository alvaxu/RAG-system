#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试混合引擎是否有memory_manager属性
"""

import requests
import json

def test_memory_attr():
    """测试混合引擎是否有memory_manager属性"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 测试混合引擎memory_manager属性")
    print("=" * 50)
    
    # 1. 检查混合引擎对象
    print("🔍 检查混合引擎对象...")
    try:
        response = requests.get(f"{base_url}/api/v2/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
            # 检查混合引擎状态
            hybrid_ready = status.get('status', {}).get('hybrid_engine_ready', False)
            print(f"\n🔧 混合引擎状态: {'✅ 就绪' if hybrid_ready else '❌ 未就绪'}")
            
        else:
            print(f"❌ 获取系统状态失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 2. 尝试直接访问混合引擎
    print("\n🔍 尝试直接访问混合引擎...")
    try:
        # 这里我们需要通过某种方式来检查混合引擎的属性
        # 由于没有直接的API来检查对象属性，我们通过问答来间接测试
        
        response = requests.post(
            f"{base_url}/api/v2/qa/ask",
            json={
                "question": "测试记忆属性",
                "user_id": "test_attr_user",
                "use_memory": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 问题回答成功")
            
            # 检查响应中是否有错误信息
            if 'error' in result:
                print(f"❌ 响应中有错误: {result['error']}")
            else:
                print(f"✅ 响应正常")
                
        else:
            print(f"❌ 问题回答失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 3. 检查记忆统计是否有变化
    print("\n📊 检查记忆统计是否有变化...")
    try:
        response = requests.get(f"{base_url}/api/v2/memory/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 记忆统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
            
            # 检查是否有新的用户
            user_id = stats['stats']['user_id']
            if user_id == 'test_attr_user':
                print("✅ 新用户记忆已创建")
            else:
                print(f"⚠️  记忆统计仍显示默认用户: {user_id}")
                
        else:
            print(f"❌ 获取记忆统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 4. 分析可能的问题
    print("\n🔍 问题分析:")
    print("1. 混合引擎可能没有正确保存memory_manager属性")
    print("2. 记忆管理器可能没有正确初始化")
    print("3. 属性设置可能在某个地方被覆盖了")
    print("4. 需要检查V800_v2_main.py中的集成逻辑")

if __name__ == "__main__":
    test_memory_attr()
