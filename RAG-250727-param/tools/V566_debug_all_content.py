'''
程序说明：
## 1. 调试数据库中所有文档的内容
## 2. 检查表格文档是否被正确存储
## 3. 分析文档检索问题
'''

import logging
from config.config_manager import ConfigManager
from core.enhanced_qa_system import load_enhanced_qa_system

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_all_content():
    """
    调试所有文档内容
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
        
        # 获取所有文档
        all_docs = qa_system.vector_store.similarity_search("", k=100)
        
        logger.info(f"=== 数据库中共有 {len(all_docs)} 个文档 ===")
        
        # 统计文档类型
        text_docs = [doc for doc in all_docs if doc.metadata.get('chunk_type') == 'text']
        table_docs = [doc for doc in all_docs if doc.metadata.get('chunk_type') == 'table']
        image_docs = [doc for doc in all_docs if doc.metadata.get('chunk_type') == 'image']
        
        logger.info(f"文本文档: {len(text_docs)} 个")
        logger.info(f"表格文档: {len(table_docs)} 个")
        logger.info(f"图片文档: {len(image_docs)} 个")
        
        # 显示表格文档内容
        if table_docs:
            logger.info("\n=== 表格文档内容 ===")
            for i, doc in enumerate(table_docs[:3]):  # 只显示前3个
                logger.info(f"\n表格文档 {i+1}:")
                logger.info(f"  元数据: {doc.metadata}")
                logger.info(f"  内容预览: {doc.page_content[:300]}...")
        else:
            logger.info("\n❌ 没有找到表格文档")
        
        # 显示一些文本文档内容
        if text_docs:
            logger.info("\n=== 文本文档内容示例 ===")
            for i, doc in enumerate(text_docs[:2]):  # 只显示前2个
                logger.info(f"\n文本文档 {i+1}:")
                logger.info(f"  元数据: {doc.metadata}")
                logger.info(f"  内容预览: {doc.page_content[:200]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        return False

if __name__ == "__main__":
    debug_all_content() 