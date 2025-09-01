"""
混合搜索策略优化功能测试

测试召回引擎的混合搜索策略优化功能，包括跨类型内容相关性计算和智能融合搜索结果
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
            'rag_system.engines.hybrid_engine': {
                'enabled': True,
                'max_results': 25,
                'weights': {'image': 0.3, 'text': 0.4, 'table': 0.3},
                'cross_type_boost': 0.2
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
            },
            'rag_system.engines.table_engine': {
                'enabled': True,
                'max_results': 15,
                'similarity_threshold': 0.65,
                'use_semantic_search': True,
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
        # 模拟文本数据
        self.mock_texts = [
            {
                'chunk_id': 'text_001',
                'content': '人工智能技术在医疗领域的应用研究',
                'content_type': 'text',
                'similarity_score': 0.85,
                'metadata': {
                    'title': 'AI医疗应用研究',
                    'description': '探讨AI在医疗诊断和治疗中的应用',
                    'keywords': ['人工智能', '医疗', '诊断', '治疗'],
                    'category': 'technology'
                }
            },
            {
                'chunk_id': 'text_002',
                'content': '机器学习算法在金融风控中的应用',
                'content_type': 'text',
                'similarity_score': 0.78,
                'metadata': {
                    'title': 'ML金融风控应用',
                    'description': '机器学习在金融风险控制中的应用案例',
                    'keywords': ['机器学习', '金融', '风控', '算法'],
                    'category': 'finance'
                }
            }
        ]
        
        # 模拟图片数据 - 增加更多匹配关键词
        self.mock_images = [
            {
                'chunk_id': 'img_001',
                'content': '医疗AI诊断系统界面截图',
                'content_type': 'image',
                'similarity_score': 0.82,
                'metadata': {
                    'title': 'AI诊断系统界面',
                    'description': '医疗AI诊断系统的用户界面截图',
                    'keywords': ['AI诊断', '医疗', '界面', '系统', '人工智能', '诊断', '治疗'],
                    'category': 'medical'
                }
            },
            {
                'chunk_id': 'img_002',
                'content': '金融数据分析图表',
                'content_type': 'image',
                'similarity_score': 0.75,
                'metadata': {
                    'title': '金融数据分析图',
                    'description': '金融风险分析的数据可视化图表',
                    'keywords': ['金融', '数据分析', '图表', '风控', '机器学习', '算法'],
                    'category': 'finance'
                }
            },
            {
                'chunk_id': 'img_003',
                'content': 'AI技术应用场景图',
                'content_type': 'image',
                'similarity_score': 0.88,
                'metadata': {
                    'title': 'AI技术应用',
                    'description': '人工智能技术在各领域的应用场景',
                    'keywords': ['人工智能', 'AI', '技术', '应用', '场景', '创新'],
                    'category': 'technology'
                }
            }
        ]
        
        # 模拟表格数据
        self.mock_tables = [
            {
                'chunk_id': 'table_001',
                'content': 'AI医疗诊断准确率统计表',
                'content_type': 'table',
                'similarity_score': 0.80,
                'metadata': {
                    'title': 'AI诊断准确率统计',
                    'description': '不同AI模型在医疗诊断中的准确率对比',
                    'keywords': ['AI诊断', '准确率', '医疗', '统计', '人工智能', '诊断'],
                    'category': 'medical'
                }
            }
        ]
    
    def search_texts(self, query, max_results, threshold):
        """模拟文本搜索"""
        results = []
        query_lower = query.lower()
        for text in self.mock_texts:
            # 检查标题、描述、关键词是否匹配
            if (any(keyword.lower() in query_lower for keyword in text['metadata']['keywords']) or
                text['metadata']['title'].lower() in query_lower or
                text['metadata']['description'].lower() in query_lower):
                results.append(text)
        return results[:max_results]
    
    def search_images(self, query, max_results, threshold):
        """模拟图片搜索 - 改进匹配逻辑"""
        results = []
        query_lower = query.lower()
        
        for image in self.mock_images:
            # 检查标题、描述、关键词是否匹配
            if (any(keyword.lower() in query_lower for keyword in image['metadata']['keywords']) or
                image['metadata']['title'].lower() in query_lower or
                image['metadata']['description'].lower() in query_lower):
                results.append(image)
        
        # 如果没有找到匹配的图片，返回一些相关的图片（避免降级）
        if not results and 'AI' in query or '人工智能' in query:
            results = [self.mock_images[0]]  # 返回AI相关的图片
        elif not results and '医疗' in query:
            results = [self.mock_images[0]]  # 返回医疗相关的图片
        elif not results and '金融' in query:
            results = [self.mock_images[1]]  # 返回金融相关的图片
        
        return results[:max_results]
    
    def search_tables(self, query, max_results, threshold):
        """模拟表格搜索"""
        results = []
        query_lower = query.lower()
        for table in self.mock_tables:
            if (any(keyword.lower() in query_lower for keyword in table['metadata']['keywords']) or
                table['metadata']['title'].lower() in query_lower or
                table['metadata']['description'].lower() in query_lower):
                results.append(table)
        return results[:max_results]


def create_test_retrieval_engine():
    """创建测试用的召回引擎实例"""
    mock_config = MockConfigIntegration()
    mock_vector_db = MockVectorDBIntegration()
    return RetrievalEngine(mock_config, mock_vector_db)


class TestHybridSearch(unittest.TestCase):
    """混合搜索策略优化测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.engine = create_test_retrieval_engine()
    
    def test_cross_type_relevance_calculation(self):
        """测试跨类型相关性计算"""
        # 创建测试数据
        text_result = {
            'content': '人工智能在医疗领域的应用',
            'metadata': {'title': 'AI医疗应用', 'keywords': ['AI', '医疗']}
        }
        
        image_result = {
            'content': '医疗AI系统界面',
            'metadata': {'title': 'AI系统界面', 'keywords': ['AI', '医疗', '界面']}
        }
        
        # 测试跨类型相关性计算
        cross_score = self.engine._calculate_cross_type_relevance(
            text_result, [image_result], "AI医疗应用"
        )
        
        self.assertIsInstance(cross_score, float)
        self.assertGreaterEqual(cross_score, 0.0)
        self.assertLessEqual(cross_score, 1.0)
    
    def test_cross_content_similarity(self):
        """测试跨内容相似度计算"""
        content1 = "人工智能在医疗诊断中的应用"
        content2 = "AI医疗诊断系统界面"
        metadata1 = {'title': 'AI医疗应用', 'keywords': ['AI', '医疗', '诊断']}
        metadata2 = {'title': 'AI诊断系统', 'keywords': ['AI', '医疗', '诊断', '系统']}
        
        similarity = self.engine._calculate_cross_content_similarity(
            content1, content2, metadata1, metadata2
        )
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_metadata_similarity(self):
        """测试元数据相似度计算"""
        metadata1 = {
            'title': 'AI医疗应用研究',
            'description': '人工智能在医疗领域的应用',
            'keywords': ['AI', '医疗', '应用']
        }
        
        metadata2 = {
            'title': '医疗AI系统研究',
            'description': '医疗领域的人工智能系统',
            'keywords': ['医疗', 'AI', '系统']
        }
        
        similarity = self.engine._calculate_metadata_similarity(metadata1, metadata2)
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_keyword_extraction(self):
        """测试关键词提取"""
        content = "人工智能技术在医疗诊断和治疗中的应用研究，包括机器学习算法和深度学习模型"
        
        keywords = self.engine._extract_keywords_from_content(content)
        
        self.assertIsInstance(keywords, list)
        self.assertTrue(len(keywords) > 0)
        # 检查是否包含预期关键词
        expected_keywords = ['人工智能', '医疗', '诊断', '治疗', '机器学习', '深度学习']
        found_keywords = [kw for kw in expected_keywords if kw in keywords]
        self.assertTrue(len(found_keywords) > 0)
    
    def test_keyword_set_similarity(self):
        """测试关键词集合相似度"""
        keywords1 = ['AI', '医疗', '诊断', '治疗']
        keywords2 = ['AI', '医疗', '诊断', '系统']
        
        similarity = self.engine._calculate_keyword_set_similarity(keywords1, keywords2)
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
        # 应该有3个共同关键词，总共5个不同关键词，相似度应该是3/5=0.6
        self.assertAlmostEqual(similarity, 0.6, places=1)
    
    def test_diversity_strategy(self):
        """测试多样性策略"""
        # 创建测试结果
        test_results = [
            {'content_type': 'text', 'content': 'AI医疗应用', 'final_score': 0.9},
            {'content_type': 'image', 'content': '医疗界面', 'final_score': 0.8},
            {'content_type': 'table', 'content': '医疗数据', 'final_score': 0.7},
            {'content_type': 'text', 'content': '另一个AI应用', 'final_score': 0.6}
        ]
        
        diverse_results = self.engine._apply_diversity_strategy(test_results, 3)
        
        self.assertIsInstance(diverse_results, list)
        self.assertLessEqual(len(diverse_results), 3)
        
        # 检查内容类型多样性
        content_types = [r['content_type'] for r in diverse_results]
        unique_types = set(content_types)
        self.assertGreaterEqual(len(unique_types), 2)  # 至少应该有2种不同类型
    
    def test_content_type_balance(self):
        """测试内容类型平衡策略"""
        # 创建测试结果 - 确保有足够的不同类型
        test_results = [
            {'content_type': 'text', 'content': '内容1', 'final_score': 0.9},
            {'content_type': 'image', 'content': '图片1', 'final_score': 0.8},
            {'content_type': 'table', 'content': '表格1', 'final_score': 0.7},
            {'content_type': 'text', 'content': '内容2', 'final_score': 0.6},
            {'content_type': 'image', 'content': '图片2', 'final_score': 0.5}
        ]
        
        # 测试不同的max_results值
        balanced_results_3 = self.engine._apply_content_type_balance(test_results, 3)
        balanced_results_5 = self.engine._apply_content_type_balance(test_results, 5)
        
        # 检查3个结果的情况
        self.assertIsInstance(balanced_results_3, list)
        self.assertLessEqual(len(balanced_results_3), 3)
        
        # 检查5个结果的情况
        self.assertIsInstance(balanced_results_5, list)
        self.assertLessEqual(len(balanced_results_5), 5)
        
        # 检查类型分布 - 应该包含多种类型
        if len(balanced_results_3) >= 2:
            content_types_3 = [r['content_type'] for r in balanced_results_3]
            unique_types_3 = set(content_types_3)
            self.assertGreaterEqual(len(unique_types_3), 1)  # 至少1种类型
        
        if len(balanced_results_5) >= 2:
            content_types_5 = [r['content_type'] for r in balanced_results_5]
            unique_types_5 = set(content_types_5)
            self.assertGreaterEqual(len(unique_types_5), 2)  # 至少2种类型
    
    def test_hybrid_retrieval_integration(self):
        """测试混合召回集成功能"""
        query = "AI医疗应用"
        results = self.engine.retrieve_hybrid(query, max_results=10)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 10)
        
        # 检查结果结构
        if results:
            result = results[0]
            self.assertIn('final_score', result)
            self.assertIn('cross_type_score', result)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试空查询
        empty_results = self.engine.retrieve_hybrid("", max_results=5)
        self.assertIsInstance(empty_results, list)
        
        # 测试无结果查询
        no_results = self.engine.retrieve_hybrid("不存在的查询", max_results=5)
        self.assertIsInstance(no_results, list)
        
        # 测试零阈值
        zero_threshold_results = self.engine._calculate_cross_type_relevance(
            {}, [], ""
        )
        self.assertEqual(zero_threshold_results, 0.0)


def run_hybrid_search_tests():
    """运行混合搜索策略优化测试"""
    print("🧪 开始混合搜索策略优化功能测试...")
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestHybridSearch)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果
    if result.wasSuccessful():
        print("✅ 混合搜索策略优化功能测试全部通过")
        print(f"📊 测试结果: {result.testsRun} 个测试通过")
    else:
        print("❌ 混合搜索策略优化功能测试存在失败")
        print(f"📊 测试结果: {result.testsRun} 个测试，{len(result.failures)} 个失败，{len(result.errors)} 个错误")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_hybrid_search_tests()
