"""
RAG系统主程序入口

启动RAG系统的API服务
"""

import logging

from rag_system.api.main import create_app
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('rag_system.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        logger.info("启动V3 RAG系统...")
        
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
        logger.info("收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
