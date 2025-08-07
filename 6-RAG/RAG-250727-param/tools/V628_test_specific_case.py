'''
程序说明：

## 1. 专门测试"有没有中芯国际的股价K线图"这个案例
## 2. 验证修复后的关键词检测逻辑是否正确工作
'''

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from V501_unified_main import UnifiedRAGSystem

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_specific_case():
    """
    测试特定案例
    """
    logger.info("开始测试特定案例...")
    
    # 初始化RAG系统
    rag_system = UnifiedRAGSystem()
    
    # 测试问题
    question = "有没有中芯国际的股价K线图"
    logger.info(f"测试问题: {question}")
    
    # 调用问答系统
    result = rag_system.ask_question(question)
    
    # 分析结果
    answer = result.get('answer', '')
    sources = result.get('sources', [])
    
    logger.info(f"完整回答: {answer}")
    logger.info(f"源文档数量: {len(sources)}")
    
    # 检查是否明确说"没有找到"
    no_found_keywords = [
        '没有找到', '未找到', '不存在', '没有直接提到', '没有展示',
        '没有相关信息', '没有相关图片', '没有相关数据', '没有相关图表',
        '没有提及', '没有涉及', '没有包含', '没有显示', '没有提供',
        '并未提供', '并未提及', '并未展示', '并未包含'
    ]
    
    answer_lower = answer.lower()
    is_no_found = any(keyword in answer_lower for keyword in no_found_keywords)
    
    logger.info(f"是否检测到'没有找到': {is_no_found}")
    
    # 验证结果
    if is_no_found:
        logger.info("✅ 系统明确表示没有找到相关内容")
        if len(sources) == 0:
            logger.info("✅ 修复成功：没有返回任何源文档")
        else:
            logger.error(f"❌ 修复失败：虽然说没找到，但仍然返回了 {len(sources)} 个源文档")
    else:
        logger.info("❌ 系统没有检测到'没有找到'的关键词")
        logger.info("需要检查关键词匹配逻辑")

if __name__ == "__main__":
    test_specific_case()
