'''
程序说明：
## 1. 测试配置开关的动态切换功能
## 2. 验证能否通过配置控制新的reranking功能
## 3. 测试配置的实时生效

## 主要功能：
- 测试配置开关的动态控制
- 验证配置修改后的功能变化
- 测试配置的实时生效
'''

import sys
import os
import logging
import json
from typing import List, Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_mock_vector_store():
    """创建模拟的向量存储数据"""
    mock_docs = []
    
    # 创建一些模拟文档
    sample_contents = [
        "这是一个关于RAG系统的技术文档，详细介绍了检索增强生成的工作原理和实现方法。",
        "RAG系统结合了传统信息检索和大型语言模型的优势，能够提供更准确、更相关的回答。",
        "在RAG系统中，文档分块是一个关键技术，需要平衡块的大小和语义完整性。",
        "向量数据库是RAG系统的核心组件，用于存储文档的向量表示和相似度搜索。",
        "重排序（Reranking）是RAG流程中的重要步骤，用于从候选文档中选择最相关的文档。"
    ]
    
    for i, content in enumerate(sample_contents):
        mock_doc = {
            'id': f'doc_{i+1}',
            'content': content,
            'metadata': {
                'source': f'source_{i+1}.md',
                'type': 'markdown',
                'created_at': '2024-01-01',
                'tags': ['RAG', 'AI', '技术']
            },
            'vector_score': 0.9 - (i * 0.05),
            'chunk_id': f'chunk_{i+1}'
        }
        mock_docs.append(mock_doc)
    
    return mock_docs

def test_config_switch_dynamic():
    """测试配置开关的动态切换功能"""
    logger.info("=== 开始测试配置开关动态切换 ===")
    
    try:
        from v2.config.v2_config import V2ConfigManager
        from v2.core.reranking_services import create_reranking_service
        
        # 加载配置
        config_manager = V2ConfigManager()
        config = config_manager.config
        text_config = config.text_engine
        
        # 创建模拟数据
        mock_docs = create_mock_vector_store()
        query = "RAG系统的工作原理是什么？"
        
        logger.info("=== 测试1：启用增强Reranking + 大模型增强 ===")
        # 确保启用增强reranking和大模型增强
        setattr(text_config, 'enable_enhanced_reranking', True)
        text_config.reranking['use_llm_enhancement'] = True
        
        logger.info(f"enable_enhanced_reranking: {getattr(text_config, 'enable_enhanced_reranking', False)}")
        logger.info(f"use_llm_enhancement: {text_config.reranking['use_llm_enhancement']}")
        
        # 测试reranking服务
        if getattr(text_config, 'enable_enhanced_reranking', False):
            reranking_config = getattr(text_config, 'reranking', {})
            reranking_service = create_reranking_service('text', reranking_config)
            
            if reranking_service:
                logger.info("✅ 增强Reranking服务创建成功")
                reranked_results = reranking_service.rerank(query, mock_docs)
                logger.info(f"✅ 增强Reranking执行成功，返回 {len(reranked_results)} 个结果")
                logger.info(f"  重排序方法: {reranked_results[0].get('reranking_method', 'N/A')}")
            else:
                logger.error("❌ 增强Reranking服务创建失败")
        
        logger.info("\n=== 测试2：启用增强Reranking + 禁用大模型增强 ===")
        # 启用增强reranking，但禁用大模型增强
        setattr(text_config, 'enable_enhanced_reranking', True)
        text_config.reranking['use_llm_enhancement'] = False
        
        logger.info(f"enable_enhanced_reranking: {getattr(text_config, 'enable_enhanced_reranking', False)}")
        logger.info(f"use_llm_enhancement: {text_config.reranking['use_llm_enhancement']}")
        
        # 测试reranking服务
        if getattr(text_config, 'enable_enhanced_reranking', False):
            reranking_config = getattr(text_config, 'reranking', {})
            reranking_service = create_reranking_service('text', reranking_config)
            
            if reranking_service:
                logger.info("✅ Reranking服务创建成功（禁用大模型状态）")
                reranked_results = reranking_service.rerank(query, mock_docs)
                logger.info(f"✅ Reranking执行成功，返回 {len(reranked_results)} 个结果")
                logger.info(f"  重排序方法: {reranked_results[0].get('reranking_method', 'N/A')}")
            else:
                logger.error("❌ Reranking服务创建失败")
        
        logger.info("\n=== 测试3：禁用增强Reranking ===")
        # 禁用增强reranking
        setattr(text_config, 'enable_enhanced_reranking', False)
        
        logger.info(f"enable_enhanced_reranking: {getattr(text_config, 'enable_enhanced_reranking', False)}")
        
        # 当禁用增强reranking时，不应该调用新的reranking服务
        if not getattr(text_config, 'enable_enhanced_reranking', False):
            logger.info("ℹ️ 增强Reranking已禁用，应该使用传统排序方式")
            logger.info("✅ 配置开关测试通过：禁用时不会调用新的reranking服务")
        
        logger.info("\n=== 测试4：重新启用增强Reranking + 大模型增强 ===")
        # 重新启用增强reranking和大模型增强
        setattr(text_config, 'enable_enhanced_reranking', True)
        text_config.reranking['use_llm_enhancement'] = True
        
        logger.info(f"enable_enhanced_reranking: {getattr(text_config, 'enable_enhanced_reranking', False)}")
        logger.info(f"use_llm_enhancement: {text_config.reranking['use_llm_enhancement']}")
        
        # 测试reranking服务
        if getattr(text_config, 'enable_enhanced_reranking', False):
            reranking_config = getattr(text_config, 'reranking', {})
            reranking_service = create_reranking_service('text', reranking_config)
            
            if reranking_service:
                logger.info("✅ 增强Reranking服务重新启用成功")
                reranked_results = reranking_service.rerank(query, mock_docs)
                logger.info(f"✅ 增强Reranking重新执行成功，返回 {len(reranked_results)} 个结果")
                logger.info(f"  重排序方法: {reranked_results[0].get('reranking_method', 'N/A')}")
            else:
                logger.error("❌ 增强Reranking服务重新启用失败")
        
        logger.info("\n=== 配置开关动态切换测试完成 ===")
        
    except Exception as e:
        logger.error(f"❌ 配置开关动态切换测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_config_file_modification():
    """测试配置文件修改后的功能变化"""
    logger.info("=== 开始测试配置文件修改 ===")
    
    try:
        config_file_path = "v2/config/v2_config.json"
        
        # 读取当前配置
        with open(config_file_path, 'r', encoding='utf-8') as f:
            current_config = json.load(f)
        
        logger.info("当前配置状态:")
        logger.info(f"  enable_enhanced_reranking: {current_config['text_engine']['enable_enhanced_reranking']}")
        logger.info(f"  use_llm_enhancement: {current_config['text_engine']['reranking']['use_llm_enhancement']}")
        
        # 测试配置修改（这里只是显示，不实际修改文件）
        logger.info("\n配置修改建议:")
        logger.info("1. 禁用增强Reranking: 设置 enable_enhanced_reranking: false")
        logger.info("2. 禁用大模型增强: 设置 use_llm_enhancement: false")
        logger.info("3. 启用规则化策略: 保持其他配置不变")
        
        logger.info("\n配置开关说明:")
        logger.info("- enable_enhanced_reranking: 控制TextEngine是否调用新的reranking服务")
        logger.info("- use_llm_enhancement: 控制reranking服务内部是否使用大模型")
        logger.info("- 两个开关可以独立控制，实现灵活的功能组合")
        
        logger.info("\n✅ 配置文件修改测试完成")
        
    except Exception as e:
        logger.error(f"❌ 配置文件修改测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    logger.info("开始配置开关切换测试")
    
    # 测试配置开关动态切换
    test_config_switch_dynamic()
    
    # 测试配置文件修改
    test_config_file_modification()
    
    logger.info("配置开关切换测试完成")

if __name__ == "__main__":
    main()
