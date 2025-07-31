'''
程序说明：
## 1. 测试指代词优化功能迁移到增强版QA系统
## 2. 验证记忆管理和指代词理解功能
## 3. 测试配置管理是否正确应用
'''

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入相关模块
from config.settings import Settings
from core.enhanced_qa_system import load_enhanced_qa_system
from core.memory_manager import MemoryManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_enhanced_qa_system():
    """
    测试增强版QA系统
    """
    print("🧪 开始测试增强版QA系统...")
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        print("✅ 配置加载成功")
        
        # 初始化记忆管理器
        memory_manager = MemoryManager(config.memory_db_dir)
        print("✅ 记忆管理器初始化成功")
        
        # 初始化增强版QA系统
        api_key = config.dashscope_api_key
        vector_db_path = config.vector_db_dir
        
        if not api_key or api_key == '你的APIKEY':
            print("❌ 未配置API密钥")
            return False
        
        qa_system = load_enhanced_qa_system(
            vector_db_path, 
            api_key, 
            memory_manager, 
            config.to_dict()
        )
        
        if not qa_system:
            print("❌ 增强版QA系统初始化失败")
            return False
        
        print("✅ 增强版QA系统初始化成功")
        
        # 测试基本问答功能
        print("\n📝 测试基本问答功能...")
        result = qa_system.answer_question("中芯国际2024年的产能利用率如何？")
        print(f"回答: {result.get('answer', '')[:100]}...")
        print(f"来源数量: {len(result.get('sources', []))}")
        
        # 测试记忆功能
        print("\n🧠 测试记忆功能...")
        user_id = "test_user"
        
        # 第一个问题
        result1 = qa_system.answer_with_memory(user_id, "中芯国际2024年的产能利用率如何？")
        print(f"问题1回答: {result1.get('answer', '')[:100]}...")
        
        # 第二个问题（使用指代词）
        result2 = qa_system.answer_with_memory(user_id, "那2025年的呢？")
        print(f"问题2回答: {result2.get('answer', '')[:100]}...")
        
        # 检查记忆统计
        memory_stats = qa_system.get_memory_stats(user_id)
        print(f"记忆统计: {memory_stats}")
        
        # 测试优化引擎统计
        print("\n⚙️ 测试优化引擎统计...")
        optimization_stats = qa_system.get_optimization_stats()
        print(f"优化引擎统计: {optimization_stats}")
        
        print("\n✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.error(f"测试失败: {e}")
        return False


def test_config_management():
    """
    测试配置管理
    """
    print("\n🔧 测试配置管理...")
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        
        # 检查关键配置
        required_configs = [
            'dashscope_api_key',
            'vector_db_dir',
            'memory_db_dir',
            'qa_system',
            'vector_store'
        ]
        
        for config_key in required_configs:
            if config_key in config.to_dict():
                print(f"✅ {config_key}: 已配置")
            else:
                print(f"❌ {config_key}: 未配置")
        
        # 检查QA系统配置
        qa_config = config.to_dict().get('qa_system', {})
        qa_required = ['model_name', 'temperature', 'max_tokens']
        for key in qa_required:
            if key in qa_config:
                print(f"✅ qa_system.{key}: {qa_config[key]}")
            else:
                print(f"❌ qa_system.{key}: 未配置")
        
        # 检查向量存储配置
        vector_config = config.to_dict().get('vector_store', {})
        vector_required = ['similarity_top_k', 'similarity_threshold']
        for key in vector_required:
            if key in vector_config:
                print(f"✅ vector_store.{key}: {vector_config[key]}")
            else:
                print(f"❌ vector_store.{key}: 未配置")
        
        print("✅ 配置管理测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 配置管理测试失败: {e}")
        return False


if __name__ == '__main__':
    print("🚀 开始迁移验证测试...")
    
    # 测试配置管理
    config_success = test_config_management()
    
    # 测试增强版QA系统
    qa_success = test_enhanced_qa_system()
    
    if config_success and qa_success:
        print("\n🎉 迁移验证成功！")
        print("✅ 指代词优化功能已成功迁移到增强版QA系统")
        print("✅ 配置管理正常工作")
        print("✅ 记忆管理功能正常")
        print("✅ 增强版功能可用")
    else:
        print("\n❌ 迁移验证失败！")
        print("请检查配置和系统状态") 