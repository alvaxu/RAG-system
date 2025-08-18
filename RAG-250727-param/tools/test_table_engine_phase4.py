#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. Table Engine 第四阶段改进测试脚本
## 2. 测试中文处理和语义增强功能
## 3. 验证中文分词、表格语义理解和复杂查询意图识别
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

class MockDocumentLoader:
    """模拟文档加载器，用于测试"""
    
    def __init__(self, full_docs):
        self.full_docs = full_docs
    
    def get_full_document_by_id(self, doc_id, chunk_type=None):
        return self.full_docs.get(doc_id)

class MockVectorStore:
    """模拟向量存储，用于测试"""
    
    def __init__(self, full_docs):
        self.full_docs = full_docs
    
    def get_full_document_by_id(self, doc_id):
        return self.full_docs.get(doc_id)

def test_chinese_tokenization():
    """测试中文分词功能"""
    print("=" * 60)
    print("🔍 测试中文分词功能")
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
        
        # 测试中文分词
        test_queries = [
            '财务报表收入情况',
            '员工薪资部门分布',
            '产品库存数量统计'
        ]
        
        for query in test_queries:
            print(f"\n测试查询: '{query}'")
            
            # 由于无法直接访问内部方法，我们通过日志或间接方法验证
            # 这里我们假设关键词搜索会使用分词结果
            results = table_engine._keyword_search(query, 10)
            print(f"  关键词搜索结果数量: {len(results)}")
            
            # 间接验证分词效果
            if results:
                print(f"  结果示例: {results[0]['score']:.2f} 分")
            else:
                print("  无结果，可能是因为没有文档")
        
        print(f"\n✅ 中文分词测试完成")
        
    except Exception as e:
        print(f"❌ 中文分词测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_semantic_understanding():
    """测试表格语义理解功能"""
    print("\n" + "=" * 60)
    print("🔍 测试表格语义理解功能")
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
        
        # 测试不同类型的表格
        test_cases = [
            {
                'name': '财务表格',
                'content': '收入 支出 利润\n1000 800 200\n2000 1500 500',
                'metadata': {
                    'table_id': 'table1',
                    'columns': ['收入', '支出', '利润'],
                    'table_row_count': 3,
                    'table_column_count': 3,
                    'original_row_count': 3
                }
            },
            {
                'name': '人事表格',
                'content': '姓名 部门 职位 薪资\n张三 技术部 工程师 8000\n李四 销售部 经理 12000',
                'metadata': {
                    'table_id': 'table2',
                    'columns': ['姓名', '部门', '职位', '薪资'],
                    'table_row_count': 2,
                    'table_column_count': 4,
                    'original_row_count': 2
                }
            },
            {
                'name': '库存表格',
                'content': '产品 价格 库存\n产品A 100 50\n产品B 200 30',
                'metadata': {
                    'table_id': 'table3',
                    'columns': ['产品', '价格', '库存'],
                    'table_row_count': 2,
                    'table_column_count': 3,
                    'original_row_count': 2
                }
            },
            {
                'name': '统计表格',
                'content': '月份 销售额 增长率\n1月 10000 0%\n2月 12000 20%',
                'metadata': {
                    'table_id': 'table4',
                    'columns': ['月份', '销售额', '增长率'],
                    'table_row_count': 2,
                    'table_column_count': 3,
                    'original_row_count': 2
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n测试 {test_case['name']}:")
            
            # 创建模拟文档
            mock_doc = MockDocument(test_case['content'], test_case['metadata'])
            
            # 分析表格结构
            analysis = table_engine._analyze_table_structure(mock_doc)
            
            print(f"  表格类型: {analysis['table_type']}")
            print(f"  业务领域: {analysis['business_domain']}")
            print(f"  主要用途: {analysis['primary_purpose']}")
            print(f"  质量评分: {analysis['quality_score']:.2f}")
        
        print(f"\n✅ 表格语义理解测试完成")
        
    except Exception as e:
        print(f"❌ 表格语义理解测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_query_intent_analysis():
    """测试复杂查询意图识别功能"""
    print("\n" + "=" * 60)
    print("🔍 测试复杂查询意图识别功能")
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
        
        # 测试不同类型的查询意图
        test_queries = [
            {
                'query': '财务报表收入情况',
                'expected_intent': 'search',
                'expected_type': 'financial',
                'expected_domain': 'finance'
            },
            {
                'query': '员工薪资详细明细',
                'expected_intent': 'detail_view',
                'expected_type': 'hr',
                'expected_domain': 'general'
            },
            {
                'query': '产品库存汇总统计',
                'expected_intent': 'summary',
                'expected_type': 'inventory',
                'expected_domain': 'manufacturing'
            },
            {
                'query': '销售额对比去年',
                'expected_intent': 'comparison',
                'expected_type': 'financial',
                'expected_domain': 'retail'
            }
        ]
        
        for test_case in test_queries:
            query = test_case['query']
            print(f"\n测试查询: '{query}'")
            
            # 分析查询意图
            intent_analysis = table_engine._analyze_query_intent(query)
            
            print(f"  主要意图: {intent_analysis['primary_intent']} (预期: {test_case['expected_intent']})")
            print(f"  目标类型: {intent_analysis['target_type']} (预期: {test_case['expected_type']})")
            print(f"  目标领域: {intent_analysis['target_domain']} (预期: {test_case['expected_domain']})")
            print(f"  目标用途: {intent_analysis['target_purpose']}")
            print(f"  特定关键词: {intent_analysis['specific_keywords']}")
            print(f"  是否需要完整表格: {intent_analysis['requires_full_table']}")
        
        print(f"\n✅ 复杂查询意图识别测试完成")
        
    except Exception as e:
        print(f"❌ 复杂查询意图识别测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_intent_based_results_adjustment():
    """测试基于意图的结果调整功能"""
    print("\n" + "=" * 60)
    print("🔍 测试基于意图的结果调整功能")
    print("=" * 60)
    
    try:
        # 创建模拟的完整文档
        full_docs = {
            'table1': MockDocument(
                '收入 支出 利润\n1000 800 200\n2000 1500 500\n完整内容...',
                {'table_id': 'table1', 'document_name': '财务报告.pdf', 'page_number': 5}
            )
        }
        
        # 创建Table Engine，使用模拟的文档加载器和向量存储
        config_manager = V2ConfigManager()
        config = config_manager.config
        
        if not hasattr(config, 'table_engine'):
            print("❌ 配置中缺少table_engine，跳过测试")
            return
        
        document_loader = MockDocumentLoader(full_docs)
        vector_store = MockVectorStore(full_docs)
        
        table_engine = TableEngine(
            config=config.table_engine,
            vector_store=vector_store,
            document_loader=document_loader,
            skip_initial_load=True
        )
        
        # 添加一些测试文档
        test_docs = [
            MockDocument(
                '收入 支出 利润\n1000 800 200\n2000 1500 500',
                {'table_id': 'table1', 'columns': ['收入', '支出', '利润'], 'table_row_count': 3, 'table_column_count': 3, 'original_row_count': 3}
            )
        ]
        
        table_engine.table_docs = test_docs
        table_engine._docs_loaded = True
        
        # 测试不同意图的查询
        test_queries = [
            {
                'query': '财务报表收入情况',
                'expected_full_content': False
            },
            {
                'query': '财务报表完整详情',
                'expected_full_content': True
            }
        ]
        
        for test_case in test_queries:
            query = test_case['query']
            print(f"\n测试查询: '{query}'")
            
            # 处理查询
            result = table_engine.process_query(query)
            
            print(f"  状态: {result['status']}")
            print(f"  结果数量: {result['total_results']}")
            
            if result['status'] == 'success' and result['results']:
                top_result = result['results'][0]
                has_full_content = 'full_content' in top_result
                print(f"  是否包含完整内容: {has_full_content} (预期: {test_case['expected_full_content']})")
                if has_full_content:
                    print(f"  完整内容长度: {len(top_result['full_content'])}")
            else:
                print(f"  无结果或查询失败")
        
        print(f"\n✅ 基于意图的结果调整测试完成")
        
    except Exception as e:
        print(f"❌ 基于意图的结果调整测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 Table Engine 第四阶段改进测试")
    print("测试内容：中文处理和语义增强功能")
    print("=" * 60)
    
    # 测试中文分词功能
    test_chinese_tokenization()
    
    # 测试表格语义理解功能
    test_semantic_understanding()
    
    # 测试复杂查询意图识别功能
    test_query_intent_analysis()
    
    # 测试基于意图的结果调整功能
    test_intent_based_results_adjustment()
    
    print("\n" + "=" * 60)
    print("🎉 第四阶段测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
