"""
程序说明：
## 1. 调试记忆系统对QA功能的影响
## 2. 检查是否记忆系统导致后续查询失败
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def debug_memory_issue():
    """调试记忆系统问题"""
    print("🔧 调试记忆系统问题")
    print("=" * 50)
    
    # 加载QA系统
    settings = Settings.load_from_file("config.json")
    api_key = settings.dashscope_api_key
    qa_system = load_enhanced_qa_system("./central/vector_db", api_key)
    
    if not qa_system:
        print("❌ QA系统加载失败")
        return
    
    # 测试问题列表（模拟前端的问题）
    test_questions = [
        "中芯国际的主要业务和核心技术是什么？",
        "中芯国际在晶圆代工行业的市场地位如何？",
        "中芯国际的产能扩张历程和现状是怎样的？",
        "中芯国际2024-2027年的净利润增长趋势如何？"
    ]
    
    print("📋 测试1: 使用answer_question（无记忆）")
    print("-" * 40)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 问题 {i}: {question}")
        
        try:
            result = qa_system.answer_question(question, k=3)
            
            if result and 'answer' in result:
                answer = result['answer']
                sources = result.get('sources', [])
                
                if "没有找到相关信息" not in answer:
                    print(f"✅ 成功 - 长度:{len(answer)}, 来源:{len(sources)}")
                else:
                    print("❌ 返回默认回答")
            else:
                print("❌ 无有效回答")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print("\n" + "=" * 50)
    print("📋 测试2: 使用answer_with_memory（有记忆）")
    print("-" * 40)
    
    # 清除记忆
    qa_system.clear_memory("test_user")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 问题 {i}: {question}")
        
        try:
            result = qa_system.answer_with_memory("test_user", question, k=3)
            
            if result and 'answer' in result:
                answer = result['answer']
                sources = result.get('sources', [])
                
                if "没有找到相关信息" not in answer:
                    print(f"✅ 成功 - 长度:{len(answer)}, 来源:{len(sources)}")
                else:
                    print("❌ 返回默认回答")
            else:
                print("❌ 无有效回答")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    debug_memory_issue() 