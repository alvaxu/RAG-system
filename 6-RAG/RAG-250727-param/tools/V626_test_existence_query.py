'''
程序说明：

## 1. 测试"是否存在"类型问题的处理逻辑
## 2. 验证当系统明确回答"没有找到"时，是否还会返回不相关的源文档
## 3. 分析当前检索逻辑的问题并提出改进方案
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

def test_existence_queries():
    """
    测试"是否存在"类型的问题
    """
    logger.info("开始测试'是否存在'类型的问题...")
    
    # 初始化RAG系统
    logger.info("初始化RAG系统...")
    rag_system = UnifiedRAGSystem()
    
    # 测试用例
    test_cases = [
        {
            "question": "有没有关于中芯国际股票走势图的图片",
            "expected": "应该明确回答没有找到，且不返回任何图片"
        },
        {
            "question": "有没有中芯国际的股价K线图",
            "expected": "应该明确回答没有找到，且不返回任何图片"
        },
        {
            "question": "文档中有没有提到台积电的股票代码",
            "expected": "应该明确回答没有找到，且不返回相关内容"
        },
        {
            "question": "有没有关于中芯国际的财务数据图表",
            "expected": "应该能找到相关图表并返回"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n=== 测试 {i}/{len(test_cases)}: {test_case['question']} ===")
        logger.info(f"期望: {test_case['expected']}")
        
        try:
            # 调用问答系统
            result = rag_system.ask_question(test_case['question'])
            
            # 分析结果
            answer = result.get('answer', '')
            sources = result.get('sources', [])
            
            logger.info(f"回答: {answer[:200]}...")
            logger.info(f"返回了 {len(sources)} 个源文档")
            
            # 检查是否明确说"没有找到"
            no_found_keywords = ['没有', '未找到', '不存在', '没有直接提到', '没有展示']
            answer_lower = answer.lower()
            is_no_found = any(keyword in answer_lower for keyword in no_found_keywords)
            
            if is_no_found:
                logger.info("✅ 系统明确表示没有找到相关内容")
                if len(sources) == 0:
                    logger.info("✅ 正确：没有返回任何源文档")
                else:
                    logger.warning(f"❌ 问题：虽然说没找到，但仍然返回了 {len(sources)} 个源文档")
                    for j, source in enumerate(sources[:3], 1):  # 只显示前3个
                        if isinstance(source, dict):
                            content = source.get('content', '')[:100]
                            logger.warning(f"  源文档 {j}: {content}...")
                        else:
                            logger.warning(f"  源文档 {j}: {str(source)[:100]}...")
            else:
                logger.info("✅ 系统找到了相关内容")
                if len(sources) > 0:
                    logger.info("✅ 正确：返回了相关源文档")
                else:
                    logger.warning("❌ 问题：说找到了但没返回源文档")
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
    
    logger.info("\n=== 测试完成 ===")

def analyze_retrieval_logic():
    """
    分析当前检索逻辑的问题
    """
    logger.info("\n=== 分析当前检索逻辑问题 ===")
    
    logger.info("问题1: 语义检索的局限性")
    logger.info("- 当前系统使用语义相似度检索")
    logger.info("- 对于'是否存在'的问题，会返回语义相关的所有内容")
    logger.info("- 即使没有找到目标内容，也会返回相关但不匹配的内容")
    
    logger.info("\n问题2: 问题类型识别缺失")
    logger.info("- 系统没有识别'是否存在'类型的问题")
    logger.info("- 没有针对这类问题的特殊处理逻辑")
    
    logger.info("\n问题3: 源文档过滤不足")
    logger.info("- 即使LLM回答'没有找到'，前端仍会显示所有检索到的源文档")
    logger.info("- 缺乏基于答案内容的源文档过滤机制")
    
    logger.info("\n=== 改进建议 ===")
    logger.info("1. 添加问题类型识别：识别'是否存在'、'有没有'等询问类型")
    logger.info("2. 改进检索策略：对于存在性查询，使用更精确的匹配")
    logger.info("3. 添加答案验证：根据LLM回答决定是否显示源文档")
    logger.info("4. 实现智能过滤：当明确说'没有找到'时，不显示源文档")

if __name__ == "__main__":
    test_existence_queries()
    analyze_retrieval_logic()
