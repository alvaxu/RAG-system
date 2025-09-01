"""
测试QueryProcessor构造函数参数修复

验证修复后的QueryProcessor能够正确接受所有服务参数
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rag_system.core.query_processor import QueryProcessor
from rag_system.core.config_integration import ConfigIntegration


class TestQueryProcessorConstructor(unittest.TestCase):
    """测试QueryProcessor构造函数参数修复"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟的配置集成管理器
        self.mock_config = Mock(spec=ConfigIntegration)
        self.mock_config.get_rag_config.return_value = {}
        self.mock_config.config_manager = Mock()
        
        # 创建模拟的服务实例
        self.mock_retrieval_engine = Mock()
        self.mock_llm_caller = Mock()
        self.mock_reranking_service = Mock()
        self.mock_attribution_service = Mock()
        self.mock_display_service = Mock()
        self.mock_metadata_manager = Mock()
        
        # 模拟查询路由器
        self.mock_query_router = Mock()
        self.mock_query_router.get_service_status.return_value = {'status': 'ready'}
        
        # 使用patch装饰器来模拟SimpleQueryRouter
        self.mock_router_patcher = unittest.mock.patch('rag_system.core.query_processor.SimpleQueryRouter')
        self.mock_router_class = self.mock_router_patcher.start()
        self.mock_router_class.return_value = self.mock_query_router
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'mock_router_patcher'):
            self.mock_router_patcher.stop()
    
    def test_constructor_with_minimal_params(self):
        """测试最小参数构造函数"""
        try:
            processor = QueryProcessor(self.mock_config)
            self.assertIsNotNone(processor)
            self.assertEqual(processor.config, self.mock_config)
            self.assertIsNone(processor.retrieval_engine)
            self.assertIsNone(processor.llm_caller)
            print("✅ 最小参数构造函数测试通过")
        except Exception as e:
            self.fail(f"最小参数构造函数测试失败: {e}")
    
    def test_constructor_with_all_services(self):
        """测试包含所有服务的构造函数"""
        try:
            processor = QueryProcessor(
                config_integration=self.mock_config,
                retrieval_engine=self.mock_retrieval_engine,
                llm_caller=self.mock_llm_caller,
                reranking_service=self.mock_reranking_service,
                attribution_service=self.mock_attribution_service,
                display_service=self.mock_display_service,
                metadata_manager=self.mock_metadata_manager
            )
            
            # 验证所有服务都被正确存储
            self.assertEqual(processor.retrieval_engine, self.mock_retrieval_engine)
            self.assertEqual(processor.llm_caller, self.mock_llm_caller)
            self.assertEqual(processor.reranking_service, self.mock_reranking_service)
            self.assertEqual(processor.attribution_service, self.mock_attribution_service)
            self.assertEqual(processor.display_service, self.mock_display_service)
            self.assertEqual(processor.metadata_manager, self.mock_metadata_manager)
            
            print("✅ 完整服务参数构造函数测试通过")
        except Exception as e:
            self.fail(f"完整服务参数构造函数测试失败: {e}")
    
    def test_constructor_with_partial_services(self):
        """测试部分服务参数的构造函数"""
        try:
            processor = QueryProcessor(
                config_integration=self.mock_config,
                retrieval_engine=self.mock_retrieval_engine,
                llm_caller=self.mock_llm_caller
            )
            
            # 验证提供的服务被正确存储
            self.assertEqual(processor.retrieval_engine, self.mock_retrieval_engine)
            self.assertEqual(processor.llm_caller, self.mock_llm_caller)
            
            # 验证未提供的服务为None
            self.assertIsNone(processor.reranking_service)
            self.assertIsNone(processor.attribution_service)
            self.assertIsNone(processor.display_service)
            self.assertIsNone(processor.metadata_manager)
            
            print("✅ 部分服务参数构造函数测试通过")
        except Exception as e:
            self.fail(f"部分服务参数构造函数测试失败: {e}")
    
    def test_service_access_methods(self):
        """测试服务访问方法"""
        processor = QueryProcessor(
            config_integration=self.mock_config,
            retrieval_engine=self.mock_retrieval_engine,
            llm_caller=self.mock_llm_caller
        )
        
        # 测试get_service_instance方法
        self.assertEqual(processor.get_service_instance('retrieval_engine'), self.mock_retrieval_engine)
        self.assertEqual(processor.get_service_instance('llm_caller'), self.mock_llm_caller)
        self.assertIsNone(processor.get_service_instance('reranking_service'))
        
        # 测试has_service方法
        self.assertTrue(processor.has_service('retrieval_engine'))
        self.assertTrue(processor.has_service('llm_caller'))
        self.assertFalse(processor.has_service('reranking_service'))
        
        print("✅ 服务访问方法测试通过")
    
    def test_service_status_method(self):
        """测试服务状态方法"""
        processor = QueryProcessor(
            config_integration=self.mock_config,
            retrieval_engine=self.mock_retrieval_engine,
            llm_caller=self.mock_llm_caller
        )
        
        status = processor.get_service_status()
        
        # 验证状态信息
        self.assertEqual(status['status'], 'ready')
        self.assertEqual(status['service_type'], 'QueryProcessor')
        self.assertTrue(status['config_integration'])
        self.assertTrue(status['query_router'])
        
        # 验证服务状态
        self.assertTrue(status['services']['retrieval_engine'])
        self.assertTrue(status['services']['llm_caller'])
        self.assertFalse(status['services']['reranking_service'])
        self.assertFalse(status['services']['attribution_service'])
        self.assertFalse(status['services']['display_service'])
        self.assertFalse(status['services']['metadata_manager'])
        
        print("✅ 服务状态方法测试通过")
    
    def test_constructor_backward_compatibility(self):
        """测试向后兼容性"""
        try:
            # 测试旧的调用方式仍然有效
            processor = QueryProcessor(self.mock_config)
            self.assertIsNotNone(processor)
            print("✅ 向后兼容性测试通过")
        except Exception as e:
            self.fail(f"向后兼容性测试失败: {e}")


def run_query_processor_constructor_tests():
    """运行QueryProcessor构造函数测试"""
    try:
        print("\n" + "="*60)
        print("🧪 运行QueryProcessor构造函数参数修复测试")
        print("="*60)
        
        # 创建测试套件
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestQueryProcessorConstructor)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        
        # 输出测试结果
        if result.wasSuccessful():
            print("\n🎉 QueryProcessor构造函数参数修复测试全部通过！")
            return True
        else:
            print(f"\n❌ QueryProcessor构造函数参数修复测试失败！失败数量: {len(result.failures)}")
            for failure in result.failures:
                print(f"   - {failure[0]}: {failure[1]}")
            return False
            
    except Exception as e:
        print(f"❌ QueryProcessor构造函数参数修复测试执行失败: {e}")
        return False


if __name__ == '__main__':
    success = run_query_processor_constructor_tests()
    sys.exit(0 if success else 1)
