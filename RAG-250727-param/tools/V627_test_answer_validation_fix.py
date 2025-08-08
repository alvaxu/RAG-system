'''
程序说明：

## 1. 测试答案验证和智能过滤修复效果
## 2. 验证当LLM明确回答"没有找到"时，系统是否不再返回源文档
## 3. 对比修复前后的行为差异
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

def test_answer_validation_fix():
    """
    测试答案验证和智能过滤修复效果
    """
    logger.info("开始测试答案验证和智能过滤修复效果...")
    
    # 初始化RAG系统
    logger.info("初始化RAG系统...")
    rag_system = UnifiedRAGSystem()
    
    # 测试用例
    test_cases = [
        {
            "question": "有没有关于中芯国际股票走势图的图片",
            "expected_behavior": "应该明确回答没有找到，且不返回任何源文档"
        },
        {
            "question": "有没有中芯国际的股价K线图",
            "expected_behavior": "应该明确回答没有找到，且不返回任何源文档"
        },
        {
            "question": "文档中有没有提到台积电的股票代码",
            "expected_behavior": "应该明确回答没有找到，且不返回任何源文档"
        },
        {
            "question": "有没有关于中芯国际的财务数据图表",
            "expected_behavior": "应该能找到相关图表并返回源文档"
        },
        {
            "question": "有没有图1",
            "expected_behavior": "应该能找到图1并返回相关源文档"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n=== 测试 {i}/{total_count}: {test_case['question']} ===")
        logger.info(f"期望行为: {test_case['expected_behavior']}")
        
        try:
            # 调用问答系统
            result = rag_system.ask_question(test_case['question'])
            
            # 分析结果
            answer = result.get('answer', '')
            sources = result.get('sources', [])
            
            logger.info(f"回答: {answer[:200]}...")
            logger.info(f"返回了 {len(sources)} 个源文档")
            
            # 检查是否明确说"没有找到"
            no_found_keywords = [
                '没有找到', '未找到', '不存在', '没有直接提到', '没有展示', '没有相关信息',
                '没有提到', '没有提到或展示', '没有提及', '没有涉及', '没有包含', '没有显示',
                '并未提供', '并未提及', '并未展示', '并未包含'
            ]
            answer_lower = answer.lower()
            is_no_found = any(keyword in answer_lower for keyword in no_found_keywords)
            
            # 验证修复效果
            if is_no_found:
                logger.info("✅ 系统明确表示没有找到相关内容")
                if len(sources) == 0:
                    logger.info("✅ 修复成功：没有返回任何源文档")
                    success_count += 1
                else:
                    logger.error(f"❌ 修复失败：虽然说没找到，但仍然返回了 {len(sources)} 个源文档")
                    for j, source in enumerate(sources[:2], 1):  # 只显示前2个
                        if isinstance(source, dict):
                            content = source.get('content', '')[:100]
                            logger.error(f"  源文档 {j}: {content}...")
                        else:
                            logger.error(f"  源文档 {j}: {str(source)[:100]}...")
            else:
                logger.info("✅ 系统找到了相关内容")
                if len(sources) > 0:
                    logger.info("✅ 正确：返回了相关源文档")
                    success_count += 1
                else:
                    logger.error("❌ 问题：说找到了但没返回源文档")
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
    
    # 输出测试结果
    logger.info(f"\n=== 测试结果 ===")
    logger.info(f"成功: {success_count}/{total_count}")
    logger.info(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        logger.info("🎉 所有测试通过！答案验证和智能过滤修复成功！")
    else:
        logger.warning(f"⚠️ 有 {total_count - success_count} 个测试失败，需要进一步调试")

def test_specific_case():
    """
    测试特定案例的详细情况
    """
    logger.info("\n=== 详细测试特定案例 ===")
    
    rag_system = UnifiedRAGSystem()
    
    # 测试最关键的案例
    question = "有没有关于中芯国际股票走势图的图片"
    logger.info(f"测试问题: {question}")
    
    result = rag_system.ask_question(question)
    answer = result.get('answer', '')
    sources = result.get('sources', [])
    
    logger.info(f"完整回答: {answer}")
    logger.info(f"源文档数量: {len(sources)}")
    
    if len(sources) == 0:
        logger.info("✅ 修复成功：当LLM说'没有找到'时，系统没有返回任何源文档")
    else:
        logger.error("❌ 修复失败：仍然返回了源文档")
        for i, source in enumerate(sources, 1):
            if isinstance(source, dict):
                content = source.get('content', '')[:150]
                logger.error(f"源文档 {i}: {content}...")

if __name__ == "__main__":
    test_answer_validation_fix()
    test_specific_case()
