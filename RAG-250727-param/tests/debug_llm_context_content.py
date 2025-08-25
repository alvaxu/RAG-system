#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试LLM上下文内容，查看实际传递给LLM的chunk内容
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v2.core.unified_pipeline import UnifiedPipeline
from v2.core.dashscope_llm_engine import DashScopeLLMEngine
from v2.config.v2_config import V2ConfigManager
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_llm_context_content():
    """调试LLM上下文内容"""
    
    try:
        # 加载配置
        config_manager = V2ConfigManager()
        config = config_manager.config
        
        # 创建LLM引擎（模拟）
        class MockLLMEngine:
            def generate_answer(self, query, context):
                logger.info("🤖 LLM引擎被调用")
                logger.info(f"📝 用户问题: {query}")
                logger.info(f"📚 上下文内容:")
                logger.info("=" * 80)
                logger.info(context)
                logger.info("=" * 80)
                logger.info(f"📊 上下文总长度: {len(context)} 字符")
                return "这是模拟的LLM回答"
        
        # 创建Pipeline配置
        pipeline_config = {
            'enable_llm_generation': True,
            'enable_source_filtering': False,
            'max_context_results': 5,
            'max_content_length': 1000
        }
        
        # 创建UnifiedPipeline实例
        pipeline = UnifiedPipeline(pipeline_config, MockLLMEngine(), None)
        
        # 模拟召回结果（第一层召回格式）
        mock_recall_results = [
            {
                'doc': type('MockDoc', (), {
                    'page_content': '这是第一层召回的page_content内容（处理后的文本）',
                    'metadata': {
                        'page_content': '<table>这是第一层召回的HTML内容（完整表格）</table>',
                        'document_name': '测试文档1',
                        'page_number': 1,
                        'chunk_type': 'table'
                    }
                })(),
                'score': 0.9,
                'source': 'structure_search',
                'layer': 1
            },
            {
                'doc': type('MockDoc', (), {
                    'page_content': '这是第二层召回的page_content内容（处理后的文本）',
                    'metadata': {
                        'page_content': '<table>这是第二层召回的HTML内容（完整表格）</table>',
                        'document_name': '测试文档2',
                        'page_number': 2,
                        'chunk_type': 'table'
                    }
                })(),
                'score': 0.8,
                'source': 'vector_search',
                'layer': 2
            }
        ]
        
        logger.info("🔍 开始测试LLM上下文构建...")
        logger.info(f"📊 召回结果数量: {len(mock_recall_results)}")
        
        # 测试上下文构建
        context = pipeline._build_context_for_llm(mock_recall_results)
        
        logger.info("✅ 上下文构建完成")
        logger.info(f"📊 构建的上下文长度: {len(context)} 字符")
        
        # 测试LLM调用
        logger.info("\n🚀 开始测试LLM调用...")
        answer = pipeline._generate_llm_answer("测试问题", mock_recall_results)
        
        logger.info("✅ 测试完成")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_llm_context_content()
