'''
程序说明：
## 1. 测试TextEngine与统一Pipeline的集成
## 2. 验证新的Pipeline流程：召回 → 重排序 → 统一Pipeline
## 3. 测试配置开关和回退机制
'''

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_text_engine_unified_pipeline():
    """测试TextEngine与统一Pipeline的集成"""
    
    logger.info("开始测试TextEngine与统一Pipeline的集成")
    
    try:
        # 导入必要的模块
        from v2.config.v2_config import V2ConfigManager
        from v2.core.text_engine import TextEngine
        from unittest.mock import Mock
        
        # 加载配置
        config_manager = V2ConfigManager()
        text_config = config_manager.get_engine_config('text')
        
        if not text_config:
            logger.error("❌ 无法获取TextEngine配置")
            return False
        
        logger.info("✅ 配置加载成功")
        logger.info(f"使用新Pipeline: {text_config.use_new_pipeline}")
        logger.info(f"启用增强重排序: {text_config.enable_enhanced_reranking}")
        
        # 创建Mock向量数据库
        mock_vector_store = Mock()
        mock_vector_store.docstore = Mock()
        mock_vector_store.docstore._dict = {
            f"doc_{i}": Mock(
                metadata={"source": f"source_{i}", "type": "text"},
                page_content=f"这是第{i}个测试文档的内容，包含一些测试信息。"
            ) for i in range(1, 21)
        }
        
        # 创建Mock文档加载器
        mock_document_loader = Mock()
        
        # 创建TextEngine实例
        text_engine = TextEngine(
            config=text_config,
            vector_store=mock_vector_store,
            document_loader=mock_document_loader,
            skip_initial_load=True  # 跳过文档加载，使用Mock数据
        )
        
        logger.info("✅ TextEngine创建成功")
        
        # 测试查询
        test_query = "测试查询：RAG系统的工作原理"
        logger.info(f"测试查询: {test_query}")
        
        # 执行查询
        result = text_engine.process_query(test_query)
        
        if result.success:
            logger.info("✅ 查询执行成功")
            logger.info(f"结果数量: {result.total_count}")
            logger.info(f"处理时间: {result.processing_time:.4f}秒")
            logger.info(f"Pipeline类型: {result.metadata.get('pipeline', 'unknown')}")
            
            # 显示Pipeline元数据
            if 'llm_answer' in result.metadata:
                logger.info(f"LLM答案: {result.metadata['llm_answer']}")
            
            if 'pipeline_metrics' in result.metadata:
                metrics = result.metadata['pipeline_metrics']
                logger.info(f"Pipeline指标: {metrics}")
            
            # 显示前几个结果
            for i, doc in enumerate(result.results[:3]):
                logger.info(f"结果 {i+1}: {doc.get('page_content', '')[:100]}...")
                if 'recall_score' in doc:
                    logger.info(f"  召回分数: {doc['recall_score']:.3f}")
                if 'final_rank' in doc:
                    logger.info(f"  最终排名: {doc['final_rank']}")
                
        else:
            logger.error(f"❌ 查询执行失败: {result.error_message}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_switches():
    """测试配置开关"""
    
    logger.info("=== 开始测试配置开关 ===")
    
    try:
        from v2.config.v2_config import V2ConfigManager
        
        config_manager = V2ConfigManager()
        text_config = config_manager.get_engine_config('text')
        
        # 测试默认配置
        logger.info(f"默认配置:")
        logger.info(f"  use_new_pipeline: {text_config.use_new_pipeline}")
        logger.info(f"  enable_enhanced_reranking: {text_config.enable_enhanced_reranking}")
        
        # 测试统一Pipeline配置
        unified_pipeline_config = config_manager.get_engine_config('unified_pipeline')
        if unified_pipeline_config:
            logger.info(f"统一Pipeline配置:")
            logger.info(f"  启用: {unified_pipeline_config.enabled}")
            logger.info(f"  LLM生成: {unified_pipeline_config.enable_llm_generation}")
            logger.info(f"  源过滤: {unified_pipeline_config.enable_source_filtering}")
            logger.info(f"  最大上下文结果: {unified_pipeline_config.max_context_results}")
            logger.info(f"  最大内容长度: {unified_pipeline_config.max_content_length}")
            
            # 添加更详细的配置检查
            logger.info(f"  配置类型: {type(unified_pipeline_config)}")
            logger.info(f"  配置属性: {dir(unified_pipeline_config)}")
            logger.info(f"  配置字典: {unified_pipeline_config.__dict__}")
        else:
            logger.warning("❌ 无法获取统一Pipeline配置")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置开关测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始TextEngine与统一Pipeline集成测试")
    
    # 测试配置开关
    if not test_config_switches():
        logger.error("配置开关测试失败")
        sys.exit(1)
    
    # 测试集成功能
    if test_text_engine_unified_pipeline():
        logger.info("🎉 所有测试通过！")
    else:
        logger.error("❌ 测试失败")
        sys.exit(1)
