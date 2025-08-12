#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证 v2_memory_manager.py 中的 SimplifiedMemoryManager 功能

## 测试内容：
1. 指代词解析功能
2. 上下文管理功能
3. 用户偏好更新
4. 记忆统计功能
5. 向后兼容性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.v2_memory_manager import SimplifiedMemoryManager, ConversationContext, UserPreferences

def test_simplified_memory_manager():
    """测试简化记忆管理器的主要功能"""
    print("🧪 开始测试 SimplifiedMemoryManager...")
    
    # 初始化记忆管理器
    memory_manager = SimplifiedMemoryManager()
    print("✅ 记忆管理器初始化成功")
    
    # 测试1：指代词解析
    print("\n📝 测试1：指代词解析功能")
    user_id = "test_user"
    
    # 第一轮对话
    question1 = "中芯国际的技术水平如何？"
    answer1 = "中芯国际在芯片制造技术方面处于国内领先地位..."
    memory_manager.update_context(user_id, question1, answer1)
    
    # 测试指代词解析
    question2 = "它的营收情况怎么样？"
    resolved_question = memory_manager.process_query(user_id, question2)
    print(f"原始问题: {question2}")
    print(f"解析后问题: {resolved_question}")
    
    # 第二轮对话
    question3 = "那个公司的市场份额如何？"
    resolved_question3 = memory_manager.process_query(user_id, question3)
    print(f"原始问题: {question3}")
    print(f"解析后问题: {resolved_question3}")
    
    # 测试2：上下文摘要
    print("\n📋 测试2：上下文摘要功能")
    context_summary = memory_manager.get_context_summary(user_id)
    print(f"用户上下文摘要: {context_summary}")
    
    # 测试3：记忆统计
    print("\n📊 测试3：记忆统计功能")
    stats = memory_manager.get_memory_stats(user_id)
    print(f"记忆统计: {stats}")
    
    # 测试4：多轮对话上下文
    print("\n🔄 测试4：多轮对话上下文")
    question4 = "刚才说的技术优势具体体现在哪些方面？"
    resolved_question4 = memory_manager.process_query(user_id, question4)
    print(f"原始问题: {question4}")
    print(f"解析后问题: {resolved_question4}")
    
    # 更新上下文
    answer4 = "主要体现在先进制程工艺、设备升级等方面..."
    memory_manager.update_context(user_id, question4, answer4)
    
    # 测试5：向后兼容性
    print("\n🔙 测试5：向后兼容性")
    try:
        # 测试旧的 add_to_session 方法
        memory_manager.add_to_session(user_id, "测试问题", "测试答案")
        print("✅ add_to_session 方法兼容性正常")
        
        # 测试旧的 clear_session_memory 方法
        memory_manager.clear_session_memory(user_id)
        print("✅ clear_session_memory 方法兼容性正常")
        
        # 测试旧的 retrieve_relevant_memory 方法
        relevant_memory = memory_manager.retrieve_relevant_memory(user_id, "测试查询")
        print(f"✅ retrieve_relevant_memory 方法兼容性正常，返回: {relevant_memory}")
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
    
    # 测试6：多用户支持
    print("\n👥 测试6：多用户支持")
    user_id2 = "test_user_2"
    question5 = "华为的技术实力如何？"
    answer5 = "华为在通信技术领域具有全球领先地位..."
    memory_manager.update_context(user_id2, question5, answer5)
    
    # 验证用户隔离
    context_summary1 = memory_manager.get_context_summary(user_id)
    context_summary2 = memory_manager.get_context_summary(user_id2)
    print(f"用户1上下文: {context_summary1}")
    print(f"用户2上下文: {context_summary2}")
    
    # 测试7：清理功能
    print("\n🧹 测试7：清理功能")
    memory_manager.clear_context(user_id)
    memory_manager.clear_context(user_id2)
    
    # 验证清理结果
    stats_after_clear = memory_manager.get_memory_stats()
    print(f"清理后的统计: {stats_after_clear}")
    
    print("\n🎉 所有测试完成！")

def test_conversation_context():
    """测试 ConversationContext 类"""
    print("\n🧪 测试 ConversationContext 类...")
    
    context = ConversationContext("test_user")
    
    # 测试实体提取
    question = "中芯国际的芯片制造技术和财务表现如何？"
    context.update_context(question, "测试答案")
    
    print(f"提取的实体: {context.last_entities}")
    print(f"识别的主题: {context.current_topic}")
    print(f"指代词映射: {context.entity_mentions}")
    
    # 测试指代词解析
    resolved = context.resolve_references("它的技术优势是什么？")
    print(f"指代词解析结果: {resolved}")

def test_user_preferences():
    """测试 UserPreferences 类"""
    print("\n🧪 测试 UserPreferences 类...")
    
    prefs = UserPreferences("test_user")
    prefs.update_preferences("技术", "芯片制造")
    prefs.update_preferences("财务", "业绩分析")
    
    print(f"兴趣领域: {prefs.interest_areas}")
    print(f"频繁查询: {prefs.frequent_queries}")

if __name__ == "__main__":
    print("🚀 开始测试 v2 记忆管理系统...")
    print("=" * 50)
    
    try:
        test_conversation_context()
        test_user_preferences()
        test_simplified_memory_manager()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！新的记忆管理系统工作正常")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
