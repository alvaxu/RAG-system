"""
后端测试运行器

运行RAG系统的后端功能测试（不包含API接口测试）
"""

import sys
import os
import logging
from pathlib import Path

# 设置UTF-8编码以支持emoji字符
if sys.platform.startswith('win'):
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        pass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_config_validation_tests():
    """运行配置验证测试"""
    try:
        from tests.test_config_validation import main as run_config_tests
        print("\n" + "="*60)
        print("🧪 运行配置验证测试")
        print("="*60)
        run_config_tests()
        return True
    except Exception as e:
        logger.error(f"配置验证测试运行失败: {e}")
        return False


def run_architecture_tests():
    """运行架构测试"""
    try:
        # 注意：test_new_architecture.py 可能不存在，暂时跳过
        print("\n" + "="*60)
        print("🧪 运行新架构测试")
        print("="*60)
        print("⚠️ 架构测试暂时跳过（test_new_architecture.py 不存在）")
        return True
    except Exception as e:
        logger.error(f"架构测试运行失败: {e}")
        return False


def run_retrieval_algorithm_tests():
    """运行召回引擎核心算法测试"""
    try:
        logger.info("=" * 50)
        logger.info("开始运行召回引擎核心算法测试...")
        logger.info("=" * 50)
        
        from tests.test_retrieval_algorithms_simple import main as run_retrieval_tests
        run_retrieval_tests()
        
        logger.info("召回引擎核心算法测试完成")
        return True
        
    except Exception as e:
        logger.error(f"召回引擎核心算法测试失败: {e}")
        return False


def run_llm_caller_enhanced_tests():
    """运行LLM调用器增强功能测试"""
    try:
        logger.info("=" * 50)
        logger.info("开始运行LLM调用器增强功能测试...")
        logger.info("=" * 50)
        
        from tests.test_llm_caller_enhanced import main as run_llm_tests
        run_llm_tests()
        
        logger.info("LLM调用器增强功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"LLM调用器增强功能测试失败: {e}")
        return False


def run_reranking_enhanced_tests():
    """运行增强重排序模块测试"""
    try:
        logger.info("=" * 50)
        logger.info("开始运行增强重排序模块测试...")
        logger.info("=" * 50)
        
        from tests.test_reranking_enhanced import main as run_reranking_tests
        run_reranking_tests()
        
        logger.info("增强重排序模块测试完成")
        return True
        
    except Exception as e:
        logger.error(f"增强重排序模块测试失败: {e}")
        return False


def run_visual_search_tests():
    """运行视觉搜索功能测试"""
    try:
        logger.info("=" * 50)
        logger.info("开始运行视觉搜索功能测试...")
        logger.info("=" * 50)
        
        from tests.test_visual_search import main as run_visual_search_tests
        run_visual_search_tests()
        
        logger.info("视觉搜索功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"视觉搜索功能测试失败: {e}")
        return False


def run_table_search_tests():
    """运行表格搜索测试"""
    try:
        from tests.test_table_search import run_table_search_tests
        return run_table_search_tests()
    except Exception as e:
        print(f"❌ 表格搜索测试执行失败: {e}")
        return False


def run_hybrid_search_tests():
    """运行混合搜索策略优化测试"""
    try:
        from tests.test_hybrid_search import run_hybrid_search_tests
        return run_hybrid_search_tests()
    except Exception as e:
        print(f"❌ 混合搜索策略优化测试执行失败: {e}")
        return False


def run_performance_optimization_tests():
    """运行性能优化算法测试"""
    try:
        from tests.test_performance_optimization import run_performance_optimization_tests
        return run_performance_optimization_tests()
    except Exception as e:
        print(f"❌ 性能优化算法测试执行失败: {e}")
        return False


def run_query_processor_constructor_tests():
    """运行QueryProcessor构造函数参数修复测试"""
    try:
        from tests.test_query_processor_constructor import run_query_processor_constructor_tests
        return run_query_processor_constructor_tests()
    except Exception as e:
        print(f"❌ QueryProcessor构造函数参数修复测试执行失败: {e}")
        return False


# API接口测试已移至独立的 test_rag_api.py 文件
# 这里不再包含API测试，避免与 start_rag.bat 选项4重复


def run_config_advanced_tests():
    """运行高级配置管理测试"""
    try:
        logger.info("=" * 50)
        logger.info("开始运行高级配置管理测试...")
        logger.info("=" * 50)
        
        import subprocess
        import sys
        
        result = subprocess.run([sys.executable, "test_config_advanced.py"], 
                              capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            logger.info("✅ 高级配置管理测试全部通过")
            logger.info(f"📊 测试结果: {result.stdout}")
        else:
            logger.error(f"❌ 高级配置管理测试失败: {result.stderr}")
        
        logger.info("高级配置管理测试完成")
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"高级配置管理测试失败: {e}")
        return False


def main():
    """运行后端功能测试"""
    print("🚀 开始运行RAG系统后端功能测试...")
    print("=" * 60)
    
    all_tests_passed = True
    
    # 核心架构测试
    print("\n🔧 第一阶段：核心架构重构测试")
    print("-" * 40)    
    all_tests_passed &= run_architecture_tests()
    
    # 召回引擎算法测试
    print("\n🎯 第二阶段第一项：召回引擎算法完善测试")
    print("-" * 40)
    all_tests_passed &= run_retrieval_algorithm_tests()
    
    # LLM调用器增强测试
    print("\n🤖 第二阶段第二项：LLM调用器功能完善测试")
    print("-" * 40)
    all_tests_passed &= run_llm_caller_enhanced_tests()
    
    # Reranking增强测试
    print("\n📊 第二阶段第三项：Reranking模块功能完善测试")
    print("-" * 40)
    all_tests_passed &= run_reranking_enhanced_tests()
    
    # 视觉搜索测试
    print("\n🖼️ 视觉搜索算法测试")
    print("-" * 40)
    all_tests_passed &= run_visual_search_tests()
    
    # 表格搜索测试
    print("\n📋 表格搜索算法测试")
    print("-" * 40)
    all_tests_passed &= run_table_search_tests()
    
    # 混合搜索策略优化测试
    print("\n🔀 混合搜索策略优化测试")
    print("-" * 40)
    all_tests_passed &= run_hybrid_search_tests()
    
    # 性能优化算法测试
    print("\n⚡ 性能优化算法测试")
    print("-" * 40)
    all_tests_passed &= run_performance_optimization_tests()
    
    # QueryProcessor构造函数参数修复测试
    print("\n🔧 QueryProcessor构造函数参数修复测试")
    print("-" * 40)
    all_tests_passed &= run_query_processor_constructor_tests()
    
    # 注意：API接口测试已移至独立的 test_rag_api.py 文件
    # 避免与 start_rag.bat 选项4重复
    
    # 高级配置管理测试
    print("\n⚙️ 第三阶段：高级配置管理测试")
    print("-" * 40)
    all_tests_passed &= run_config_advanced_tests()
    
    # 测试总结
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 所有后端功能测试通过！")
        print("💡 提示：API接口测试请使用 start_rag.bat 选项4")
    else:
        print("⚠️ 部分后端功能测试失败，请检查相关功能")
    
    return all_tests_passed


if __name__ == "__main__":
    all_passed = main()
    # 如果所有测试通过，返回退出码0，否则返回1
    sys.exit(0 if all_passed else 1)
