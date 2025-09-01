"""
高级配置管理模块测试

测试配置导入导出、版本管理、热更新等高级功能
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 导入被测试的模块
from rag_system.core.config_advanced import (
    AdvancedConfigManager, 
    ConfigFormat, 
    ConfigOperation,
    ConfigVersion,
    ConfigMetrics,
    ConfigChange
)


class TestAdvancedConfigManager(unittest.TestCase):
    """高级配置管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟的配置集成管理器
        self.mock_config_integration = Mock()
        self.mock_config_manager = Mock()
        self.mock_config_integration.config_manager = self.mock_config_manager
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建高级配置管理器实例
        with patch('rag_system.core.config_advanced.Path') as mock_path:
            mock_path.return_value.mkdir = Mock()
            self.config_manager = AdvancedConfigManager(self.mock_config_integration)
            
            # 设置临时目录路径
            self.config_manager.versions_dir = Path(self.temp_dir) / "versions"
            self.config_manager.backup_dir = Path(self.temp_dir) / "backups"
            self.config_manager.versions_dir.mkdir(exist_ok=True)
            self.config_manager.backup_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.config_manager)
        self.assertEqual(self.config_manager.metrics.total_operations, 0)
        self.assertFalse(self.config_manager.hot_reload_enabled)
        self.assertEqual(len(self.config_manager.hot_reload_listeners), 0)
    
    def test_export_rag_config_json(self):
        """测试导出JSON格式配置"""
        # 准备测试数据
        test_config = {
            "query_processing": {"max_results": 10},
            "retrieval": {"similarity_threshold": 0.5},
            "llm_caller": {"model_name": "qwen-turbo"}
        }
        
        # 模拟获取配置数据
        self.config_manager._get_rag_config_data = Mock(return_value=test_config)
        
        # 执行导出
        export_path = os.path.join(self.temp_dir, "test_config.json")
        result = self.config_manager.export_rag_config(export_path, ConfigFormat.JSON)
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # 验证文件内容
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        self.assertEqual(exported_data, test_config)
    
    def test_export_rag_config_yaml(self):
        """测试导出YAML格式配置"""
        # 准备测试数据
        test_config = {
            "query_processing": {"max_results": 10},
            "retrieval": {"similarity_threshold": 0.5}
        }
        
        # 模拟获取配置数据
        self.config_manager._get_rag_config_data = Mock(return_value=test_config)
        
        # 执行导出
        export_path = os.path.join(self.temp_dir, "test_config.yaml")
        result = self.config_manager.export_rag_config(export_path, ConfigFormat.YAML)
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
    
    def test_import_rag_config_json(self):
        """测试导入JSON格式配置"""
        # 准备测试数据
        test_config = {
            "query_processing": {"max_results": 10},
            "retrieval": {"similarity_threshold": 0.5},
            "llm_caller": {"model_name": "qwen-turbo"}
        }
        
        # 创建测试文件
        import_path = os.path.join(self.temp_dir, "import_config.json")
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        # 模拟方法
        self.config_manager._validate_import_file = Mock(return_value=True)
        self.config_manager._validate_config_data = Mock(return_value=True)
        self.config_manager._apply_config_data = Mock(return_value=True)
        self.config_manager._create_backup = Mock(return_value="backup_path")
        
        # 执行导入
        result = self.config_manager.import_rag_config(import_path, ConfigFormat.JSON)
        
        # 验证结果
        self.assertTrue(result)
        self.config_manager._apply_config_data.assert_called_once_with(test_config)
    
    def test_import_rag_config_validation_failure(self):
        """测试导入配置验证失败"""
        # 准备无效的测试数据
        invalid_config = {"invalid": "config"}
        
        # 创建测试文件
        import_path = os.path.join(self.temp_dir, "invalid_config.json")
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_config, f)
        
        # 模拟方法
        self.config_manager._validate_import_file = Mock(return_value=True)
        self.config_manager._validate_config_data = Mock(return_value=False)
        self.config_manager._create_backup = Mock(return_value="backup_path")
        
        # 执行导入
        result = self.config_manager.import_rag_config(import_path, ConfigFormat.JSON)
        
        # 验证结果
        self.assertFalse(result)
    
    def test_get_rag_config_metrics(self):
        """测试获取配置性能指标"""
        # 设置一些测试数据
        self.config_manager.metrics.total_operations = 10
        self.config_manager.metrics.import_count = 3
        self.config_manager.metrics.export_count = 2
        self.config_manager.metrics.success_rate = 90.0
        
        # 执行获取指标
        metrics = self.config_manager.get_rag_config_metrics("all")
        
        # 验证结果
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics['total_operations'], 10)
        self.assertEqual(metrics['import_count'], 3)
        self.assertEqual(metrics['export_count'], 2)
        self.assertEqual(metrics['success_rate'], 90.0)
        self.assertIn('time_range', metrics)
        self.assertIn('generated_at', metrics)
    
    def test_backup_current_config(self):
        """测试备份当前配置"""
        # 准备测试数据
        test_config = {"test": "config"}
        
        # 模拟方法
        self.config_manager._get_rag_config_data = Mock(return_value=test_config)
        
        # 执行备份
        backup_path = self.config_manager.backup_current_config("test_backup")
        
        # 验证结果
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        
        # 验证备份内容
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data, test_config)
    
    def test_restore_config_from_backup(self):
        """测试从备份恢复配置"""
        # 准备测试数据
        test_config = {"restored": "config"}
        
        # 创建备份文件在正确的备份目录中
        backup_path = self.config_manager.backup_dir / "test_backup.json"
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        # 模拟方法
        self.config_manager._create_backup = Mock(return_value="current_backup")
        self.config_manager._apply_config_data = Mock(return_value=True)
        
        # 执行恢复
        result = self.config_manager.restore_config_from_backup("test_backup")
        
        # 验证结果
        self.assertTrue(result)
        self.config_manager._apply_config_data.assert_called_once_with(test_config)
    
    def test_enable_disable_hot_reload(self):
        """测试启用和禁用热更新"""
        # 测试启用
        result = self.config_manager.enable_hot_reload()
        self.assertTrue(result)
        self.assertTrue(self.config_manager.hot_reload_enabled)
        
        # 测试禁用
        result = self.config_manager.disable_hot_reload()
        self.assertTrue(result)
        self.assertFalse(self.config_manager.hot_reload_enabled)
        self.assertEqual(len(self.config_manager.hot_reload_listeners), 0)
    
    def test_hot_reload_listeners(self):
        """测试热更新监听器"""
        # 创建测试监听器
        listener1 = Mock()
        listener2 = Mock()
        
        # 添加监听器
        self.config_manager.add_hot_reload_listener(listener1)
        self.config_manager.add_hot_reload_listener(listener2)
        
        self.assertEqual(len(self.config_manager.hot_reload_listeners), 2)
        
        # 测试通知监听器
        self.config_manager._notify_hot_reload_listeners("test_section")
        listener1.assert_called_once_with("test_section")
        listener2.assert_called_once_with("test_section")
        
        # 移除监听器
        self.config_manager.remove_hot_reload_listener(listener1)
        self.assertEqual(len(self.config_manager.hot_reload_listeners), 1)
    
    def test_reload_config_section(self):
        """测试重新加载配置节"""
        # 启用热更新
        self.config_manager.enable_hot_reload()
        
        # 模拟配置管理器
        self.mock_config_manager.reload_section = Mock(return_value=True)
        
        # 执行重新加载
        result = self.config_manager.reload_config_section("test_section")
        
        # 验证结果
        self.assertTrue(result)
        self.mock_config_manager.reload_section.assert_called_once_with("test_section")
    
    def test_validate_imported_config(self):
        """测试验证导入的配置"""
        # 准备有效配置
        valid_config = {
            "query_processing": {"max_results": 10},
            "retrieval": {"similarity_threshold": 0.5},
            "llm_caller": {"model_name": "qwen-turbo"}
        }
        
        # 准备无效配置
        invalid_config = {"invalid": "config"}
        
        # 模拟验证方法
        self.config_manager._validate_config_data = Mock(side_effect=lambda x: x == valid_config)
        
        # 测试有效配置
        result = self.config_manager.validate_imported_config(valid_config)
        self.assertTrue(result)
        
        # 测试无效配置
        result = self.config_manager.validate_imported_config(invalid_config)
        self.assertFalse(result)
    
    def test_get_service_status(self):
        """测试获取服务状态"""
        # 执行获取状态
        status = self.config_manager.get_service_status()
        
        # 验证结果
        self.assertIsInstance(status, dict)
        self.assertEqual(status['status'], 'ready')
        self.assertEqual(status['service_type'], 'Advanced Config Manager')
        self.assertIn('features', status)
        self.assertIn('metrics', status)
    
    def test_config_change_recording(self):
        """测试配置变更记录"""
        # 记录一个操作
        self.config_manager._record_operation(ConfigOperation.UPDATE, "测试更新")
        
        # 验证记录
        self.assertEqual(len(self.config_manager.changes_log), 1)
        change = self.config_manager.changes_log[0]
        self.assertEqual(change.operation, ConfigOperation.UPDATE)
        self.assertEqual(change.description, "测试更新")
    
    def test_metrics_update(self):
        """测试性能指标更新"""
        # 更新指标
        self.config_manager._update_metrics(ConfigOperation.IMPORT, 1.5, True)
        
        # 验证指标
        self.assertEqual(self.config_manager.metrics.total_operations, 1)
        self.assertEqual(self.config_manager.metrics.import_count, 1)
        self.assertEqual(self.config_manager.metrics.average_operation_time, 1.5)
        self.assertEqual(self.config_manager.metrics.success_rate, 100.0)
        
        # 更新失败指标
        self.config_manager._update_metrics(ConfigOperation.EXPORT, 0.5, False)
        
        # 验证失败指标
        self.assertEqual(self.config_manager.metrics.total_operations, 2)
        self.assertEqual(self.config_manager.metrics.error_count, 1)
        self.assertEqual(self.config_manager.metrics.success_rate, 50.0)


class TestConfigFormat(unittest.TestCase):
    """配置格式枚举测试"""
    
    def test_config_format_values(self):
        """测试配置格式枚举值"""
        self.assertEqual(ConfigFormat.JSON.value, "json")
        self.assertEqual(ConfigFormat.YAML.value, "yaml")
        self.assertEqual(ConfigFormat.PYTHON.value, "python")


class TestConfigOperation(unittest.TestCase):
    """配置操作枚举测试"""
    
    def test_config_operation_values(self):
        """测试配置操作枚举值"""
        self.assertEqual(ConfigOperation.CREATE.value, "create")
        self.assertEqual(ConfigOperation.UPDATE.value, "update")
        self.assertEqual(ConfigOperation.DELETE.value, "delete")
        self.assertEqual(ConfigOperation.IMPORT.value, "import")
        self.assertEqual(ConfigOperation.EXPORT.value, "export")
        self.assertEqual(ConfigOperation.BACKUP.value, "backup")
        self.assertEqual(ConfigOperation.RESTORE.value, "restore")


if __name__ == '__main__':
    unittest.main()
