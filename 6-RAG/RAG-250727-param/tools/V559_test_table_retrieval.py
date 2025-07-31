'''
程序说明：
## 1. 测试表格数据检索
## 2. 检查向量数据库中是否包含表格数据
## 3. 验证检索功能
'''

import logging
from config.config_manager import ConfigManager
from core.enhanced_qa_system import load_enhanced_qa_system

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_table_retrieval():
    """
    测试表格数据检索
    """
    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.settings.to_dict()
        
        # 加载QA系统
        vector_db_path = config_manager.settings.get_vector_db_path()
        api_key = config_manager.settings.dashscope_api_key
        
        logger.info(f"向量数据库路径: {vector_db_path}")
        logger.info(f"API密钥: {'已配置' if api_key else '未配置'}")
        
        # 加载增强版QA系统
        qa_system = load_enhanced_qa_system(vector_db_path, api_key, None, config)
        
        if not qa_system or not qa_system.vector_store:
            logger.error("QA系统加载失败")
            return
        
        # 测试查询
        test_queries = [
            "收盘价",
            "2024年营业收入",
            "2023年净利润",
            "市净率",
            "中芯国际2024年的营业收入"
        ]
        
        logger.info("=== 开始测试表格数据检索 ===")
        
        for query in test_queries:
            logger.info(f"\n查询: {query}")
            
            try:
                # 直接检索文档
                docs = qa_system.vector_store.similarity_search(query, k=3)
                
                logger.info(f"检索到 {len(docs)} 个文档")
                
                for i, doc in enumerate(docs):
                    logger.info(f"文档 {i+1}:")
                    logger.info(f"  内容长度: {len(doc.page_content)}")
                    logger.info(f"  元数据: {doc.metadata}")
                    logger.info(f"  内容预览: {doc.page_content[:200]}...")
                    
                    # 检查是否包含表格数据
                    if "表格" in doc.page_content or "table" in str(doc.metadata).lower():
                        logger.info("  ✅ 包含表格数据")
                    else:
                        logger.info("  ❌ 不包含表格数据")
                        
            except Exception as e:
                logger.error(f"检索失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    test_table_retrieval() 