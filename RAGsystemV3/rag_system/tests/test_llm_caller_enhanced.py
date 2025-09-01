"""
LLM调用器增强功能测试模块

测试新实现的LLM调用器功能：
1. 提示词管理器（PromptManager）
2. 上下文管理器（ContextManager）
3. Token统计功能
4. 返回数据结构优化
"""

import sys
import os
import logging
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.llm_caller import LLMCaller, LLMResponse
from core.prompt_manager import PromptManager, PromptTemplate
from core.context_manager import ContextManager, ContextChunk
from core.config_integration import ConfigIntegration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class MockConfigIntegration:
    """模拟配置集成管理器"""
    
    def __init__(self):
        self.config = {
            'rag_system.models.llm.model_name': 'qwen-turbo',
            'rag_system.models.llm.max_tokens': 2048,
            'rag_system.models.llm.temperature': 0.7,
            'rag_system.query_processing.max_context_length': 4000,
            'rag_system.query_processing.max_chunks': 10,
            'rag_system.query_processing.relevance_threshold': 0.7
        }
    
    def get(self, key: str, default=None):
        """模拟配置获取"""
        return self.config.get(key, default)
    
    def get_rag_config(self, key: str, default=None):
        """模拟RAG配置获取"""
        config_key = f'rag_system.{key}'
        return self.config.get(config_key, default)
    
    def get_env_var(self, key: str):
        """模拟环境变量获取"""
        env_vars = {
            'DASHSCOPE_API_KEY': 'mock_key'
        }
        return env_vars.get(key)

def create_test_context_chunks():
    """创建测试用的上下文块"""
    return [
        ContextChunk(
            content="人工智能是计算机科学的一个分支，致力于开发能够执行通常需要人类智能的任务的系统。",
            chunk_id="chunk_001",
            content_type="text",
            relevance_score=0.9,
            source="AI_intro.txt",
            metadata={"category": "definition", "language": "zh"}
        ),
        ContextChunk(
            content="机器学习是人工智能的一个重要子领域，它使计算机能够在没有明确编程的情况下学习和改进。",
            chunk_id="chunk_002",
            content_type="text",
            relevance_score=0.8,
            source="ML_intro.txt",
            metadata={"category": "subfield", "language": "zh"}
        ),
        ContextChunk(
            content="深度学习是机器学习的一个分支，使用多层神经网络来模拟人脑的学习过程。",
            chunk_id="chunk_003",
            content_type="text",
            relevance_score=0.7,
            source="DL_intro.txt",
            metadata={"category": "technique", "language": "zh"}
        ),
        ContextChunk(
            content="自然语言处理（NLP）是人工智能的另一个重要应用领域，专注于计算机理解和生成人类语言。",
            chunk_id="chunk_004",
            content_type="text",
            relevance_score=0.6,
            source="NLP_intro.txt",
            metadata={"category": "application", "language": "zh"}
        )
    ]

def test_prompt_manager():
    """测试提示词管理器"""
    logger.info("测试提示词管理器...")
    
    try:
        # 创建模拟配置
        mock_config = MockConfigIntegration()
        
        # 初始化提示词管理器
        prompt_manager = PromptManager(mock_config)
        
        # 测试1: 获取默认模板
        templates = prompt_manager.list_templates()
        logger.info(f"  默认模板数量: {len(templates)}")
        
        if len(templates) < 3:
            logger.error("  错误: 默认模板数量不足")
            return False
        
        # 测试2: 生成提示词
        test_params = {
            'context': '人工智能是计算机科学的一个分支...',
            'query': '什么是人工智能？'
        }
        
        prompt = prompt_manager.generate_prompt('rag_qa', test_params)
        logger.info(f"  生成的提示词长度: {len(prompt)}")
        
        if not prompt or len(prompt) < 50:
            logger.error("  错误: 生成的提示词无效")
            return False
        
        # 测试3: 添加自定义模板
        custom_template = PromptTemplate(
            name='custom_qa',
            template="基于上下文回答问题：\n上下文：{context}\n问题：{query}\n答案：",
            description='自定义问答模板',
            category='custom',
            version='1.0.0',
            parameters=['context', 'query'],
            examples=[],
            created_at=time.time(),
            updated_at=time.time()
        )
        
        success = prompt_manager.add_template(custom_template)
        if not success:
            logger.error("  错误: 添加自定义模板失败")
            return False
        
        # 测试4: 搜索模板
        search_results = prompt_manager.search_templates('分析')
        logger.info(f"  搜索'分析'的结果数量: {len(search_results)}")
        
        # 测试5: 获取使用统计
        usage_stats = prompt_manager.get_usage_stats()
        logger.info(f"  使用统计: {usage_stats}")
        
        logger.info("✅ 提示词管理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 提示词管理器测试失败: {e}")
        return False

def test_context_manager():
    """测试上下文管理器"""
    logger.info("测试上下文管理器...")
    
    try:
        # 创建模拟配置
        mock_config = MockConfigIntegration()
        
        # 初始化上下文管理器
        context_manager = ContextManager(mock_config)
        
        # 创建测试上下文块
        context_chunks = create_test_context_chunks()
        
        # 测试1: 上下文优化
        query = "什么是机器学习和深度学习？"
        optimized_context = context_manager.optimize_context(context_chunks, query)
        
        logger.info(f"  原始上下文块数量: {len(context_chunks)}")
        logger.info(f"  优化后上下文长度: {len(optimized_context)}")
        
        if not optimized_context:
            logger.error("  错误: 上下文优化失败")
            return False
        
        # 测试2: 长度限制
        short_context = context_manager.optimize_context(context_chunks, query, max_length=100)
        logger.info(f"  限制长度后的上下文长度: {len(short_context)}")
        
        if len(short_context) > 100:
            logger.error("  错误: 长度限制未生效")
            return False
        
        # 测试3: 相关性排序
        # 修改一些块的分数
        context_chunks[0].relevance_score = 0.5
        context_chunks[1].relevance_score = 0.9
        
        sorted_chunks = context_manager._sort_by_relevance(context_chunks, query)
        logger.info(f"  排序后最高相关性: {sorted_chunks[0].relevance_score:.3f}")
        
        if sorted_chunks[0].relevance_score != 0.9:
            logger.error("  错误: 相关性排序失败")
            return False
        
        # 测试4: 获取统计信息
        stats = context_manager.get_context_stats()
        logger.info(f"  上下文处理统计: {stats}")
        
        logger.info("✅ 上下文管理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 上下文管理器测试失败: {e}")
        return False

def test_llm_caller_enhanced():
    """测试增强的LLM调用器"""
    logger.info("测试增强的LLM调用器...")
    
    try:
        # 创建模拟配置
        mock_config = MockConfigIntegration()
        
        # 初始化LLM调用器
        llm_caller = LLMCaller(mock_config)
        
        # 创建测试上下文块
        context_chunks = create_test_context_chunks()
        
        # 测试1: 生成答案（模拟模式）
        query = "请解释人工智能、机器学习和深度学习的关系"
        response = llm_caller.generate_answer(query, context_chunks, 'rag_qa')
        
        logger.info(f"  响应类型: {type(response)}")
        logger.info(f"  响应成功: {response.success}")
        logger.info(f"  答案长度: {len(response.answer)}")
        logger.info(f"  处理时间: {response.processing_time:.3f}s")
        
        if not isinstance(response, LLMResponse):
            logger.error("  错误: 返回类型不是LLMResponse")
            return False
        
        if not response.success:
            logger.error("  错误: 响应生成失败")
            return False
        
        # 测试2: Token统计
        logger.info(f"  Prompt Tokens: {response.prompt_tokens}")
        logger.info(f"  Completion Tokens: {response.completion_tokens}")
        logger.info(f"  Total Tokens: {response.total_tokens}")
        
        if response.total_tokens <= 0:
            logger.error("  错误: Token统计无效")
            return False
        
        # 测试3: 元数据
        metadata = response.metadata
        logger.info(f"  元数据: {metadata}")
        
        if not metadata or 'context_chunks_count' not in metadata:
            logger.error("  错误: 元数据不完整")
            return False
        
        # 测试4: 获取Token统计
        token_stats = llm_caller.get_token_stats()
        logger.info(f"  累计Token统计: {token_stats}")
        
        if token_stats['total_tokens'] <= 0:
            logger.error("  错误: 累计Token统计无效")
            return False
        
        # 测试5: 服务状态
        service_status = llm_caller.get_service_status()
        logger.info(f"  服务状态: {service_status}")
        
        if service_status['status'] != 'ready':
            logger.error("  错误: 服务状态异常")
            return False
        
        logger.info("✅ 增强的LLM调用器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 增强的LLM调用器测试失败: {e}")
        return False

def test_integration():
    """测试组件集成"""
    logger.info("测试组件集成...")
    
    try:
        # 创建模拟配置
        mock_config = MockConfigIntegration()
        
        # 初始化所有组件
        prompt_manager = PromptManager(mock_config)
        context_manager = ContextManager(mock_config)
        llm_caller = LLMCaller(mock_config)
        
        # 测试1: 组件状态
        prompt_status = prompt_manager.get_service_status()
        context_status = context_manager.get_service_status()
        llm_status = llm_caller.get_service_status()
        
        logger.info(f"  提示词管理器状态: {prompt_status['status']}")
        logger.info(f"  上下文管理器状态: {context_status['status']}")
        logger.info(f"  LLM调用器状态: {llm_status['status']}")
        
        if not all(status['status'] == 'ready' for status in [prompt_status, context_status, llm_status]):
            logger.error("  错误: 组件状态异常")
            return False
        
        # 测试2: 完整流程
        context_chunks = create_test_context_chunks()
        query = "总结人工智能的主要技术"
        
        # 使用不同的提示词模板
        templates = ['rag_qa', 'rag_summary', 'rag_analysis']
        
        for template in templates:
            response = llm_caller.generate_answer(query, context_chunks, template)
            logger.info(f"  模板 {template} 响应成功: {response.success}")
            
            if not response.success:
                logger.error(f"  错误: 模板 {template} 响应失败")
                return False
        
        logger.info("✅ 组件集成测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 组件集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("LLM调用器增强功能测试开始")
    logger.info("=" * 60)
    
    tests = [
        ("提示词管理器", test_prompt_manager),
        ("上下文管理器", test_context_manager),
        ("增强的LLM调用器", test_llm_caller_enhanced),
        ("组件集成", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 运行测试: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} 通过")
                passed += 1
            else:
                logger.error(f"❌ {test_name} 失败")
        except Exception as e:
            logger.error(f"💥 {test_name} 执行异常: {e}")
    
    logger.info(f"\n📊 测试结果汇总:")
    logger.info(f"   总测试数: {total}")
    logger.info(f"   通过数量: {passed}")
    logger.info(f"   失败数量: {total - passed}")
    logger.info(f"   通过率: {(passed/total)*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 所有测试通过！LLM调用器增强功能实现成功")
        return 0
    else:
        logger.error("💥 部分测试失败！需要检查实现")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
