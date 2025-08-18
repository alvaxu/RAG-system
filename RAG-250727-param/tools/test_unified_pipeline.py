'''
程序说明：
## 1. 测试统一Pipeline功能
## 2. 验证LLM生成和源过滤
## 3. 测试与TextEngine的集成

## 主要功能：
- 测试统一Pipeline的初始化
- 验证LLM生成功能
- 验证源过滤功能
- 测试完整流程
'''

import sys
import os
import logging
from typing import List, Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_mock_engines():
    """创建模拟的引擎"""
    
    class MockLLMEngine:
        def generate_answer(self, query: str, context: str) -> str:
            return f"基于查询'{query}'和上下文信息，我为您生成了答案。上下文包含{len(context)}个字符的信息。"
    
    class MockSourceFilterEngine:
        def filter_sources(self, llm_answer: str, sources: List[Dict], query: str) -> List[Dict]:
            # 模拟源过滤：保留前3个源
            filtered_sources = []
            for i, source in enumerate(sources[:3]):
                source_copy = source.copy()
                source_copy['relevance_score'] = 0.9 - (i * 0.1)
                filtered_sources.append(source_copy)
            return filtered_sources
    
    return MockLLMEngine(), MockSourceFilterEngine()

def create_mock_reranked_results():
    """创建模拟的重排序结果"""
    mock_results = []
    
    sample_contents = [
        "这是一个关于RAG系统的技术文档，详细介绍了检索增强生成的工作原理和实现方法。",
        "RAG系统结合了传统信息检索和大型语言模型的优势，能够提供更准确、更相关的回答。",
        "在RAG系统中，文档分块是一个关键技术，需要平衡块的大小和语义完整性。",
        "向量数据库是RAG系统的核心组件，用于存储文档的向量表示和相似度搜索。",
        "重排序（Reranking）是RAG流程中的重要步骤，用于从候选文档中选择最相关的文档。",
        "智能问答系统需要处理多种类型的查询，包括事实性查询、推理查询和创造性查询。",
        "文档预处理包括文本清洗、分块、向量化等步骤，直接影响检索质量。",
        "多模态RAG系统能够处理文本、图像、表格等多种类型的内容。",
        "配置管理是RAG系统的重要组成部分，需要支持灵活的配置调整和热更新。",
        "性能优化包括向量检索优化、重排序优化和LLM生成优化等多个方面。"
    ]
    
    for i, content in enumerate(sample_contents):
        mock_result = {
            'id': f'doc_{i+1}',
            'content': content,
            'metadata': {
                'source': f'source_{i+1}.md',
                'type': 'markdown',
                'created_at': '2024-01-01',
                'tags': ['RAG', 'AI', '技术']
            },
            'rerank_score': 0.9 - (i * 0.05),
            'rerank_rank': i + 1
        }
        mock_results.append(mock_result)
    
    return mock_results

def test_unified_pipeline():
    """测试统一Pipeline功能"""
    logger.info("=== 开始测试统一Pipeline ===")
    
    try:
        # 导入统一Pipeline
        from v2.core.unified_pipeline import UnifiedPipeline
        
        # 创建模拟引擎
        mock_llm_engine, mock_source_filter_engine = create_mock_engines()
        
        # 创建Pipeline配置
        pipeline_config = {
            'enable_llm_generation': True,
            'enable_source_filtering': True,
            'max_context_results': 10,
            'max_content_length': 1000,
            'retry_count': 3,
            'enable_fallback': True
        }
        
        # 初始化统一Pipeline
        pipeline = UnifiedPipeline(pipeline_config, mock_llm_engine, mock_source_filter_engine)
        logger.info("✅ 统一Pipeline初始化成功")
        
        # 创建模拟的重排序结果
        mock_results = create_mock_reranked_results()
        query = "RAG系统的工作原理是什么？"
        
        logger.info(f"测试查询: {query}")
        logger.info(f"输入结果数量: {len(mock_results)}")
        
        # 执行Pipeline处理
        result = pipeline.process(query, mock_results)
        
        # 验证结果
        if result.success:
            logger.info("✅ Pipeline处理成功")
            logger.info(f"LLM答案长度: {len(result.llm_answer)}")
            logger.info(f"过滤后源数量: {len(result.filtered_sources)}")
            logger.info(f"处理耗时: {result.pipeline_metrics.get('total_time', 0):.2f}秒")
            
            # 显示LLM答案
            logger.info(f"LLM生成的答案: {result.llm_answer[:100]}...")
            
            # 显示过滤后的源
            logger.info("过滤后的源:")
            for i, source in enumerate(result.filtered_sources[:3]):
                logger.info(f"  第{i+1}名: {source.get('content', '')[:50]}...")
                logger.info(f"    源相关性分数: {source.get('source_relevance_score', 'N/A')}")
                logger.info("---")
                
        else:
            logger.error(f"❌ Pipeline处理失败: {result.error_message}")
            
    except Exception as e:
        logger.error(f"❌ 统一Pipeline测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_pipeline_config():
    """测试Pipeline配置"""
    logger.info("=== 开始测试Pipeline配置 ===")
    
    try:
        from v2.config.v2_config import V2ConfigManager
        
        # 加载配置
        config_manager = V2ConfigManager()
        config = config_manager.config
        
        # 检查统一Pipeline配置
        if hasattr(config, 'unified_pipeline') and config.unified_pipeline:
            pipeline_config = config.unified_pipeline
            logger.info("✅ 统一Pipeline配置加载成功")
            logger.info(f"  启用LLM生成: {pipeline_config.enable_llm_generation}")
            logger.info(f"  启用源过滤: {pipeline_config.enable_source_filtering}")
            logger.info(f"  最大上下文结果数: {pipeline_config.max_context_results}")
            logger.info(f"  最大内容长度: {pipeline_config.max_content_length}")
        else:
            logger.warning("⚠️ 统一Pipeline配置未找到")
            
    except Exception as e:
        logger.error(f"❌ Pipeline配置测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    logger.info("开始统一Pipeline测试")
    
    # 测试Pipeline配置
    test_pipeline_config()
    
    # 测试统一Pipeline功能
    test_unified_pipeline()
    
    logger.info("统一Pipeline测试完成")

if __name__ == "__main__":
    main()
