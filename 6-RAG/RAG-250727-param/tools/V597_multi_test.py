"""
程序说明：
## 1. 多问题测试RAG系统
## 2. 验证不同类型问题的回答能力
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def multi_test():
    """多问题测试"""
    print("🧪 多问题测试RAG系统")
    print("=" * 50)
    
    # 加载QA系统
    settings = Settings.load_from_file("config.json")
    api_key = settings.dashscope_api_key
    qa_system = load_enhanced_qa_system("./central/vector_db", api_key)
    
    if not qa_system:
        print("❌ QA系统加载失败")
        return
    
    # 测试问题列表
    test_questions = [
        "中芯国际的主要业务是什么？",
        "中芯国际的产能利用率如何？", 
        "中芯国际的营业收入预测是多少？",
        "中芯国际的核心技术有哪些？"
    ]
    
    success_count = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 问题 {i}: {question}")
        
        try:
            result = qa_system.answer_question(question, k=3)
            
            if result and 'answer' in result:
                answer = result['answer']
                sources = result.get('sources', [])
                
                if "没有找到相关信息" not in answer:
                    print(f"✅ 成功 - 长度:{len(answer)}, 来源:{len(sources)}")
                    success_count += 1
                else:
                    print("❌ 返回默认回答")
            else:
                print("❌ 无有效回答")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print(f"\n📊 测试结果: {success_count}/{len(test_questions)} 成功")
    print("=" * 50)

if __name__ == "__main__":
    multi_test() 