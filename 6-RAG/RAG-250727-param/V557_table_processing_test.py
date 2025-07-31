'''
程序说明：
## 1. 表格处理测试脚本
## 2. 验证表格数据是否正确解析和向量化
## 3. 测试表格检索功能
'''

import json
import logging
from pathlib import Path
from document_processing.table_processor import process_tables_from_document_with_config
from config.config_manager import ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_table_processing():
    """
    测试表格处理功能
    """
    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.settings.to_dict()
        
        # 读取JSON文件
        json_file_path = Path("md_test/【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评_1.json")
        
        if not json_file_path.exists():
            logger.error(f"JSON文件不存在: {json_file_path}")
            return
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        logger.info(f"加载JSON数据，共 {len(json_data)} 个元素")
        
        # 处理表格
        document_name = "【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评"
        table_chunks = process_tables_from_document_with_config(json_data, document_name, config)
        
        logger.info(f"表格处理完成，共生成 {len(table_chunks)} 个表格分块")
        
        # 显示表格内容
        for i, chunk in enumerate(table_chunks):
            logger.info(f"\n=== 表格分块 {i+1} ===")
            logger.info(f"表格ID: {chunk.table_id}")
            logger.info(f"表格类型: {chunk.table_type}")
            logger.info(f"文档名称: {chunk.document_name}")
            logger.info(f"页码: {chunk.page_number}")
            logger.info(f"分块索引: {chunk.chunk_index}")
            logger.info(f"内容长度: {len(chunk.content)}")
            logger.info("内容预览:")
            logger.info(chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content)
        
        # 测试特定数据检索
        test_queries = [
            "收盘价",
            "2024年营业收入",
            "2023年净利润",
            "市净率"
        ]
        
        logger.info("\n=== 测试数据检索 ===")
        for query in test_queries:
            logger.info(f"\n查询: {query}")
            found = False
            for chunk in table_chunks:
                if query.lower() in chunk.content.lower():
                    logger.info(f"在表格分块中找到匹配: {chunk.table_id}")
                    logger.info(f"匹配内容: {chunk.content}")
                    found = True
                    break
            if not found:
                logger.info("未找到匹配内容")
        
        return table_chunks
        
    except Exception as e:
        logger.error(f"表格处理测试失败: {e}")
        return None

if __name__ == "__main__":
    test_table_processing() 