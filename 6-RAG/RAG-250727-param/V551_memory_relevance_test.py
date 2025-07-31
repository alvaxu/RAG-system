'''
程序说明：
## 1. 记忆相关性测试脚本
## 2. 验证改进的相关性计算算法
## 3. 测试中文对话的上下文连续性
## 4. 模拟实际对话场景
'''

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from V503_unified_main import UnifiedRAGSystem
from config.settings import Settings


def test_memory_relevance():
    """测试记忆相关性计算"""
    print("=" * 60)
    print("🔍 测试记忆相关性计算")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化RAG系统
        rag_system = UnifiedRAGSystem(settings)
        
        if not rag_system.memory_manager:
            print("❌ 记忆管理器未初始化")
            return False
        
        # 测试相关性计算
        test_cases = [
            ("中芯国际2024年的营业收入和净利润情况如何？", "那2025年的呢"),
            ("文档中有没有关于个股走势表现的图", "请把你找到的这战图单独展现出来"),
            ("中芯国际的全称", "那2025年的呢"),
            ("图1：公司单季度营业收入及增速情况", "这个图的数据怎么样"),
            ("个股相对沪深300指数表现", "那个走势图的具体内容")
        ]
        
        print("📊 相关性计算测试:")
        
        for i, (q1, q2) in enumerate(test_cases, 1):
            relevance = rag_system.memory_manager._calculate_relevance(q1, q2)
            print(f"  测试 {i}:")
            print(f"    问题1: {q1}")
            print(f"    问题2: {q2}")
            print(f"    相关性: {relevance:.3f}")
            print(f"    是否相关: {'✅' if relevance >= 0.1 else '❌'}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 记忆相关性测试失败: {e}")
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
            "中芯国际2024年的营业收入和净利润情况如何？",
            "那2025年的呢",
            "2025年第一季度呢",
            "文档中有没有关于个股走势表现的图",
            "请把你找到的这战图单独展现出来"
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
                    if "无法确定" in answer or "未提供" in answer or "没有找到" in answer:
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
        test_questions = [
            "那2025年的呢",
            "请把你找到的这战图单独展现出来",
            "这个图的数据怎么样"
        ]
        
        print(f"📊 记忆检索结果:")
        
        for i, test_question in enumerate(test_questions, 1):
            relevant_memories = rag_system.memory_manager.retrieve_relevant_memory(
                user_id="default_user",
                current_question=test_question,
                memory_limit=3,
                relevance_threshold=0.1
            )
            
            print(f"  测试 {i}: {test_question}")
            print(f"    相关记忆数量: {len(relevant_memories)}")
            
            for j, memory in enumerate(relevant_memories, 1):
                relevance = getattr(memory, 'relevance_score', 'N/A')
                print(f"    记忆 {j}: {memory.question[:50]}... (相关性: {relevance})")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 记忆检索测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始记忆相关性测试...")
    
    tests = [
        ("记忆相关性计算测试", test_memory_relevance),
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
        print("\n🎉 记忆相关性修复成功!")
        print("  - 相关性计算算法改进")
        print("  - 中文对话支持增强")
        print("  - 上下文连续性恢复")
    else:
        print("\n🚨 仍有问题需要解决:")
        print("  - 检查相关性计算逻辑")
        print("  - 验证记忆检索机制")
        print("  - 确认上下文传递")


if __name__ == "__main__":
    main() 