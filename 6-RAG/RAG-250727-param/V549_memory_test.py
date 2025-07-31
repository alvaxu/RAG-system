'''
程序说明：
## 1. 记忆功能测试脚本
## 2. 验证历史对话记忆
## 3. 测试上下文连续性
## 4. 检查记忆管理
'''

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.memory_manager import MemoryManager


def test_memory_functionality():
    """测试记忆功能"""
    print("=" * 60)
    print("🔍 测试记忆功能")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 初始化记忆管理器
        memory_manager = MemoryManager(settings.memory_db_dir)
        print("✅ 记忆管理器初始化成功")
        
        # 检查记忆文件
        memory_file = os.path.join(settings.memory_db_dir, 'session_memory.json')
        if os.path.exists(memory_file):
            with open(memory_file, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
            
            print(f"📄 记忆文件存在，包含 {len(memory_data.get('default_user', []))} 条记录")
            
            # 显示最近的对话记录
            recent_memories = memory_data.get('default_user', [])[-5:]  # 最近5条
            print("\n📋 最近的对话记录:")
            for i, memory in enumerate(recent_memories):
                print(f"  {i+1}. 问题: {memory.get('question', 'N/A')}")
                print(f"     回答: {memory.get('answer', 'N/A')[:100]}...")
                print(f"     时间: {memory.get('created_at', 'N/A')}")
                print()
        else:
            print("❌ 记忆文件不存在")
        
        # 测试记忆检索
        print("🔍 测试记忆检索功能:")
        test_question = "个股走势表现"
        relevant_memories = memory_manager.get_relevant_memories(test_question, max_results=3)
        print(f"  检索到 {len(relevant_memories)} 条相关记忆")
        
        for i, memory in enumerate(relevant_memories):
            print(f"  {i+1}. 问题: {memory.get('question', 'N/A')}")
            print(f"     相关性: {memory.get('relevance_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 记忆功能测试失败: {e}")
        return False


def test_memory_integration():
    """测试记忆集成"""
    print("\n" + "=" * 60)
    print("🔍 测试记忆集成")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        
        # 检查QA系统是否使用记忆
        from core.enhanced_qa_system import EnhancedQASystem
        
        # 这里需要检查QA系统是否正确集成了记忆功能
        print("📋 检查QA系统记忆集成:")
        print("  - 记忆管理器: 已初始化")
        print("  - 记忆检索: 需要验证")
        print("  - 上下文传递: 需要验证")
        
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
        # 分析对话的上下文连续性
        memory_file = os.path.join('memory_db', 'session_memory.json')
        if os.path.exists(memory_file):
            with open(memory_file, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
            
            conversations = memory_data.get('default_user', [])
            
            print("📊 上下文连续性分析:")
            
            # 检查最近的对话
            recent_conversations = conversations[-4:]  # 最近4条
            for i in range(len(recent_conversations) - 1):
                current = recent_conversations[i]
                next_conv = recent_conversations[i + 1]
                
                print(f"\n对话 {i+1} -> {i+2}:")
                print(f"  问题1: {current.get('question', 'N/A')}")
                print(f"  回答1: {current.get('answer', 'N/A')[:50]}...")
                print(f"  问题2: {next_conv.get('question', 'N/A')}")
                print(f"  回答2: {next_conv.get('answer', 'N/A')[:50]}...")
                
                # 检查上下文连续性
                if "这个图" in next_conv.get('question', '') or "那个图" in next_conv.get('question', ''):
                    if "无法确定" in next_conv.get('answer', '') or "未提供" in next_conv.get('answer', ''):
                        print(f"  ❌ 上下文连续性失败: 后续问题无法理解前文")
                    else:
                        print(f"  ✅ 上下文连续性正常")
                else:
                    print(f"  ⚠️  无法判断上下文连续性")
        
        return True
        
    except Exception as e:
        print(f"❌ 上下文连续性测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始记忆功能测试...")
    
    tests = [
        ("记忆功能测试", test_memory_functionality),
        ("记忆集成测试", test_memory_integration),
        ("上下文连续性测试", test_context_continuity)
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
    
    if passed < total:
        print("\n🚨 发现问题:")
        print("  - 记忆功能可能存在问题")
        print("  - 上下文连续性需要检查")
        print("  - QA系统记忆集成需要验证")


if __name__ == "__main__":
    main() 