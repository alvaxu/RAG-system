#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 深度调试table_engine的score计算问题
## 2. 分析为什么实际table文档的score都低于0.35
## 3. 找出score计算逻辑的问题
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

def debug_score_calculation_step_by_step():
    """逐步调试score计算过程"""
    try:
        # 创建配置
        config = TableEngineConfigV2()
        
        # 创建mock的table_engine实例
        class MockTableEngine(TableEngine):
            def __init__(self, config):
                super().__init__(config, vector_store=None, skip_initial_load=True)
        
        engine = MockTableEngine(config)
        
        # 实际查询
        query = "中芯国际的营业收入从2017年到2024年的变化趋势如何？"
        
        # 模拟一些可能的实际table内容（基于日志中提到的13个table文档）
        test_contents = [
            # 可能的高相关性内容
            "中芯国际营业收入统计表，2017年营收100亿，2018年营收120亿，2019年营收150亿，2020年营收180亿，2021年营收220亿，2022年营收250亿，2023年营收280亿，2024年营收300亿",
            "中芯国际财务数据表，包含营业收入、净利润、毛利率等关键财务指标，数据涵盖2017-2024年",
            "中芯国际季度财报汇总，营业收入从2017年到2024年持续增长，年复合增长率约15%",
            
            # 中等相关性内容
            "半导体行业分析报告，涉及中芯国际、台积电等主要企业的营收对比分析",
            "集成电路制造企业财务数据，中芯国际在营收规模方面表现突出",
            "中芯国际企业年报，详细记录了营业收入变化趋势和增长驱动因素",
            
            # 低相关性内容
            "科技企业营收排行榜，包含中芯国际等半导体企业",
            "制造业企业财务分析，中芯国际作为代表企业之一",
            "上市公司财务数据统计，中芯国际营收表现分析"
        ]
        
        logger.info(f"🔍 深度调试查询: '{query}'")
        logger.info("=" * 100)
        
        for i, content in enumerate(test_contents, 1):
            logger.info(f"\n📋 内容{i}: '{content}'")
            logger.info("-" * 80)
            
            # 逐步分析score计算过程
            try:
                # 1. 基础检查
                if not content or not query:
                    logger.info("❌ 内容或查询为空")
                    continue
                
                query_lower = query.lower()
                content_lower = content.lower()
                logger.info(f"查询转小写: '{query_lower}'")
                logger.info(f"内容转小写: '{content_lower}'")
                
                # 2. 直接包含检查
                if query_lower in content_lower:
                    logger.info("✅ 直接包含检查通过，返回0.8")
                    score = 0.8
                else:
                    logger.info("❌ 直接包含检查失败，继续分词计算")
                    
                    # 3. 分词处理
                    try:
                        import jieba
                        query_keywords = jieba.lcut(query_lower, cut_all=False)
                        query_words = [word for word in query_keywords if len(word) > 1]
                        if not query_words:
                            query_words = [word for word in query_lower.split() if len(word) > 1]
                        
                        content_keywords = jieba.lcut(content_lower, cut_all=False)
                        content_words = [word for word in content_keywords if len(word) > 1]
                        if not content_words:
                            content_words = [word for word in content_lower.split() if len(word) > 1]
                        
                        logger.info(f"查询分词结果: {query_keywords}")
                        logger.info(f"查询关键词(>1字符): {query_words}")
                        logger.info(f"内容分词结果: {content_keywords}")
                        logger.info(f"内容关键词(>1字符): {content_words}")
                        
                        if not query_words or not content_words:
                            logger.info("❌ 分词后无有效关键词")
                            score = 0.0
                        else:
                            # 4. 关键词匹配计算
                            matched_words = 0
                            total_score = 0.0
                            
                            logger.info("\n🔍 关键词匹配详情:")
                            for query_word in query_words:
                                if query_word in content_words:
                                    matched_words += 1
                                    word_count = content_lower.count(query_word)
                                    word_score = min(word_count / len(content_words), 0.3)
                                    total_score += word_score
                                    logger.info(f"  ✅ '{query_word}' 匹配成功，出现{word_count}次，单词分数: {word_score:.4f}")
                                else:
                                    logger.info(f"  ❌ '{query_word}' 匹配失败")
                            
                            # 5. 最终分数计算
                            match_rate = matched_words / len(query_words) if query_words else 0
                            final_score = (match_rate * 0.7 + total_score * 0.3)
                            score = min(final_score, 1.0)
                            
                            logger.info(f"\n📊 分数计算详情:")
                            logger.info(f"  匹配关键词数: {matched_words}/{len(query_words)}")
                            logger.info(f"  匹配率: {match_rate:.4f}")
                            logger.info(f"  单词分数总和: {total_score:.4f}")
                            logger.info(f"  最终分数: {final_score:.4f}")
                            logger.info(f"  最终分数(限制): {score:.4f}")
                            
                    except Exception as e:
                        logger.error(f"分词处理异常: {e}")
                        score = 0.0
                
                # 6. 阈值检查
                logger.info(f"\n🎯 阈值检查结果:")
                logger.info(f"  分数: {score:.4f}")
                logger.info(f"  通过0.35阈值: {'✅' if score >= 0.35 else '❌'}")
                logger.info(f"  通过0.3阈值: {'✅' if score >= 0.3 else '❌'}")
                logger.info(f"  通过0.2阈值: {'✅' if score >= 0.2 else '❌'}")
                
            except Exception as e:
                logger.error(f"计算过程异常: {e}")
                score = 0.0
            
            logger.info("=" * 100)
        
        return True
    except Exception as e:
        logger.error(f"❌ 深度调试失败: {e}")
        return False

def analyze_score_formula():
    """分析score计算公式的合理性"""
    try:
        logger.info("🔬 分析score计算公式的合理性")
        logger.info("=" * 80)
        
        # 分析当前公式: (match_rate * 0.7 + total_score * 0.3)
        logger.info("当前公式: (match_rate * 0.7 + total_score * 0.3)")
        logger.info("其中:")
        logger.info("  match_rate = 匹配关键词数 / 总关键词数")
        logger.info("  total_score = 所有匹配关键词的单词分数总和")
        logger.info("  单词分数 = min(出现次数/内容总词数, 0.3)")
        
        # 分析问题
        logger.info("\n⚠️ 可能的问题:")
        logger.info("1. match_rate权重0.7可能过高，导致整体分数偏低")
        logger.info("2. 单词分数上限0.3可能过低")
        logger.info("3. 没有考虑关键词重要性权重")
        logger.info("4. 没有考虑部分匹配的奖励机制")
        
        # 建议的改进公式
        logger.info("\n💡 建议的改进公式:")
        logger.info("方案1: (match_rate * 0.5 + total_score * 0.5)")
        logger.info("方案2: (match_rate * 0.6 + total_score * 0.4) + 部分匹配奖励")
        logger.info("方案3: 关键词重要性加权 + 基础匹配分数")
        
        return True
    except Exception as e:
        logger.error(f"❌ 公式分析失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始深度调试table_engine的score计算问题")
    
    tests = [
        ("Score计算逐步调试", debug_score_calculation_step_by_step),
        ("Score公式分析", analyze_score_formula),
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
        logger.info("🎉 深度调试完成！")
        logger.info("\n💡 关键发现:")
        logger.info("1. 需要分析实际table文档的score计算过程")
        logger.info("2. 可能需要调整score计算公式")
        logger.info("3. 考虑降低阈值或改进算法")
    else:
        logger.error("⚠️ 部分测试失败，需要进一步分析")
    
    return passed == total

if __name__ == "__main__":
    main()
