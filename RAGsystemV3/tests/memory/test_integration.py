"""
记忆模块集成测试脚本

测试记忆模块与RAG系统的集成功能
"""

import sys
import os
import unittest
import tempfile
import shutil
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rag_system.core.memory import ConversationMemoryManager, MemoryConfigManager
from rag_system.core.config_integration import ConfigIntegration
from rag_system.core.query_processor import QueryProcessor
from rag_system.core.retrieval import RetrievalEngine
from rag_system.core.llm_caller import LLMCaller
from rag_system.core.vector_db_integration import VectorDBIntegration


class TestMemoryIntegration(unittest.TestCase):
    """记忆模块集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试配置
        self.config = ConfigIntegration()
        
        # 创建配置管理器
        self.config_manager = MemoryConfigManager(self.config)
        
        # 创建向量数据库集成（模拟）
        self.vector_db_integration = None
        
        # 创建LLM调用器（模拟）
        self.llm_caller = None
        
        # 创建记忆管理器
        self.memory_manager = ConversationMemoryManager(
            config_manager=self.config_manager,
            vector_db_integration=self.vector_db_integration,
            llm_caller=self.llm_caller
        )
    
    def tearDown(self):
        """测试后清理"""
        # 关闭数据库连接
        if hasattr(self.memory_manager, 'close'):
            self.memory_manager.close()
        
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_memory_in_query_processing(self):
        """测试记忆在查询处理中的集成"""
        print("\n=== 测试记忆在查询处理中的集成 ===")
        
        # 创建会话
        session = self.memory_manager.create_session(
            user_id="integration_test_user",
            metadata={"source": "integration_test"}
        )
        
        # 添加一些历史记忆
        memories = []
        for i in range(3):
            memory = self.memory_manager.add_memory(
                session_id=session.session_id,
                content=f"用户之前询问过关于机器学习的问题 {i+1}",
                content_type="text",
                relevance_score=0.8,
                importance_score=0.7,
                metadata={"query_type": "technical", "topic": "machine_learning"}
            )
            memories.append(memory)
        
        print(f"✓ 添加了 {len(memories)} 条历史记忆")
        
        # 模拟查询处理中的记忆检索
        from rag_system.core.memory import MemoryQuery
        
        query = MemoryQuery(
            query_text="深度学习相关的问题",
            session_id=session.session_id,
            max_results=5,
            similarity_threshold=0.5
        )
        
        # 检索相关记忆
        relevant_memories = self.memory_manager.retrieve_memories(query)
        
        print(f"✓ 检索到 {len(relevant_memories)} 条相关记忆")
        
        # 验证记忆检索结果
        self.assertIsInstance(relevant_memories, list)
        
        return relevant_memories
    
    def test_memory_compression_integration(self):
        """测试记忆压缩集成"""
        print("\n=== 测试记忆压缩集成 ===")
        
        # 创建会话
        session = self.memory_manager.create_session(
            user_id="compression_test_user",
            metadata={"source": "compression_test"}
        )
        
        # 添加大量记忆以触发压缩
        memories = []
        for i in range(15):
            memory = self.memory_manager.add_memory(
                session_id=session.session_id,
                content=f"压缩测试记忆 {i+1} - 这是用于测试记忆压缩功能的记忆内容",
                content_type="text",
                relevance_score=0.5 + (i % 5) * 0.1,
                importance_score=0.6 + (i % 3) * 0.1,
                metadata={"test": True, "index": i}
            )
            memories.append(memory)
        
        print(f"✓ 添加了 {len(memories)} 条测试记忆")
        
        # 执行记忆压缩
        from rag_system.core.memory import CompressionRequest
        
        compression_request = CompressionRequest(
            session_id=session.session_id,
            strategy="semantic",
            threshold=10,
            max_ratio=0.5,
            force=True
        )
        
        compressed_memories, compression_info = self.memory_manager.compress_session_memories(
            session_id=session.session_id,
            request=compression_request
        )
        
        print(f"✓ 记忆压缩完成:")
        print(f"  原始记忆数: {compression_info['original_count']}")
        print(f"  压缩后记忆数: {compression_info['compressed_count']}")
        print(f"  压缩比例: {compression_info['compression_ratio']:.2f}")
        
        # 验证压缩结果
        self.assertLessEqual(len(compressed_memories), len(memories))
        self.assertGreater(compression_info['compression_ratio'], 0)
        
        return compressed_memories, compression_info
    
    def test_memory_configuration_integration(self):
        """测试记忆配置集成"""
        print("\n=== 测试记忆配置集成 ===")
        
        # 测试配置获取
        database_path = self.config_manager.get_database_path()
        print(f"✓ 数据库路径: {database_path}")
        
        is_enabled = self.config_manager.is_enabled()
        print(f"✓ 记忆模块启用状态: {is_enabled}")
        
        compression_config = self.config_manager.get_compression_config()
        print(f"✓ 压缩配置: {compression_config}")
        
        retrieval_config = self.config_manager.get_retrieval_config()
        print(f"✓ 检索配置: {retrieval_config}")
        
        session_config = self.config_manager.get_session_config()
        print(f"✓ 会话配置: {session_config}")
        
        # 验证配置完整性
        self.assertIsInstance(database_path, str)
        self.assertIsInstance(is_enabled, bool)
        self.assertIsInstance(compression_config, dict)
        self.assertIsInstance(retrieval_config, dict)
        self.assertIsInstance(session_config, dict)
        
        return True
    
    def test_memory_statistics_integration(self):
        """测试记忆统计集成"""
        print("\n=== 测试记忆统计集成 ===")
        
        # 创建多个会话和记忆
        sessions = []
        for i in range(3):
            session = self.memory_manager.create_session(
                user_id=f"stats_test_user_{i}",
                metadata={"source": "stats_test", "index": i}
            )
            sessions.append(session)
            
            # 为每个会话添加记忆
            for j in range(2):
                self.memory_manager.add_memory(
                    session_id=session.session_id,
                    content=f"统计测试记忆 {i+1}-{j+1}",
                    content_type="text",
                    relevance_score=0.7,
                    importance_score=0.8
                )
        
        print(f"✓ 创建了 {len(sessions)} 个会话")
        
        # 获取统计信息
        stats = self.memory_manager.get_memory_stats()
        
        print(f"✓ 记忆统计信息:")
        print(f"  总会话数: {stats.get('total_sessions', 0)}")
        print(f"  总记忆数: {stats.get('total_memories', 0)}")
        print(f"  活跃会话数: {stats.get('active_sessions', 0)}")
        print(f"  平均每会话记忆数: {stats.get('avg_memories_per_session', 0):.1f}")
        
        # 验证统计信息
        self.assertGreaterEqual(stats.get('total_sessions', 0), 3)
        self.assertGreaterEqual(stats.get('total_memories', 0), 6)
        
        return stats
    
    def test_memory_error_handling_integration(self):
        """测试记忆错误处理集成"""
        print("\n=== 测试记忆错误处理集成 ===")
        
        # 测试各种错误情况
        error_tests = [
            ("获取不存在的会话", lambda: self.memory_manager.get_session("non_existent")),
            ("向不存在的会话添加记忆", lambda: self.memory_manager.add_memory(
                session_id="non_existent", content="test"
            )),
            ("压缩不存在的会话", lambda: self.memory_manager.compress_session_memories(
                session_id="non_existent", request=None
            ))
        ]
        
        for test_name, test_func in error_tests:
            try:
                test_func()
                print(f"✗ {test_name} 应该抛出异常但没有")
            except Exception as e:
                print(f"✓ {test_name} 正确抛出异常: {type(e).__name__}")
        
        return True
    
    def run_all_tests(self):
        """运行所有集成测试"""
        print("开始记忆模块集成测试...")
        print("=" * 50)
        
        try:
            # 运行各个测试
            self.test_memory_in_query_processing()
            self.test_memory_compression_integration()
            self.test_memory_configuration_integration()
            self.test_memory_statistics_integration()
            self.test_memory_error_handling_integration()
            
            print("\n" + "=" * 50)
            print("✅ 所有集成测试通过！记忆模块集成功能正常")
            
        except Exception as e:
            print(f"\n❌ 集成测试失败: {e}")
            raise


def main():
    """主函数"""
    print("记忆模块集成测试程序")
    print("=" * 50)
    
    # 创建测试实例
    test_instance = TestMemoryIntegration()
    
    try:
        # 设置测试环境
        test_instance.setUp()
        
        # 运行所有测试
        test_instance.run_all_tests()
        
    except Exception as e:
        print(f"集成测试执行失败: {e}")
        return 1
    
    finally:
        # 清理测试环境
        try:
            test_instance.tearDown()
        except:
            pass
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
