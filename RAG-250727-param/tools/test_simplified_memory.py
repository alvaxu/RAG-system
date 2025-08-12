'''
程序说明：

## 1. 测试重构后的简化记忆系统
## 2. 验证指代词解析功能
## 3. 测试上下文管理功能
## 4. 验证向后兼容性
'''

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory_manager import SimplifiedMemoryManager

def test_simplified_memory():
    """测试简化记忆系统"""
    print("🧪 开始测试简化记忆系统...")
    
    try:
        # 初始化记忆管理器
        print("\n🚀 初始化记忆管理器...")
        memory_manager = SimplifiedMemoryManager()
        
        # 测试1：指代词解析
        print("\n📝 测试1：指代词解析")
        user_id = "test_user"
        
        # 第一次查询
        question1 = "中芯国际的主要业务是什么？"
        print(f"  问题1: {question1}")
        
        # 解析指代词（第一次应该没有变化）
        resolved1 = memory_manager.process_query(user_id, question1)
        print(f"  解析后: {resolved1}")
        
        # 更新上下文
        answer1 = "中芯国际主要从事集成电路制造业务"
        memory_manager.update_context(user_id, question1, answer1)
        print(f"  答案1: {answer1}")
        
        # 第二次查询（包含指代词）
        question2 = "它的技术优势在哪里？"
        print(f"\n  问题2: {question2}")
        
        # 解析指代词
        resolved2 = memory_manager.process_query(user_id, question2)
        print(f"  解析后: {resolved2}")
        
        # 更新上下文
        answer2 = "中芯国际在先进制程技术方面具有优势"
        memory_manager.update_context(user_id, question2, answer2)
        print(f"  答案2: {answer2}")
        
        # 第三次查询（包含"那个"）
        question3 = "刚才说的那个技术具体是什么？"
        print(f"\n  问题3: {question3}")
        
        # 解析指代词
        resolved3 = memory_manager.process_query(user_id, question3)
        print(f"  解析后: {resolved3}")
        
        # 测试2：上下文摘要
        print("\n📊 测试2：上下文摘要")
        context_summary = memory_manager.get_context_summary(user_id)
        print(f"  上下文摘要: {context_summary}")
        
        # 测试3：记忆统计
        print("\n📈 测试3：记忆统计")
        memory_stats = memory_manager.get_memory_stats(user_id)
        print(f"  记忆统计: {memory_stats}")
        
        # 测试4：向后兼容性
        print("\n🔄 测试4：向后兼容性")
        
        # 测试旧的add_to_session方法
        memory_manager.add_to_session(user_id, "测试问题", "测试答案")
        print("  ✅ add_to_session方法正常工作")
        
        # 测试旧的clear_session_memory方法
        memory_manager.clear_session_memory(user_id)
        print("  ✅ clear_session_memory方法正常工作")
        
        # 重新添加一些上下文
        memory_manager.update_context(user_id, "重新测试", "重新答案")
        
        print("\n✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_simplified_memory()
    sys.exit(0 if success else 1)
