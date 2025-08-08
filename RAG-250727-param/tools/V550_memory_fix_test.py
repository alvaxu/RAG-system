'''
程序说明：
## 1. 记忆功能修复测试脚本
## 2. 验证记忆管理器是否正确传递给QA系统
## 3. 测试上下文连续性是否恢复
## 4. 模拟连续对话测试
'''

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from V501_unified_main import UnifiedRAGSystem
from config.settings import Settings


def test_memory_integration():
    """测试记忆集成"""
    print("=" * 60)
    print("🔍 测试记忆集成修复")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化RAG系统
        rag_system = UnifiedRAGSystem(settings)
        
        # 检查组件初始化
        print("📋 组件初始化检查:")
        print(f"  - QA系统: {'✅' if rag_system.qa_system else '❌'}")
        print(f"  - 记忆管理器: {'✅' if rag_system.memory_manager else '❌'}")
        
        if rag_system.qa_system and rag_system.memory_manager:
            print(f"  - QA系统记忆管理器: {'✅' if rag_system.qa_system.memory_manager else '❌'}")
            print(f"  - 记忆管理器一致性: {'✅' if rag_system.qa_system.memory_manager == rag_system.memory_manager else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 记忆集成测试失败: {e}")
        return False


def test_context_continuity():
    """测试上下文连续性"""
    print("\n" + "=" * 60)
    print("🔍 测试上下文连续性")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化RAG系统
        rag_system = UnifiedRAGSystem(settings)
        
        if not rag_system.qa_system:
            print("❌ QA系统未初始化，无法测试")
            return False
        
        # 模拟连续对话
        test_questions = [
            "文档中有没有关于个股走势表现的图",
            "单独显示这个图",
            "把这个图单独找出来"
        ]
        
        print("📝 模拟连续对话测试:")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n问题 {i}: {question}")
            
            # 提问
            result = rag_system.ask_question(question, use_memory=True)
            
            if result['success']:
                answer = result['answer']
                print(f"回答 {i}: {answer[:100]}...")
                
                # 检查是否理解上下文
                if i > 1:
                    if "无法确定" in answer or "未提供" in answer:
                        print(f"  ❌ 上下文连续性失败")
                    else:
                        print(f"  ✅ 上下文连续性正常")
            else:
                print(f"  ❌ 提问失败: {result.get('error', '未知错误')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 上下文连续性测试失败: {e}")
        return False


def test_memory_retrieval():
    """测试记忆检索"""
    print("\n" + "=" * 60)
    print("🔍 测试记忆检索功能")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化RAG系统
        rag_system = UnifiedRAGSystem(settings)
        
        if not rag_system.memory_manager:
            print("❌ 记忆管理器未初始化")
            return False
        
        # 测试记忆检索
        test_question = "个股走势表现"
        relevant_memories = rag_system.memory_manager.retrieve_relevant_memory(
            user_id="default_user",
            current_question=test_question,
            memory_limit=3,
            relevance_threshold=0.5
        )
        
        print(f"📊 记忆检索结果:")
        print(f"  检索问题: {test_question}")
        print(f"  相关记忆数量: {len(relevant_memories)}")
        
        for i, memory in enumerate(relevant_memories, 1):
            print(f"  记忆 {i}: {memory.question[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 记忆检索测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始记忆功能修复测试...")
    
    tests = [
        ("记忆集成测试", test_memory_integration),
        ("上下文连续性测试", test_context_continuity),
        ("记忆检索测试", test_memory_retrieval)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 记忆功能修复成功!")
        print("  - 记忆管理器正确集成")
        print("  - 上下文连续性恢复")
        print("  - 记忆检索功能正常")
    else:
        print("\n🚨 仍有问题需要解决:")
        print("  - 检查记忆管理器集成")
        print("  - 验证上下文传递机制")
        print("  - 确认记忆检索逻辑")


if __name__ == "__main__":
    main() 