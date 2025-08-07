'''
程序说明：

## 1. 测试修改后的程序是否正常工作
## 2. 验证图4检索修复是否已正确应用
## 3. 测试多种查询方式
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from V501_unified_main import UnifiedRAGSystem
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_modified_program():
    """
    测试修改后的程序
    """
    try:
        logger.info("开始测试修改后的程序...")
        
        # 初始化RAG系统
        logger.info("初始化RAG系统...")
        rag_system = UnifiedRAGSystem()
        
        # 测试问题列表
        test_questions = [
            "请显示图4",
            "图4是什么？",
            "请看看图4",
            "图4显示了什么内容？",
            "请展示图4"
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
                    
                    # 检查是否包含图4
                    found_figure4 = False
                    for source in sources:
                        if isinstance(source, dict):
                            metadata = source.get('metadata', {})
                            content = source.get('content', '')
                            
                            # 检查是否是图片文档且包含图4
                            if metadata.get('chunk_type') == 'image':
                                caption = metadata.get('img_caption', [])
                                caption_text = ' '.join(caption) if caption else ''
                                
                                if '图4' in caption_text:
                                    found_figure4 = True
                                    logger.info(f"✅ 找到图4: {caption_text}")
                                    break
                        else:
                            # 如果是Document对象
                            if hasattr(source, 'metadata') and hasattr(source, 'page_content'):
                                metadata = source.metadata
                                content = source.page_content
                                
                                if metadata.get('chunk_type') == 'image':
                                    caption = metadata.get('img_caption', [])
                                    caption_text = ' '.join(caption) if caption else ''
                                    
                                    if '图4' in caption_text:
                                        found_figure4 = True
                                        logger.info(f"✅ 找到图4: {caption_text}")
                                        break
                    
                    if found_figure4:
                        success_count += 1
                        logger.info("✅ 测试通过")
                    else:
                        logger.warning("❌ 未找到图4")
                        
                        # 显示返回的源文档信息
                        for j, source in enumerate(sources):
                            if isinstance(source, dict):
                                metadata = source.get('metadata', {})
                                chunk_type = metadata.get('chunk_type', 'unknown')
                                caption = metadata.get('img_caption', [])
                                caption_text = ' '.join(caption) if caption else ''
                                logger.info(f"源文档 {j+1}: 类型={chunk_type}, 标题={caption_text}")
                            else:
                                logger.info(f"源文档 {j+1}: 类型={type(source)}")
                else:
                    logger.warning("❌ 未返回有效结果")
                    
            except Exception as e:
                logger.error(f"测试失败: {e}")
        
        # 输出测试结果
        success_rate = (success_count / total_count) * 100
        logger.info(f"\n=== 测试结果 ===")
        logger.info(f"成功: {success_count}/{total_count}")
        logger.info(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("🎉 程序修改成功！图4检索功能正常工作")
        else:
            logger.warning("⚠️ 程序可能需要进一步调试")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_modified_program()
