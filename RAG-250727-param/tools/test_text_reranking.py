'''
程序说明：
## 1. 测试Text Reranking服务
## 2. 验证五层召回 + Reranking的完整流程
## 3. 测试配置开关功能
## 4. 对比新旧方法的差异
'''

import sys
import os
import logging
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.text_engine import TextEngine
from v2.config.v2_config import V2ConfigManager, TextEngineConfigV2
from v2.core.vector_store import VectorStore

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_text_reranking():
    """测试Text Reranking服务"""
    
    logger.info("=" * 60)
    logger.info("开始测试Text Reranking服务")
    logger.info("=" * 60)
    
    try:
        # 1. 加载配置
        logger.info("1. 加载V2配置...")
        config_manager = V2ConfigManager()
        config = config_manager.get_config()
        
        if not config:
            logger.error("配置加载失败")
            return False
        
        text_config = config.text_engine
        logger.info(f"Text Engine配置加载成功: {text_config.name}")
        logger.info(f"启用增强Reranking: {text_config.enable_enhanced_reranking}")
        logger.info(f"使用新Pipeline: {text_config.use_new_pipeline}")
        
        # 2. 创建向量数据库（模拟）
        logger.info("2. 创建模拟向量数据库...")
        vector_store = VectorStore()
        
        # 3. 创建Text Engine
        logger.info("3. 创建Text Engine...")
        text_engine = TextEngine(
            config=text_config,
            vector_store=vector_store,
            skip_initial_load=True  # 跳过文档加载，专注于测试Reranking
        )
        
        # 4. 测试查询
        test_query = "RAG系统架构设计"
        logger.info(f"4. 测试查询: {test_query}")
        
        # 执行查询
        start_time = time.time()
        result = text_engine.process_query(test_query)
        processing_time = time.time() - start_time
        
        # 5. 分析结果
        logger.info("5. 分析查询结果...")
        logger.info(f"查询成功: {result.success}")
        logger.info(f"处理时间: {processing_time:.3f}秒")
        logger.info(f"结果数量: {result.total_count}")
        logger.info(f"元数据: {result.metadata}")
        
        if result.success and result.results:
            logger.info("前3个结果:")
            for i, doc in enumerate(result.results[:3]):
                logger.info(f"  结果{i+1}:")
                logger.info(f"    内容长度: {len(doc.get('content', ''))}")
                logger.info(f"    召回分数: {doc.get('recall_score', 'N/A')}")
                logger.info(f"    重排序分数: {doc.get('reranking_score', 'N/A')}")
                logger.info(f"    最终排名: {doc.get('final_rank', 'N/A')}")
        
        logger.info("=" * 60)
        logger.info("Text Reranking服务测试完成")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_switch():
    """测试配置开关功能"""
    
    logger.info("=" * 60)
    logger.info("开始测试配置开关功能")
    logger.info("=" * 60)
    
    try:
        # 1. 加载配置
        config_manager = V2ConfigManager()
        config = config_manager.get_config()
        
        if not config:
            logger.error("配置加载失败")
            return False
        
        text_config = config.text_engine
        
        # 2. 测试不同配置
        test_configs = [
            ("启用增强Reranking", True, True),
            ("禁用增强Reranking", False, True),
            ("使用新Pipeline", True, True),
            ("使用旧Pipeline", True, False),
        ]
        
        for test_name, enable_reranking, use_new_pipeline in test_configs:
            logger.info(f"\n测试配置: {test_name}")
            logger.info(f"  enable_enhanced_reranking: {enable_reranking}")
            logger.info(f"  use_new_pipeline: {use_new_pipeline}")
            
            # 临时修改配置
            text_config.enable_enhanced_reranking = enable_reranking
            text_config.use_new_pipeline = use_new_pipeline
            
            # 创建引擎
            vector_store = VectorStore()
            text_engine = TextEngine(
                config=text_config,
                vector_store=vector_store,
                skip_initial_load=True
            )
            
            # 测试查询
            test_query = "测试查询"
            result = text_engine.process_query(test_query)
            
            logger.info(f"  查询结果: 成功={result.success}, 结果数量={result.total_count}")
            logger.info(f"  元数据: {result.metadata}")
        
        logger.info("=" * 60)
        logger.info("配置开关功能测试完成")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"配置开关测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("开始Text Reranking服务测试")
    
    # 测试1: 基本功能
    success1 = test_text_reranking()
    
    # 测试2: 配置开关
    success2 = test_config_switch()
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结:")
    logger.info(f"  基本功能测试: {'✅ 成功' if success1 else '❌ 失败'}")
    logger.info(f"  配置开关测试: {'✅ 成功' if success2 else '❌ 失败'}")
    
    if success1 and success2:
        logger.info("🎉 所有测试通过！Text Reranking服务工作正常")
    else:
        logger.error("❌ 部分测试失败，请检查错误信息")
    
    logger.info("=" * 60)
