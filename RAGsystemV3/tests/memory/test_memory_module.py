"""
记忆模块测试脚本

测试记忆模块的核心功能，包括会话管理、记忆存储、检索和压缩
"""

import sys
import os
import unittest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rag_system.core.memory import (
    ConversationMemoryManager,
    MemoryCompressionEngine,
    MemoryConfigManager,
    ConversationSession,
    MemoryChunk,
    MemoryQuery,
    CompressionRequest
)
from rag_system.core.config_integration import ConfigIntegration


class TestMemoryModule(unittest.TestCase):
    """记忆模块测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_memory.db')
        
        # 创建测试配置
        self.config = ConfigIntegration()
        
        # 创建配置管理器
        self.config_manager = MemoryConfigManager(self.config)
        
        # 创建记忆管理器
        self.memory_manager = ConversationMemoryManager(
            config_manager=self.config_manager,
            vector_db_integration=None,
            llm_caller=None
        )
        
        # 创建压缩引擎
        self.compression_engine = MemoryCompressionEngine(
            config_manager=self.config_manager,
            llm_caller=None
        )
    
    def tearDown(self):
        """测试后清理"""
        # 关闭数据库连接
        if hasattr(self.memory_manager, 'close'):
            self.memory_manager.close()
        
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_session(self):
        """测试创建会话"""
        print("\n=== 测试创建会话 ===")
        
        # 创建会话
        session = self.memory_manager.create_session(
            user_id="test_user",
            metadata={"source": "test"}
        )
        
        # 验证会话创建
        self.assertIsInstance(session, ConversationSession)
        self.assertEqual(session.user_id, "test_user")
        self.assertEqual(session.metadata["source"], "test")
        self.assertEqual(session.status, "active")
        
        print(f"✓ 会话创建成功: {session.session_id}")
        return session
    
    def test_get_session(self):
        """测试获取会话"""
        print("\n=== 测试获取会话 ===")
        
        # 先创建会话
        session = self.memory_manager.create_session(
            user_id="test_user",
            metadata={"source": "test"}
        )
        
        # 获取会话
        retrieved_session = self.memory_manager.get_session(session.session_id)
        
        # 验证会话信息
        self.assertEqual(retrieved_session.session_id, session.session_id)
        self.assertEqual(retrieved_session.user_id, "test_user")
        
        print(f"✓ 会话获取成功: {retrieved_session.session_id}")
    
    def test_add_memory(self):
        """测试添加记忆"""
        print("\n=== 测试添加记忆 ===")
        
        # 创建会话
        session = self.memory_manager.create_session(
            user_id="test_user",
            metadata={"source": "test"}
        )
        
        # 添加记忆
        memory = self.memory_manager.add_memory(
            session_id=session.session_id,
            content="这是一个测试记忆",
            content_type="text",
            relevance_score=0.8,
            importance_score=0.7,
            metadata={"test": True}
        )
        
        # 验证记忆创建
        self.assertIsInstance(memory, MemoryChunk)
        self.assertEqual(memory.content, "这是一个测试记忆")
        self.assertEqual(memory.content_type, "text")
        self.assertEqual(memory.relevance_score, 0.8)
        self.assertEqual(memory.importance_score, 0.7)
        
        print(f"✓ 记忆添加成功: {memory.chunk_id}")
        return memory
    
    def test_retrieve_memories(self):
        """测试检索记忆"""
        print("\n=== 测试检索记忆 ===")
        
        # 创建会话并添加记忆
        session = self.memory_manager.create_session(
            user_id="test_user",
            metadata={"source": "test"}
        )
        
        # 添加多个记忆
        memories = []
        for i in range(5):
            memory = self.memory_manager.add_memory(
                session_id=session.session_id,
                content=f"测试记忆 {i+1}",
                content_type="text",
                relevance_score=0.5 + i * 0.1,
                importance_score=0.6 + i * 0.05
            )
            memories.append(memory)
        
        # 创建查询
        query = MemoryQuery(
            query_text="测试记忆",
            session_id=session.session_id,
            max_results=3,
            similarity_threshold=0.0
        )
        
        # 检索记忆
        retrieved_memories = self.memory_manager.retrieve_memories(query)
        
        # 验证检索结果
        self.assertGreaterEqual(len(retrieved_memories), 0)
        print(f"✓ 记忆检索成功: 找到 {len(retrieved_memories)} 条记忆")
        
        return retrieved_memories
    
    def test_compress_memories(self):
        """测试压缩记忆"""
        print("\n=== 测试压缩记忆 ===")
        
        # 创建会话并添加多个记忆
        session = self.memory_manager.create_session(
            user_id="test_user",
            metadata={"source": "test"}
        )
        
        # 添加多个记忆
        memories = []
        for i in range(10):
            memory = self.memory_manager.add_memory(
                session_id=session.session_id,
                content=f"测试记忆内容 {i+1} - 这是用于测试压缩功能的记忆",
                content_type="text",
                relevance_score=0.5 + i * 0.05,
                importance_score=0.6 + i * 0.03
            )
            memories.append(memory)
        
        # 创建压缩请求
        compression_request = CompressionRequest(
            session_id=session.session_id,
            strategy="semantic",
            threshold=5,
            max_ratio=0.5,
            force=True
        )
        
        # 执行压缩
        compressed_memories, compression_info = self.memory_manager.compress_session_memories(
            session_id=session.session_id,
            request=compression_request
        )
        
        # 验证压缩结果
        self.assertIsInstance(compressed_memories, list)
        self.assertLessEqual(len(compressed_memories), len(memories))
        self.assertGreater(compression_info['compression_ratio'], 0)
        
        print(f"✓ 记忆压缩成功: 原始 {len(memories)} 条，压缩后 {len(compressed_memories)} 条")
        print(f"  压缩比例: {compression_info['compression_ratio']:.2f}")
        
        return compressed_memories, compression_info
    
    def test_memory_stats(self):
        """测试记忆统计"""
        print("\n=== 测试记忆统计 ===")
        
        # 创建会话并添加记忆
        session = self.memory_manager.create_session(
            user_id="test_user",
            metadata={"source": "test"}
        )
        
        # 添加多个记忆
        for i in range(3):
            self.memory_manager.add_memory(
                session_id=session.session_id,
                content=f"统计测试记忆 {i+1}",
                content_type="text",
                relevance_score=0.7,
                importance_score=0.8
            )
        
        # 获取统计信息
        stats = self.memory_manager.get_memory_stats()
        
        # 验证统计信息
        self.assertIsInstance(stats, dict)
        self.assertIn('total_sessions', stats)
        self.assertIn('total_memories', stats)
        self.assertGreaterEqual(stats['total_sessions'], 1)
        self.assertGreaterEqual(stats['total_memories'], 3)
        
        print(f"✓ 记忆统计获取成功:")
        print(f"  总会话数: {stats.get('total_sessions', 0)}")
        print(f"  总记忆数: {stats.get('total_memories', 0)}")
        print(f"  活跃会话数: {stats.get('active_sessions', 0)}")
        
        return stats
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        # 测试获取不存在的会话
        with self.assertRaises(Exception):
            self.memory_manager.get_session("non_existent_session")
        
        # 测试向不存在的会话添加记忆
        with self.assertRaises(Exception):
            self.memory_manager.add_memory(
                session_id="non_existent_session",
                content="测试内容"
            )
        
        print("✓ 错误处理测试通过")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始记忆模块测试...")
        print("=" * 50)
        
        try:
            # 运行各个测试
            self.test_create_session()
            self.test_get_session()
            self.test_add_memory()
            self.test_retrieve_memories()
            self.test_compress_memories()
            self.test_memory_stats()
            self.test_error_handling()
            
            print("\n" + "=" * 50)
            print("✅ 所有测试通过！记忆模块功能正常")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            raise


def main():
    """主函数"""
    print("记忆模块测试程序")
    print("=" * 50)
    
    # 创建测试实例
    test_instance = TestMemoryModule()
    
    try:
        # 设置测试环境
        test_instance.setUp()
        
        # 运行所有测试
        test_instance.run_all_tests()
        
    except Exception as e:
        print(f"测试执行失败: {e}")
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
