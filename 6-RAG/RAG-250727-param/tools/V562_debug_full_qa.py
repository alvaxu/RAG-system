'''
程序说明：
## 1. 调试完整QA流程
## 2. 检查实际的LLM回答和源数据
## 3. 分析源过滤的具体问题
'''

import logging
from config.config_manager import ConfigManager
from core.enhanced_qa_system import load_enhanced_qa_system

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_full_qa():
    """
    调试完整QA流程
    """
    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.settings.to_dict()
        
        # 加载QA系统
        vector_db_path = config_manager.settings.get_vector_db_path()
        api_key = config_manager.settings.dashscope_api_key
        
        qa_system = load_enhanced_qa_system(vector_db_path, api_key, None, config)
        
        if not qa_system or not qa_system.vector_store:
            logger.error("QA系统加载失败")
            return
        
        # 测试问题
        question = "中芯国际2024年的营业收入是多少？"
        
        logger.info("=== 开始调试完整QA流程 ===")
        logger.info(f"问题: {question}")
        
        # 1. 初始检索
        logger.info("\n1. 初始检索:")
        docs = qa_system.vector_store.similarity_search(question, k=3)
        logger.info(f"检索到 {len(docs)} 个文档")
        
        for i, doc in enumerate(docs):
            logger.info(f"文档 {i+1}:")
            logger.info(f"  类型: {doc.metadata.get('chunk_type', 'unknown')}")
            logger.info(f"  内容预览: {doc.page_content[:100]}...")
        
        # 2. 重排序
        logger.info("\n2. 重排序:")
        reranked_docs = qa_system._apply_reranking(question, docs)
        logger.info(f"重排序后保留 {len(reranked_docs)} 个文档")
        
        # 3. 智能过滤
        logger.info("\n3. 智能过滤:")
        filtered_docs = qa_system._apply_smart_filtering(question, reranked_docs)
        logger.info(f"智能过滤后保留 {len(filtered_docs)} 个文档")
        
        # 4. 生成答案
        logger.info("\n4. 生成答案:")
        result = qa_system._generate_answer(question, filtered_docs)
        llm_answer = result.get('answer', '')
        logger.info(f"LLM回答: {llm_answer}")
        
        # 5. 源过滤
        logger.info("\n5. 源过滤:")
        sources = qa_system._apply_source_filtering(llm_answer, filtered_docs)
        logger.info(f"源过滤后保留 {len(sources)} 个源")
        
        # 6. 详细分析源过滤
        logger.info("\n6. 详细分析源过滤:")
        for i, source in enumerate(filtered_docs):
            logger.info(f"源 {i+1}:")
            logger.info(f"  类型: {source.metadata.get('chunk_type', 'unknown')}")
            logger.info(f"  内容预览: {source.page_content[:100]}...")
            
            # 手动计算相关性分数
            relevance_score = qa_system.source_filter_engine._calculate_source_relevance(llm_answer, {
                'content': source.page_content,
                'metadata': source.metadata
            })
            logger.info(f"  相关性分数: {relevance_score:.4f}")
            logger.info(f"  阈值: {qa_system.source_filter_engine.min_relevance_score:.4f}")
            logger.info(f"  是否通过过滤: {'是' if relevance_score >= qa_system.source_filter_engine.min_relevance_score else '否'}")
        
        return True
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        return False

if __name__ == "__main__":
    debug_full_qa() 