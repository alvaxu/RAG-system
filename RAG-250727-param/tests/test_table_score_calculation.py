#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 测试table_engine的score计算逻辑
## 2. 验证不同阈值下的结果数量
## 3. 分析score计算是否合理
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

def test_score_calculation():
    """测试score计算逻辑"""
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
        query = "中芯国际的营业收入从2017年到2024年的变化趋势如何？"
        
        # 模拟不同的table内容
        test_contents = [
            "中芯国际营业收入统计表，2017年营收100亿，2018年营收120亿，2019年营收150亿",
            "中芯国际财务数据，包含营业收入、净利润等关键指标",
            "半导体行业分析报告，涉及中芯国际等主要企业",
            "中芯国际季度财报，营业收入持续增长",
            "集成电路制造企业营收对比，中芯国际表现突出"
        ]
        
        logger.info(f"查询: '{query}'")
        logger.info("=" * 80)
        
        for i, content in enumerate(test_contents, 1):
            score = engine._calculate_content_relevance(query, content)
            logger.info(f"内容{i}: '{content}'")
            logger.info(f"相关性分数: {score:.4f}")
            logger.info(f"是否通过0.65阈值: {'✅' if score >= 0.65 else '❌'}")
            logger.info(f"是否通过0.4阈值: {'✅' if score >= 0.4 else '❌'}")
            logger.info(f"是否通过0.3阈值: {'✅' if score >= 0.3 else '❌'}")
            logger.info("-" * 60)
        
        return True
    except Exception as e:
        logger.error(f"❌ score计算测试失败: {e}")
        return False

def test_threshold_analysis():
    """测试不同阈值下的结果分析"""
    try:
        # 创建配置
        config = TableEngineConfigV2()
        
        # 检查当前阈值设置
        layer2_config = config.recall_strategy.get('layer2_vector_search', {})
        current_threshold = layer2_config.get('similarity_threshold', 0.65)
        
        logger.info(f"当前第二层向量搜索阈值: {current_threshold}")
        
        # 分析阈值设置是否合理
        if current_threshold > 0.5:
            logger.warning(f"⚠️ 阈值 {current_threshold} 可能过高，建议降低到 0.3-0.4 范围")
        elif current_threshold < 0.2:
            logger.warning(f"⚠️ 阈值 {current_threshold} 可能过低，可能返回过多无关结果")
        else:
            logger.info(f"✅ 阈值 {current_threshold} 设置合理")
        
        # 建议的阈值范围
        logger.info("建议的阈值范围:")
        logger.info("  0.8-1.0: 极高精度，低召回（适合精确匹配）")
        logger.info("  0.6-0.8: 高精度，中等召回（适合高质量结果）")
        logger.info("  0.4-0.6: 中等精度，中等召回（平衡精度和召回）")
        logger.info("  0.2-0.4: 中等精度，高召回（适合广泛搜索）")
        logger.info("  0.1-0.2: 低精度，极高召回（兜底策略）")
        
        return True
    except Exception as e:
        logger.error(f"❌ 阈值分析失败: {e}")
        return False

def test_query_analysis():
    """分析查询的关键词"""
    try:
        query = "中芯国际的营业收入从2017年到2024年的变化趋势如何？"
        
        # 使用jieba分词
        try:
            import jieba
            keywords = jieba.lcut(query, cut_all=False)
            # 过滤掉停用词和短词
            filtered_keywords = [word for word in keywords if len(word) > 1 and word not in ['的', '从', '到', '年', '如何', '变化', '趋势']]
            
            logger.info(f"查询: '{query}'")
            logger.info(f"jieba分词结果: {keywords}")
            logger.info(f"过滤后关键词: {filtered_keywords}")
            
            # 分析关键词重要性
            important_keywords = ['中芯国际', '营业收入', '2017', '2024']
            logger.info(f"重要关键词: {important_keywords}")
            
            # 计算匹配要求
            min_matches = len(important_keywords) * 0.6  # 至少60%的关键词匹配
            logger.info(f"建议至少匹配 {min_matches:.1f} 个重要关键词")
            
        except ImportError:
            logger.warning("jieba未安装，使用简单分词")
            words = query.split()
            logger.info(f"简单分词结果: {words}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 查询分析失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始测试table_engine的score计算和阈值设置")
    
    tests = [
        ("Score计算测试", test_score_calculation),
        ("阈值分析测试", test_threshold_analysis),
        ("查询分析测试", test_query_analysis),
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
        logger.info("🎉 所有测试通过！")
        logger.info("\n💡 建议:")
        logger.info("1. 降低第二层向量搜索阈值到 0.3-0.4")
        logger.info("2. 检查内容相关性计算是否过于严格")
        logger.info("3. 考虑添加关键词权重调整")
    else:
        logger.error("⚠️ 部分测试失败，需要检查实现")
    
    return passed == total

if __name__ == "__main__":
    main()
