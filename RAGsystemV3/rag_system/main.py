"""
RAG系统主程序入口

启动RAG系统的API服务
"""

import logging
import os
import sys

# 导入V3配置管理器 - 使用完整包路径
try:
    from db_system.config.config_manager import ConfigManager
    from db_system.config.path_manager import PathManager
except ImportError as e:
    logging.error(f"无法导入V3配置管理器: {e}")
    raise

from rag_system.api.main import create_app
import uvicorn

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO", logs_dir: str = None):
    """
    设置日志配置
    
    :param log_level: 日志级别
    :param logs_dir: 日志目录
    """
    try:
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"无效的日志级别: {log_level}")

        # 使用传入的logs_dir，如果没有则使用默认值
        if logs_dir:
            log_file_path = os.path.join(logs_dir, 'rag_system.log')
        else:
            log_file_path = './rag_system.log'  # 默认值

        # 确保日志目录存在
        log_dir = os.path.dirname(log_file_path)
        os.makedirs(log_dir, exist_ok=True)

        # 清除现有的日志配置
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # 创建新的日志配置
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 配置根日志器
        logging.root.setLevel(numeric_level)
        logging.root.addHandler(console_handler)
        logging.root.addHandler(file_handler)
        
        logging.info(f"日志配置完成 - 级别: {log_level}, 文件: {log_file_path}")
        
    except Exception as e:
        logging.error(f"日志配置失败: {e}")
        raise


def main():
    """主函数"""
    try:
        # 创建配置管理器并获取日志目录
        config_manager = ConfigManager()
        config_manager.load_config()  # 加载配置
        logs_dir = config_manager.get_path('logs_dir')  # 使用M06的路径管理功能
        
        # 设置日志（传入logs_dir）
        setup_logging("INFO", logs_dir)
        
        # 添加测试日志（在日志配置完成后）
        logging.info(f"RAG系统日志目录配置: {logs_dir}")
        logging.info("V3版本RAG系统启动完成")
        
        # 创建FastAPI应用
        app = create_app()
        
        # 启动服务器
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,  # 生产环境关闭热重载
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        logging.info("收到中断信号，正在关闭服务...")
    except Exception as e:
        logging.error(f"服务启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
