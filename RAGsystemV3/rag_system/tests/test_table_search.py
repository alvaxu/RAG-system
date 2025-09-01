"""
表格搜索功能测试

测试表格召回引擎的各项功能，包括结构搜索、语义搜索、关键词搜索和扩展搜索
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.retrieval import RetrievalEngine


class MockConfigIntegration:
    """模拟配置集成管理器"""
    
    def __init__(self):
        self.config_data = {
            'rag_system.engines.table_engine': {
                'enabled': True,
                'max_results': 15,
                'similarity_threshold': 0.65,
                'use_semantic_search': True,
                'use_keyword_search': True,
                'use_expansion_search': True
            },
            'rag_system.engines.text_engine': {
                'enabled': True,
                'max_results': 30,
                'similarity_threshold': 0.7,
                'use_keyword_search': True,
                'use_expansion_search': True
            },
            'rag_system.engines.image_engine': {
                'enabled': True,
                'max_results': 20,
                'similarity_threshold': 0.3,
                'use_keyword_search': True,
                'use_expansion_search': True
            }
        }
    
    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config_data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


class MockVectorDBIntegration:
    """模拟向量数据库集成管理器"""
    
    def __init__(self):
        # 模拟表格数据 - 使用字典而不是Mock对象
        self.mock_tables = [
            {
                'chunk_id': 'table_001',
                'content': '财务收入统计表\n月份\t收入\t支出\t利润\n1月\t10000\t8000\t2000\n2月\t12000\t9000\t3000',
                'content_type': 'table',
                'similarity_score': 0.85,
                'metadata': {
                    'chunk_type': 'table',
                    'table_title': '财务收入统计表',
                    'table_headers': ['月份', '收入', '支出', '利润'],
                    'table_type': 'financial',
                    'enhanced_description': '本表记录了公司各月份的财务收支情况，包括收入、支出和利润数据'
                }
            },
            {
                'chunk_id': 'table_002',
                'content': '员工绩效评估表\n员工姓名\t部门\t绩效评分\t评级\n张三\t技术部\t85\tA\n李四\t销售部\t92\tA+',
                'content_type': 'table',
                'similarity_score': 0.78,
                'metadata': {
                    'chunk_type': 'table',
                    'table_title': '员工绩效评估表',
                    'table_headers': ['员工姓名', '部门', '绩效评分', '评级'],
                    'table_type': 'personnel',
                    'enhanced_description': '员工年度绩效评估结果，包含各部门员工的绩效评分和评级信息'
                }
            },
            {
                'chunk_id': 'table_003',
                'content': '库存商品清单\n商品编号\t商品名称\t库存数量\t单价\n001\t笔记本电脑\t50\t5000\n002\t鼠标\t200\t50',
                'content_type': 'table',
                'similarity_score': 0.72,
                'metadata': {
                    'chunk_type': 'table',
                    'table_title': '库存商品清单',
                    'table_headers': ['商品编号', '商品名称', '库存数量', '单价'],
                    'table_type': 'inventory',
                    'enhanced_description': '当前库存商品清单，包含商品编号、名称、库存数量和单价信息'
                }
            }
        ]
    
    def similarity_search(self, query, k=10, filter_dict=None):
        """模拟相似度搜索"""
        # 简单的关键词匹配
        results = []
        for table in self.mock_tables:
            if any(keyword in table['metadata']['table_title'] for keyword in query.split()):
                results.append(table)
        return results[:k]
    
    def search_tables(self, query, max_results, threshold):
        """模拟表格搜索"""
        # 简单的关键词匹配
        results = []
        for table in self.mock_tables:
            if any(keyword in table['metadata']['table_title'] for keyword in query.split()):
                results.append(table)
        return results[:max_results]


def create_test_retrieval_engine():
    """创建测试用的召回引擎实例"""
    mock_config = MockConfigIntegration()
    mock_vector_db = MockVectorDBIntegration()
    return RetrievalEngine(mock_config, mock_vector_db)


class TestTableSearch(unittest.TestCase):
    """表格搜索测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.engine = create_test_retrieval_engine()
    
    def test_table_keyword_extraction(self):
        """测试表格关键词提取"""
        # 测试基础关键词提取
        query1 = "找财务收入统计表格"
        keywords1 = self.engine._extract_table_keywords(query1)
        self.assertIsInstance(keywords1, list)
        self.assertTrue(len(keywords1) > 0)
        
        # 测试专业词汇识别
        query2 = "分析员工绩效数据"
        keywords2 = self.engine._extract_table_keywords(query2)
        self.assertIsInstance(keywords2, list)
        self.assertTrue(len(keywords2) > 0)
        
        # 测试空查询处理
        keywords3 = self.engine._extract_table_keywords("")
        self.assertIsInstance(keywords3, list)
    
    def test_table_structure_search(self):
        """测试表格结构搜索"""
        query = "财务收入统计"
        results = self.engine._table_structure_search(query, max_results=5, threshold=0.5)
        
        self.assertIsInstance(results, list)
        if results:
            result = results[0]
            self.assertIn('strategy', result)
            self.assertEqual(result['strategy'], 'structure_similarity')
            self.assertIn('layer', result)
            self.assertEqual(result['layer'], 1)
    
    def test_table_semantic_search(self):
        """测试表格语义搜索"""
        query = "财务收支情况"
        results = self.engine._table_semantic_search(query, max_results=5, threshold=0.5)
        
        self.assertIsInstance(results, list)
        if results:
            result = results[0]
            self.assertIn('strategy', result)
            self.assertEqual(result['strategy'], 'semantic_similarity')
            self.assertIn('layer', result)
            self.assertEqual(result['layer'], 2)
    
    def test_table_keyword_search(self):
        """测试表格关键词搜索"""
        query = "员工绩效评估"
        results = self.engine._table_keyword_search(query, max_results=5, threshold=0.5)
        
        self.assertIsInstance(results, list)
        if results:
            result = results[0]
            self.assertIn('strategy', result)
            self.assertEqual(result['strategy'], 'keyword_matching')
            self.assertIn('layer', result)
            self.assertEqual(result['layer'], 3)
    
    def test_table_expansion_search(self):
        """测试表格扩展搜索"""
        query = "库存商品信息"
        results = self.engine._table_expansion_search(query, max_results=5, threshold=0.5)
        
        self.assertIsInstance(results, list)
        if results:
            result = results[0]
            self.assertIn('strategy', result)
            self.assertEqual(result['strategy'], 'query_expansion')
            self.assertIn('layer', result)
            self.assertEqual(result['layer'], 4)
    
    def test_table_retrieval_integration(self):
        """测试表格召回集成功能"""
        query = "财务数据表格"
        results = self.engine.retrieve_tables(query, max_results=10)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 10)
        
        # 检查统计信息更新
        stats = self.engine.get_retrieval_stats()
        self.assertIn('table_searches', stats)
        self.assertGreater(stats['table_searches'], 0)
    
    def test_table_expanded_queries(self):
        """测试表格扩展查询生成"""
        query = "财务表格"
        expanded = self.engine._generate_table_expanded_queries(query)
        
        self.assertIsInstance(expanded, list)
        self.assertTrue(len(expanded) > 0)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试空查询
        empty_results = self.engine.retrieve_tables("", max_results=5)
        self.assertEqual(len(empty_results), 0)
        
        # 测试无结果查询
        no_results = self.engine.retrieve_tables("不存在的表格", max_results=5)
        self.assertIsInstance(no_results, list)
        
        # 测试零阈值
        zero_threshold_results = self.engine._table_structure_search("测试", max_results=5, threshold=0.0)
        self.assertIsInstance(zero_threshold_results, list)


def run_table_search_tests():
    """运行表格搜索测试"""
    print("🧪 开始表格搜索功能测试...")
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTableSearch)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果
    if result.wasSuccessful():
        print("✅ 表格搜索功能测试全部通过")
        print(f"📊 测试结果: {result.testsRun} 个测试通过")
    else:
        print("❌ 表格搜索功能测试存在失败")
        print(f"📊 测试结果: {result.testsRun} 个测试，{len(result.failures)} 个失败，{len(result.errors)} 个错误")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_table_search_tests()
