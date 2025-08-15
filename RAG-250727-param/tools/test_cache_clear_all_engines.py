'''
程序说明：
## 1. 测试所有引擎的缓存清理功能
## 2. 验证优雅退出时的缓存清理机制
## 3. 确保系统资源得到正确释放
'''

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from v2.core.document_loader import DocumentLoader
from v2.core.text_engine import TextEngine
from v2.core.image_engine import ImageEngine
from v2.core.table_engine import TableEngine
from v2.core.dashscope_reranking_engine import DashScopeRerankingEngine
from v2.core.dashscope_llm_engine import DashScopeLLMEngine
from v2.config.v2_config import V2ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_document_loader_cache_clear():
    """测试文档加载器缓存清理"""
    logger.info("🧪 测试文档加载器缓存清理...")
    
    try:
        # 创建文档加载器
        config_manager = V2ConfigManager()
        doc_loader = DocumentLoader(config_manager.config)
        
        # 模拟加载一些文档
        doc_loader._docs_cache = {"doc1": "content1", "doc2": "content2"}
        doc_loader._loaded = True
        doc_loader._load_time = 1.0
        
        logger.info(f"清理前状态: 缓存文档数={len(doc_loader._docs_cache)}, 已加载={doc_loader._loaded}")
        
        # 清理缓存
        doc_loader.clear_cache()
        
        logger.info(f"清理后状态: 缓存文档数={len(doc_loader._docs_cache)}, 已加载={doc_loader._loaded}")
        
        assert len(doc_loader._docs_cache) == 0, "文档缓存应该被清空"
        assert not doc_loader._loaded, "加载状态应该被重置"
        assert doc_loader._load_time == 0.0, "加载时间应该被重置"
        
        logger.info("✅ 文档加载器缓存清理测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 文档加载器缓存清理测试失败: {e}")
        return False

def test_text_engine_cache_clear():
    """测试文本引擎缓存清理"""
    logger.info("🧪 测试文本引擎缓存清理...")
    
    try:
        # 创建文本引擎配置
        from v2.config.v2_config import TextEngineConfigV2
        text_config = TextEngineConfigV2()
        
        # 创建模拟的向量数据库
        class MockVectorStore:
            def __init__(self):
                self.docstore = {}
        
        # 创建文本引擎
        text_engine = TextEngine(text_config, vector_store=MockVectorStore(), skip_initial_load=True)
        
        # 模拟加载一些文档
        text_engine.text_docs = {"text1": "content1", "text2": "content2"}
        text_engine._docs_loaded = True
        
        logger.info(f"清理前状态: 缓存文档数={len(text_engine.text_docs)}, 已加载={text_engine._docs_loaded}")
        
        # 清理缓存
        cleared_count = text_engine.clear_cache()
        
        logger.info(f"清理后状态: 缓存文档数={len(text_engine.text_docs)}, 已加载={text_engine._docs_loaded}, 清理数量={cleared_count}")
        
        assert len(text_engine.text_docs) == 0, "文本文档缓存应该被清空"
        assert not text_engine._docs_loaded, "加载状态应该被重置"
        assert cleared_count == 2, "应该清理2个文档"
        
        logger.info("✅ 文本引擎缓存清理测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 文本引擎缓存清理测试失败: {e}")
        return False

def test_image_engine_cache_clear():
    """测试图片引擎缓存清理"""
    logger.info("🧪 测试图片引擎缓存清理...")
    
    try:
        # 创建图片引擎配置
        from v2.config.v2_config import ImageEngineConfigV2
        image_config = ImageEngineConfigV2()
        
        # 创建模拟的向量数据库
        class MockVectorStore:
            def __init__(self):
                self.docstore = {}
        
        # 创建图片引擎
        image_engine = ImageEngine(image_config, vector_store=MockVectorStore(), skip_initial_load=True)
        
        # 模拟加载一些文档
        image_engine.image_docs = {"img1": "content1", "img2": "content2", "img3": "content3"}
        image_engine._docs_loaded = True
        
        logger.info(f"清理前状态: 缓存文档数={len(image_engine.image_docs)}, 已加载={image_engine._docs_loaded}")
        
        # 清理缓存
        cleared_count = image_engine.clear_cache()
        
        logger.info(f"清理后状态: 缓存文档数={len(image_engine.image_docs)}, 已加载={image_engine._docs_loaded}, 清理数量={cleared_count}")
        
        assert len(image_engine.image_docs) == 0, "图片文档缓存应该被清空"
        assert not image_engine._docs_loaded, "加载状态应该被重置"
        assert cleared_count == 3, "应该清理3个文档"
        
        logger.info("✅ 图片引擎缓存清理测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 图片引擎缓存清理测试失败: {e}")
        return False

def test_table_engine_cache_clear():
    """测试表格引擎缓存清理"""
    logger.info("🧪 测试表格引擎缓存清理...")
    
    try:
        # 创建表格引擎配置
        from v2.config.v2_config import TableEngineConfigV2
        table_config = TableEngineConfigV2()
        
        # 创建模拟的向量数据库
        class MockVectorStore:
            def __init__(self):
                self.docstore = {}
        
        # 创建表格引擎
        table_engine = TableEngine(table_config, vector_store=MockVectorStore(), skip_initial_load=True)
        
        # 模拟加载一些文档
        table_engine.table_docs = {"table1": "content1", "table2": "content2"}
        table_engine._docs_loaded = True
        
        logger.info(f"清理前状态: 缓存文档数={len(table_engine.table_docs)}, 已加载={table_engine._docs_loaded}")
        
        # 清理缓存
        cleared_count = table_engine.clear_cache()
        
        logger.info(f"清理后状态: 缓存文档数={len(table_engine.table_docs)}, 已加载={table_engine._docs_loaded}, 清理数量={cleared_count}")
        
        assert len(table_engine.table_docs) == 0, "表格文档缓存应该被清空"
        assert not table_engine._docs_loaded, "加载状态应该被重置"
        assert cleared_count == 2, "应该清理2个文档"
        
        logger.info("✅ 表格引擎缓存清理测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 表格引擎缓存清理测试失败: {e}")
        return False

def test_reranking_engine_cache_clear():
    """测试重新排序引擎缓存清理"""
    logger.info("🧪 测试重新排序引擎缓存清理...")
    
    try:
        # 创建重新排序引擎
        reranking_engine = DashScopeRerankingEngine("test_key")
        
        # 清理缓存
        cleared_count = reranking_engine.clear_cache()
        
        logger.info(f"重新排序引擎缓存清理完成，清理数量={cleared_count}")
        
        assert cleared_count == 0, "重新排序引擎没有大量缓存，应该返回0"
        
        logger.info("✅ 重新排序引擎缓存清理测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 重新排序引擎缓存清理测试失败: {e}")
        return False

def test_llm_engine_cache_clear():
    """测试LLM引擎缓存清理"""
    logger.info("🧪 测试LLM引擎缓存清理...")
    
    try:
        # 创建LLM引擎
        llm_engine = DashScopeLLMEngine("test_key")
        
        # 清理缓存
        cleared_count = llm_engine.clear_cache()
        
        logger.info(f"LLM引擎缓存清理完成，清理数量={cleared_count}")
        
        assert cleared_count == 0, "LLM引擎没有大量缓存，应该返回0"
        
        logger.info("✅ LLM引擎缓存清理测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM引擎缓存清理测试失败: {e}")
        return False

def test_all_engines_cache_clear():
    """测试所有引擎的缓存清理"""
    logger.info("🚀 开始测试所有引擎的缓存清理功能...")
    
    test_results = []
    
    # 测试各个引擎
    test_results.append(("文档加载器", test_document_loader_cache_clear()))
    test_results.append(("文本引擎", test_text_engine_cache_clear()))
    test_results.append(("图片引擎", test_image_engine_cache_clear()))
    test_results.append(("表格引擎", test_table_engine_cache_clear()))
    test_results.append(("重新排序引擎", test_reranking_engine_cache_clear()))
    test_results.append(("LLM引擎", test_llm_engine_cache_clear()))
    
    # 统计结果
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    logger.info(f"\n📊 测试结果统计:")
    logger.info(f"总计: {total} 个引擎")
    logger.info(f"通过: {passed} 个")
    logger.info(f"失败: {total - passed} 个")
    
    for engine_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {engine_name}: {status}")
    
    if passed == total:
        logger.info("🎉 所有引擎缓存清理测试通过！")
        return True
    else:
        logger.error("💥 部分引擎缓存清理测试失败！")
        return False

def main():
    """主函数"""
    logger.info("🔧 V2.0系统引擎缓存清理功能测试")
    logger.info("=" * 50)
    
    try:
        success = test_all_engines_cache_clear()
        
        if success:
            logger.info("🎯 所有测试完成，系统优雅退出功能已就绪！")
            return 0
        else:
            logger.error("💥 部分测试失败，请检查相关引擎实现！")
            return 1
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生未预期的错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
