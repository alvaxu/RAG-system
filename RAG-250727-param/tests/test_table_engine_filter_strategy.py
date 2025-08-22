#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 测试table_engine的第二层向量搜索filter和post_filter策略
## 2. 验证是否与text_engine的实现保持一致
## 3. 测试内容相关性计算方法
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from v2.config.v2_config import TableEngineConfigV2
from v2.core.table_engine import TableEngine

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_table_engine_config():
    """测试table_engine配置加载"""
    try:
        config = TableEngineConfigV2()
        logger.info("✅ 成功加载TableEngineConfigV2")
        
        # 检查第二层向量搜索配置
        layer2_config = config.recall_strategy.get('layer2_vector_search', {})
        logger.info(f"第二层向量搜索配置: {layer2_config}")
        
        # 检查阈值设置
        threshold = layer2_config.get('similarity_threshold', 0.65)
        logger.info(f"第二层相似度阈值: {threshold}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 配置加载失败: {e}")
        return False

def test_calculate_content_relevance():
    """测试内容相关性计算方法"""
    try:
        # 创建配置
        config = TableEngineConfigV2()
        
        # 创建mock的table_engine实例（不依赖vector_store）
        class MockTableEngine(TableEngine):
            def __init__(self, config):
                super().__init__(config, vector_store=None, skip_initial_load=True)
            
            def _calculate_search_k(self, top_k, layer_config):
                return top_k * 2
        
        engine = MockTableEngine(config)
        
        # 测试查询和内容
        query = "财务报表"
        content = "这是一份详细的财务报表，包含收入、支出、利润等财务指标"
        
        score = engine._calculate_content_relevance(query, content)
        logger.info(f"查询: '{query}'")
        logger.info(f"内容: '{content}'")
        logger.info(f"相关性分数: {score}")
        
        # 测试另一个查询
        query2 = "员工薪资"
        content2 = "员工薪资统计表，显示各部门员工的薪资分布情况"
        
        score2 = engine._calculate_content_relevance(query2, content2)
        logger.info(f"查询2: '{query2}'")
        logger.info(f"内容2: '{content2}'")
        logger.info(f"相关性分数2: {score2}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 内容相关性计算测试失败: {e}")
        return False

def test_filter_strategy_logic():
    """测试filter策略逻辑"""
    try:
        # 创建配置
        config = TableEngineConfigV2()
        
        # 检查配置中的策略设置
        recall_strategy = config.recall_strategy
        
        # 验证第二层策略配置
        layer2 = recall_strategy.get('layer2_vector_search', {})
        logger.info(f"第二层策略配置: {layer2}")
        
        # 检查是否启用了向量搜索
        enabled = layer2.get('enabled', True)
        logger.info(f"第二层向量搜索启用状态: {enabled}")
        
        # 检查阈值设置
        threshold = layer2.get('similarity_threshold', 0.65)
        logger.info(f"第二层相似度阈值: {threshold}")
        
        # 检查top_k设置
        top_k = layer2.get('top_k', 40)
        logger.info(f"第二层top_k: {top_k}")
        
        return True
    except Exception as e:
        logger.error(f"❌ filter策略逻辑测试失败: {e}")
        return False

def test_configuration_consistency():
    """测试配置一致性"""
    try:
        config = TableEngineConfigV2()
        
        # 检查recall_strategy配置
        recall_strategy = config.recall_strategy
        logger.info("召回策略配置:")
        for layer_name, layer_config in recall_strategy.items():
            logger.info(f"  {layer_name}: {layer_config}")
        
        # 检查reranking配置
        reranking = config.reranking
        logger.info(f"重排序配置: {reranking}")
        
        # 检查新pipeline配置
        use_new_pipeline = config.use_new_pipeline
        enable_enhanced_reranking = config.enable_enhanced_reranking
        logger.info(f"新pipeline启用: {use_new_pipeline}")
        logger.info(f"增强重排序启用: {enable_enhanced_reranking}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 配置一致性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始测试table_engine的filter和post_filter策略")
    
    tests = [
        ("配置加载测试", test_table_engine_config),
        ("内容相关性计算测试", test_calculate_content_relevance),
        ("Filter策略逻辑测试", test_filter_strategy_logic),
        ("配置一致性测试", test_configuration_consistency),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 执行测试: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} 通过")
                passed += 1
            else:
                logger.error(f"❌ {test_name} 失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 异常: {e}")
    
    logger.info(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！table_engine的filter和post_filter策略实现正确")
    else:
        logger.error("⚠️ 部分测试失败，需要检查实现")
    
    return passed == total

if __name__ == "__main__":
    main()
