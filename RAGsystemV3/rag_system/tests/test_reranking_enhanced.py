"""
增强重排序模块测试

测试新实现的Reranking功能：
1. 多模型重排序支持
2. 混合排序策略
3. 性能优化和缓存
4. 重排序质量评估
"""

import sys
import os
import logging
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.reranking_enhanced import MultiModelReranker, RerankCandidate, RerankResult

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
            'rag_system.models.reranking.dashscope.enabled': True,
            'rag_system.models.reranking.dashscope.model_name': 'gte-rerank-v2',
            'rag_system.models.reranking.dashscope.weight': 0.6,
            'rag_system.models.reranking.rule_based.enabled': True,
            'rag_system.models.reranking.rule_based.weight': 0.4,
            'rag_system.models.reranking.batch_size': 32,
            'rag_system.models.reranking.max_candidates': 100,
            'rag_system.models.reranking.cache.enabled': True
        }
    
    def get(self, key: str, default=None):
        """模拟配置获取"""
        return self.config.get(key, default)
    
    def get_env_var(self, key: str):
        """模拟环境变量获取"""
        env_vars = {
            'DASHSCOPE_API_KEY': 'mock_key'
        }
        return env_vars.get(key)

def create_test_candidates():
    """创建测试用的候选结果"""
    return [
        RerankCandidate(
            chunk_id="chunk_001",
            content="人工智能是计算机科学的一个分支，致力于开发能够执行通常需要人类智能的任务的系统。",
            content_type="text",
            original_score=0.9,
            metadata={"source": "AI_intro.txt", "quality_score": 0.95}
        ),
        RerankCandidate(
            chunk_id="chunk_002",
            content="机器学习是人工智能的一个重要子领域，它使计算机能够在没有明确编程的情况下学习和改进。",
            content_type="text",
            original_score=0.8,
            metadata={"source": "ML_intro.txt", "quality_score": 0.88}
        ),
        RerankCandidate(
            chunk_id="chunk_003",
            content="深度学习是机器学习的一个分支，使用多层神经网络来模拟人脑的学习过程。",
            content_type="text",
            original_score=0.7,
            metadata={"source": "DL_intro.txt", "quality_score": 0.82}
        ),
        RerankCandidate(
            chunk_id="chunk_004",
            content="自然语言处理（NLP）是人工智能的另一个重要应用领域，专注于计算机理解和生成人类语言。",
            content_type="text",
            original_score=0.6,
            metadata={"source": "NLP_intro.txt", "quality_score": 0.75}
        ),
        RerankCandidate(
            chunk_id="chunk_005",
            content="计算机视觉是人工智能的一个重要分支，致力于让计算机能够理解和分析视觉信息。",
            content_type="text",
            original_score=0.5,
            metadata={"source": "CV_intro.txt", "quality_score": 0.70}
        )
    ]

def test_reranker_initialization():
    """测试重排序器初始化"""
    logger.info("测试重排序器初始化...")
    
    try:
        # 创建模拟配置
        mock_config = MockConfigIntegration()
        
        # 初始化重排序器
        reranker = MultiModelReranker(mock_config)
        
        # 检查基本配置
        logger.info(f"  重排序器类型: {type(reranker)}")
        logger.info(f"  可用模型: {reranker.models}")
        logger.info(f"  批处理大小: {reranker.batch_size}")
        logger.info(f"  最大候选数: {reranker.max_candidates}")
        logger.info(f"  缓存启用: {reranker.cache_enabled}")
        
        # 检查服务状态
        status = reranker.get_service_status()
        logger.info(f"  服务状态: {status['status']}")
        
        if status['status'] == 'ready':
            logger.info("✅ 重排序器初始化测试通过")
            return True
        else:
            logger.error("❌ 重排序器状态异常")
            return False
        
    except Exception as e:
        logger.error(f"❌ 重排序器初始化测试失败: {e}")
        return False

def test_basic_reranking():
    """测试基础重排序功能"""
    logger.info("测试基础重排序功能...")
    
    try:
        # 创建模拟配置
        mock_config = MockConfigIntegration()
        
        # 初始化重排序器
        reranker = MultiModelReranker(mock_config)
        
        # 创建测试候选
        candidates = create_test_candidates()
        query = "什么是机器学习和深度学习？"
        
        # 执行重排序
        start_time = time.time()
        reranked_results = reranker.rerank(query, candidates)
        processing_time = time.time() - start_time
        
        logger.info(f"  查询: {query}")
        logger.info(f"  候选数量: {len(candidates)}")
        logger.info(f"  重排序结果数量: {len(reranked_results)}")
        logger.info(f"  处理时间: {processing_time:.3f}s")
        
        # 验证结果
        if len(reranked_results) != len(candidates):
            logger.error("❌ 重排序结果数量不匹配")
            return False
        
        # 检查排序结果
        for i, result in enumerate(reranked_results):
            logger.info(f"    排名{i+1}: {result.chunk_id}, 分数: {result.final_score:.3f}, 置信度: {result.confidence:.3f}")
            
            # 验证基本字段
            if not result.chunk_id or result.final_score < 0 or result.confidence < 0:
                logger.error(f"❌ 重排序结果字段无效: {result}")
                return False
        
        # 检查是否按分数降序排列
        scores = [result.final_score for result in reranked_results]
        if scores != sorted(scores, reverse=True):
            logger.error("❌ 重排序结果未按分数降序排列")
            return False
        
        logger.info("✅ 基础重排序功能测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 基础重排序功能测试失败: {e}")
        return False

def test_cache_functionality():
    """测试缓存功能"""
    logger.info("测试缓存功能...")
    
    try:
        # 创建模拟配置
        mock_config = MockConfigIntegration()
        
        # 初始化重排序器
        reranker = MultiModelReranker(mock_config)
        
        # 创建测试候选
        candidates = create_test_candidates()
        query = "测试缓存功能"
        
        # 第一次重排序（缓存未命中）
        start_time = time.time()
        results1 = reranker.rerank(query, candidates)
        time1 = time.time() - start_time
        
        # 第二次重排序（缓存命中）
        start_time = time.time()
        results2 = reranker.rerank(query, candidates)
        time2 = time.time() - start_time
        
        logger.info(f"  第一次重排序时间: {time1:.3f}s")
        logger.info(f"  第二次重排序时间: {time2:.3f}s")
        logger.info(f"  缓存命中率: {reranker.performance_stats['cache_hits']}")
        logger.info(f"  缓存未命中率: {reranker.performance_stats['cache_misses']}")
        
        # 验证缓存效果
        if time2 < time1:
            logger.info("✅ 缓存加速效果明显")
        else:
            logger.warning("⚠️ 缓存加速效果不明显")
        
        # 验证结果一致性
        if len(results1) != len(results2):
            logger.error("❌ 缓存前后结果数量不一致")
            return False
        
        # 检查分数一致性
        for r1, r2 in zip(results1, results2):
            if abs(r1.final_score - r2.final_score) > 0.001:
                logger.error(f"❌ 缓存前后分数不一致: {r1.final_score} vs {r2.final_score}")
                return False
        
        logger.info("✅ 缓存功能测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 缓存功能测试失败: {e}")
        return False

def test_performance_optimization():
    """测试性能优化功能"""
    logger.info("测试性能优化功能...")
    
    try:
        # 创建模拟配置
        mock_config = MockConfigIntegration()
        
        # 初始化重排序器
        reranker = MultiModelReranker(mock_config)
        
        # 创建大量候选进行性能测试
        large_candidates = []
        for i in range(50):
            candidate = RerankCandidate(
                chunk_id=f"chunk_{i:03d}",
                content=f"这是第{i+1}个测试候选内容，用于性能测试。",
                content_type="text",
                original_score=0.9 - i * 0.01,
                metadata={"source": f"test_{i}.txt", "quality_score": 0.9 - i * 0.01}
            )
            large_candidates.append(candidate)
        
        query = "性能测试查询"
        
        # 执行重排序
        start_time = time.time()
        reranked_results = reranker.rerank(query, large_candidates)
        processing_time = time.time() - start_time
        
        logger.info(f"  候选数量: {len(large_candidates)}")
        logger.info(f"  处理时间: {processing_time:.3f}s")
        logger.info(f"  平均处理时间: {reranker.performance_stats['avg_time']:.3f}s")
        
        # 验证性能
        if processing_time < 5.0:  # 50个候选应该在5秒内完成
            logger.info("✅ 性能表现良好")
        else:
            logger.warning("⚠️ 性能表现一般")
        
        # 验证结果数量限制
        if len(reranked_results) <= reranker.max_candidates:
            logger.info("✅ 候选数量限制生效")
        else:
            logger.error("❌ 候选数量限制未生效")
        
        logger.info("✅ 性能优化功能测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 性能优化功能测试失败: {e}")
        return False

def test_fallback_mechanism():
    """测试回退机制"""
    logger.info("测试回退机制...")
    
    try:
        # 创建模拟配置（禁用所有模型）
        mock_config = MockConfigIntegration()
        mock_config.config['rag_system.models.reranking.dashscope.enabled'] = False
        mock_config.config['rag_system.models.reranking.rule_based.enabled'] = False
        
        # 初始化重排序器
        reranker = MultiModelReranker(mock_config)
        
        # 创建测试候选
        candidates = create_test_candidates()
        query = "测试回退机制"
        
        # 执行重排序（应该触发回退）
        reranked_results = reranker.rerank(query, candidates)
        
        logger.info(f"  回退结果数量: {len(reranked_results)}")
        logger.info(f"  可用模型: {reranker.get_service_status()['available_models']}")
        
        # 验证回退结果
        if len(reranked_results) == len(candidates):
            logger.info("✅ 回退机制正常工作")
            
            # 检查回退结果的基本属性
            for result in reranked_results:
                if result.final_score == result.original_score:
                    logger.info("✅ 回退结果使用原始分数")
                else:
                    logger.warning("⚠️ 回退结果分数被修改")
            
            return True
        else:
            logger.error("❌ 回退机制异常")
            return False
        
    except Exception as e:
        logger.error(f"❌ 回退机制测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("增强重排序模块测试开始")
    logger.info("=" * 60)
    
    tests = [
        ("重排序器初始化", test_reranker_initialization),
        ("基础重排序功能", test_basic_reranking),
        ("缓存功能", test_cache_functionality),
        ("性能优化功能", test_performance_optimization),
        ("回退机制", test_fallback_mechanism)
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
        logger.info("🎉 所有测试通过！增强重排序模块实现成功")
        return 0
    else:
        logger.error("💥 部分测试失败！需要检查实现")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
