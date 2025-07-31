'''
程序说明：
## 1. 重新构建向量数据库
## 2. 确保表格数据被正确包含
## 3. 验证所有数据类型都被向量化
'''

import logging
import os
from pathlib import Path
from config.config_manager import ConfigManager
from V501_simplified_document_processor import SimplifiedDocumentProcessor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rebuild_vector_database():
    """
    重新构建向量数据库
    """
    try:
        logger.info("开始重新构建向量数据库...")
        
        # 加载配置
        config_manager = ConfigManager()
        
        # 获取路径
        md_dir = config_manager.settings.md_dir
        vector_db_path = config_manager.settings.get_vector_db_path()
        
        logger.info(f"Markdown目录: {md_dir}")
        logger.info(f"向量数据库路径: {vector_db_path}")
        
        # 检查Markdown目录是否存在
        if not os.path.exists(md_dir):
            logger.error(f"Markdown目录不存在: {md_dir}")
            return False
        
        # 检查是否有Markdown文件
        md_files = list(Path(md_dir).glob("*.md"))
        if not md_files:
            logger.error(f"Markdown目录中没有找到.md文件: {md_dir}")
            return False
        
        logger.info(f"找到 {len(md_files)} 个Markdown文件")
        
        # 删除现有的向量数据库
        if os.path.exists(vector_db_path):
            logger.info(f"删除现有向量数据库: {vector_db_path}")
            import shutil
            shutil.rmtree(vector_db_path)
        
        # 重新处理文档
        processor = SimplifiedDocumentProcessor()
        
        # 从Markdown开始处理（跳过PDF转换步骤）
        success = processor.process_from_markdown(md_dir, vector_db_path)
        
        if success:
            logger.info("向量数据库重新构建成功！")
            
            # 验证结果
            verify_vector_database(vector_db_path)
            
            return True
        else:
            logger.error("向量数据库重新构建失败！")
            return False
            
    except Exception as e:
        logger.error(f"重新构建向量数据库失败: {e}")
        return False

def verify_vector_database(vector_db_path):
    """
    验证向量数据库内容
    """
    try:
        logger.info("验证向量数据库内容...")
        
        # 加载QA系统来验证
        config_manager = ConfigManager()
        config = config_manager.settings.to_dict()
        api_key = config_manager.settings.dashscope_api_key
        
        from core.enhanced_qa_system import load_enhanced_qa_system
        qa_system = load_enhanced_qa_system(vector_db_path, api_key, None, config)
        
        if not qa_system or not qa_system.vector_store:
            logger.error("无法加载向量数据库进行验证")
            return
        
        # 统计文档类型
        all_docs = qa_system.vector_store.similarity_search("", k=1000)  # 获取所有文档
        
        text_docs = [doc for doc in all_docs if doc.metadata.get('chunk_type') == 'text']
        table_docs = [doc for doc in all_docs if doc.metadata.get('chunk_type') == 'table']
        image_docs = [doc for doc in all_docs if doc.metadata.get('chunk_type') == 'image']
        
        logger.info(f"向量数据库统计:")
        logger.info(f"  总文档数: {len(all_docs)}")
        logger.info(f"  文本文档: {len(text_docs)}")
        logger.info(f"  表格文档: {len(table_docs)}")
        logger.info(f"  图片文档: {len(image_docs)}")
        
        # 测试表格数据检索
        test_queries = ["收盘价", "2024年营业收入", "市净率"]
        
        logger.info("\n测试表格数据检索:")
        for query in test_queries:
            docs = qa_system.vector_store.similarity_search(query, k=3)
            table_docs_found = [doc for doc in docs if doc.metadata.get('chunk_type') == 'table']
            
            if table_docs_found:
                logger.info(f"  ✅ '{query}' 找到 {len(table_docs_found)} 个表格文档")
            else:
                logger.info(f"  ❌ '{query}' 未找到表格文档")
        
    except Exception as e:
        logger.error(f"验证向量数据库失败: {e}")

if __name__ == "__main__":
    rebuild_vector_database() 