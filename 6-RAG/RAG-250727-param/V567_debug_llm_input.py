'''
程序说明：
## 1. 调试LLM实际收到的输入内容
## 2. 检查表格数据是否被正确传递给LLM
## 3. 分析LLM理解问题的原因
'''

import logging
from config.config_manager import ConfigManager
from core.enhanced_qa_system import load_enhanced_qa_system

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_llm_input():
    """
    调试LLM输入内容
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
        test_query = "中芯国际2024年的营业收入是多少？"
        
        logger.info(f"=== 调试LLM输入内容 ===")
        logger.info(f"查询: {test_query}")
        
        # 获取检索结果
        docs = qa_system.vector_store.similarity_search(test_query, k=5)
        
        logger.info(f"检索到 {len(docs)} 个文档")
        
        # 检查每个文档的内容
        for i, doc in enumerate(docs):
            logger.info(f"\n文档 {i+1}:")
            logger.info(f"  类型: {doc.metadata.get('chunk_type')}")
            logger.info(f"  元数据: {doc.metadata}")
            logger.info(f"  内容预览: {doc.page_content[:300]}...")
            
            # 如果是表格文档，显示完整内容
            if doc.metadata.get('chunk_type') == 'table':
                logger.info(f"  完整表格内容:")
                logger.info(doc.page_content)
        
        # 模拟LLM的输入
        logger.info(f"\n=== 模拟LLM输入 ===")
        
        # 构建上下文
        context_parts = []
        for i, doc in enumerate(docs):
            context_parts.append(f"文档{i+1}:\n{doc.page_content}")
        
        context = "\n\n".join(context_parts)
        
        logger.info(f"LLM将收到的上下文长度: {len(context)} 字符")
        logger.info(f"上下文预览:")
        logger.info(context[:500] + "..." if len(context) > 500 else context)
        
        return True
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        return False

if __name__ == "__main__":
    debug_llm_input() 