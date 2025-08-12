'''
程序说明：

## 1. V2版本RAG系统主程序入口
## 2. 集成V2引擎系统（图片、文本、表格、混合引擎）
## 3. 提供命令行接口和Web服务
## 4. 支持V2配置管理和错误处理
## 5. 基于原有架构，实现V2功能升级
'''

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入相关模块
from config.settings import Settings
from document_processing.pipeline import DocumentProcessingPipeline
from core.memory_manager import MemoryManager
from v2.config.v2_config import V2ConfigManager
from v2.core.hybrid_engine import HybridEngine
from v2.api.v2_routes import create_v2_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class V2RAGSystem:
    """
    V2版本RAG系统类
    """
    
    def __init__(self, config: Settings = None):
        """
        初始化V2 RAG系统
        :param config: 配置对象
        """
        if config is None:
            # 从配置文件加载设置
            self.config = Settings.load_from_file('config.json')
        else:
            self.config = config
        
        # 初始化V2配置管理器
        self.v2_config_manager = V2ConfigManager()
        self.v2_config = self.v2_config_manager.config
        
        self.qa_system = None
        self.memory_manager = None
        self.document_pipeline = None
        self.hybrid_engine = None
        
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
            
            # 初始化V2混合引擎
            vector_db_path = self.config.vector_db_dir
            if os.path.exists(vector_db_path):
                from document_processing.vector_generator import VectorGenerator
                vector_store = VectorGenerator(self.config).load_vector_store(vector_db_path)
                
                # 创建各个子引擎
                from v2.core.image_engine import ImageEngine
                from v2.core.text_engine import TextEngine
                from v2.core.table_engine import TableEngine
                
                image_engine = ImageEngine(
                    config=self.v2_config.image_engine,
                    vector_store=vector_store
                )
                text_engine = TextEngine(
                    config=self.v2_config.text_engine,
                    vector_store=vector_store
                )
                table_engine = TableEngine(
                    config=self.v2_config.table_engine,
                    vector_store=vector_store
                )
                
                self.hybrid_engine = HybridEngine(
                    config=self.v2_config.hybrid_engine,
                    image_engine=image_engine,
                    text_engine=text_engine,
                    table_engine=table_engine
                )
                
                # 将记忆管理器集成到混合引擎中
                if hasattr(self.hybrid_engine, 'memory_manager'):
                    self.hybrid_engine.memory_manager = self.memory_manager
                else:
                    # 如果混合引擎没有memory_manager属性，动态添加
                    setattr(self.hybrid_engine, 'memory_manager', self.memory_manager)
                
                logger.info("V2混合引擎初始化成功，记忆管理器已集成")
            else:
                logger.warning(f"向量数据库路径不存在: {vector_db_path}")
                
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
            success = self.document_pipeline.run_pipeline(pdf_dir, output_dir)
            
            if success:
                logger.info("文档处理完成")
                return True
            else:
                logger.error("文档处理失败")
                return False
                
        except Exception as e:
            logger.error(f"文档处理过程中发生错误: {e}")
            return False
    
    def ask_question(self, question: str, query_type: str = 'hybrid', user_id: str = "default_user", use_memory: bool = True) -> dict:
        """
        使用V2引擎回答问题
        :param question: 问题
        :param query_type: 查询类型 (hybrid, image, text, table)
        :param user_id: 用户ID
        :param use_memory: 是否使用记忆
        :return: 查询结果
        """
        try:
            if not self.hybrid_engine:
                return {
                    'success': False,
                    'error': 'V2混合引擎未初始化'
                }
            
            logger.info(f"用户 {user_id} 提问: {question}")
            logger.info(f"查询类型: {query_type}")
            
            # 执行查询
            if query_type == 'hybrid':
                result = self.hybrid_engine.process_query(question)
            elif query_type == 'image':
                result = self.hybrid_engine.image_engine.process_query(question)
            elif query_type == 'text':
                result = self.hybrid_engine.text_engine.process_query(question)
            elif query_type == 'table':
                result = self.hybrid_engine.table_engine.process_query(question)
            else:
                return {
                    'success': False,
                    'error': f'不支持的查询类型: {query_type}'
                }
            
            # 格式化响应
            response = {
                'success': True,
                'question': question,
                'query_type': query_type,
                'answer': result.answer if hasattr(result, 'answer') else str(result),
                'sources': result.sources if hasattr(result, 'sources') else [],
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'use_memory': use_memory
            }
            
            return response
            
        except Exception as e:
            logger.error(f"查询过程中发生错误: {e}")
            return {
                'success': False,
                'error': f'查询失败: {str(e)}'
            }
    
    def get_system_status(self) -> dict:
        """
        获取系统状态
        :return: 系统状态信息
        """
        try:
            status = {
                'system_version': 'V2.0.0',
                'config_loaded': self.v2_config is not None,
                'hybrid_engine_ready': self.hybrid_engine is not None,
                'memory_manager_ready': self.memory_manager is not None,
                'document_pipeline_ready': self.document_pipeline is not None
            }
            
            # 获取向量数据库统计信息
            if self.config.vector_db_dir and os.path.exists(self.config.vector_db_dir):
                try:
                    vector_db_path = Path(self.config.vector_db_dir)
                    metadata_file = vector_db_path / 'metadata.pkl'
                    index_file = vector_db_path / 'index.faiss'
                    
                    status['vector_db'] = {
                        'path': str(vector_db_path),
                        'metadata_exists': metadata_file.exists(),
                        'index_exists': index_file.exists(),
                        'metadata_size': metadata_file.stat().st_size if metadata_file.exists() else 0,
                        'index_size': index_file.stat().st_size if index_file.exists() else 0
                    }
                except Exception as e:
                    status['vector_db'] = {'error': str(e)}
            
            # 获取记忆统计信息
            if self.memory_manager:
                try:
                    memory_stats = self.memory_manager.get_memory_stats()
                    status['memory_stats'] = memory_stats
                except Exception as e:
                    status['memory_stats'] = {'error': str(e)}
            
            # 获取V2配置信息
            if self.v2_config:
                status['v2_config'] = {
                    'image_engine_ready': hasattr(self.v2_config, 'image_engine'),
                    'text_engine_ready': hasattr(self.v2_config, 'text_engine'),
                    'table_engine_ready': hasattr(self.v2_config, 'table_engine'),
                    'hybrid_engine_ready': hasattr(self.v2_config, 'hybrid_engine')
                }
            
            return status
            
        except Exception as e:
            logger.error(f"获取系统状态时发生错误: {e}")
            return {'error': str(e)}
    
    def start_web_server(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        启动V2 Web服务器
        :param host: 主机地址
        :param port: 端口
        :param debug: 调试模式
        """
        try:
            # 创建V2 Flask应用
            from v2.api.v2_routes import create_v2_app
            app = create_v2_app(self.config, self.v2_config, self.hybrid_engine)
            logger.info(f"启动V2 Web服务器: http://{host}:{port}")
            app.run(host=host, port=port, debug=debug)
            
        except Exception as e:
            logger.error(f"启动V2 Web服务器失败: {e}")


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='V2版本RAG系统')
    parser.add_argument('--mode', choices=['process', 'qa', 'web', 'status'], 
                       default='status', help='运行模式')
    parser.add_argument('--question', type=str, help='问题（qa模式）')
    parser.add_argument('--query-type', choices=['hybrid', 'image', 'text', 'table'], 
                       default='hybrid', help='查询类型（qa模式）')
    parser.add_argument('--user-id', type=str, default='default_user', help='用户ID')
    parser.add_argument('--no-memory', action='store_true', help='不使用记忆（qa模式）')
    parser.add_argument('--pdf-dir', type=str, help='PDF目录（process模式）')
    parser.add_argument('--output-dir', type=str, help='输出目录（process模式）')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Web服务器主机地址')
    parser.add_argument('--port', type=int, default=5000, help='Web服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    # 初始化V2系统
    print("🚀 初始化V2 RAG系统...")
    v2_rag_system = V2RAGSystem()
    
    if args.mode == 'status':
        # 显示系统状态
        print("\n📊 V2系统状态:")
        status = v2_rag_system.get_system_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    elif args.mode == 'process':
        # 处理文档
        print("\n📄 开始处理文档...")
        success = v2_rag_system.process_documents(args.pdf_dir, args.output_dir)
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
        print(f"🔍 查询类型: {args.query_type}")
        result = v2_rag_system.ask_question(
            args.question, 
            args.query_type,
            args.user_id, 
            not args.no_memory
        )
        
        if result['success']:
            print(f"✅ 回答: {result['answer']}")
            if result.get('sources'):
                print(f"📚 来源: {len(result['sources'])} 个文档")
        else:
            print(f"❌ 错误: {result['error']}")
    
    elif args.mode == 'web':
        # Web服务器模式
        print(f"\n🌐 启动V2 Web服务器...")
        v2_rag_system.start_web_server(args.host, args.port, args.debug)


if __name__ == '__main__':
    main()
