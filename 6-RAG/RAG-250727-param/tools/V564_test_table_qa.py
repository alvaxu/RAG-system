'''
程序说明：
## 1. 测试改进后的表格处理在实际问答中的效果
## 2. 验证LLM对表格数据的理解能力
## 3. 检查通用表格处理方法的实际效果
'''

import logging
from config.config_manager import ConfigManager
from core.enhanced_qa_system import load_enhanced_qa_system

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_table_qa():
    """
    测试表格问答效果
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
        
        # 测试问题列表
        test_questions = [
            "中芯国际2024年的营业收入是多少？",
            "2023年的净利润是多少？",
            "2025年的每股收益预测是多少？",
            "2024年的市盈率是多少？",
            "营业收入在2023年到2024年的增长情况如何？"
        ]
        
        logger.info("=== 测试表格问答效果 ===")
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n问题 {i}: {question}")
            
            try:
                # 获取答案
                result = qa_system.answer_question(question)
                answer = result.get('answer', '未找到答案')
                
                logger.info(f"答案: {answer}")
                
                # 显示相关源
                sources = result.get('sources', [])
                if sources:
                    logger.info(f"相关源数量: {len(sources)}")
                    for j, source in enumerate(sources[:2]):  # 只显示前2个源
                        if hasattr(source, 'metadata'):
                            source_type = source.metadata.get('chunk_type', 'unknown')
                            logger.info(f"  源{j+1} ({source_type}): {source.page_content[:100]}...")
                        else:
                            logger.info(f"  源{j+1}: {source.get('content', '')[:100]}...")
                else:
                    logger.info("未找到相关源")
                    
            except Exception as e:
                logger.error(f"处理问题失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    test_table_qa() 