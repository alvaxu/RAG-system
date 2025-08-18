#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. Table Engine 第三阶段改进测试脚本
## 2. 测试智能截断处理功能
## 3. 验证截断感知搜索、截断信息元数据增强和查看完整表格功能
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

def test_truncation_detection():
    """测试截断检测功能"""
    print("=" * 60)
    print("🔍 测试截断检测功能")
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
        
        # 测试不同类型的截断表格
        test_cases = [
            {
                'name': '未截断表格',
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
                'name': '行截断表格',
                'content': '姓名 部门 职位 薪资\n张三 技术部 工程师 8000\n[表格数据行已截断处理]',
                'metadata': {
                    'table_id': 'table2',
                    'columns': ['姓名', '部门', '职位', '薪资'],
                    'table_row_count': 2,
                    'table_column_count': 4,
                    'original_row_count': 10
                }
            },
            {
                'name': '内容截断表格',
                'content': '月份 销售额 增长率\n1月 10000 0%\n[表格内容已截断处理]',
                'metadata': {
                    'table_id': 'table3',
                    'columns': ['月份', '销售额', '增长率'],
                    'table_row_count': 2,
                    'table_column_count': 3,
                    'original_row_count': 5
                }
            },
            {
                'name': '格式优化表格',
                'content': '产品 价格 库存\n产品A 100 50\n[表格格式已优化]',
                'metadata': {
                    'table_id': 'table4',
                    'columns': ['产品', '价格', '库存'],
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
            print(f"  是否截断: {analysis['is_truncated']}")
            print(f"  截断类型: {analysis['truncation_type']}")
            print(f"  截断行数: {analysis['truncated_rows']}")
            print(f"  当前行数: {analysis['row_count']}")
            print(f"  原始行数: {analysis['original_row_count']}")
            print(f"  质量评分: {analysis['quality_score']:.2f}")
        
        print(f"\n✅ 截断检测测试完成")
        
    except Exception as e:
        print(f"❌ 截断检测测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_truncation_aware_search():
    """测试截断感知搜索功能"""
    print("\n" + "=" * 60)
    print("🔍 测试截断感知搜索功能")
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
                '姓名 部门 职位 薪资\n张三 技术部 工程师 8000\n[表格数据行已截断处理]',
                {'table_id': 'table2', 'columns': ['姓名', '部门', '职位', '薪资'], 'table_row_count': 2, 'table_column_count': 4, 'original_row_count': 10}
            ),
            MockDocument(
                '月份 销售额 增长率\n1月 10000 0%\n[表格内容已截断处理]',
                {'table_id': 'table3', 'columns': ['月份', '销售额', '增长率'], 'table_row_count': 2, 'table_column_count': 3, 'original_row_count': 5}
            )
        ]
        
        table_engine.table_docs = test_docs
        table_engine._docs_loaded = True
        
        # 测试不同的查询
        test_queries = [
            '收入',
            '姓名',
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
                        print(f"      是否截断: {analysis['is_truncated']}")
                        print(f"      截断类型: {analysis['truncation_type']}")
                        print(f"      截断行数: {analysis['truncated_rows']}")
                
            except Exception as e:
                print(f"  查询失败: {e}")
        
        print(f"\n✅ 截断感知搜索测试完成")
        
    except Exception as e:
        print(f"❌ 截断感知搜索测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_full_table_retrieval():
    """测试查看完整表格功能"""
    print("\n" + "=" * 60)
    print("🔍 测试查看完整表格功能")
    print("=" * 60)
    
    try:
        # 创建模拟的完整文档
        full_docs = {
            'table1': MockDocument(
                '收入 支出 利润\n1000 800 200\n2000 1500 500',
                {'table_id': 'table1', 'document_name': '财务报告.pdf', 'page_number': 5}
            ),
            'table2': MockDocument(
                '姓名 部门 职位 薪资\n张三 技术部 工程师 8000\n李四 销售部 经理 12000\n王五 市场部 专员 6000\n赵六 财务部 会计 7000\n...（共10行）',
                {'table_id': 'table2', 'document_name': '员工名单.pdf', 'page_number': 3}
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
        
        # 测试获取完整表格
        test_table_ids = ['table1', 'table2', 'table3']
        
        for table_id in test_table_ids:
            print(f"\n获取完整表格: '{table_id}'")
            
            try:
                # 获取完整表格内容
                result = table_engine.get_full_table(table_id)
                
                print(f"  状态: {result['status']}")
                print(f"  表格ID: {result['table_id']}")
                if result['status'] == 'success':
                    print(f"  内容长度: {len(result['content'])}")
                    print(f"  文档名称: {result['metadata'].get('document_name', '未知')}")
                    print(f"  页码: {result['metadata'].get('page_number', '未知')}")
                else:
                    print(f"  错误信息: {result['message']}")
                
            except Exception as e:
                print(f"  获取失败: {e}")
        
        print(f"\n✅ 查看完整表格功能测试完成")
        
    except Exception as e:
        print(f"❌ 查看完整表格功能测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_truncation_metadata_in_results():
    """测试查询结果中的截断元数据"""
    print("\n" + "=" * 60)
    print("🔍 测试查询结果中的截断元数据")
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
                '姓名 部门 职位 薪资\n张三 技术部 工程师 8000\n[表格数据行已截断处理]',
                {'table_id': 'table2', 'columns': ['姓名', '部门', '职位', '薪资'], 'table_row_count': 2, 'table_column_count': 4, 'original_row_count': 10}
            ),
            MockDocument(
                '月份 销售额 增长率\n1月 10000 0%\n[表格内容已截断处理]',
                {'table_id': 'table3', 'columns': ['月份', '销售额', '增长率'], 'table_row_count': 2, 'table_column_count': 3, 'original_row_count': 5}
            )
        ]
        
        table_engine.table_docs = test_docs
        table_engine._docs_loaded = True
        
        # 执行查询
        query = '收入'
        print(f"\n查询: '{query}'")
        
        try:
            # 处理查询
            result = table_engine.process_query(query)
            
            print(f"  状态: {result['status']}")
            print(f"  结果数量: {result['total_results']}")
            
            if result['status'] == 'success':
                for i, res in enumerate(result['results'][:3]):  # 只显示前3个
                    print(f"    结果 {i+1}: ID={res['id']}, 分数={res['score']:.2f}")
                    metadata = res['metadata']
                    print(f"      文档名称: {metadata['document_name']}")
                    print(f"      页码: {metadata['page_number']}")
                    print(f"      表格类型: {metadata['table_type']}")
                    print(f"      是否截断: {metadata['is_truncated']}")
                    print(f"      截断类型: {metadata['truncation_type']}")
                    print(f"      截断行数: {metadata['truncated_rows']}")
                    print(f"      当前行数: {metadata['current_rows']}")
                    print(f"      原始行数: {metadata['original_rows']}")
            else:
                print(f"  错误信息: {result['message']}")
            
        except Exception as e:
            print(f"  查询失败: {e}")
        
        print(f"\n✅ 查询结果中的截断元数据测试完成")
        
    except Exception as e:
        print(f"❌ 查询结果中的截断元数据测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 Table Engine 第三阶段改进测试")
    print("测试内容：智能截断处理功能")
    print("=" * 60)
    
    # 测试截断检测功能
    test_truncation_detection()
    
    # 测试截断感知搜索功能
    test_truncation_aware_search()
    
    # 测试查看完整表格功能
    test_full_table_retrieval()
    
    # 测试查询结果中的截断元数据
    test_truncation_metadata_in_results()
    
    print("\n" + "=" * 60)
    print("🎉 第三阶段测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
