'''
程序说明：
## 1. 统一的主程序入口
## 2. 整合文档处理、问答系统、API服务
## 3. 提供命令行接口和Web服务
## 4. 支持配置管理和错误处理
'''

import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入相关模块
from config.settings import Settings
from document_processing.pipeline import DocumentProcessingPipeline
from core.qa_system import load_qa_system
from core.memory_manager import MemoryManager
from api.app import create_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedRAGSystem:
    """
    统一的RAG系统类
    """
    
    def __init__(self, config: Settings = None):
        """
        初始化RAG系统
        :param config: 配置对象
        """
        if config is None:
            # 从配置文件加载设置
            self.config = Settings.load_from_file('config.json')
        else:
            self.config = config
        self.qa_system = None
        self.memory_manager = None
        self.document_pipeline = None
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self):
        """
        初始化系统组件
        """
        try:
            # 初始化文档处理管道
            self.document_pipeline = DocumentProcessingPipeline(self.config.to_dict())
            logger.info("文档处理管道初始化成功")
            
            # 初始化记忆管理器
            self.memory_manager = MemoryManager(self.config.memory_db_dir)
            logger.info("记忆管理器初始化成功")
            
            # 初始化问答系统
            api_key = self.config.dashscope_api_key
            vector_db_path = self.config.vector_db_dir
            
            if api_key and api_key != '你的APIKEY':
                self.qa_system = load_qa_system(vector_db_path, api_key, self.memory_manager)
                if self.qa_system:
                    logger.info("问答系统初始化成功")
                else:
                    logger.warning("问答系统初始化失败")
            else:
                logger.warning("未配置API密钥，问答系统无法初始化")
                
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
    
    def process_documents(self, pdf_dir: str = None, output_dir: str = None) -> bool:
        """
        处理文档
        :param pdf_dir: PDF目录
        :param output_dir: 输出目录
        :return: 是否成功
        """
        try:
            if not self.document_pipeline:
                logger.error("文档处理管道未初始化")
                return False
            
            # 使用配置中的路径
            pdf_dir = pdf_dir or self.config.pdf_dir
            output_dir = output_dir or self.config.output_dir
            
            logger.info(f"开始处理文档...")
            logger.info(f"PDF目录: {pdf_dir}")
            logger.info(f"输出目录: {output_dir}")
            
            # 执行文档处理
            success = self.document_pipeline.process_pipeline(pdf_dir, output_dir)
            
            if success:
                logger.info("文档处理完成")
                # 重新初始化问答系统
                self._initialize_components()
            else:
                logger.error("文档处理失败")
            
            return success
            
        except Exception as e:
            logger.error(f"处理文档时发生错误: {e}")
            return False
    
    def ask_question(self, question: str, user_id: str = "default_user", use_memory: bool = True) -> dict:
        """
        提问
        :param question: 问题
        :param user_id: 用户ID
        :param use_memory: 是否使用记忆
        :return: 回答结果
        """
        try:
            if not self.qa_system:
                return {
                    'success': False,
                    'error': '问答系统未初始化'
                }
            
            if use_memory:
                result = self.qa_system.answer_with_memory(user_id, question)
            else:
                result = self.qa_system.answer_question(question)
            
            return {
                'success': True,
                'question': question,
                'answer': result.get('answer', ''),
                'sources': result.get('sources', []),
                'cost': result.get('cost', 0.0),
                'user_id': user_id,
                'use_memory': use_memory
            }
            
        except Exception as e:
            logger.error(f"提问时发生错误: {e}")
            return {
                'success': False,
                'error': f'提问失败: {str(e)}'
            }
    
    def get_system_status(self) -> dict:
        """
        获取系统状态
        :return: 系统状态信息
        """
        try:
            status = {
                'qa_system': self.qa_system is not None,
                'memory_manager': self.memory_manager is not None,
                'document_pipeline': self.document_pipeline is not None,
                'api_key_configured': bool(self.config.dashscope_api_key and self.config.dashscope_api_key != '你的APIKEY'),
                'vector_store_loaded': self.qa_system and self.qa_system.vector_store is not None
            }
            
            # 获取向量存储统计信息
            if self.qa_system and self.qa_system.vector_store:
                try:
                    stats = self.qa_system.get_memory_stats()
                    status['vector_store_stats'] = stats
                except Exception as e:
                    status['vector_store_stats'] = {'error': str(e)}
            
            # 获取记忆统计信息
            if self.memory_manager:
                try:
                    memory_stats = self.memory_manager.get_memory_stats()
                    status['memory_stats'] = memory_stats
                except Exception as e:
                    status['memory_stats'] = {'error': str(e)}
            
            return status
            
        except Exception as e:
            logger.error(f"获取系统状态时发生错误: {e}")
            return {'error': str(e)}
    
    def start_web_server(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        启动Web服务器
        :param host: 主机地址
        :param port: 端口
        :param debug: 调试模式
        """
        try:
            app = create_app(self.config)
            logger.info(f"启动Web服务器: http://{host}:{port}")
            app.run(host=host, port=port, debug=debug)
            
        except Exception as e:
            logger.error(f"启动Web服务器失败: {e}")


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='统一的RAG系统')
    parser.add_argument('--mode', choices=['process', 'qa', 'web', 'status'], 
                       default='status', help='运行模式')
    parser.add_argument('--question', type=str, help='问题（qa模式）')
    parser.add_argument('--user-id', type=str, default='default_user', help='用户ID')
    parser.add_argument('--no-memory', action='store_true', help='不使用记忆（qa模式）')
    parser.add_argument('--pdf-dir', type=str, help='PDF目录（process模式）')
    parser.add_argument('--output-dir', type=str, help='输出目录（process模式）')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Web服务器主机地址')
    parser.add_argument('--port', type=int, default=5000, help='Web服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    # 初始化系统
    print("🚀 初始化RAG系统...")
    rag_system = UnifiedRAGSystem()
    
    if args.mode == 'status':
        # 显示系统状态
        print("\n📊 系统状态:")
        status = rag_system.get_system_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    elif args.mode == 'process':
        # 处理文档
        print("\n📄 开始处理文档...")
        success = rag_system.process_documents(args.pdf_dir, args.output_dir)
        if success:
            print("✅ 文档处理完成")
        else:
            print("❌ 文档处理失败")
    
    elif args.mode == 'qa':
        # 问答模式
        if not args.question:
            print("❌ 请提供问题")
            return
        
        print(f"\n❓ 问题: {args.question}")
        result = rag_system.ask_question(
            args.question, 
            args.user_id, 
            not args.no_memory
        )
        
        if result['success']:
            print(f"✅ 回答: {result['answer']}")
            if result.get('sources'):
                print(f"📚 来源: {len(result['sources'])} 个文档")
            if result.get('cost'):
                print(f"💰 成本: {result['cost']:.6f} 元")
        else:
            print(f"❌ 错误: {result['error']}")
    
    elif args.mode == 'web':
        # Web服务器模式
        print(f"\n🌐 启动Web服务器...")
        rag_system.start_web_server(args.host, args.port, args.debug)


if __name__ == '__main__':
    main() 