#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试记忆模块的所有查询类型
包括text、image、table等类型的多轮对话测试
"""

import requests
import json
import time

def test_memory_all_types():
    """测试记忆模块的所有查询类型"""
    print("🧠 测试记忆模块 - 所有查询类型")
    print("=" * 80)
    
    base_url = "http://localhost:8000"
    session_id = None
    
    # 测试用例：每种类型3轮对话
    test_cases = [
        {
            "type": "text",
            "questions": [
                "中芯国际是什么公司？",
                "它的主要业务是什么？", 
                "这家公司的技术实力如何？"
            ]
        },
        {
            "type": "image", 
            "questions": [
                "图4：中芯国际归母净利润情况概览",
                "这个图表显示了什么信息？",
                "从图表中可以看出什么趋势？"
            ]
        },
        {
            "type": "table",
            "questions": [
                "中芯国际的基本财务数据表格",
                "这些数据说明了什么？",
                "表格中的关键指标有哪些？"
            ]
        },
        {
            "type": "smart",
            "questions": [
                "中芯国际的竞争优势是什么？",
                "这些优势如何体现？",
                "它们对公司发展有什么影响？"
            ]
        },
        {
            "type": "hybrid",
            "questions": [
                "中芯国际的财务状况和股价表现如何？",
                "这些表现说明了什么问题？",
                "从多个角度看有什么趋势？"
            ]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 测试 {test_case['type'].upper()} 类型对话")
        print("-" * 60)
        
        session_id = None
        
        for i, question in enumerate(test_case['questions'], 1):
            print(f"\n第{i}轮对话 ({test_case['type']}):")
            print(f"问题: {question}")
            
            try:
                response = requests.post(f"{base_url}/api/v3/rag/query", json={
                    "query": question,
                    "query_type": test_case['type'],
                    "user_id": f"test_user_{test_case['type']}",
                    "session_id": session_id
                }, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get('session_id')
                    
                    if i == 1:
                        print(f"✅ 创建会话: {session_id}")
                        print(f"🤖 系统回答: {data.get('answer', '')[:200]}...")
                        print(f"🧠 记忆增强: {'使用历史记忆' if data.get('processing_metadata', {}).get('memory_enhanced') else '未使用历史记忆'}")
                    else:
                        print(f"🤖 系统回答: {data.get('answer', '')[:300]}...")
                        print(f"🧠 记忆增强: {'使用历史记忆' if data.get('processing_metadata', {}).get('memory_enhanced') else '未使用历史记忆'}")
                        
                        # 检查是否理解代词指代
                        answer = data.get('answer', '')
                        if any(keyword in answer for keyword in ['中芯国际', 'SMIC', '这家公司', '该公司']):
                            print("✅ 系统正确理解了代词指代")
                        else:
                            print("❌ 系统没有理解代词指代")
                else:
                    print(f"❌ 请求失败: {response.status_code}")
                    print(response.text)
                    
            except Exception as e:
                print(f"❌ 请求异常: {e}")
            
            time.sleep(1)  # 避免请求过快
    
    print("\n" + "=" * 80)
    print("🎯 所有类型测试完成")

def test_specific_text_scenarios():
    """测试特定的文本场景"""
    print("\n📝 测试特定文本场景")
    print("-" * 60)
    
    base_url = "http://localhost:8000"
    
    # 场景1：技术相关对话
    print("\n🔧 场景1：技术相关对话")
    tech_questions = [
        "中芯国际的制程技术如何？",
        "它的先进制程有哪些？",
        "这些技术有什么优势？"
    ]
    
    session_id = None
    for i, question in enumerate(tech_questions, 1):
        print(f"\n第{i}轮: {question}")
        try:
            response = requests.post(f"{base_url}/api/v3/rag/query", json={
                "query": question,
                "query_type": "text",
                "user_id": "test_tech_user",
                "session_id": session_id
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get('session_id')
                print(f"🤖 回答: {data.get('answer', '')[:200]}...")
                print(f"🧠 记忆: {'使用' if data.get('processing_metadata', {}).get('memory_enhanced') else '未使用'}")
            else:
                print(f"❌ 失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 异常: {e}")
        time.sleep(1)
    
    # 场景2：财务相关对话
    print("\n💰 场景2：财务相关对话")
    finance_questions = [
        "中芯国际的财务状况如何？",
        "它的营收结构是怎样的？",
        "这些数据说明了什么？"
    ]
    
    session_id = None
    for i, question in enumerate(finance_questions, 1):
        print(f"\n第{i}轮: {question}")
        try:
            response = requests.post(f"{base_url}/api/v3/rag/query", json={
                "query": question,
                "query_type": "text",
                "user_id": "test_finance_user",
                "session_id": session_id
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get('session_id')
                print(f"🤖 回答: {data.get('answer', '')[:200]}...")
                print(f"🧠 记忆: {'使用' if data.get('processing_metadata', {}).get('memory_enhanced') else '未使用'}")
            else:
                print(f"❌ 失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 异常: {e}")
        time.sleep(1)

if __name__ == "__main__":
    test_memory_all_types()
    test_specific_text_scenarios()
