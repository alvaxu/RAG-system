'''
程序说明：
## 1. 测试记忆模块修复效果
## 2. 验证改进的检索策略
## 3. 测试降低的相关性阈值
## 4. 提供修复效果对比
'''

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.memory_manager import MemoryManager
from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def test_memory_fix():
    """
    测试记忆模块修复效果
    """
    print("🧪 测试记忆模块修复效果")
    print("=" * 50)
    
    # 1. 测试记忆管理器修复
    print("\n📋 1. 测试记忆管理器修复...")
    try:
        memory_manager = MemoryManager()
        print("✅ 记忆管理器初始化成功")
        
        # 测试相关性阈值降低
        test_questions = [
            "中芯国际的主要业务和核心技术是什么？",
            "中芯国际在晶圆代工行业的市场地位如何？",
            "中芯国际的产能扩张历程和现状是怎样的？",
            "中芯国际2024-2027年的净利润增长趋势如何？"
        ]
        
        for i, question in enumerate(test_questions):
            print(f"\n   测试问题 {i+1}: {question}")
            
            # 测试记忆检索
            relevant_memories = memory_manager.retrieve_relevant_memory("default_user", question)
            print(f"   相关记忆数量: {len(relevant_memories)}")
            
            for j, memory in enumerate(relevant_memories):
                print(f"     记忆 {j+1}: {memory.question}")
                print(f"     相关性: {getattr(memory, 'relevance_score', 'N/A')}")
            
            # 测试上下文构建
            context = memory_manager.build_context("default_user", question)
            print(f"   上下文构建: {context.get('has_memory', False)}")
            print(f"   记忆数量: {context.get('memory_count', 0)}")
        
    except Exception as e:
        print(f"❌ 记忆管理器测试失败: {e}")
    
    # 2. 测试QA系统修复
    print("\n📋 2. 测试QA系统修复...")
    try:
        # 加载配置
        settings = Settings.load_from_file("config.json")
        api_key = settings.dashscope_api_key
        
        if not api_key or api_key == '你的APIKEY':
            print("⚠️  未配置API密钥，跳过QA系统测试")
        else:
            # 加载QA系统
            vector_db_path = "./central/vector_db"
            qa_system = load_enhanced_qa_system(vector_db_path, api_key)
            
            if qa_system:
                print("✅ QA系统加载成功")
                
                # 测试改进的检索策略
                test_question = "中芯国际的主要业务和核心技术是什么？"
                print(f"\n   测试问题: {test_question}")
                
                # 测试初始检索
                initial_docs = qa_system._initial_retrieval(test_question, 5)
                print(f"   初始检索结果数量: {len(initial_docs)}")
                
                # 分析检索结果类型
                text_count = 0
                image_count = 0
                for doc in initial_docs:
                    chunk_type = doc.metadata.get('chunk_type', 'unknown')
                    if chunk_type == 'text':
                        text_count += 1
                    elif chunk_type == 'image':
                        image_count += 1
                
                print(f"   文本内容: {text_count}")
                print(f"   图片内容: {image_count}")
                
                # 测试记忆功能
                result = qa_system.answer_with_memory("test_user", test_question, 5)
                print(f"   记忆问答结果: {'成功' if result.get('answer') else '失败'}")
                
            else:
                print("❌ QA系统加载失败")
                
    except Exception as e:
        print(f"❌ QA系统测试失败: {e}")
    
    # 3. 对比修复前后效果
    print("\n📋 3. 修复效果对比...")
    print("修复前问题:")
    print("  - 后续查询只检索到图片内容，缺乏文本内容")
    print("  - 记忆相关性阈值过高(0.1)，导致记忆无法正确关联")
    print("  - 检索策略不平衡，偏向图片而非文本")
    
    print("\n修复后改进:")
    print("  - 相关性阈值降低到0.05，提高记忆关联性")
    print("  - 改进检索策略，确保文本和图片平衡")
    print("  - 增加更多相关性判断规则")
    print("  - 添加错误处理和降级机制")
    
    # 4. 验证修复效果
    print("\n📋 4. 验证修复效果...")
    
    # 检查记忆文件
    memory_file = "memory_db/session_memory.json"
    if os.path.exists(memory_file):
        import json
        with open(memory_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"   记忆文件大小: {os.path.getsize(memory_file)} 字节")
        print(f"   用户数量: {len(data)}")
        
        for user_id, memories in data.items():
            print(f"   用户 {user_id}: {len(memories)} 条记忆")
            
            # 分析记忆质量
            success_count = 0
            fail_count = 0
            for memory in memories:
                if '没有找到相关信息' in memory['answer']:
                    fail_count += 1
                else:
                    success_count += 1
            
            print(f"     成功回答: {success_count}")
            print(f"     失败回答: {fail_count}")
            print(f"     成功率: {success_count/(success_count+fail_count)*100:.1f}%")
    else:
        print("   ❌ 记忆文件不存在")
    
    print("\n" + "=" * 50)
    print("🎯 记忆模块修复测试完成")

def main():
    """
    主函数
    """
    test_memory_fix()

if __name__ == "__main__":
    main() 