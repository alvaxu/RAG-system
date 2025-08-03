'''
程序说明：
## 1. 调试记忆模块问题
## 2. 分析后续查询失败的原因
## 3. 检查记忆存储和检索逻辑
## 4. 提供问题诊断和解决方案
'''

import os
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.memory_manager import MemoryManager
from core.enhanced_qa_system import EnhancedQASystem
from config import ConfigManager

def analyze_memory_file():
    """
    分析记忆文件的内容
    """
    print("=== 分析记忆文件 ===")
    
    memory_file = "memory_db/session_memory.json"
    if not os.path.exists(memory_file):
        print(f"记忆文件不存在: {memory_file}")
        return
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"记忆文件大小: {os.path.getsize(memory_file)} 字节")
    print(f"用户数量: {len(data)}")
    
    for user_id, memories in data.items():
        print(f"\n用户 {user_id}:")
        print(f"  记忆数量: {len(memories)}")
        
        for i, memory in enumerate(memories):
            print(f"  记忆 {i+1}:")
            print(f"    问题: {memory['question']}")
            print(f"    回答: {memory['answer'][:100]}...")
            print(f"    时间: {memory['created_at']}")
            print(f"    相关记忆数: {memory['context'].get('relevant_memories', 0)}")
            
            # 检查sources
            sources = memory['context'].get('sources', [])
            print(f"    来源数量: {len(sources)}")
            
            if sources:
                print("    来源类型分析:")
                text_sources = 0
                image_sources = 0
                for source in sources:
                    chunk_type = source.get('metadata', {}).get('chunk_type', 'unknown')
                    if chunk_type == 'text':
                        text_sources += 1
                    elif chunk_type == 'image':
                        image_sources += 1
                
                print(f"      文本来源: {text_sources}")
                print(f"      图片来源: {image_sources}")

def test_memory_manager():
    """
    测试记忆管理器
    """
    print("\n=== 测试记忆管理器 ===")
    
    try:
        memory_manager = MemoryManager()
        print("记忆管理器初始化成功")
        
        # 测试记忆检索
        test_question = "中芯国际在晶圆代工行业的市场地位如何？"
        relevant_memories = memory_manager.retrieve_relevant_memory("default_user", test_question)
        print(f"相关问题检索结果: {len(relevant_memories)} 条")
        
        for i, memory in enumerate(relevant_memories):
            print(f"  相关记忆 {i+1}:")
            print(f"    问题: {memory.question}")
            print(f"    相关性: {getattr(memory, 'relevance_score', 'N/A')}")
        
        # 测试上下文构建
        context = memory_manager.build_context("default_user", test_question)
        print(f"上下文构建结果:")
        print(f"  有记忆: {context.get('has_memory', False)}")
        print(f"  记忆数量: {context.get('memory_count', 0)}")
        print(f"  记忆上下文长度: {len(context.get('memory_context', ''))}")
        
    except Exception as e:
        print(f"记忆管理器测试失败: {e}")

def test_qa_system_memory():
    """
    测试QA系统的记忆功能
    """
    print("\n=== 测试QA系统记忆功能 ===")
    
    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.settings
        
        # 初始化记忆管理器
        memory_manager = MemoryManager()
        
        # 加载向量存储
        vector_db_path = config.vector_db_dir
        if not os.path.exists(vector_db_path):
            print(f"向量数据库不存在: {vector_db_path}")
            return
        
        # 这里需要实际的向量存储，暂时跳过
        print("向量存储加载跳过（需要实际数据）")
        
        # 测试记忆相关功能
        test_questions = [
            "中芯国际的主要业务和核心技术是什么？",
            "中芯国际在晶圆代工行业的市场地位如何？",
            "中芯国际的产能扩张历程和现状是怎样的？"
        ]
        
        for i, question in enumerate(test_questions):
            print(f"\n测试问题 {i+1}: {question}")
            
            # 测试记忆检索
            relevant_memories = memory_manager.retrieve_relevant_memory("default_user", question)
            print(f"  相关记忆数量: {len(relevant_memories)}")
            
            # 测试上下文构建
            context = memory_manager.build_context("default_user", question)
            print(f"  上下文构建: {context.get('has_memory', False)}")
            print(f"  记忆数量: {context.get('memory_count', 0)}")
            
    except Exception as e:
        print(f"QA系统记忆功能测试失败: {e}")

def analyze_problem_pattern():
    """
    分析问题模式
    """
    print("\n=== 分析问题模式 ===")
    
    memory_file = "memory_db/session_memory.json"
    if not os.path.exists(memory_file):
        print("记忆文件不存在")
        return
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for user_id, memories in data.items():
        print(f"\n用户 {user_id} 的问题模式分析:")
        
        for i, memory in enumerate(memories):
            question = memory['question']
            answer = memory['answer']
            sources = memory['context'].get('sources', [])
            
            print(f"  问题 {i+1}: {question}")
            print(f"    回答长度: {len(answer)}")
            print(f"    是否失败: {'是' if '没有找到相关信息' in answer else '否'}")
            print(f"    来源数量: {len(sources)}")
            
            # 分析来源类型
            text_count = 0
            image_count = 0
            for source in sources:
                chunk_type = source.get('metadata', {}).get('chunk_type', 'unknown')
                if chunk_type == 'text':
                    text_count += 1
                elif chunk_type == 'image':
                    image_count += 1
            
            print(f"    文本来源: {text_count}, 图片来源: {image_count}")
            
            # 分析相关性分数
            if sources:
                scores = [source.get('score', 0) for source in sources]
                print(f"    平均相关性分数: {sum(scores)/len(scores):.4f}")

def check_memory_consistency():
    """
    检查记忆一致性
    """
    print("\n=== 检查记忆一致性 ===")
    
    memory_file = "memory_db/session_memory.json"
    if not os.path.exists(memory_file):
        print("记忆文件不存在")
        return
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for user_id, memories in data.items():
        print(f"\n用户 {user_id} 的记忆一致性检查:")
        
        for i, memory in enumerate(memories):
            question = memory['question']
            answer = memory['answer']
            context = memory['context']
            
            # 检查必要字段
            required_fields = ['question', 'answer', 'context', 'timestamp', 'created_at']
            missing_fields = [field for field in required_fields if field not in memory]
            
            if missing_fields:
                print(f"  记忆 {i+1} 缺少字段: {missing_fields}")
            
            # 检查上下文结构
            if 'sources' not in context:
                print(f"  记忆 {i+1} 缺少sources字段")
            
            # 检查时间戳
            if 'timestamp' in memory:
                try:
                    float(memory['timestamp'])
                except (ValueError, TypeError):
                    print(f"  记忆 {i+1} 时间戳格式错误")
            
            # 检查记忆ID
            if 'memory_id' not in memory:
                print(f"  记忆 {i+1} 缺少memory_id")

def main():
    """
    主函数
    """
    print("记忆模块问题诊断工具")
    print("=" * 50)
    
    # 1. 分析记忆文件
    analyze_memory_file()
    
    # 2. 测试记忆管理器
    test_memory_manager()
    
    # 3. 测试QA系统记忆功能
    test_qa_system_memory()
    
    # 4. 分析问题模式
    analyze_problem_pattern()
    
    # 5. 检查记忆一致性
    check_memory_consistency()
    
    print("\n=== 诊断总结 ===")
    print("基于分析，可能的问题原因：")
    print("1. 后续查询只检索到图片内容，缺乏文本内容")
    print("2. 记忆模块的相关性计算可能过于严格")
    print("3. 向量检索可能偏向图片而非文本")
    print("4. 记忆上下文构建可能存在问题")
    print("\n建议解决方案：")
    print("1. 调整检索策略，确保文本和图片的平衡")
    print("2. 优化记忆相关性计算算法")
    print("3. 检查向量存储的索引质量")
    print("4. 增加记忆模块的调试日志")

if __name__ == "__main__":
    main() 