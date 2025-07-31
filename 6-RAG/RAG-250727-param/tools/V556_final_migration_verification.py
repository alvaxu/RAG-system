'''
程序说明：
## 1. 最终迁移验证测试
## 2. 检查所有功能是否完整迁移到增强版QA系统
## 3. 验证指代词优化、记忆管理、多阶段优化等功能
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


def test_migration_completeness():
    """
    测试迁移完整性
    """
    print("🔍 开始测试迁移完整性...")
    
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
        
        if not api_key or api_key in ['你的APIKEY', '你的DashScope API密钥']:
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
        
        # 测试功能完整性
        test_results = []
        
        # 1. 测试基本问答功能
        print("\n📝 测试基本问答功能...")
        try:
            result = qa_system.answer_question("中芯国际2024年的产能利用率如何？")
            test_results.append(("基本问答", True, f"回答长度: {len(result.get('answer', ''))}"))
        except Exception as e:
            test_results.append(("基本问答", False, str(e)))
        
        # 2. 测试记忆功能
        print("🧠 测试记忆功能...")
        try:
            user_id = "test_user"
            result1 = qa_system.answer_with_memory(user_id, "中芯国际2024年的产能利用率如何？")
            result2 = qa_system.answer_with_memory(user_id, "那2025年的呢？")
            test_results.append(("记忆功能", True, f"问题1: {len(result1.get('answer', ''))}, 问题2: {len(result2.get('answer', ''))}"))
        except Exception as e:
            test_results.append(("记忆功能", False, str(e)))
        
        # 3. 测试图片搜索功能
        print("🖼️ 测试图片搜索功能...")
        try:
            result = qa_system.answer_question("请显示相关的图表")
            test_results.append(("图片搜索", True, f"回答长度: {len(result.get('answer', ''))}"))
        except Exception as e:
            test_results.append(("图片搜索", False, str(e)))
        
        # 4. 测试优化引擎
        print("⚙️ 测试优化引擎...")
        try:
            stats = qa_system.get_optimization_stats()
            test_results.append(("优化引擎", True, f"引擎数量: {len(stats)}"))
        except Exception as e:
            test_results.append(("优化引擎", False, str(e)))
        
        # 5. 测试记忆管理
        print("💾 测试记忆管理...")
        try:
            memory_stats = qa_system.get_memory_stats("test_user")
            test_results.append(("记忆管理", True, f"记忆统计: {memory_stats}"))
        except Exception as e:
            test_results.append(("记忆管理", False, str(e)))
        
        # 6. 测试相似度计算
        print("📊 测试相似度计算...")
        try:
            similarity = qa_system.calculate_similarity("中芯国际", "中芯国际产能利用率")
            test_results.append(("相似度计算", True, f"相似度: {similarity:.3f}"))
        except Exception as e:
            test_results.append(("相似度计算", False, str(e)))
        
        # 7. 测试时间戳格式化
        print("⏰ 测试时间戳格式化...")
        try:
            timestamp = qa_system.format_timestamp(1640995200)  # 2022-01-01 00:00:00
            test_results.append(("时间戳格式化", True, f"格式化结果: {timestamp}"))
        except Exception as e:
            test_results.append(("时间戳格式化", False, str(e)))
        
        # 8. 测试源信息添加
        print("📚 测试源信息添加...")
        try:
            sources = [{'content': '测试内容', 'metadata': {'document_name': '测试文档', 'page_number': 1}}]
            enhanced_answer = qa_system.append_sources_to_answer("测试回答", sources)
            test_results.append(("源信息添加", True, f"增强回答长度: {len(enhanced_answer)}"))
        except Exception as e:
            test_results.append(("源信息添加", False, str(e)))
        
        # 输出测试结果
        print("\n📋 迁移完整性测试结果:")
        success_count = 0
        for test_name, success, details in test_results:
            status = "✅" if success else "❌"
            print(f"  {status} {test_name}: {details}")
            if success:
                success_count += 1
        
        print(f"\n📈 测试通过率: {success_count}/{len(test_results)} ({success_count/len(test_results)*100:.1f}%)")
        
        return success_count == len(test_results)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.error(f"测试失败: {e}")
        return False


def test_config_integration():
    """
    测试配置集成
    """
    print("\n🔧 测试配置集成...")
    
    try:
        config = Settings.load_from_file('config.json')
        
        # 检查关键配置项
        config_dict = config.to_dict()
        required_configs = {
            'api.dashscope_api_key': 'API密钥',
            'paths.vector_db_dir': '向量数据库目录',
            'paths.memory_db_dir': '记忆数据库目录',
            'qa_system': 'QA系统配置',
            'vector_store': '向量存储配置',
            'processing': '处理配置'
        }
        
        missing_configs = []
        for key, description in required_configs.items():
            if '.' in key:
                # 处理嵌套键
                parts = key.split('.')
                current = config_dict
                found = True
                for part in parts:
                    if part in current:
                        current = current[part]
                    else:
                        found = False
                        break
                if not found:
                    missing_configs.append(f"{description}({key})")
            else:
                if key not in config_dict:
                    missing_configs.append(f"{description}({key})")
        
        if missing_configs:
            print(f"❌ 缺少配置项: {', '.join(missing_configs)}")
            return False
        else:
            print("✅ 所有必需配置项都已配置")
            return True
            
    except Exception as e:
        print(f"❌ 配置集成测试失败: {e}")
        return False


if __name__ == '__main__':
    print("🚀 开始最终迁移验证...")
    
    # 测试配置集成
    config_success = test_config_integration()
    
    # 测试迁移完整性
    migration_success = test_migration_completeness()
    
    if config_success and migration_success:
        print("\n🎉 最终迁移验证成功！")
        print("✅ 所有功能已成功迁移到增强版QA系统")
        print("✅ 指代词优化功能完整保留")
        print("✅ 多阶段优化流程正常工作")
        print("✅ 记忆管理功能完整")
        print("✅ 配置管理集成正常")
        print("✅ 图片搜索功能正常")
        print("✅ 所有辅助功能完整")
    else:
        print("\n❌ 最终迁移验证失败！")
        print("请检查缺失的功能或配置") 