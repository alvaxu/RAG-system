#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. Table Engine 第四阶段增强功能测试脚本
## 2. 测试完善后的中文处理和语义增强功能
## 3. 验证jieba分词配置、关键词提取、停用词过滤等功能
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from v2.config.v2_config import V2ConfigManager
from v2.core.table_engine import TableEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MockDocument:
    """模拟文档对象，用于测试"""
    
    def __init__(self, content, metadata):
        self.page_content = content
        self.metadata = metadata

def test_jieba_configuration():
    """测试jieba分词配置"""
    print("=" * 60)
    print("🔍 测试jieba分词配置")
    print("=" * 60)
    
    try:
        # 创建Table Engine（跳过初始文档加载）
        config_manager = V2ConfigManager()
        config = config_manager.config
        
        if not hasattr(config, 'table_engine'):
            print("❌ 配置中缺少table_engine，跳过测试")
            return
        
        table_engine = TableEngine(
            config=config.table_engine,
            vector_store=None,
            document_loader=None,
            skip_initial_load=True
        )
        
        # 测试自定义词典
        test_texts = [
            '财务报表收入情况分析',
            '员工薪资部门分布统计',
            '产品库存数量管理报表',
            '详细明细汇总统计'
        ]
        
        for text in test_texts:
            print(f"\n测试文本: '{text}'")
            
            # 测试关键词提取
            keywords = table_engine._extract_keywords(text, top_k=10)
            print(f"  提取关键词: {keywords}")
            
            # 测试分词
            tokens = table_engine._tokenize_text(text)
            print(f"  分词结果: {tokens}")
        
        print(f"\n✅ jieba分词配置测试完成")
        
    except Exception as e:
        print(f"❌ jieba分词配置测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_keyword_extraction():
    """测试关键词提取功能"""
    print("\n" + "=" * 60)
    print("🔍 测试关键词提取功能")
    print("=" * 60)
    
    try:
        # 创建Table Engine（跳过初始文档加载）
        config_manager = V2ConfigManager()
        config = config_manager.config
        
        if not hasattr(config, 'table_engine'):
            print("❌ 配置中缺少table_engine，跳过测试")
            return
        
        table_engine = TableEngine(
            config=config.table_engine,
            vector_store=None,
            document_loader=None,
            skip_initial_load=True
        )
        
        # 测试不同类型的文本
        test_cases = [
            {
                'name': '财务文本',
                'text': '本季度财务报表显示收入增长15%，支出控制良好，利润达到预期目标。'
            },
            {
                'name': '人事文本',
                'text': '员工薪资结构合理，部门分布均衡，绩效评估体系完善。'
            },
            {
                'name': '库存文本',
                'text': '产品库存数量充足，库存管理规范，库存周转率良好。'
            },
            {
                'name': '统计文本',
                'text': '销售数据统计显示，各区域增长趋势明显，市场份额稳步提升。'
            }
        ]
        
        for test_case in test_cases:
            print(f"\n测试 {test_case['name']}:")
            text = test_case['text']
            
            # 提取关键词
            keywords = table_engine._extract_keywords(text, top_k=15)
            print(f"  关键词: {keywords}")
            
            # 分词
            tokens = table_engine._tokenize_text(text)
            print(f"  分词: {tokens}")
            
            # 验证停用词过滤
            stop_words_in_tokens = [token for token in tokens if token in ['的', '了', '在', '是', '有', '和', '就', '不', '人', '都', '一', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这']]
            if stop_words_in_tokens:
                print(f"  ⚠️  发现停用词: {stop_words_in_tokens}")
            else:
                print(f"  ✅ 停用词过滤正常")
        
        print(f"\n✅ 关键词提取功能测试完成")
        
    except Exception as e:
        print(f"❌ 关键词提取功能测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_enhanced_search_algorithms():
    """测试增强的搜索算法"""
    print("\n" + "=" * 60)
    print("🔍 测试增强的搜索算法")
    print("=" * 60)
    
    try:
        # 创建Table Engine（跳过初始文档加载）
        config_manager = V2ConfigManager()
        config = config_manager.config
        
        if not hasattr(config, 'table_engine'):
            print("❌ 配置中缺少table_engine，跳过测试")
            return
        
        table_engine = TableEngine(
            config=config.table_engine,
            vector_store=None,
            document_loader=None,
            skip_initial_load=True
        )
        
        # 添加一些测试文档
        test_docs = [
            MockDocument(
                '收入 支出 利润\n1000 800 200\n2000 1500 500',
                {'table_id': 'table1', 'columns': ['收入', '支出', '利润'], 'table_row_count': 3, 'table_column_count': 3, 'original_row_count': 3}
            ),
            MockDocument(
                '姓名 部门 职位 薪资\n张三 技术部 工程师 8000\n李四 销售部 经理 12000',
                {'table_id': 'table2', 'columns': ['姓名', '部门', '职位', '薪资'], 'table_row_count': 2, 'table_column_count': 4, 'original_row_count': 2}
            ),
            MockDocument(
                '产品 价格 库存\n产品A 100 50\n产品B 200 30',
                {'table_id': 'table3', 'columns': ['产品', '价格', '库存'], 'table_row_count': 2, 'table_column_count': 3, 'original_row_count': 2}
            )
        ]
        
        table_engine.table_docs = test_docs
        table_engine._docs_loaded = True
        
        # 测试不同的查询
        test_queries = [
            '财务报表收入情况',
            '员工薪资部门分布',
            '产品库存数量统计'
        ]
        
        for query in test_queries:
            print(f"\n查询: '{query}'")
            
            # 测试关键词搜索
            keyword_results = table_engine._keyword_search(query, 10)
            print(f"  关键词搜索结果: {len(keyword_results)} 个")
            if keyword_results:
                print(f"  最高分数: {keyword_results[0]['score']:.2f}")
            
            # 测试模糊搜索
            fuzzy_results = table_engine._fuzzy_search(query, 10)
            print(f"  模糊搜索结果: {len(fuzzy_results)} 个")
            if fuzzy_results:
                print(f"  最高分数: {fuzzy_results[0]['score']:.2f}")
        
        print(f"\n✅ 增强的搜索算法测试完成")
        
    except Exception as e:
        print(f"❌ 增强的搜索算法测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_intent_analysis_enhancement():
    """测试增强的意图分析功能"""
    print("\n" + "=" * 60)
    print("🔍 测试增强的意图分析功能")
    print("=" * 60)
    
    try:
        # 创建Table Engine（跳过初始文档加载）
        config_manager = V2ConfigManager()
        config = config_manager.config
        
        if not hasattr(config, 'table_engine'):
            print("❌ 配置中缺少table_engine，跳过测试")
            return
        
        table_engine = TableEngine(
            config=config.table_engine,
            vector_store=None,
            document_loader=None,
            skip_initial_load=True
        )
        
        # 测试复杂的查询意图
        test_queries = [
            {
                'query': '财务报表收入情况详细分析',
                'expected_intent': 'detail_view',
                'expected_type': 'financial'
            },
            {
                'query': '员工薪资部门分布汇总统计',
                'expected_intent': 'summary',
                'expected_type': 'hr'
            },
            {
                'query': '产品库存数量管理对比分析',
                'expected_intent': 'comparison',
                'expected_type': 'inventory'
            }
        ]
        
        for test_case in test_queries:
            query = test_case['query']
            print(f"\n测试查询: '{query}'")
            
            # 分析查询意图
            intent_analysis = table_engine._analyze_query_intent(query)
            
            print(f"  主要意图: {intent_analysis['primary_intent']} (预期: {test_case['expected_intent']})")
            print(f"  目标类型: {intent_analysis['target_type']} (预期: {test_case['expected_type']})")
            print(f"  目标领域: {intent_analysis['target_domain']}")
            print(f"  目标用途: {intent_analysis['target_purpose']}")
            print(f"  特定关键词: {intent_analysis['specific_keywords']}")
            print(f"  是否需要完整表格: {intent_analysis['requires_full_table']}")
            
            # 验证意图识别准确性
            intent_correct = intent_analysis['primary_intent'] == test_case['expected_intent']
            type_correct = intent_analysis['target_type'] == test_case['expected_type']
            
            if intent_correct and type_correct:
                print(f"  ✅ 意图识别完全正确")
            elif intent_correct or type_correct:
                print(f"  ⚠️  意图识别部分正确")
            else:
                print(f"  ❌ 意图识别不正确")
        
        print(f"\n✅ 增强的意图分析功能测试完成")
        
    except Exception as e:
        print(f"❌ 增强的意图分析功能测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 Table Engine 第四阶段增强功能测试")
    print("测试内容：完善后的中文处理和语义增强功能")
    print("=" * 60)
    
    # 测试jieba分词配置
    test_jieba_configuration()
    
    # 测试关键词提取功能
    test_keyword_extraction()
    
    # 测试增强的搜索算法
    test_enhanced_search_algorithms()
    
    # 测试增强的意图分析功能
    test_intent_analysis_enhancement()
    
    print("\n" + "=" * 60)
    print("🎉 第四阶段增强功能测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
