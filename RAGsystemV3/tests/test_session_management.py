#!/usr/bin/env python3
"""
测试会话管理和查询重写功能
"""

import requests
import json
import time

def test_session_management():
    """测试会话管理功能"""
    base_url = "http://localhost:8000/api/v3/rag"
    
    print("🧪 开始测试会话管理和查询重写功能")
    print("="*60)
    
    # 第一次查询
    print("\n📝 第一次查询：中芯国际的股东组成是怎样的？")
    query1 = {
        "query": "中芯国际的股东组成是怎样的？",
        "query_type": "text",
        "user_id": "test_user",
        "include_sources": True
    }
    
    response1 = requests.post(f"{base_url}/query", json=query1)
    if response1.status_code == 200:
        result1 = response1.json()
        session_id = result1.get('session_id')
        print(f"✅ 第一次查询成功")
        print(f"   会话ID: {session_id}")
        print(f"   答案长度: {len(result1.get('answer', ''))}")
    else:
        print(f"❌ 第一次查询失败: {response1.status_code}")
        return False
    
    # 等待一下，确保记忆被记录
    time.sleep(2)
    
    # 第二次查询（使用代词）
    print(f"\n📝 第二次查询：它的情况如何？（使用会话ID: {session_id}）")
    query2 = {
        "query": "它的情况如何？",
        "query_type": "text",
        "session_id": session_id,
        "user_id": "test_user",
        "include_sources": True
    }
    
    response2 = requests.post(f"{base_url}/query", json=query2)
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"✅ 第二次查询成功")
        print(f"   会话ID: {result2.get('session_id')}")
        print(f"   答案长度: {len(result2.get('answer', ''))}")
        
        # 检查是否有查询重写信息
        metadata = result2.get('processing_metadata', {})
        print(f"🔍 调试信息 - processing_metadata: {metadata}")
        if 'query_rewritten' in metadata:
            print(f"🔄 查询重写: {metadata.get('original_query')} -> {metadata.get('rewritten_query')}")
        else:
            print("⏭️ 未检测到查询重写")
            
    else:
        print(f"❌ 第二次查询失败: {response2.status_code}")
        return False
    
    # 第三次查询（使用"这家公司"）
    print(f"\n📝 第三次查询：这家公司的发展前景如何？")
    query3 = {
        "query": "这家公司的发展前景如何？",
        "query_type": "text",
        "session_id": session_id,
        "user_id": "test_user",
        "include_sources": True
    }
    
    response3 = requests.post(f"{base_url}/query", json=query3)
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"✅ 第三次查询成功")
        print(f"   会话ID: {result3.get('session_id')}")
        print(f"   答案长度: {len(result3.get('answer', ''))}")
        
        # 检查是否有查询重写信息
        metadata = result3.get('processing_metadata', {})
        if 'query_rewritten' in metadata:
            print(f"🔄 查询重写: {metadata.get('original_query')} -> {metadata.get('rewritten_query')}")
        else:
            print("⏭️ 未检测到查询重写")
            
    else:
        print(f"❌ 第三次查询失败: {response3.status_code}")
        return False
    
    print("\n🎉 会话管理测试完成！")
    return True

if __name__ == "__main__":
    test_session_management()
