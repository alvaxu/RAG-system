#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查记忆文件内容
"""

import json

def check_memory_content():
    """检查记忆文件内容"""
    
    print("📁 检查记忆文件内容")
    print("=" * 50)
    
    # 检查conversation_contexts.json
    try:
        with open('central/memory_db/conversation_contexts.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("📝 conversation_contexts.json:")
        for user_id, context in data.items():
            history = context.get('conversation_history', [])
            print(f"  {user_id}: {len(history)} 条记录")
            if user_id == 'test_user':
                print("    最后3个问题:")
                for i, item in enumerate(history[-3:]):
                    print(f"      {i+1}. {item['question']}")
                print(f"    最新问题: {context.get('last_question', 'N/A')}")
    except Exception as e:
        print(f"❌ 读取conversation_contexts.json失败: {e}")
    
    # 检查user_preferences.json
    try:
        with open('central/memory_db/user_preferences.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n📊 user_preferences.json:")
        for user_id, prefs in data.items():
            interest_areas = prefs.get('interest_areas', [])
            frequent_queries = prefs.get('frequent_queries', [])
            print(f"  {user_id}: {len(interest_areas)} 个兴趣领域, {len(frequent_queries)} 个常用查询")
    except Exception as e:
        print(f"❌ 读取user_preferences.json失败: {e}")

if __name__ == "__main__":
    check_memory_content()
