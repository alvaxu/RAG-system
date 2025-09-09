"""
记忆模块监控脚本

监控记忆模块的运行状态和性能指标
"""

import os
import sys
import time
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# 项目内包导入 - 遵循技术规范
from db_system.config.config_manager import ConfigManager
from db_system.config.path_manager import PathManager


class MemoryModuleMonitor:
    """记忆模块监控器"""
    
    def __init__(self, config_file="monitor_config.json"):
        # 使用配置管理器获取路径 - 遵循技术规范
        self.config_manager = ConfigManager()
        self.path_manager = PathManager()
        
        # 获取项目根目录 - PathManager返回的是db_system目录，需要获取上级目录
        self.project_root = Path(self.path_manager.get_base_dir()).parent
        # 配置文件现在位于tools/monitor目录下
        self.config_file = self.project_root / "tools" / "monitor" / config_file
        self.log_file = self.project_root / "logs" / "memory_monitor.log"
        
        # 确保日志目录存在
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载监控配置
        self.config = self.load_config()
        
        # 监控数据
        self.monitor_data = {
            "start_time": datetime.now(),
            "checks": [],
            "alerts": []
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载监控配置"""
        default_config = {
            "api_url": "http://localhost:8000",
            "memory_db_path": "rag_memory.db",  # 默认值，会被配置文件覆盖
            "check_interval": 60,  # 秒
            "alert_thresholds": {
                "memory_usage_mb": 100,
                "session_count": 1000,
                "memory_count": 10000,
                "response_time_ms": 5000
            },
            "alerts": {
                "enabled": True,
                "email": "admin@example.com",
                "webhook": None
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"加载配置文件失败，使用默认配置: {e}")
                return default_config
        else:
            # 创建默认配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def check_api_health(self) -> Dict[str, Any]:
        """检查API健康状态"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.config['api_url']}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time_ms": None,
                "timestamp": datetime.now().isoformat()
            }
    
    def check_memory_api(self) -> Dict[str, Any]:
        """检查记忆模块API"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.config['api_url']}/api/v3/memory/stats", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                stats = response.json()
                return {
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "stats": stats,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time_ms": None,
                "timestamp": datetime.now().isoformat()
            }
    
    def check_database_health(self) -> Dict[str, Any]:
        """检查数据库健康状态"""
        try:
            # 优先从RAG系统配置中获取数据库路径
            try:
                from rag_system.core.config_integration import ConfigIntegration
                config = ConfigIntegration()
                db_path = Path(config.get('rag_system.memory_module.database_path', 'rag_memory.db'))
                if not db_path.is_absolute():
                    db_path = self.project_root / db_path
            except Exception:
                # 如果无法获取配置，使用监控配置
                db_path = self.project_root / self.config["memory_db_path"]
            
            if not db_path.exists():
                return {
                    "status": "error",
                    "error": "数据库文件不存在",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 检查数据库文件大小
            file_size_mb = db_path.stat().st_size / (1024 * 1024)
            
            # 检查数据库连接
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['conversation_sessions', 'memory_chunks', 'compression_records']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            # 获取基本统计信息
            cursor.execute("SELECT COUNT(*) FROM conversation_sessions")
            session_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memory_chunks")
            memory_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "status": "healthy" if not missing_tables else "warning",
                "file_size_mb": file_size_mb,
                "session_count": session_count,
                "memory_count": memory_count,
                "missing_tables": missing_tables,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源使用情况"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_percent = memory.percent
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_used_mb = disk.used / (1024 * 1024)
            disk_percent = (disk.used / disk.total) * 100
            
            return {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_used_mb": memory_used_mb,
                "memory_percent": memory_percent,
                "disk_used_mb": disk_used_mb,
                "disk_percent": disk_percent,
                "timestamp": datetime.now().isoformat()
            }
            
        except ImportError:
            return {
                "status": "warning",
                "error": "psutil未安装，无法获取系统资源信息",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_alert_conditions(self, check_results: Dict[str, Any]) -> List[str]:
        """检查告警条件"""
        alerts = []
        thresholds = self.config["alert_thresholds"]
        
        # 检查API响应时间
        if "api_health" in check_results:
            api_result = check_results["api_health"]
            if (api_result.get("response_time_ms") and 
                api_result["response_time_ms"] > thresholds["response_time_ms"]):
                alerts.append(f"API响应时间过长: {api_result['response_time_ms']:.2f}ms")
        
        # 检查记忆模块API响应时间
        if "memory_api" in check_results:
            memory_result = check_results["memory_api"]
            if (memory_result.get("response_time_ms") and 
                memory_result["response_time_ms"] > thresholds["response_time_ms"]):
                alerts.append(f"记忆模块API响应时间过长: {memory_result['response_time_ms']:.2f}ms")
        
        # 检查数据库大小
        if "database_health" in check_results:
            db_result = check_results["database_health"]
            if (db_result.get("file_size_mb") and 
                db_result["file_size_mb"] > thresholds["memory_usage_mb"]):
                alerts.append(f"数据库文件过大: {db_result['file_size_mb']:.2f}MB")
        
        # 检查会话数量
        if "database_health" in check_results:
            db_result = check_results["database_health"]
            if (db_result.get("session_count") and 
                db_result["session_count"] > thresholds["session_count"]):
                alerts.append(f"会话数量过多: {db_result['session_count']}")
        
        # 检查记忆数量
        if "database_health" in check_results:
            db_result = check_results["database_health"]
            if (db_result.get("memory_count") and 
                db_result["memory_count"] > thresholds["memory_count"]):
                alerts.append(f"记忆数量过多: {db_result['memory_count']}")
        
        # 检查系统资源
        if "system_resources" in check_results:
            sys_result = check_results["system_resources"]
            if sys_result.get("memory_percent", 0) > 90:
                alerts.append(f"内存使用率过高: {sys_result['memory_percent']:.1f}%")
            if sys_result.get("disk_percent", 0) > 90:
                alerts.append(f"磁盘使用率过高: {sys_result['disk_percent']:.1f}%")
        
        return alerts
    
    def send_alert(self, alerts: List[str]):
        """发送告警"""
        if not self.config["alerts"]["enabled"] or not alerts:
            return
        
        alert_message = f"记忆模块告警 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        alert_message += "\n".join(f"- {alert}" for alert in alerts)
        
        self.log(f"发送告警: {alert_message}", "ALERT")
        
        # 这里可以添加发送邮件、Webhook等告警逻辑
        # 例如：发送到钉钉、企业微信、邮件等
    
    def run_check(self) -> Dict[str, Any]:
        """执行一次完整检查"""
        self.log("开始执行健康检查...")
        
        check_results = {
            "timestamp": datetime.now().isoformat(),
            "api_health": self.check_api_health(),
            "memory_api": self.check_memory_api(),
            "database_health": self.check_database_health(),
            "system_resources": self.check_system_resources()
        }
        
        # 检查告警条件
        alerts = self.check_alert_conditions(check_results)
        if alerts:
            self.send_alert(alerts)
            check_results["alerts"] = alerts
        
        # 记录检查结果
        self.monitor_data["checks"].append(check_results)
        
        # 只保留最近100次检查记录
        if len(self.monitor_data["checks"]) > 100:
            self.monitor_data["checks"] = self.monitor_data["checks"][-100:]
        
        self.log(f"健康检查完成，发现 {len(alerts)} 个告警")
        
        return check_results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成监控报告"""
        if not self.monitor_data["checks"]:
            return {"error": "没有检查数据"}
        
        recent_checks = self.monitor_data["checks"][-24:]  # 最近24次检查
        
        # 计算统计信息
        api_healthy_count = sum(1 for check in recent_checks 
                              if check.get("api_health", {}).get("status") == "healthy")
        memory_api_healthy_count = sum(1 for check in recent_checks 
                                     if check.get("memory_api", {}).get("status") == "healthy")
        
        # 计算平均响应时间
        api_response_times = [check.get("api_health", {}).get("response_time_ms") 
                            for check in recent_checks 
                            if check.get("api_health", {}).get("response_time_ms")]
        memory_api_response_times = [check.get("memory_api", {}).get("response_time_ms") 
                                   for check in recent_checks 
                                   if check.get("memory_api", {}).get("response_time_ms")]
        
        avg_api_response_time = sum(api_response_times) / len(api_response_times) if api_response_times else 0
        avg_memory_api_response_time = sum(memory_api_response_times) / len(memory_api_response_times) if memory_api_response_times else 0
        
        # 统计告警数量
        total_alerts = sum(len(check.get("alerts", [])) for check in recent_checks)
        
        report = {
            "report_time": datetime.now().isoformat(),
            "monitoring_duration_hours": (datetime.now() - self.monitor_data["start_time"]).total_seconds() / 3600,
            "total_checks": len(recent_checks),
            "api_health_rate": api_healthy_count / len(recent_checks) * 100,
            "memory_api_health_rate": memory_api_healthy_count / len(recent_checks) * 100,
            "avg_api_response_time_ms": avg_api_response_time,
            "avg_memory_api_response_time_ms": avg_memory_api_response_time,
            "total_alerts": total_alerts,
            "latest_check": recent_checks[-1] if recent_checks else None
        }
        
        return report
    
    def start_monitoring(self):
        """开始持续监控"""
        self.log("开始记忆模块监控...")
        self.log(f"检查间隔: {self.config['check_interval']}秒")
        
        try:
            while True:
                check_results = self.run_check()
                
                # 每10次检查生成一次报告
                if len(self.monitor_data["checks"]) % 10 == 0:
                    report = self.generate_report()
                    self.log(f"监控报告: API健康率 {report['api_health_rate']:.1f}%, "
                           f"记忆API健康率 {report['memory_api_health_rate']:.1f}%, "
                           f"总告警数 {report['total_alerts']}")
                
                time.sleep(self.config["check_interval"])
                
        except KeyboardInterrupt:
            self.log("监控已停止")
        except Exception as e:
            self.log(f"监控异常: {e}", "ERROR")


def main():
    """主函数"""
    print("记忆模块监控程序")
    print("=" * 50)
    
    monitor = MemoryModuleMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "report":
            # 生成报告模式
            print("执行健康检查并生成报告...")
            monitor.run_check()  # 先执行一次检查
            report = monitor.generate_report()
            
            # 输出到控制台
            print(json.dumps(report, indent=2, ensure_ascii=False))
            
            # 保存到文件
            report_file = monitor.project_root / "logs" / f"monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n报告已保存到: {report_file}")
        elif sys.argv[1] == "check":
            # 单次检查模式
            print("执行单次健康检查...")
            result = monitor.run_check()
            print("\n检查结果:")
            print(f"API健康状态: {result.get('api_health', {}).get('status', 'unknown')}")
            print(f"记忆API状态: {result.get('memory_api', {}).get('status', 'unknown')}")
            print(f"数据库状态: {result.get('database_health', {}).get('status', 'unknown')}")
            print(f"系统资源状态: {result.get('system_resources', {}).get('status', 'unknown')}")
            if result.get('alerts'):
                print(f"告警数量: {len(result['alerts'])}")
                for alert in result['alerts']:
                    print(f"  - {alert}")
            else:
                print("无告警")
        elif sys.argv[1] == "monitor":
            # 持续监控模式
            monitor.start_monitoring()
        else:
            print("使用方法:")
            print("  python monitor_memory_module.py check    # 单次检查")
            print("  python monitor_memory_module.py report   # 生成报告")
            print("  python monitor_memory_module.py monitor  # 持续监控")
    else:
        # 默认：单次检查模式
        print("执行单次健康检查...")
        result = monitor.run_check()
        print("\n检查结果:")
        print(f"API健康状态: {result.get('api_health', {}).get('status', 'unknown')}")
        print(f"记忆API状态: {result.get('memory_api', {}).get('status', 'unknown')}")
        print(f"数据库状态: {result.get('database_health', {}).get('status', 'unknown')}")
        print(f"系统资源状态: {result.get('system_resources', {}).get('status', 'unknown')}")
        if result.get('alerts'):
            print(f"告警数量: {len(result['alerts'])}")
            for alert in result['alerts']:
                print(f"  - {alert}")
        else:
            print("无告警")


if __name__ == "__main__":
    main()
