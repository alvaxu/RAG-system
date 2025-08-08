'''
程序说明：

## 1. 调试图1检索问题
## 2. 验证系统是否返回了不相关的图片（如图11、图12等）
## 3. 分析问题的根本原因
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V501_unified_main import UnifiedRAGSystem
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_figure1_retrieval():
    """
    调试图1检索问题
    """
    try:
        logger.info("开始调试图1检索问题...")
        
        # 初始化RAG系统
        logger.info("初始化RAG系统...")
        rag_system = UnifiedRAGSystem()
        
        # 测试问题
        question = "请显示图1"
        logger.info(f"测试问题: {question}")
        
        # 调用问答系统
        result = rag_system.ask_question(question)
        
        # 分析结果
        if result and 'sources' in result:
            sources = result['sources']
            logger.info(f"返回了 {len(sources)} 个源文档")
            
            # 分析每个源文档
            figure1_count = 0
            irrelevant_count = 0
            
            for i, source in enumerate(sources):
                if isinstance(source, dict):
                    metadata = source.get('metadata', {})
                    content = source.get('content', '')
                    
                    # 检查是否是图片文档
                    if metadata.get('chunk_type') == 'image':
                        caption = metadata.get('img_caption', [])
                        caption_text = ' '.join(caption) if caption else ''
                        
                        # 检查是否包含图1
                        if '图1' in caption_text:
                            figure1_count += 1
                            logger.info(f"✅ 相关图片 {i+1}: {caption_text}")
                        else:
                            irrelevant_count += 1
                            logger.info(f"❌ 不相关图片 {i+1}: {caption_text}")
                            
                            # 检查是否包含其他图号
                            import re
                            other_figures = re.findall(r'图(\d+)', caption_text)
                            if other_figures:
                                logger.warning(f"   包含其他图号: {other_figures}")
                else:
                    logger.info(f"源文档 {i+1}: 类型={type(source)}")
            
            # 输出统计结果
            logger.info(f"\n=== 统计结果 ===")
            logger.info(f"相关图片（图1）: {figure1_count} 个")
            logger.info(f"不相关图片: {irrelevant_count} 个")
            logger.info(f"总图片数: {figure1_count + irrelevant_count} 个")
            
            if irrelevant_count > 0:
                logger.warning("⚠️ 发现问题：返回了不相关的图片")
                logger.info("问题分析：")
                logger.info("1. 图4修复逻辑能正确找到图1")
                logger.info("2. 但后续的常规检索/重排序仍然返回了不相关图片")
                logger.info("3. 需要修改逻辑，当找到特定图片时，只返回相关图片")
            else:
                logger.info("✅ 没有发现问题，所有返回的图片都是相关的")
                
        else:
            logger.warning("❌ 未返回有效结果")
            
    except Exception as e:
        logger.error(f"调试过程中发生错误: {e}")

if __name__ == "__main__":
    debug_figure1_retrieval()
