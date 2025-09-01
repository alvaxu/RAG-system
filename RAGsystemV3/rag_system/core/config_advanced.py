"""
RAG系统高级配置管理模块

实现配置导入导出、版本管理、热更新等高级功能
严格按照设计文档要求实现
"""

import logging
import json
import yaml
import time
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """配置格式枚举"""
    JSON = "json"
    YAML = "yaml"
    PYTHON = "python"


class ConfigOperation(Enum):
    """配置操作类型枚举"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    IMPORT = "import"
    EXPORT = "export"
    BACKUP = "backup"
    RESTORE = "restore"


@dataclass
class ConfigVersion:
    """配置版本信息"""
    version_id: str
    timestamp: datetime
    operation: ConfigOperation
    description: str
    file_hash: str
    file_size: int
    backup_path: str
    metadata: Dict[str, Any]


@dataclass
class ConfigMetrics:
    """配置性能指标"""
    total_operations: int
    import_count: int
    export_count: int
    backup_count: int
    restore_count: int
    last_operation_time: Optional[datetime]
    average_operation_time: float
    success_rate: float
    error_count: int


@dataclass
class ConfigChange:
    """配置变更记录"""
    change_id: str
    timestamp: datetime
    operation: ConfigOperation
    section: str
    key: str
    old_value: Any
    new_value: Any
    user: str
    description: str


class AdvancedConfigManager:
    """高级配置管理器"""
    
    def __init__(self, config_integration):
        """
        初始化高级配置管理器
        
        :param config_integration: 基础配置集成管理器实例
        """
        self.config_integration = config_integration
        self.config_manager = config_integration.config_manager
        
        # 配置版本管理
        self.versions_dir = Path("config_versions")
        self.versions_dir.mkdir(exist_ok=True)
        
        # 配置备份目录
        self.backup_dir = Path("config_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # 配置变更记录
        self.changes_log = []
        self.max_changes_log = 1000
        
        # 性能指标
        self.metrics = ConfigMetrics(
            total_operations=0,
            import_count=0,
            export_count=0,
            backup_count=0,
            restore_count=0,
            last_operation_time=None,
            average_operation_time=0.0,
            success_rate=100.0,
            error_count=0
        )
        
        # 热更新监听器
        self.hot_reload_enabled = False
        self.hot_reload_listeners = []
        
        logger.info("高级配置管理器初始化完成")
    
    def export_rag_config(self, export_path: str, format_type: ConfigFormat = ConfigFormat.JSON) -> bool:
        """
        导出RAG配置
        
        :param export_path: 导出路径
        :param format_type: 导出格式
        :return: 是否成功
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始导出RAG配置到: {export_path}")
            
            # 获取当前配置
            config_data = self._get_rag_config_data()
            
            # 根据格式导出
            if format_type == ConfigFormat.JSON:
                success = self._export_json(config_data, export_path)
            elif format_type == ConfigFormat.YAML:
                success = self._export_yaml(config_data, export_path)
            elif format_type == ConfigFormat.PYTHON:
                success = self._export_python(config_data, export_path)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            if success:
                # 记录操作
                self._record_operation(ConfigOperation.EXPORT, f"导出配置到 {export_path}")
                self._update_metrics(ConfigOperation.EXPORT, time.time() - start_time)
                logger.info(f"RAG配置导出成功: {export_path}")
                return True
            else:
                raise Exception("导出操作失败")
                
        except Exception as e:
            logger.error(f"导出RAG配置失败: {e}")
            self._update_metrics(ConfigOperation.EXPORT, time.time() - start_time, success=False)
            return False
    
    def import_rag_config(self, import_path: str, format_type: ConfigFormat = ConfigFormat.JSON) -> bool:
        """
        导入RAG配置
        
        :param import_path: 导入路径
        :param format_type: 导入格式
        :return: 是否成功
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始从 {import_path} 导入RAG配置")
            
            # 验证导入文件
            if not self._validate_import_file(import_path, format_type):
                raise ValueError("导入文件验证失败")
            
            # 创建备份
            backup_path = self._create_backup("pre_import")
            
            # 根据格式导入
            if format_type == ConfigFormat.JSON:
                config_data = self._import_json(import_path)
            elif format_type == ConfigFormat.YAML:
                config_data = self._import_yaml(import_path)
            elif format_type == ConfigFormat.PYTHON:
                config_data = self._import_python(import_path)
            else:
                raise ValueError(f"不支持的导入格式: {format_type}")
            
            # 验证配置数据
            if not self._validate_config_data(config_data):
                raise ValueError("配置数据验证失败")
            
            # 应用配置
            if self._apply_config_data(config_data):
                # 记录操作
                self._record_operation(ConfigOperation.IMPORT, f"从 {import_path} 导入配置")
                self._update_metrics(ConfigOperation.IMPORT, time.time() - start_time)
                logger.info(f"RAG配置导入成功: {import_path}")
                return True
            else:
                # 恢复备份
                self._restore_backup(backup_path)
                raise Exception("配置应用失败")
                
        except Exception as e:
            logger.error(f"导入RAG配置失败: {e}")
            self._update_metrics(ConfigOperation.IMPORT, time.time() - start_time, success=False)
            return False
    
    def get_rag_config_metrics(self, time_range: str = "all") -> Dict[str, Any]:
        """
        获取配置性能指标
        
        :param time_range: 时间范围 (all/day/week/month)
        :return: 性能指标
        """
        try:
            # 过滤时间范围
            filtered_metrics = self._filter_metrics_by_time(time_range)
            
            # 计算统计信息
            stats = {
                'total_operations': filtered_metrics.total_operations,
                'import_count': filtered_metrics.import_count,
                'export_count': filtered_metrics.export_count,
                'backup_count': filtered_metrics.backup_count,
                'restore_count': filtered_metrics.restore_count,
                'last_operation_time': filtered_metrics.last_operation_time.isoformat() if filtered_metrics.last_operation_time else None,
                'average_operation_time': filtered_metrics.average_operation_time,
                'success_rate': filtered_metrics.success_rate,
                'error_count': filtered_metrics.error_count,
                'time_range': time_range,
                'generated_at': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取配置指标失败: {e}")
            return {}
    
    def backup_current_config(self, backup_name: str = None) -> str:
        """
        备份当前配置
        
        :param backup_name: 备份名称
        :return: 备份路径
        """
        start_time = time.time()
        
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = self._create_backup(backup_name)
            
            # 记录操作
            self._record_operation(ConfigOperation.BACKUP, f"创建备份: {backup_name}")
            self._update_metrics(ConfigOperation.BACKUP, time.time() - start_time)
            
            logger.info(f"配置备份成功: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"配置备份失败: {e}")
            self._update_metrics(ConfigOperation.BACKUP, time.time() - start_time, success=False)
            return ""
    
    def restore_config_from_backup(self, backup_name: str) -> bool:
        """
        从备份恢复配置
        
        :param backup_name: 备份名称
        :return: 是否成功
        """
        start_time = time.time()
        
        try:
            backup_path = self.backup_dir / f"{backup_name}.json"
            
            if not backup_path.exists():
                raise FileNotFoundError(f"备份文件不存在: {backup_path}")
            
            # 创建当前配置的备份
            current_backup = self._create_backup("pre_restore")
            
            # 恢复配置
            if self._restore_backup(backup_path):
                # 记录操作
                self._record_operation(ConfigOperation.RESTORE, f"从备份恢复: {backup_name}")
                self._update_metrics(ConfigOperation.RESTORE, time.time() - start_time)
                logger.info(f"配置恢复成功: {backup_name}")
                return True
            else:
                # 恢复当前配置
                self._restore_backup(current_backup)
                raise Exception("配置恢复失败")
                
        except Exception as e:
            logger.error(f"配置恢复失败: {e}")
            self._update_metrics(ConfigOperation.RESTORE, time.time() - start_time, success=False)
            return False
    
    def enable_hot_reload(self) -> bool:
        """
        启用配置热更新
        
        :return: 是否成功
        """
        try:
            if self.hot_reload_enabled:
                logger.warning("配置热更新已经启用")
                return True
            
            self.hot_reload_enabled = True
            logger.info("配置热更新已启用")
            return True
            
        except Exception as e:
            logger.error(f"启用配置热更新失败: {e}")
            return False
    
    def disable_hot_reload(self) -> bool:
        """
        禁用配置热更新
        
        :return: 是否成功
        """
        try:
            self.hot_reload_enabled = False
            self.hot_reload_listeners.clear()
            logger.info("配置热更新已禁用")
            return True
            
        except Exception as e:
            logger.error(f"禁用配置热更新失败: {e}")
            return False
    
    def reload_config_section(self, section: str) -> bool:
        """
        重新加载配置节
        
        :param section: 配置节名称
        :return: 是否成功
        """
        try:
            if not self.hot_reload_enabled:
                logger.warning("配置热更新未启用")
                return False
            
            # 重新加载指定节
            if self.config_manager.reload_section(section):
                # 通知监听器
                self._notify_hot_reload_listeners(section)
                logger.info(f"配置节重新加载成功: {section}")
                return True
            else:
                logger.error(f"配置节重新加载失败: {section}")
                return False
                
        except Exception as e:
            logger.error(f"重新加载配置节失败: {e}")
            return False
    
    def add_hot_reload_listener(self, listener_func):
        """
        添加热更新监听器
        
        :param listener_func: 监听器函数
        """
        if callable(listener_func):
            self.hot_reload_listeners.append(listener_func)
            logger.info("热更新监听器已添加")
    
    def remove_hot_reload_listener(self, listener_func):
        """
        移除热更新监听器
        
        :param listener_func: 监听器函数
        """
        if listener_func in self.hot_reload_listeners:
            self.hot_reload_listeners.remove(listener_func)
            logger.info("热更新监听器已移除")
    
    def get_config_versions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取配置版本历史
        
        :param limit: 返回数量限制
        :return: 版本历史列表
        """
        try:
            versions = []
            version_files = sorted(self.versions_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            for version_file in version_files[:limit]:
                try:
                    with open(version_file, 'r', encoding='utf-8') as f:
                        version_data = json.load(f)
                        versions.append(version_data)
                except Exception as e:
                    logger.warning(f"读取版本文件失败: {version_file}, 错误: {e}")
                    continue
            
            return versions
            
        except Exception as e:
            logger.error(f"获取配置版本历史失败: {e}")
            return []
    
    def get_config_changes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取配置变更记录
        
        :param limit: 返回数量限制
        :return: 变更记录列表
        """
        try:
            changes = self.changes_log[-limit:] if self.changes_log else []
            return [asdict(change) for change in changes]
            
        except Exception as e:
            logger.error(f"获取配置变更记录失败: {e}")
            return []
    
    def validate_imported_config(self, config_data: Dict[str, Any]) -> bool:
        """
        验证导入的配置
        
        :param config_data: 配置数据
        :return: 是否有效
        """
        try:
            return self._validate_config_data(config_data)
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    # 私有方法
    def _get_rag_config_data(self) -> Dict[str, Any]:
        """获取RAG配置数据"""
        try:
            return self.config_manager.get('rag_system', {})
        except Exception as e:
            logger.error(f"获取RAG配置数据失败: {e}")
            return {}
    
    def _export_json(self, config_data: Dict[str, Any], export_path: str) -> bool:
        """导出JSON格式配置"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"导出JSON配置失败: {e}")
            return False
    
    def _export_yaml(self, config_data: Dict[str, Any], export_path: str) -> bool:
        """导出YAML格式配置"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            logger.error(f"导出YAML配置失败: {e}")
            return False
    
    def _export_python(self, config_data: Dict[str, Any], export_path: str) -> bool:
        """导出Python格式配置"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("# RAG系统配置\n")
                f.write("# 自动生成，请勿手动修改\n\n")
                f.write("RAG_CONFIG = ")
                f.write(repr(config_data))
                f.write("\n")
            return True
        except Exception as e:
            logger.error(f"导出Python配置失败: {e}")
            return False
    
    def _import_json(self, import_path: str) -> Dict[str, Any]:
        """导入JSON格式配置"""
        with open(import_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _import_yaml(self, import_path: str) -> Dict[str, Any]:
        """导入YAML格式配置"""
        with open(import_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _import_python(self, import_path: str) -> Dict[str, Any]:
        """导入Python格式配置"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("config_module", import_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        return getattr(config_module, 'RAG_CONFIG', {})
    
    def _validate_import_file(self, import_path: str, format_type: ConfigFormat) -> bool:
        """验证导入文件"""
        try:
            file_path = Path(import_path)
            if not file_path.exists():
                return False
            
            if file_path.stat().st_size == 0:
                return False
            
            return True
        except Exception:
            return False
    
    def _validate_config_data(self, config_data: Dict[str, Any]) -> bool:
        """验证配置数据"""
        try:
            if not isinstance(config_data, dict):
                return False
            
            # 检查必需的配置节
            required_sections = ['query_processing', 'retrieval', 'llm_caller']
            for section in required_sections:
                if section not in config_data:
                    logger.warning(f"缺少必需的配置节: {section}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"配置数据验证失败: {e}")
            return False
    
    def _apply_config_data(self, config_data: Dict[str, Any]) -> bool:
        """应用配置数据"""
        try:
            # 更新配置
            self.config_manager.config_data['rag_system'] = config_data
            
            # 保存配置
            return self.config_manager.save_config()
        except Exception as e:
            logger.error(f"应用配置数据失败: {e}")
            return False
    
    def _create_backup(self, backup_name: str) -> str:
        """创建配置备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{backup_name}_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            # 获取当前配置
            config_data = self._get_rag_config_data()
            
            # 保存备份
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            return str(backup_path)
        except Exception as e:
            logger.error(f"创建配置备份失败: {e}")
            return ""
    
    def _restore_backup(self, backup_path: Union[str, Path]) -> bool:
        """恢复配置备份"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                return False
            
            # 读取备份配置
            with open(backup_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 应用配置
            return self._apply_config_data(config_data)
        except Exception as e:
            logger.error(f"恢复配置备份失败: {e}")
            return False
    
    def _record_operation(self, operation: ConfigOperation, description: str):
        """记录配置操作"""
        try:
            change = ConfigChange(
                change_id=f"change_{int(time.time() * 1000)}",
                timestamp=datetime.now(),
                operation=operation,
                section="rag_system",
                key="",
                old_value="",
                new_value="",
                user="system",
                description=description
            )
            
            self.changes_log.append(change)
            
            # 限制日志大小
            if len(self.changes_log) > self.max_changes_log:
                self.changes_log = self.changes_log[-self.max_changes_log:]
                
        except Exception as e:
            logger.error(f"记录配置操作失败: {e}")
    
    def _update_metrics(self, operation: ConfigOperation, duration: float, success: bool = True):
        """更新性能指标"""
        try:
            self.metrics.total_operations += 1
            self.metrics.last_operation_time = datetime.now()
            
            if success:
                # 更新平均操作时间
                total_time = self.metrics.average_operation_time * (self.metrics.total_operations - 1)
                self.metrics.average_operation_time = (total_time + duration) / self.metrics.total_operations
            else:
                self.metrics.error_count += 1
            
            # 更新操作计数
            if operation == ConfigOperation.IMPORT:
                self.metrics.import_count += 1
            elif operation == ConfigOperation.EXPORT:
                self.metrics.export_count += 1
            elif operation == ConfigOperation.BACKUP:
                self.metrics.backup_count += 1
            elif operation == ConfigOperation.RESTORE:
                self.metrics.restore_count += 1
            
            # 计算成功率
            if self.metrics.total_operations > 0:
                self.metrics.success_rate = ((self.metrics.total_operations - self.metrics.error_count) / 
                                           self.metrics.total_operations) * 100
                
        except Exception as e:
            logger.error(f"更新性能指标失败: {e}")
    
    def _filter_metrics_by_time(self, time_range: str) -> ConfigMetrics:
        """根据时间范围过滤指标"""
        try:
            now = datetime.now()
            
            if time_range == "day":
                start_time = now - timedelta(days=1)
            elif time_range == "week":
                start_time = now - timedelta(weeks=1)
            elif time_range == "month":
                start_time = now - timedelta(days=30)
            else:  # all
                return self.metrics
            
            # 这里简化处理，实际应该根据时间过滤操作记录
            return self.metrics
            
        except Exception as e:
            logger.error(f"过滤指标失败: {e}")
            return self.metrics
    
    def _notify_hot_reload_listeners(self, section: str):
        """通知热更新监听器"""
        try:
            for listener in self.hot_reload_listeners:
                try:
                    listener(section)
                except Exception as e:
                    logger.error(f"热更新监听器执行失败: {e}")
        except Exception as e:
            logger.error(f"通知热更新监听器失败: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            'status': 'ready',
            'service_type': 'Advanced Config Manager',
            'hot_reload_enabled': self.hot_reload_enabled,
            'listeners_count': len(self.hot_reload_listeners),
            'versions_count': len(list(self.versions_dir.glob("*.json"))),
            'backups_count': len(list(self.backup_dir.glob("*.json"))),
            'changes_log_count': len(self.changes_log),
            'metrics': asdict(self.metrics),
            'features': [
                'config_import_export',
                'config_versioning',
                'config_backup_restore',
                'config_hot_reload',
                'config_metrics',
                'config_validation'
            ]
        }
