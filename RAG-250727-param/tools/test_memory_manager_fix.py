#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 测试SimplifiedMemoryManager的clear_all_memories方法
## 2. 验证系统优雅退出时的记忆清理功能
## 3. 确保修复后的代码能正常工作
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_memory_manager_clear_all():
    """测试记忆管理器的clear_all_memories方法"""
    try:
        from v2.core.v2_memory_manager import SimplifiedMemoryManager
        
        logger.info("🔧 开始测试SimplifiedMemoryManager的clear_all_memories方法")
        
        # 创建记忆管理器实例
        memory_manager = SimplifiedMemoryManager()
        
        # 添加一些测试数据
        logger.info("📝 添加测试数据...")
        memory_manager.update_context("user1", "测试问题1", "测试答案1")
        memory_manager.update_context("user2", "测试问题2", "测试答案2")
        memory_manager.update_context("user3", "测试问题3", "测试答案3")
        
        # 检查数据是否添加成功
        stats_before = memory_manager.get_memory_stats()
        logger.info(f"📊 清理前的记忆统计: {stats_before}")
        
        # 测试clear_all_memories方法
        logger.info("🧹 执行clear_all_memories方法...")
        result = memory_manager.clear_all_memories()
        logger.info(f"✅ 清理结果: {result}")
        
        # 检查清理后的状态
        stats_after = memory_manager.get_memory_stats()
        logger.info(f"📊 清理后的记忆统计: {stats_after}")
        
        # 验证清理是否成功
        if stats_after.get('total_users', 0) == 0:
            logger.info("🎯 测试成功：所有记忆数据已正确清理")
            return True
        else:
            logger.error("❌ 测试失败：记忆数据未完全清理")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

def test_memory_manager_methods():
    """测试记忆管理器的其他相关方法"""
    try:
        from v2.core.v2_memory_manager import SimplifiedMemoryManager
        
        logger.info("🔧 测试记忆管理器的其他方法...")
        
        memory_manager = SimplifiedMemoryManager()
        
        # 测试clear_context方法
        memory_manager.update_context("test_user", "测试问题", "测试答案")
        memory_manager.clear_context("test_user")
        
        # 测试clear_session_memory方法
        memory_manager.update_context("test_user2", "测试问题2", "测试答案2")
        memory_manager.clear_session_memory("test_user2")
        
        # 测试clear_user_memory方法
        memory_manager.update_context("test_user3", "测试问题3", "测试答案3")
        memory_manager.clear_user_memory("test_user3")
        
        logger.info("✅ 所有方法测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 方法测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🧪 SimplifiedMemoryManager修复验证测试")
    logger.info("=" * 50)
    
    try:
        # 测试clear_all_memories方法
        test1_success = test_memory_manager_clear_all()
        
        # 测试其他方法
        test2_success = test_memory_manager_methods()
        
        if test1_success and test2_success:
            logger.info("🎯 所有测试通过！SimplifiedMemoryManager修复成功！")
            logger.info("✅ 系统优雅退出功能现在应该能正常工作")
            return 0
        else:
            logger.error("💥 部分测试失败，请检查修复")
            return 1
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生未预期的错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
