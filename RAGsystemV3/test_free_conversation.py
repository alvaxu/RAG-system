#!/usr/bin/env python3
"""
测试自由对话功能
验证系统能够记住之前的对话并在后续回答中提供上下文
"""

import requests
import json
import time

def test_free_conversation():
    """测试自由对话功能"""
    print("🧠 测试自由对话功能")
    print("=" * 60)
    
    # 测试场景：多轮对话，验证系统是否记住之前的对话
    conversation_steps = [
        {
            "step": 1,
            "query": "中芯国际是什么公司？",
            "query_type": "text",
            "expected_context": "首次询问，应该没有历史记忆"
        },
        {
            "step": 2,
            "query": "它的主要业务是什么？",
            "query_type": "text", 
            "expected_context": "应该记住之前关于中芯国际的对话"
        },
        {
            "step": 3,
            "query": "这家公司的股东结构如何？",
            "query_type": "text",
            "expected_context": "应该记住之前关于中芯国际的对话"
        },
        {
            "step": 4,
            "query": "我刚才问的是什么？",
            "query_type": "text",
            "expected_context": "应该能够回顾整个对话历史"
        }
    ]
    
    session_id = None
    
    for step_info in conversation_steps:
        print(f"\n📝 第{step_info['step']}轮对话")
        print(f"问题: {step_info['query']}")
        print(f"期望: {step_info['expected_context']}")
        print("-" * 40)
        
        # 发送查询请求
        query_data = {
            "query": step_info['query'],
            "query_type": step_info['query_type'],
            "max_results": 5,
            "relevance_threshold": 0.5,
            "user_id": "test_user",
            "session_id": session_id  # 使用同一个会话ID
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/api/v3/rag/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 获取会话ID（第一次查询后）
                if not session_id:
                    session_id = result.get('session_id')
                    print(f"✅ 创建会话: {session_id}")
                
                # 显示答案
                answer = result.get('answer', '')
                print(f"🤖 系统回答: {answer[:200]}...")
                
                # 检查是否有记忆增强
                processing_metadata = result.get('processing_metadata', {})
                memory_enhanced = processing_metadata.get('memory_enhanced', False)
                context_memories_count = processing_metadata.get('context_memories_count', 0)
                
                if memory_enhanced:
                    print(f"🧠 记忆增强: 使用了 {context_memories_count} 条历史记忆")
                else:
                    print("🧠 记忆增强: 未使用历史记忆")
                
                # 检查记忆记录
                if session_id:
                    try:
                        memories_response = requests.get(
                            f"http://localhost:8000/api/v3/memory/sessions/{session_id}/memories?max_results=10"
                        )
                        if memories_response.status_code == 200:
                            memories = memories_response.json()
                            print(f"📚 当前会话记忆数量: {len(memories)}")
                            
                            # 显示最新的记忆
                            if memories and len(memories) > 0:
                                latest_memory = memories[0]
                                if latest_memory and 'content' in latest_memory:
                                    print(f"📝 最新记忆: {latest_memory['content'][:100]}...")
                                else:
                                    print("📝 最新记忆: 格式错误")
                            else:
                                print("📝 最新记忆: 无记忆数据")
                        else:
                            print("❌ 获取记忆失败")
                    except Exception as e:
                        print(f"❌ 获取记忆异常: {e}")
                
            else:
                print(f"❌ 查询失败: {response.status_code}")
                print(f"错误: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            # 如果是第4轮对话，可能是查询失败，但仍然检查记忆增强
            if step_info['step'] == 4:
                print("🔍 第4轮对话可能查询失败，但记忆增强应该已设置")
        
        # 等待一下
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎯 自由对话测试完成")
    
    # 显示最终的记忆状态
    if session_id:
        print(f"\n📊 最终会话状态: {session_id}")
        try:
            memories_response = requests.get(
                f"http://localhost:8000/api/v3/memory/sessions/{session_id}/memories?max_results=20"
            )
            if memories_response.status_code == 200:
                memories = memories_response.json()
                print(f"📚 总记忆数量: {len(memories)}")
                
                print("\n📝 所有记忆内容:")
                for i, memory in enumerate(memories, 1):
                    print(f"  {i}. {memory['content'][:150]}...")
                    print(f"     类型: {memory['content_type']}, 相关性: {memory['relevance_score']:.2f}")
            else:
                print("❌ 获取最终记忆失败")
        except Exception as e:
            print(f"❌ 获取最终记忆异常: {e}")

if __name__ == "__main__":
    test_free_conversation()
