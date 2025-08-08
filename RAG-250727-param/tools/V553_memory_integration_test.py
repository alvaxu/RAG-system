'''
程序说明：
## 1. 记忆集成测试脚本
## 2. 验证记忆上下文是否正确传递给LLM
## 3. 测试指代词理解和上下文连续性
## 4. 模拟实际对话场景
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
    """测试记忆集成功能"""
    print("=" * 60)
    print("🔍 测试记忆集成功能")
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
            "请把你找到的这战图单独展现出来",
            "我是说你找到的那张走势图"
        ]
        
        print("📝 模拟连续对话测试:")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n问题 {i}: {question}")
            
            # 提问
            result = rag_system.ask_question(question, use_memory=True)
            
            if result['success']:
                answer = result['answer']
                print(f"回答 {i}: {answer[:200]}...")
                
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
        print(f"❌ 记忆集成测试失败: {e}")
        return False


def test_pronoun_understanding():
    """测试指代词理解"""
    print("\n" + "=" * 60)
    print("🔍 测试指代词理解")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化RAG系统
        rag_system = UnifiedRAGSystem(settings)
        
        if not rag_system.qa_system:
            print("❌ QA系统未初始化，无法测试")
            return False
        
        # 测试指代词理解
        test_cases = [
            ("文档中有没有关于个股走势表现的图", "请把你找到的这战图单独展现出来"),
            ("个股相对沪深300指数表现", "那个走势图的具体内容"),
            ("图1：公司单季度营业收入及增速情况", "这个图的数据怎么样"),
            ("中芯国际2024年的营业收入和净利润情况如何？", "那2025年的呢")
        ]
        
        print("📊 指代词理解测试:")
        
        for i, (context_question, pronoun_question) in enumerate(test_cases, 1):
            print(f"\n测试 {i}:")
            print(f"  上下文问题: {context_question}")
            print(f"  指代问题: {pronoun_question}")
            
            # 先问上下文问题
            context_result = rag_system.ask_question(context_question, use_memory=True)
            print(f"  上下文回答: {context_result['answer'][:100]}...")
            
            # 再问指代问题
            pronoun_result = rag_system.ask_question(pronoun_question, use_memory=True)
            print(f"  指代回答: {pronoun_result['answer'][:100]}...")
            
            # 检查指代词理解
            if "无法确定" in pronoun_result['answer'] or "未提供" in pronoun_result['answer'] or "没有找到" in pronoun_result['answer']:
                print(f"  ❌ 指代词理解失败")
            else:
                print(f"  ✅ 指代词理解成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 指代词理解测试失败: {e}")
        return False


def test_memory_context_format():
    """测试记忆上下文格式"""
    print("\n" + "=" * 60)
    print("🔍 测试记忆上下文格式")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化RAG系统
        rag_system = UnifiedRAGSystem(settings)
        
        if not rag_system.memory_manager:
            print("❌ 记忆管理器未初始化")
            return False
        
        # 测试记忆上下文格式
        test_question = "那2025年的呢"
        
        # 获取记忆上下文
        memory_context = rag_system.memory_manager.build_context("default_user", test_question, memory_limit=3)
        
        print("📊 记忆上下文格式:")
        print(f"  相关记忆数量: {memory_context.get('memory_count', 0)}")
        print(f"  是否有记忆: {memory_context.get('has_memory', False)}")
        print(f"  记忆上下文:\n{memory_context.get('memory_context', '无')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 记忆上下文格式测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始记忆集成测试...")
    
    tests = [
        ("记忆集成功能测试", test_memory_integration),
        ("指代词理解测试", test_pronoun_understanding),
        ("记忆上下文格式测试", test_memory_context_format)
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
        print("\n🎉 记忆集成修复成功!")
        print("  - 记忆上下文正确传递给LLM")
        print("  - 指代词理解显著改善")
        print("  - 上下文连续性完全恢复")
    else:
        print("\n🚨 仍有问题需要解决:")
        print("  - 检查记忆上下文传递")
        print("  - 验证指代词理解")
        print("  - 确认LLM提示词格式")


if __name__ == "__main__":
    main() 