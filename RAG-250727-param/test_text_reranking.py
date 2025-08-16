'''
程序说明：
## 1. 测试TextRerankingService的大模型功能
## 2. 验证配置开关和API密钥管理
## 3. 测试大模型和规则化策略的回退机制

## 主要功能：
- 测试大模型Reranking
- 测试配置开关功能
- 测试API密钥管理
- 测试错误处理和回退机制
'''

import sys
import os
import json
import logging
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
        "重排序（Reranking）是RAG流程中的重要步骤，用于从候选文档中选择最相关的文档。",
        "智能问答系统需要处理多种类型的查询，包括事实性查询、推理查询和创造性查询。",
        "文档预处理包括文本清洗、分块、向量化等步骤，直接影响检索质量。",
        "多模态RAG系统能够处理文本、图像、表格等多种类型的内容。",
        "配置管理是RAG系统的重要组成部分，需要支持灵活的配置调整和热更新。",
        "性能优化包括向量检索优化、重排序优化和LLM生成优化等多个方面。",
        "错误处理和日志记录对于生产环境的RAG系统至关重要。",
        "API接口设计需要考虑易用性、安全性和扩展性。",
        "测试和验证是确保RAG系统质量的重要手段。",
        "部署和运维需要考虑资源管理、监控告警和故障恢复。",
        "用户反馈和持续改进是RAG系统成功的关键因素。"
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
            'vector_score': 0.9 - (i * 0.05),  # 模拟向量相似度分数
            'chunk_id': f'chunk_{i+1}'
        }
        mock_docs.append(mock_doc)
    
    return mock_docs

def test_text_reranking():
    """测试TextRerankingService的基本功能"""
    logger.info("=== 开始测试TextRerankingService ===")
    
    try:
        # 导入必要的模块
        from v2.core.reranking_services import create_reranking_service
        from v2.config.v2_config import V2ConfigManager
        
        # 加载配置（使用与主程序相同的方式）
        config_manager = V2ConfigManager()
        config = config_manager.config
        text_config = config.text_engine
        
        # 创建模拟数据
        mock_docs = create_mock_vector_store()
        query = "RAG系统的工作原理是什么？"
        
        logger.info(f"查询: {query}")
        logger.info(f"候选文档数量: {len(mock_docs)}")
        
        # 创建Reranking服务
        reranking_config = text_config.reranking
        logger.info(f"Reranking配置: {reranking_config}")
        
        reranking_service = create_reranking_service('text', reranking_config)
        
        if reranking_service:
            logger.info("Reranking服务创建成功")
            
            # 执行重排序
            reranked_results = reranking_service.rerank(query, mock_docs)
            
            logger.info(f"重排序完成，返回 {len(reranked_results)} 个结果")
            
            # 显示前5个结果
            for i, result in enumerate(reranked_results[:5]):
                logger.info(f"第{i+1}名: {result.get('content', '')[:50]}...")
                logger.info(f"  重排序分数: {result.get('rerank_score', 'N/A')}")
                logger.info(f"  重排序方法: {result.get('reranking_method', 'N/A')}")
                logger.info("---")
                
        else:
            logger.error("Reranking服务创建失败")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def test_config_switch():
    """测试配置开关功能"""
    logger.info("=== 开始测试配置开关功能 ===")
    
    try:
        from v2.config.v2_config import V2ConfigManager
        
        # 加载配置（使用与主程序相同的方式）
        config_manager = V2ConfigManager()
        config = config_manager.config
        
        # 检查配置开关
        use_new_pipeline = getattr(config.text_engine, 'use_new_pipeline', False)
        enable_enhanced_reranking = getattr(config.text_engine, 'enable_enhanced_reranking', False)
        
        logger.info(f"use_new_pipeline: {use_new_pipeline}")
        logger.info(f"enable_enhanced_reranking: {enable_enhanced_reranking}")
        
        # 检查reranking配置
        reranking_config = config.text_engine.reranking
        use_llm_enhancement = reranking_config.get('use_llm_enhancement', False)
        model_name = reranking_config.get('model_name', 'N/A')
        
        logger.info(f"use_llm_enhancement: {use_llm_enhancement}")
        logger.info(f"model_name: {model_name}")
        
        # 验证配置完整性
        required_keys = ['target_count', 'use_llm_enhancement', 'model_name', 'similarity_threshold']
        missing_keys = [key for key in required_keys if key not in reranking_config]
        
        if missing_keys:
            logger.warning(f"缺少配置项: {missing_keys}")
        else:
            logger.info("配置完整性检查通过")
            
    except Exception as e:
        logger.error(f"配置开关测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_api_key_management():
    """测试API密钥管理"""
    logger.info("=== 开始测试API密钥管理 ===")
    
    try:
        # 测试环境变量
        import os
        dashscope_key = os.getenv('DASHSCOPE_API_KEY')
        logger.info(f"环境变量DASHSCOPE_API_KEY: {'已设置' if dashscope_key else '未设置'}")
        
        # 测试API密钥管理器
        try:
            from config.api_key_manager import APIKeyManager
            key_manager = APIKeyManager()
            api_key = key_manager.get_dashscope_api_key()
            logger.info(f"API密钥管理器获取dashscope密钥: {'成功' if api_key else '失败'}")
        except Exception as e:
            logger.warning(f"API密钥管理器测试失败: {e}")
            
    except Exception as e:
        logger.error(f"API密钥管理测试失败: {e}")

def test_error_handling():
    """测试错误处理机制"""
    logger.info("=== 开始测试错误处理机制 ===")
    
    try:
        from v2.core.reranking_services import create_reranking_service
        
        # 测试无效配置
        invalid_config = {'invalid_key': 'invalid_value'}
        service = create_reranking_service('text', invalid_config)
        
        if service:
            logger.info("使用无效配置创建服务成功（应该有默认值）")
        else:
            logger.warning("使用无效配置创建服务失败")
            
    except Exception as e:
        logger.error(f"错误处理测试失败: {e}")

def main():
    """主测试函数"""
    logger.info("开始TextRerankingService测试")
    
    # 测试配置开关
    test_config_switch()
    
    # 测试API密钥管理
    test_api_key_management()
    
    # 测试错误处理
    test_error_handling()
    
    # 测试基本功能（需要API密钥）
    test_text_reranking()
    
    logger.info("测试完成")

if __name__ == "__main__":
    main()
