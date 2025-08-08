'''
程序说明：

## 1. 测试图1检索修复是否成功
## 2. 验证只返回真正的图1，不返回图11、图12等
## 3. 测试多种图号查询的精确性
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V501_unified_main import UnifiedRAGSystem
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_figure1_fix():
    """
    测试图1检索修复
    """
    try:
        logger.info("开始测试图1检索修复...")
        
        # 初始化RAG系统
        logger.info("初始化RAG系统...")
        rag_system = UnifiedRAGSystem()
        
        # 测试问题列表
        test_questions = [
            "请显示图1",
            "图1是什么？",
            "请看看图1",
            "图1显示了什么内容？",
            "请展示图1"
        ]
        
        success_count = 0
        total_count = len(test_questions)
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n=== 测试 {i}/{total_count}: {question} ===")
            
            try:
                # 调用问答系统
                result = rag_system.ask_question(question)
                
                # 检查结果
                if result and 'sources' in result:
                    sources = result['sources']
                    logger.info(f"返回了 {len(sources)} 个源文档")
                    
                    # 分析返回的图片
                    figure1_count = 0
                    irrelevant_count = 0
                    irrelevant_figures = []
                    
                    for j, source in enumerate(sources):
                        if isinstance(source, dict):
                            metadata = source.get('metadata', {})
                            
                            # 检查是否是图片文档
                            if metadata.get('chunk_type') == 'image':
                                caption = metadata.get('img_caption', [])
                                caption_text = ' '.join(caption) if caption else ''
                                
                                # 检查是否包含图1
                                if '图1：' in caption_text or '图1 ' in caption_text:
                                    figure1_count += 1
                                    logger.info(f"✅ 相关图片 {j+1}: {caption_text}")
                                else:
                                    irrelevant_count += 1
                                    irrelevant_figures.append(caption_text)
                                    logger.info(f"❌ 不相关图片 {j+1}: {caption_text}")
                        else:
                            logger.info(f"源文档 {j+1}: 类型={type(source)}")
                    
                    # 判断测试结果
                    if figure1_count > 0 and irrelevant_count == 0:
                        success_count += 1
                        logger.info("✅ 测试通过：只返回了相关的图1")
                    elif figure1_count > 0 and irrelevant_count > 0:
                        logger.warning(f"⚠️ 部分成功：返回了 {figure1_count} 个图1，但也返回了 {irrelevant_count} 个不相关图片")
                        logger.warning(f"不相关图片: {irrelevant_figures}")
                    else:
                        logger.error("❌ 测试失败：没有找到图1或只返回了不相关图片")
                        
                else:
                    logger.warning("❌ 未返回有效结果")
                    
            except Exception as e:
                logger.error(f"测试失败: {e}")
        
        # 输出测试结果
        success_rate = (success_count / total_count) * 100
        logger.info(f"\n=== 测试结果 ===")
        logger.info(f"完全成功: {success_count}/{total_count}")
        logger.info(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("🎉 图1检索修复成功！系统现在能精确匹配图号")
        else:
            logger.warning("⚠️ 修复可能还需要进一步调整")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")

def test_multiple_figures():
    """
    测试多种图号的精确性
    """
    logger.info("\n=== 测试多种图号的精确性 ===")
    
    try:
        rag_system = UnifiedRAGSystem()
        
        test_cases = [
            ("图1", "应该只返回图1"),
            ("图4", "应该只返回图4"),
            ("图11", "应该只返回图11"),
            ("图12", "应该只返回图12")
        ]
        
        for figure_query, expected in test_cases:
            logger.info(f"\n--- 测试 {figure_query} ---")
            logger.info(f"期望: {expected}")
            
            result = rag_system.ask_question(f"请显示{figure_query}")
            
            if result and 'sources' in result:
                sources = result['sources']
                logger.info(f"返回了 {len(sources)} 个源文档")
                
                for i, source in enumerate(sources):
                    if isinstance(source, dict):
                        metadata = source.get('metadata', {})
                        if metadata.get('chunk_type') == 'image':
                            caption = metadata.get('img_caption', [])
                            caption_text = ' '.join(caption) if caption else ''
                            logger.info(f"  图片 {i+1}: {caption_text}")
                            
                            # 检查是否包含正确的图号
                            if figure_query in caption_text:
                                logger.info(f"  ✅ 正确匹配")
                            else:
                                logger.warning(f"  ❌ 错误匹配")
            else:
                logger.warning("未返回有效结果")
                
    except Exception as e:
        logger.error(f"多图号测试失败: {e}")

if __name__ == "__main__":
    test_figure1_fix()
    test_multiple_figures()
