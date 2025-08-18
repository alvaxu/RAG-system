#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. Table Engine 第二阶段改进测试脚本
## 2. 测试表格结构理解增强和专用搜索策略重构
## 3. 验证表格类型识别、业务领域识别、质量评分等功能
## 4. 验证新的六层召回策略
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from v2.config.v2_config import V2ConfigManager, TableEngineConfigV2
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

def test_table_structure_analysis():
    """测试表格结构分析功能"""
    print("=" * 60)
    print("🔍 测试表格结构分析功能")
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
                    'columns': ['收入', '支出', '利润'],
                    'table_row_count': 3,
                    'table_column_count': 3,
                    'table_type': 'financial'
                }
            },
            {
                'name': '人事表格',
                'content': '姓名 部门 职位 薪资\n张三 技术部 工程师 8000\n李四 销售部 经理 12000',
                'metadata': {
                    'columns': ['姓名', '部门', '职位', '薪资'],
                    'table_row_count': 3,
                    'table_column_count': 4,
                    'table_type': 'hr'
                }
            },
            {
                'name': '统计表格',
                'content': '月份 销售额 增长率\n1月 10000 0%\n2月 12000 20%',
                'metadata': {
                    'columns': ['月份', '销售额', '增长率'],
                    'table_row_count': 3,
                    'table_column_count': 3,
                    'table_type': 'statistical'
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
            print(f"  数据完整性: {analysis['data_completeness']:.2f}")
            print(f"  质量评分: {analysis['quality_score']:.2f}")
            print(f"  列数: {analysis['column_count']}")
            print(f"  行数: {analysis['row_count']}")
        
        print(f"\n✅ 表格结构分析测试完成")
        
    except Exception as e:
        print(f"❌ 表格结构分析测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_six_layer_recall_strategy():
    """测试六层召回策略"""
    print("\n" + "=" * 60)
    print("🔍 测试六层召回策略")
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
        
        # 检查六层召回策略配置
        if hasattr(table_engine.config, 'recall_strategy'):
            strategy = table_engine.config.recall_strategy
            print("六层召回策略配置:")
            
            layers = [
                'layer1_structure_search',
                'layer2_vector_search',
                'layer3_keyword_search',
                'layer4_hybrid_search',
                'layer5_fuzzy_search',
                'layer6_expansion_search'
            ]
            
            for layer in layers:
                if layer in strategy:
                    layer_config = strategy[layer]
                    enabled = layer_config.get('enabled', False)
                    top_k = layer_config.get('top_k', 0)
                    print(f"  ✅ {layer}: {'启用' if enabled else '禁用'}, top_k: {top_k}")
                else:
                    print(f"  ❌ {layer}: 缺失")
        else:
            print("❌ 召回策略配置缺失")
        
        print(f"\n✅ 六层召回策略测试完成")
        
    except Exception as e:
        print(f"❌ 六层召回策略测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_table_structure_search():
    """测试表格结构搜索功能"""
    print("\n" + "=" * 60)
    print("🔍 测试表格结构搜索功能")
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
                {'columns': ['收入', '支出', '利润'], 'table_row_count': 3, 'table_column_count': 3}
            ),
            MockDocument(
                '姓名 部门 职位 薪资\n张三 技术部 工程师 8000\n李四 销售部 经理 12000',
                {'columns': ['姓名', '部门', '职位', '薪资'], 'table_row_count': 3, 'table_column_count': 4}
            ),
            MockDocument(
                '月份 销售额 增长率\n1月 10000 0%\n2月 12000 20%',
                {'columns': ['月份', '销售额', '增长率'], 'table_row_count': 3, 'table_column_count': 3}
            )
        ]
        
        table_engine.table_docs = test_docs
        table_engine._docs_loaded = True
        
        # 测试不同的查询
        test_queries = [
            '财务',
            '人事',
            '统计',
            '收入',
            '员工',
            '销售额'
        ]
        
        for query in test_queries:
            print(f"\n查询: '{query}'")
            
            try:
                # 执行表格结构搜索
                results = table_engine._table_structure_search(query, 10)
                
                print(f"  找到 {len(results)} 个结果")
                for i, result in enumerate(results[:3]):  # 只显示前3个
                    score = result['score']
                    source = result['source']
                    layer = result['layer']
                    print(f"    结果 {i+1}: 分数={score:.2f}, 来源={source}, 层级={layer}")
                    
                    if 'structure_analysis' in result:
                        analysis = result['structure_analysis']
                        print(f"      表格类型: {analysis['table_type']}")
                        print(f"      业务领域: {analysis['business_domain']}")
                        print(f"      质量评分: {analysis['quality_score']:.2f}")
                
            except Exception as e:
                print(f"  查询失败: {e}")
        
        print(f"\n✅ 表格结构搜索测试完成")
        
    except Exception as e:
        print(f"❌ 表格结构搜索测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 Table Engine 第二阶段改进测试")
    print("测试内容：表格结构理解增强和专用搜索策略重构")
    print("=" * 60)
    
    # 测试表格结构分析功能
    test_table_structure_analysis()
    
    # 测试六层召回策略
    test_six_layer_recall_strategy()
    
    # 测试表格结构搜索功能
    test_table_structure_search()
    
    print("\n" + "=" * 60)
    print("🎉 第二阶段测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
