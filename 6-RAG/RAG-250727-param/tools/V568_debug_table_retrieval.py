'''
程序说明：
## 1. 调试表格数据的检索问题
## 2. 检查为什么表格数据没有被检索到
## 3. 分析向量检索的相似度问题
'''

import logging
from config.config_manager import ConfigManager
from core.enhanced_qa_system import load_enhanced_qa_system

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_table_retrieval():
    """
    调试表格数据检索
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
        
        # 测试不同的查询
        test_queries = [
            "营业收入",
            "2024年",
            "净利润",
            "每股收益",
            "表格",
            "数据"
        ]
        
        logger.info("=== 调试表格数据检索 ===")
        
        for query in test_queries:
            logger.info(f"\n查询: {query}")
            
            # 获取检索结果
            docs = qa_system.vector_store.similarity_search(query, k=10)
            
            # 统计文档类型
            text_docs = [doc for doc in docs if doc.metadata.get('chunk_type') == 'text']
            table_docs = [doc for doc in docs if doc.metadata.get('chunk_type') == 'table']
            image_docs = [doc for doc in docs if doc.metadata.get('chunk_type') == 'image']
            
            logger.info(f"  检索到 {len(docs)} 个文档")
            logger.info(f"  文本文档: {len(text_docs)} 个")
            logger.info(f"  表格文档: {len(table_docs)} 个")
            logger.info(f"  图片文档: {len(image_docs)} 个")
            
            # 显示表格文档内容
            if table_docs:
                logger.info(f"  表格文档内容:")
                for i, doc in enumerate(table_docs[:2]):
                    logger.info(f"    表格{i+1}: {doc.page_content[:200]}...")
            else:
                logger.info(f"  ❌ 没有找到表格文档")
        
        # 直接搜索表格文档
        logger.info(f"\n=== 直接搜索表格文档 ===")
        all_docs = qa_system.vector_store.similarity_search("", k=100)
        table_docs = [doc for doc in all_docs if doc.metadata.get('chunk_type') == 'table']
        
        logger.info(f"数据库中总共有 {len(table_docs)} 个表格文档")
        
        if table_docs:
            logger.info("表格文档列表:")
            for i, doc in enumerate(table_docs[:3]):
                logger.info(f"  表格{i+1}: {doc.metadata.get('table_id')} - {doc.page_content[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        return False

if __name__ == "__main__":
    debug_table_retrieval() 