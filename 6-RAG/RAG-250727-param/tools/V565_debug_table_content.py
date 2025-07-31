'''
程序说明：
## 1. 调试当前数据库中表格数据的实际格式
## 2. 检查表格数据是否被正确处理
## 3. 分析LLM理解问题的原因
'''

import logging
from config.config_manager import ConfigManager
from core.enhanced_qa_system import load_enhanced_qa_system

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_table_content():
    """
    调试表格数据内容
    """
    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.settings.to_dict()
        
        # 加载QA系统
        vector_db_path = config_manager.settings.get_vector_db_path()
        api_key = config_manager.settings.dashscope_api_key
        
        qa_system = load_enhanced_qa_system(vector_db_path, api_key, None, config)
        
        if not qa_system:
            logger.error("QA系统加载失败")
            return False
        
        # 测试查询
        test_queries = [
            "2024年营业收入",
            "净利润",
            "每股收益",
            "市盈率"
        ]
        
        logger.info("=== 调试表格数据内容 ===")
        
        for query in test_queries:
            logger.info(f"\n查询: {query}")
            
            # 直接检索文档
            docs = qa_system.vector_store.similarity_search(query, k=5)
            
            table_docs = [doc for doc in docs if doc.metadata.get('chunk_type') == 'table']
            
            if table_docs:
                logger.info(f"找到 {len(table_docs)} 个表格文档")
                for i, doc in enumerate(table_docs[:2]):  # 只显示前2个
                    logger.info(f"表格文档 {i+1}:")
                    logger.info(f"  内容: {doc.page_content[:200]}...")
                    logger.info(f"  元数据: {doc.metadata}")
            else:
                logger.info("未找到表格文档")
        
        return True
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        return False

if __name__ == "__main__":
    debug_table_content() 