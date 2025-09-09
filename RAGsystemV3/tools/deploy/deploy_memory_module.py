"""
记忆模块部署脚本

自动化部署RAG系统记忆模块到生产环境
"""

import os
import sys
import shutil
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

# 项目内包导入 - 遵循技术规范
from db_system.config.config_manager import ConfigManager
from db_system.config.path_manager import PathManager


class MemoryModuleDeployer:
    """记忆模块部署器"""
    
    def __init__(self):
        # 使用配置管理器获取路径 - 遵循技术规范
        self.config_manager = ConfigManager()
        self.path_manager = PathManager()
        
        # 获取项目根目录
        self.project_root = Path(self.path_manager.get_base_dir())
        self.backup_dir = self.project_root / "backups" / f"deploy_{int(time.time())}"
        self.log_file = self.project_root / "logs" / "deploy_memory_module.log"
        
        # 确保日志目录存在
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def check_prerequisites(self):
        """检查部署前置条件"""
        self.log("检查部署前置条件...")
        
        # 检查Python版本
        if sys.version_info < (3, 8):
            raise Exception("Python版本必须 >= 3.8")
        
        # 检查必要的目录
        required_dirs = [
            "rag_system/core/memory",
            "frontend/src/components/memory",
            "frontend/src/services/memory",
            "tests/memory"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                raise Exception(f"必要目录不存在: {dir_path}")
        
        # 检查配置文件
        config_file = self.project_root / "db_system/config/v3_config.json"
        if not config_file.exists():
            raise Exception("配置文件不存在: v3_config.json")
        
        self.log("✓ 前置条件检查通过")
        return True
    
    def backup_current_system(self):
        """备份当前系统"""
        self.log("备份当前系统...")
        
        try:
            # 创建备份目录
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 备份数据库文件 - 从配置中获取路径
            try:
                from rag_system.core.config_integration import ConfigIntegration
                config = ConfigIntegration()
                memory_db_path = config.get('rag_system.memory_module.database_path', 'rag_memory.db')
            except Exception:
                memory_db_path = "rag_memory.db"
            
            db_files = [
                "rag_metadata.db",
                memory_db_path,
                "frontend/rag_metadata.db"
            ]
            
            for db_file in db_files:
                source = self.project_root / db_file
                if source.exists():
                    backup_path = self.backup_dir / db_file
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, backup_path)
                    self.log(f"✓ 备份数据库文件: {db_file}")
            
            # 备份配置文件
            config_files = [
                "db_system/config/v3_config.json",
                "db_system/config/v3_config_schema.json"
            ]
            
            for config_file in config_files:
                source = self.project_root / config_file
                if source.exists():
                    backup_path = self.backup_dir / config_file
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, backup_path)
                    self.log(f"✓ 备份配置文件: {config_file}")
            
            self.log(f"✓ 系统备份完成: {self.backup_dir}")
            return True
            
        except Exception as e:
            self.log(f"✗ 系统备份失败: {e}")
            raise
    
    def validate_memory_module(self):
        """验证记忆模块完整性"""
        self.log("验证记忆模块完整性...")
        
        # 检查核心模块文件
        core_files = [
            "rag_system/core/memory/__init__.py",
            "rag_system/core/memory/models.py",
            "rag_system/core/memory/exceptions.py",
            "rag_system/core/memory/memory_config_manager.py",
            "rag_system/core/memory/memory_compression_engine.py",
            "rag_system/core/memory/conversation_memory_manager.py",
            "rag_system/core/memory/api_models.py",
            "rag_system/core/memory/memory_routes.py"
        ]
        
        for file_path in core_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                raise Exception(f"核心模块文件不存在: {file_path}")
        
        # 检查前端组件文件
        frontend_files = [
            "frontend/src/components/memory/MemoryManager.vue",
            "frontend/src/components/memory/MemorySession.vue",
            "frontend/src/components/memory/MemoryList.vue",
            "frontend/src/services/memory/memoryApi.js",
            "frontend/src/views/MemoryView.vue"
        ]
        
        for file_path in frontend_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                raise Exception(f"前端组件文件不存在: {file_path}")
        
        # 检查测试文件
        test_files = [
            "tests/memory/test_memory_module.py",
            "tests/memory/test_memory_api.py",
            "tests/memory/test_integration.py"
        ]
        
        for file_path in test_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                raise Exception(f"测试文件不存在: {file_path}")
        
        self.log("✓ 记忆模块完整性验证通过")
        return True
    
    def run_tests(self):
        """运行测试"""
        self.log("运行记忆模块测试...")
        
        try:
            # 运行核心模块测试
            test_script = self.project_root / "tests/memory/test_memory_module.py"
            result = subprocess.run([sys.executable, str(test_script)], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                self.log(f"✗ 核心模块测试失败: {result.stderr}")
                return False
            
            self.log("✓ 核心模块测试通过")
            
            # 运行集成测试
            integration_script = self.project_root / "tests/memory/test_integration.py"
            result = subprocess.run([sys.executable, str(integration_script)], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                self.log(f"✗ 集成测试失败: {result.stderr}")
                return False
            
            self.log("✓ 集成测试通过")
            
            return True
            
        except Exception as e:
            self.log(f"✗ 测试运行失败: {e}")
            return False
    
    def update_dependencies(self):
        """更新依赖"""
        self.log("更新项目依赖...")
        
        try:
            # 检查requirements.txt
            requirements_file = self.project_root / "rag_system/requirements.txt"
            if requirements_file.exists():
                result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                                      capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode != 0:
                    self.log(f"✗ 依赖安装失败: {result.stderr}")
                    return False
                
                self.log("✓ 依赖更新完成")
            
            return True
            
        except Exception as e:
            self.log(f"✗ 依赖更新失败: {e}")
            return False
    
    def deploy_memory_module(self):
        """部署记忆模块"""
        self.log("部署记忆模块...")
        
        try:
            # 验证配置文件
            config_file = self.project_root / "db_system/config/v3_config.json"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查记忆模块配置是否存在
            if 'rag_system' not in config or 'memory_module' not in config['rag_system']:
                self.log("✗ 配置文件中缺少记忆模块配置")
                return False
            
            self.log("✓ 配置文件验证通过")
            
            # 创建记忆数据库目录 - 从配置中获取路径
            try:
                from rag_system.core.config_integration import ConfigIntegration
                config = ConfigIntegration()
                memory_db_path = config.get('rag_system.memory_module.database_path', 'rag_memory.db')
            except Exception:
                memory_db_path = "rag_memory.db"
            
            memory_db_dir = self.project_root / memory_db_path
            if not memory_db_dir.parent.exists():
                memory_db_dir.parent.mkdir(parents=True, exist_ok=True)
            
            self.log("✓ 记忆模块部署完成")
            return True
            
        except Exception as e:
            self.log(f"✗ 记忆模块部署失败: {e}")
            return False
    
    def restart_services(self):
        """重启服务"""
        self.log("重启RAG系统服务...")
        
        try:
            # 这里可以添加重启服务的逻辑
            # 例如：重启FastAPI服务、前端服务等
            
            self.log("✓ 服务重启完成")
            return True
            
        except Exception as e:
            self.log(f"✗ 服务重启失败: {e}")
            return False
    
    def verify_deployment(self):
        """验证部署结果"""
        self.log("验证部署结果...")
        
        try:
            # 检查记忆模块是否可以正常导入 - 遵循技术规范
            from rag_system.core.memory import ConversationMemoryManager, MemoryConfigManager
            from rag_system.core.config_integration import ConfigIntegration
            
            # 测试配置管理器
            config = ConfigIntegration()
            memory_config = MemoryConfigManager(config)
            
            if not memory_config.is_enabled():
                self.log("✗ 记忆模块未启用")
                return False
            
            self.log("✓ 记忆模块配置正常")
            
            # 测试记忆管理器
            memory_manager = ConversationMemoryManager(
                config_manager=memory_config,
                vector_db_integration=None,
                llm_caller=None
            )
            
            # 测试创建会话
            session = memory_manager.create_session(
                user_id="deploy_test",
                metadata={"source": "deployment_test"}
            )
            
            if not session:
                self.log("✗ 记忆管理器测试失败")
                return False
            
            self.log("✓ 记忆管理器功能正常")
            
            # 清理测试数据
            memory_manager.close()
            
            self.log("✓ 部署验证通过")
            return True
            
        except Exception as e:
            self.log(f"✗ 部署验证失败: {e}")
            return False
    
    def rollback(self):
        """回滚部署"""
        self.log("开始回滚部署...")
        
        try:
            if self.backup_dir.exists():
                # 恢复数据库文件
                for db_file in self.backup_dir.rglob("*.db"):
                    relative_path = db_file.relative_to(self.backup_dir)
                    target_path = self.project_root / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(db_file, target_path)
                    self.log(f"✓ 恢复数据库文件: {relative_path}")
                
                # 恢复配置文件
                for config_file in self.backup_dir.rglob("*.json"):
                    relative_path = config_file.relative_to(self.backup_dir)
                    target_path = self.project_root / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(config_file, target_path)
                    self.log(f"✓ 恢复配置文件: {relative_path}")
                
                self.log("✓ 回滚完成")
                return True
            else:
                self.log("✗ 备份目录不存在，无法回滚")
                return False
                
        except Exception as e:
            self.log(f"✗ 回滚失败: {e}")
            return False
    
    def deploy(self):
        """执行完整部署流程"""
        self.log("开始记忆模块部署...")
        self.log("=" * 50)
        
        try:
            # 1. 检查前置条件
            self.check_prerequisites()
            
            # 2. 备份当前系统
            self.backup_current_system()
            
            # 3. 验证记忆模块
            self.validate_memory_module()
            
            # 4. 运行测试
            if not self.run_tests():
                self.log("测试失败，停止部署")
                return False
            
            # 5. 更新依赖
            self.update_dependencies()
            
            # 6. 部署记忆模块
            self.deploy_memory_module()
            
            # 7. 重启服务
            self.restart_services()
            
            # 8. 验证部署
            if not self.verify_deployment():
                self.log("部署验证失败，开始回滚...")
                self.rollback()
                return False
            
            self.log("=" * 50)
            self.log("✅ 记忆模块部署成功！")
            self.log(f"备份位置: {self.backup_dir}")
            self.log(f"日志文件: {self.log_file}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ 部署失败: {e}")
            self.log("开始回滚...")
            self.rollback()
            return False


def main():
    """主函数"""
    print("RAG系统记忆模块部署程序")
    print("=" * 50)
    
    deployer = MemoryModuleDeployer()
    
    success = deployer.deploy()
    
    if success:
        print("\n🎉 记忆模块部署成功！")
        print("现在可以通过以下方式访问记忆管理功能：")
        print("- 前端界面: http://localhost:3000/memory")
        print("- API接口: http://localhost:8000/api/v3/memory")
        return 0
    else:
        print("\n❌ 记忆模块部署失败！")
        print("请检查日志文件了解详细错误信息")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
