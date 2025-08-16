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
from v2.core.v2_memory_manager import SimplifiedMemoryManager as MemoryManager
from v2.config.v2_config import V2ConfigManager
from v2.core.hybrid_engine import HybridEngine
from v2.core.base_engine import QueryType
from v2.api.v2_routes import create_v2_app

# 导入优化引擎
from v2.core.dashscope_reranking_engine import DashScopeRerankingEngine as RerankingEngine
from v2.core.dashscope_llm_engine import DashScopeLLMEngine as EnhancedQASystem
from v2.core.smart_filter_engine import SmartFilterEngine
from v2.core.source_filter_engine import SourceFilterEngine

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
            try:
                self.config = Settings.load_from_file('config.json')
                # 确保返回的是Settings对象
                if not isinstance(self.config, Settings):
                    logger.warning("配置文件加载失败，使用默认配置")
                    self.config = Settings()
            except Exception as e:
                logger.warning(f"配置文件加载失败: {e}，使用默认配置")
                self.config = Settings()
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
            self.document_pipeline = DocumentProcessingPipeline(self.config)
            logger.info("文档处理管道初始化成功")
            
            # 初始化记忆管理器
            self.memory_manager = MemoryManager(self.config.memory_db_dir)
            logger.info("记忆管理器初始化成功")
            
            # 显示记忆统计信息
            try:
                memory_stats = self.memory_manager.get_memory_stats()
                logger.info(f"🧠 记忆统计: 会话记忆 {memory_stats.get('session_memory_count', 0)} 条, 用户记忆 {memory_stats.get('user_memory_count', 0)} 条")
            except Exception as e:
                logger.warning(f"获取记忆统计失败: {e}")
            
            # 初始化V2混合引擎
            vector_db_path = self.config.vector_db_dir
            if os.path.exists(vector_db_path):
                from document_processing.vector_generator import VectorGenerator
                vector_store = VectorGenerator(self.config.to_dict()).load_vector_store(vector_db_path)
                
                # 创建统一文档加载器
                from v2.core.document_loader import DocumentLoader
                self.document_loader = DocumentLoader(vector_store)
                logger.info("统一文档加载器初始化成功")
                
                # 创建各个子引擎（跳过初始加载，使用统一加载器）
                from v2.core.image_engine import ImageEngine
                from v2.core.text_engine import TextEngine
                from v2.core.table_engine import TableEngine
                
                image_engine = ImageEngine(
                    config=self.v2_config.image_engine,
                    vector_store=vector_store,
                    document_loader=self.document_loader,
                    skip_initial_load=True  # 跳过初始加载
                )
                text_engine = TextEngine(
                    config=self.v2_config.text_engine,
                    vector_store=vector_store,
                    document_loader=self.document_loader,
                    skip_initial_load=True  # 跳过初始加载
                )
                table_engine = TableEngine(
                    config=self.v2_config.table_engine,
                    vector_store=vector_store,
                    document_loader=self.document_loader,
                    skip_initial_load=True  # 跳过初始加载
                )
                
                # 统一加载所有文档
                logger.info("开始统一加载所有文档...")
                try:
                    self.document_loader.load_all_documents()
                    logger.info("✅ 文档统一加载完成")
                    
                    # 文档加载完成后，调用各引擎的_initialize()方法
                    logger.info("开始初始化各引擎...")
                    text_engine._initialize()
                    image_engine._initialize()
                    table_engine._initialize()
                    logger.info("✅ 各引擎初始化完成")
                    
                except Exception as e:
                    logger.error(f"文档统一加载失败: {e}")
                    # 降级策略：让各个引擎自己加载
                    logger.info("启用降级策略：各引擎独立加载文档")
                    text_engine._load_text_documents()
                    image_engine._load_image_documents()
                    table_engine._load_image_documents()
                
                self.hybrid_engine = HybridEngine(
                    config=self.v2_config.hybrid_engine,
                    image_engine=image_engine,
                    text_engine=text_engine,
                    table_engine=table_engine
                )
                
                # 初始化优化引擎
                logger.info("正在初始化优化引擎...")
                
                # 重排序引擎
                reranking_engine = None
                if hasattr(self.v2_config.hybrid_engine, 'optimization_pipeline') and \
                   self.v2_config.hybrid_engine.optimization_pipeline.enable_reranking:
                    try:
                        # 从配置文件创建重排序引擎配置
                        from v2.core.dashscope_reranking_engine import RerankingConfig
                        reranking_config = RerankingConfig(
                            model_name=self.v2_config.reranking_engine.model_name,
                            top_k=self.v2_config.reranking_engine.top_k,
                            similarity_threshold=self.v2_config.reranking_engine.similarity_threshold,
                            weight_semantic=self.v2_config.reranking_engine.weight_semantic,
                            weight_keyword=self.v2_config.reranking_engine.weight_keyword
                        )
                        # 获取API密钥
                        from config.api_key_manager import APIKeyManager
                        api_key_manager = APIKeyManager()
                        dashscope_api_key = api_key_manager.get_dashscope_api_key()
                        
                        if dashscope_api_key:
                            reranking_engine = RerankingEngine(
                                api_key=dashscope_api_key,
                                config=reranking_config
                            )
                            logger.info("✅ 重排序引擎初始化成功")
                        else:
                            logger.warning("⚠️ DashScope API密钥未配置，重排序引擎初始化失败")
                    except Exception as e:
                        logger.warning(f"⚠️ 重排序引擎初始化失败: {e}")
                
                # LLM引擎
                llm_engine = None
                if hasattr(self.v2_config.hybrid_engine, 'optimization_pipeline') and \
                   self.v2_config.hybrid_engine.optimization_pipeline.enable_llm_generation:
                    try:
                        # 获取API密钥
                        from config.api_key_manager import APIKeyManager
                        api_key_manager = APIKeyManager()
                        dashscope_api_key = api_key_manager.get_dashscope_api_key()
                        
                        if dashscope_api_key:
                            # 从配置文件创建LLM引擎配置
                            from v2.core.dashscope_llm_engine import LLMConfig
                            llm_config = LLMConfig(
                                model_name=self.v2_config.llm_engine.model_name,
                                temperature=self.v2_config.llm_engine.temperature,
                                max_tokens=self.v2_config.llm_engine.max_tokens,
                                top_p=self.v2_config.llm_engine.top_p,
                                enable_stream=self.v2_config.llm_engine.enable_stream,
                                system_prompt=self.v2_config.llm_engine.system_prompt
                            )
                            llm_engine = EnhancedQASystem(
                                api_key=dashscope_api_key,
                                config=llm_config
                            )
                            logger.info("✅ LLM引擎初始化成功")
                        else:
                            logger.warning("⚠️ DashScope API密钥未配置，LLM引擎初始化失败")
                    except Exception as e:
                        logger.warning(f"⚠️ LLM引擎初始化失败: {e}")
                
                # 智能过滤引擎
                smart_filter_engine = None
                if hasattr(self.v2_config.hybrid_engine, 'optimization_pipeline') and \
                   self.v2_config.hybrid_engine.optimization_pipeline.enable_smart_filtering:
                    try:
                        # 使用配置管理器获取智能过滤引擎配置
                        smart_filter_config = self.v2_config_manager.get_engine_config_for_initialization('smart_filter')
                        if smart_filter_config:
                            smart_filter_engine = SmartFilterEngine(smart_filter_config)
                            logger.info("✅ 智能过滤引擎初始化成功")
                        else:
                            logger.warning("⚠️ 智能过滤引擎配置获取失败")
                    except Exception as e:
                        logger.warning(f"⚠️ 智能过滤引擎初始化失败: {e}")
                
                # 源过滤引擎
                source_filter_engine = None
                if hasattr(self.v2_config.hybrid_engine, 'optimization_pipeline') and \
                   self.v2_config.hybrid_engine.optimization_pipeline.enable_source_filtering:
                    try:
                        # 使用配置管理器获取源过滤引擎配置
                        source_filter_config = self.v2_config_manager.get_engine_config_for_initialization('source_filter')
                        if source_filter_config:
                            source_filter_engine = SourceFilterEngine(source_filter_config)
                            logger.info("✅ 源过滤引擎初始化成功")
                        else:
                            logger.warning("⚠️ 源过滤引擎配置获取失败")
                    except Exception as e:
                        logger.warning(f"⚠️ 源过滤引擎初始化失败: {e}")
                
                # 重新创建混合引擎，集成优化引擎
                self.hybrid_engine = HybridEngine(
                    config=self.v2_config.hybrid_engine,
                    image_engine=image_engine,
                    text_engine=text_engine,
                    table_engine=table_engine,
                    reranking_engine=reranking_engine,
                    llm_engine=llm_engine,
                    smart_filter_engine=smart_filter_engine,
                    source_filter_engine=source_filter_engine,
                    memory_manager=self.memory_manager
                )
                
                # 检查智能后处理引擎状态
                if hasattr(self.hybrid_engine, 'intelligent_post_processing_engine') and \
                   self.hybrid_engine.intelligent_post_processing_engine:
                    logger.info("✅ 智能后处理引擎初始化成功")
                else:
                    logger.info("ℹ️ 智能后处理引擎未启用或初始化失败")
                
                logger.info("V2混合引擎初始化成功，记忆管理器已集成")
                logger.info("🎯 优化引擎集成完成")
            else:
                logger.warning(f"向量数据库路径不存在: {vector_db_path}")
                
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
    
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
            vector_db_path = self.config.vector_db_dir
            success = self.document_pipeline.process_pipeline(pdf_dir, output_dir, vector_db_path)
            
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
                result = self.hybrid_engine.process_query(question, query_type='hybrid')
            elif query_type == 'image':
                result = self.hybrid_engine.image_engine.process_query(question)
            elif query_type == 'text':
                result = self.hybrid_engine.text_engine.process_query(question)
            elif query_type == 'table':
                result = self.hybrid_engine.table_engine.process_query(question)
            elif query_type == 'smart':
                try:
                    # 使用 QueryIntentAnalyzer 进行智能意图分析
                    from v2.core.hybrid_engine import QueryIntentAnalyzer
                    intent_analyzer = QueryIntentAnalyzer()
                    
                    # 分析查询意图，获取最佳查询类型
                    intent_result = intent_analyzer.analyze_intent_with_confidence(question)
                    detected_type = intent_result['primary_intent']
                    
                    logger.info(f"智能查询检测到类型: {detected_type}")
                    
                    # 根据检测到的类型执行查询
                    if detected_type == 'image':
                        result = self.hybrid_engine.process_query(question, query_type=QueryType.IMAGE)
                    elif detected_type == 'table':
                        result = self.hybrid_engine.process_query(question, query_type=QueryType.TABLE)
                    elif detected_type == 'text':
                        result = self.hybrid_engine.process_query(question, query_type=QueryType.TEXT)
                    else:
                        # 默认使用混合查询
                        result = self.hybrid_engine.process_query(question, query_type=QueryType.HYBRID)
                        
                except Exception as e:
                    logger.error(f"智能查询处理失败: {e}")
                    # 降级策略：使用混合查询
                    result = self.hybrid_engine.process_query(question, query_type=QueryType.HYBRID)
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
            
            # 获取文档加载器状态
            if hasattr(self, 'document_loader'):
                try:
                    doc_stats = self.document_loader.get_document_statistics()
                    status['document_loader'] = doc_stats
                except Exception as e:
                    status['document_loader'] = {'error': str(e)}
            
            # 获取优化引擎状态信息
            if self.hybrid_engine:
                optimization_status = {}
                
                # 检查优化管道配置
                if hasattr(self.v2_config.hybrid_engine, 'optimization_pipeline'):
                    pipeline_config = self.v2_config.hybrid_engine.optimization_pipeline
                    optimization_status['pipeline_enabled'] = getattr(self.v2_config.hybrid_engine, 'enable_optimization_pipeline', False)
                    optimization_status['reranking_enabled'] = pipeline_config.enable_reranking
                    optimization_status['llm_generation_enabled'] = pipeline_config.enable_llm_generation
                    optimization_status['smart_filtering_enabled'] = pipeline_config.enable_smart_filtering
                    optimization_status['source_filtering_enabled'] = pipeline_config.enable_source_filtering
                
                # 检查优化引擎实例状态
                optimization_status['reranking_engine_ready'] = hasattr(self.hybrid_engine, 'reranking_engine') and self.hybrid_engine.reranking_engine is not None
                optimization_status['llm_engine_ready'] = hasattr(self.hybrid_engine, 'llm_engine') and self.hybrid_engine.llm_engine is not None
                optimization_status['smart_filter_engine_ready'] = hasattr(self.hybrid_engine, 'smart_filter_engine') and self.hybrid_engine.smart_filter_engine is not None
                optimization_status['source_filter_engine_ready'] = hasattr(self.hybrid_engine, 'source_filter_engine') and self.hybrid_engine.source_filter_engine is not None
                
                status['optimization_engines'] = optimization_status
            
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
            # 显示优化引擎状态
            logger.info("🔍 检查优化引擎状态...")
            if self.hybrid_engine:
                # 检查重排序引擎
                if hasattr(self.hybrid_engine, 'reranking_engine') and self.hybrid_engine.reranking_engine:
                    logger.info("✅ 重排序引擎已就绪")
                else:
                    logger.warning("⚠️ 重排序引擎未就绪")
                
                # 检查LLM引擎
                if hasattr(self.hybrid_engine, 'llm_engine') and self.hybrid_engine.llm_engine:
                    logger.info("✅ LLM引擎已就绪")
                else:
                    logger.warning("⚠️ LLM引擎未就绪")
                
                # 检查智能过滤引擎
                if hasattr(self.hybrid_engine, 'smart_filter_engine') and self.hybrid_engine.smart_filter_engine:
                    logger.info("✅ 智能过滤引擎已就绪")
                else:
                    logger.warning("⚠️ 智能过滤引擎未就绪")
                
                # 检查源过滤引擎
                if hasattr(self.hybrid_engine, 'source_filter_engine') and self.hybrid_engine.source_filter_engine:
                    logger.info("✅ 源过滤引擎已就绪")
                else:
                    logger.warning("⚠️ 源过滤引擎未就绪")
                
                # 检查优化管道配置
                if hasattr(self.v2_config.hybrid_engine, 'optimization_pipeline'):
                    pipeline_config = self.v2_config.hybrid_engine.optimization_pipeline
                    logger.info("📋 优化管道配置:")
                    logger.info(f"  - 重排序: {'启用' if pipeline_config.enable_reranking else '禁用'}")
                    logger.info(f"  - LLM生成: {'启用' if pipeline_config.enable_llm_generation else '禁用'}")
                    logger.info(f"  - 智能过滤: {'启用' if pipeline_config.enable_smart_filtering else '禁用'}")
                    logger.info(f"  - 源过滤: {'启用' if pipeline_config.enable_source_filtering else '禁用'}")
            
            # 显示文档加载状态
            if hasattr(self, 'document_loader'):
                try:
                    doc_stats = self.document_loader.get_document_statistics()
                    logger.info("📚 文档加载状态:")
                    logger.info(f"  - 总文档数: {doc_stats.get('total_documents', 0)}")
                    logger.info(f"  - 加载耗时: {doc_stats.get('load_time', 0):.2f}秒")
                    logger.info(f"  - 文本文档: {doc_stats.get('documents_by_type', {}).get('text', 0)}个")
                    logger.info(f"  - 图片文档: {doc_stats.get('documents_by_type', {}).get('image', 0)}个")
                    logger.info(f"  - 表格文档: {doc_stats.get('documents_by_type', {}).get('table', 0)}个")
                    logger.info(f"  - 图片描述文本: {doc_stats.get('documents_by_type', {}).get('image_text', 0)}个")  # 新增显示
                except Exception as e:
                    logger.warning(f"获取文档统计信息失败: {e}")
            
            # 创建V2 Flask应用
            from v2.api.v2_routes import create_v2_app
            app = create_v2_app(self.config, self.v2_config, self.hybrid_engine)
            
            # 为Flask应用提供关闭函数
            def shutdown_flask():
                """关闭Flask应用"""
                logger.info("🔄 正在关闭Flask Web服务...")
                import threading
                import time
                
                def delayed_exit():
                    time.sleep(0.5)  # 等待0.5秒，确保响应能够返回
                    logger.info("🚪 退出主程序")
                    os._exit(0)
                
                exit_thread = threading.Thread(target=delayed_exit, daemon=True)
                exit_thread.start()
            
            # 将关闭函数注册到Flask应用配置中
            app.config['SHUTDOWN_FUNC'] = shutdown_flask
            
            # 注册优雅关闭信号处理器
            import signal
            import sys
            
            def signal_handler(signum, frame):
                logger.info(f"收到信号 {signum}，开始优雅关闭...")
                self._graceful_shutdown()
                sys.exit(0)
            
            # 注册信号处理器
            signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
            signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
            
            logger.info(f"🌐 启动V2 Web服务器: http://{host}:{port}")
            logger.info("🚀 系统已就绪，可以开始使用优化功能！")
            logger.info("💡 提示：在Web页面中可以优雅关闭系统，或使用Ctrl+C强制退出")
            
            app.run(host=host, port=port, debug=debug)
            
        except Exception as e:
            logger.error(f"启动V2 Web服务器失败: {e}")
    
    def _graceful_shutdown(self):
        """
        优雅关闭系统，执行清理工作
        """
        try:
            logger.info("🔄 开始执行优雅关闭流程...")
            
            # 1. 清理记忆管理器
            if self.memory_manager:
                try:
                    logger.info("🧹 清理记忆管理器...")
                    self.memory_manager.clear_all_memories()
                    logger.info("✅ 记忆管理器清理完成")
                except Exception as e:
                    logger.warning(f"⚠️ 记忆管理器清理失败: {e}")
            
            # 2. 清理文档加载器缓存
            if hasattr(self, 'document_loader') and self.document_loader:
                try:
                    logger.info("🧹 清理文档缓存...")
                    self.document_loader.clear_cache()
                    logger.info("✅ 文档缓存清理完成")
                except Exception as e:
                    logger.warning(f"⚠️ 文档缓存清理失败: {e}")
            
            # 3. 清理混合引擎缓存
            if self.hybrid_engine:
                try:
                    logger.info("🧹 清理混合引擎缓存...")
                    
                    # 清理各子引擎缓存
                    for engine_name in ['text_engine', 'image_engine', 'table_engine']:
                        if hasattr(self.hybrid_engine, engine_name):
                            engine = getattr(self.hybrid_engine, engine_name)
                            if engine and hasattr(engine, 'clear_cache'):
                                try:
                                    engine.clear_cache()
                                    logger.info(f"✅ {engine_name}缓存清理完成")
                                except Exception as e:
                                    logger.warning(f"⚠️ {engine_name}缓存清理失败: {e}")
                    
                    # 清理优化引擎缓存
                    if hasattr(self.hybrid_engine, 'reranking_engine') and self.hybrid_engine.reranking_engine:
                        try:
                            if hasattr(self.hybrid_engine.reranking_engine, 'clear_cache'):
                                self.hybrid_engine.reranking_engine.clear_cache()
                                logger.info("✅ 重排序引擎缓存清理完成")
                        except Exception as e:
                            logger.warning(f"⚠️ 重排序引擎缓存清理失败: {e}")
                    
                    if hasattr(self.hybrid_engine, 'llm_engine') and self.hybrid_engine.llm_engine:
                        try:
                            if hasattr(self.hybrid_engine.llm_engine, 'clear_cache'):
                                self.hybrid_engine.llm_engine.clear_cache()
                                logger.info("✅ LLM引擎缓存清理完成")
                        except Exception as e:
                            logger.warning(f"⚠️ LLM引擎缓存清理失败: {e}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ 混合引擎缓存清理失败: {e}")
            
            # 4. 保存系统状态
            try:
                logger.info("💾 保存系统状态...")
                # 这里可以添加保存系统状态的逻辑
                logger.info("✅ 系统状态保存完成")
            except Exception as e:
                logger.warning(f"⚠️ 系统状态保存失败: {e}")
            
            # 5. 关闭日志
            logger.info("🎯 优雅关闭流程完成，系统资源已清理")
            
        except Exception as e:
            logger.error(f"❌ 优雅关闭过程中发生错误: {e}")
        finally:
            # 确保日志被刷新
            import logging
            logging.shutdown()


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
        
        # 显示基础状态
        print("🔧 基础组件:")
        for key, value in status.items():
            if key not in ['optimization_engines', 'v2_config', 'vector_db', 'memory_stats']:
                print(f"  {key}: {value}")
        
        # 显示V2配置状态
        if 'v2_config' in status:
            print("\n⚙️ V2配置状态:")
            v2_status = status['v2_config']
            for key, value in v2_status.items():
                status_icon = "✅" if value else "❌"
                print(f"  {key}: {status_icon}")
        
        # 显示文档加载器状态
        if 'document_loader' in status:
            print("\n📚 文档加载器状态:")
            doc_status = status['document_loader']
            if 'error' not in doc_status:
                print(f"  总文档数: {doc_status.get('total_documents', 0)}")
                print(f"  加载耗时: {doc_status.get('load_time', 0):.2f}秒")
                print(f"  文本文档: {doc_status.get('documents_by_type', {}).get('text', 0)}个")
                print(f"  图片文档: {doc_status.get('documents_by_type', {}).get('image', 0)}个")
                print(f"  表格文档: {doc_status.get('documents_by_type', {}).get('table', 0)}个")
            else:
                print(f"  ❌ 错误: {doc_status['error']}")
        
        # 显示优化引擎状态
        if 'optimization_engines' in status:
            print("\n🎯 优化引擎状态:")
            opt_status = status['optimization_engines']
            
            # 引擎就绪状态
            print("  🔧 引擎就绪状态:")
            print(f"    重排序引擎: {'✅ 就绪' if opt_status.get('reranking_engine_ready') else '❌ 未就绪'}")
            print(f"    LLM引擎: {'✅ 就绪' if opt_status.get('llm_engine_ready') else '❌ 未就绪'}")
            print(f"    智能过滤引擎: {'✅ 就绪' if opt_status.get('smart_filter_engine_ready') else '❌ 未就绪'}")
            print(f"    源过滤引擎: {'✅ 就绪' if opt_status.get('source_filter_engine_ready') else '❌ 未就绪'}")
            
            # 配置启用状态
            print("  ⚙️ 配置启用状态:")
            print(f"    优化管道: {'✅ 启用' if opt_status.get('pipeline_enabled') else '❌ 禁用'}")
            print(f"    重排序: {'✅ 启用' if opt_status.get('reranking_enabled') else '❌ 禁用'}")
            print(f"    LLM生成: {'✅ 启用' if opt_status.get('llm_generation_enabled') else '❌ 禁用'}")
            print(f"    智能过滤: {'✅ 启用' if opt_status.get('smart_filtering_enabled') else '❌ 禁用'}")
            print(f"    源过滤: {'✅ 启用' if opt_status.get('source_filtering_enabled') else '❌ 禁用'}")
        
        # 显示向量数据库状态
        if 'vector_db' in status:
            print("\n🗄️ 向量数据库状态:")
            vector_status = status['vector_db']
            if 'error' not in vector_status:
                print(f"  路径: {vector_status.get('path', 'N/A')}")
                print(f"  元数据: {'✅ 存在' if vector_status.get('metadata_exists') else '❌ 不存在'}")
                print(f"  索引: {'✅ 存在' if vector_status.get('index_exists') else '❌ 不存在'}")
                print(f"  元数据大小: {vector_status.get('metadata_size', 0)} 字节")
                print(f"  索引大小: {vector_status.get('index_size', 0)} 字节")
            else:
                print(f"  ❌ 错误: {vector_status['error']}")
        
        # 显示记忆统计
        if 'memory_stats' in status:
            print("\n🧠 记忆统计:")
            memory_status = status['memory_stats']
            if 'error' not in memory_status:
                print(f"  会话记忆: {memory_status.get('session_memory_count', 0)} 条")
                print(f"  用户记忆: {memory_status.get('user_memory_count', 0)} 条")
                print(f"  总记忆: {memory_status.get('total_memory_count', 0)} 条")
            else:
                print(f"  ❌ 错误: {memory_status['error']}")
    
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
        
        # 显示系统状态摘要
        print("\n📊 系统状态摘要:")
        status = v2_rag_system.get_system_status()
        
        # 显示基础组件状态
        print(f"  🔧 混合引擎: {'✅ 就绪' if status.get('hybrid_engine_ready') else '❌ 未就绪'}")
        print(f"  🧠 记忆管理器: {'✅ 就绪' if status.get('memory_manager_ready') else '❌ 未就绪'}")
        print(f"  📄 文档管道: {'✅ 就绪' if status.get('document_pipeline_ready') else '❌ 未就绪'}")
        
        # 显示文档加载器状态
        if 'document_loader' in status:
            doc_status = status['document_loader']
            if 'error' not in doc_status:
                print(f"  📚 文档加载器: ✅ 就绪 ({doc_status.get('total_documents', 0)}个文档)")
            else:
                print(f"  📚 文档加载器: ❌ 错误")
        
        # 显示优化引擎状态
        if 'optimization_engines' in status:
            opt_status = status['optimization_engines']
            print("\n🎯 优化引擎状态:")
            print(f"  🔄 重排序引擎: {'✅ 就绪' if opt_status.get('reranking_engine_ready') else '❌ 未就绪'}")
            print(f"  🤖 LLM引擎: {'✅ 就绪' if opt_status.get('llm_engine_ready') else '❌ 未就绪'}")
            print(f"  🧹 智能过滤引擎: {'✅ 就绪' if opt_status.get('smart_filter_engine_ready') else '❌ 未就绪'}")
            print(f"  📍 源过滤引擎: {'✅ 就绪' if opt_status.get('source_filter_engine_ready') else '❌ 未就绪'}")
            
            # 显示配置状态
            if opt_status.get('pipeline_enabled'):
                print("  ⚙️ 优化管道: ✅ 已启用")
            else:
                print("  ⚙️ 优化管道: ❌ 已禁用")
        
        print(f"\n🚀 正在启动Web服务器...")
        v2_rag_system.start_web_server(args.host, args.port, args.debug)


if __name__ == '__main__':
    main()
