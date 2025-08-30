"""
V3版本主处理器

V3版本向量数据库构建系统的核心控制器，负责统一管理整个文档处理流程。
完全符合设计文档规范，位于core模块下。
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from config.config_manager import ConfigManager
from utils.document_type_detector import DocumentTypeDetector
from .model_caller import LangChainModelCaller as ModelCaller
from .content_processor import ContentProcessor
from .vectorization_manager import VectorizationManager
from .metadata_manager import MetadataManager
from .vector_store_manager import LangChainVectorStoreManager as VectorStoreManager

class V3MainProcessor:
    """
    V3版本主处理器

    功能：
    - 统一的程序入口和流程控制
    - 智能模式选择（新建 vs 增量）
    - 与所有子模块的深度集成
    - 配置管理和验证
    - 失败处理和状态跟踪
    - 完全符合设计文档规范
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化主处理器

        :param config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 1. 初始化配置管理器
        self.config_manager = ConfigManager(config_path)

        # 2. 加载配置
        if not self.config_manager.load_config():
            raise RuntimeError("配置加载失败")

        # 3. 初始化子模块
        self._initialize_modules()

        # 4. 验证环境
        self._validate_environment()
        
        # 5. 系统状态
        self.system_status = {
            'initialized': True,
            'initialization_time': int(time.time()),
            'version': '3.0.0',
            'status': 'ready'
        }

        logging.info("V3MainProcessor初始化完成")

    def _initialize_modules(self):
        """初始化所有子模块"""
        try:
            # 文档类型检测器
            self.document_type_detector = DocumentTypeDetector(self.config_manager)

            # AI模型调用器
            self.model_caller = ModelCaller(self.config_manager)

            # 内容处理器
            self.content_processor = ContentProcessor(self.config_manager)

            # 向量化管理器
            self.vectorization_manager = VectorizationManager(self.config_manager)

            # 元数据管理器
            self.metadata_manager = MetadataManager(self.config_manager)

            # 向量存储管理器
            self.vector_store_manager = VectorStoreManager(self.config_manager)

            # 失败处理器（通过配置管理器获取）
            self.failure_handler = self.config_manager.get_failure_handler()

            logging.info("所有子模块初始化完成")

        except Exception as e:
            logging.error(f"子模块初始化失败: {e}")
            raise

    def _validate_environment(self):
        """验证环境配置"""
        try:
            # 验证环境变量
            from config.environment_manager import environment_manager
            if not environment_manager.setup_environment():
                environment_manager.print_environment_setup_guide()
                raise RuntimeError("环境变量验证失败")

            # 验证路径配置
            paths = self.config_manager.get('paths', {})
            for path_key, path_value in paths.items():
                if path_value and not os.path.exists(path_value):
                    os.makedirs(path_value, exist_ok=True)
                    logging.info(f"创建目录: {path_value}")

            # 验证API密钥（通过EnvironmentManager获取，符合设计文档）
            env_manager = self.config_manager.get_environment_manager()
            required_keys = ['DASHSCOPE_API_KEY', 'MINERU_API_KEY']
            for key in required_keys:
                if not env_manager.get_required_var(key):
                    logging.warning(f"缺少API密钥: {key}")
                else:
                    logging.info(f"API密钥已设置: {key}")

            logging.info("环境验证完成")

        except Exception as e:
            logging.error(f"环境验证失败: {e}")
            raise

    def process_documents(self, input_type: str = None, input_path: str = None,
                         output_path: str = None) -> Dict[str, Any]:
        """
        处理文档（带默认值支持）

        :param input_type: 输入类型，如果为None则使用默认值'pdf'
        :param input_path: 输入路径，如果为None则使用配置默认值
        :param output_path: 输出路径，如果为None则使用配置默认值
        :return: 处理结果
        """
        try:
            print("=" * 50)
            print("      V3版本向量数据库构建系统")
            print("=" * 50)

            # 1. 使用DocumentTypeDetector验证输入类型和路径
            validation_result = self.document_type_detector.validate_input_type(
                input_type, input_path, output_path
            )

            if not validation_result['valid']:
                error_msg = f"输入验证失败: {validation_result.get('message', '未知错误')}"
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'validation_result': validation_result
                }

            # 2. 显示处理信息
            self._display_processing_info(validation_result)

            # 3. 根据输入类型选择处理流程
            if validation_result['input_type'] == 'pdf':
                result = self._process_from_pdf(validation_result)
            elif validation_result['input_type'] == 'mineru_output':
                result = self._process_from_mineru_output(validation_result)
            else:
                error_msg = f"不支持的输入类型: {validation_result['input_type']}"
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

            # 4. 生成最终报告
            final_result = self._generate_final_report(result)
            
            # 确保返回实际使用的数据库路径
            final_result['storage_path'] = validation_result['output_path']
            
            return final_result

        except Exception as e:
            error_msg = f"文档处理失败: {str(e)}"
            print(f"❌ {error_msg}")
            logging.error(error_msg, exc_info=True)

            # 记录失败信息
            if hasattr(self, 'failure_handler') and self.failure_handler:
                self.failure_handler.record_failure(
                    image_info={'operation': 'document_processing'},
                    error_type='processing_error',
                    error_message=str(e)
                )

            return {
                'success': False,
                'error': error_msg,
                'exception': str(e)
            }

    def _display_processing_info(self, validation_result: Dict[str, Any]):
        """显示处理信息"""
        print("\n📋 处理信息:")
        print(f"   输入类型: {validation_result['input_type']}")
        print(f"   输入路径: {validation_result['input_path']}")
        print(f"   输出路径: {validation_result['output_path']}")
        print(f"   是否需要minerU: {'是' if validation_result['needs_mineru'] else '否'}")

        if validation_result.get('file_count'):
            print(f"   文件数量: {validation_result['file_count']}")

        if validation_result.get('file_size'):
            size_mb = validation_result['file_size'] / (1024 * 1024)
            print(f"   文件大小: {size_mb:.1f} MB")

        print(f"   描述: {validation_result['description']}")

    def _process_from_pdf(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """从PDF开始处理"""
        print("\n🚀 从PDF开始处理")
        print("   注意: 从PDF开始处理需要较长时间，包含minerU解析步骤")

        # 1. 检查目标向量数据库状态
        target_vector_db = validation_result['output_path']
        db_exists = self._check_vector_db_exists(target_vector_db)

        # 2. 智能选择模式
        if db_exists:
            print("   📊 检测到现有向量数据库，使用增量模式")
            result = self._incremental_process(validation_result, target_vector_db)
        else:
            print("   🆕 未检测到现有向量数据库，使用新建模式")
            result = self._new_process(validation_result, target_vector_db)

        return result

    def _process_from_mineru_output(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """从minerU输出开始处理"""
        print("\n⚡ 从minerU输出开始处理")
        print("   注意: 从minerU输出开始处理，跳过解析步骤，速度较快")

        # 1. 检查目标向量数据库状态
        target_vector_db = validation_result['output_path']
        db_exists = self._check_vector_db_exists(target_vector_db)

        # 2. 智能选择模式
        if db_exists:
            print("   📊 检测到现有向量数据库，使用增量模式")
            result = self._incremental_process(validation_result, target_vector_db)
        else:
            print("   🆕 未检测到现有向量数据库，使用新建模式")
            result = self._new_process(validation_result, target_vector_db)

        return result

    def _check_vector_db_exists(self, target_vector_db: str) -> bool:
        """检查向量数据库是否存在"""
        # 直接使用文件检测方法，避免FAISS.load_local的路径问题
        # V3版本的文件结构：central/vector_db/langchain_faiss_index/
        index_file = os.path.join(target_vector_db, 'langchain_faiss_index', 'index.faiss')
        index_pkl_file = os.path.join(target_vector_db, 'langchain_faiss_index', 'index.pkl')
        
        exists = os.path.exists(index_file) and os.path.exists(index_pkl_file)
        
        if exists:
            logging.info(f"检测到现有向量数据库: {target_vector_db}")
        else:
            logging.info(f"未检测到向量数据库: {target_vector_db}")
        
        return exists

    def _get_existing_document_names(self) -> List[str]:
        """获取现有数据库中的文档名列表"""
        try:
            if not self.vector_store_manager.vector_store:
                return []
            
            docstore = self.vector_store_manager.vector_store.docstore._dict
            document_names = set()
            
            for doc_id, doc in docstore.items():
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                doc_name = metadata.get('document_name', '')
                if doc_name and doc_name != 'unknown':
                    document_names.add(doc_name)
            
            return list(document_names)
            
        except Exception as e:
            logging.error(f"获取现有文档名失败: {e}")
            return []

    def _new_process(self, validation_result: Dict[str, Any], target_vector_db: str) -> Dict[str, Any]:
        """新建模式处理"""
        try:
            print("\n🏗️  开始新建模式处理...")

            # 1. 初始化向量数据库
            success = self.vector_store_manager.create_vector_store(
                dimension=1536  # 默认向量维度
            )

            if not success:
                raise RuntimeError("向量数据库初始化失败")

            # 2. 处理文档内容
            processing_result = self._process_documents_new(validation_result)

            # 3. 存储结果
            storage_result = self._store_results(processing_result, target_vector_db)

            # 4. 生成报告
            result = {
                'success': True,
                'mode': 'new',
                'processing_result': processing_result,
                'storage_result': storage_result,
                'target_vector_db': target_vector_db
            }

            print("✅ 新建模式处理完成")
            return result

        except Exception as e:
            logging.error(f"新建模式处理失败: {e}")
            raise

    def _incremental_process(self, validation_result: Dict[str, Any], target_vector_db: str) -> Dict[str, Any]:
        """增量模式处理"""
        try:
            print("\n🔄 开始增量模式处理...")

            # 1. 加载现有向量数据库
            print("   📊 加载现有向量数据库...")
            load_success = self.vector_store_manager.load(target_vector_db)
            if not load_success:
                raise RuntimeError("无法加载现有向量数据库")
            
            # 获取现有文档列表，用于去重
            existing_docs = self._get_existing_document_names()
            print(f"   📚 现有文档: {existing_docs}")
            
            # 2. 处理新增文档内容
            print("   📄 增量模式：处理新增文档内容...")
            processing_result = self._process_documents_incremental(validation_result, existing_docs)

            # 3. 更新向量数据库
            storage_result = self._update_results(processing_result, target_vector_db)

            # 4. 生成报告
            result = {
                'success': True,
                'mode': 'incremental',
                'processing_result': processing_result,
                'storage_result': storage_result,
                'target_vector_db': target_vector_db,
                'storage_path': target_vector_db  # 添加storage_path字段
            }

            print("✅ 增量模式处理完成")
            return result

        except Exception as e:
            logging.error(f"增量模式处理失败: {e}")
            raise

    def _process_documents_new(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """新建模式文档处理"""
        try:
            print("   📄 处理文档内容...")
            
            # 调试信息：显示validation_result的内容
            print(f"   🔍 调试信息: validation_result.keys() = {list(validation_result.keys())}")
            print(f"   🔍 调试信息: file_list = {validation_result.get('file_list', [])}")
            print(f"   🔍 调试信息: file_count = {validation_result.get('file_count', 0)}")
            print(f"   🔍 调试信息: input_type = {validation_result.get('input_type', 'unknown')}")
            
            # 获取文件列表和输入类型
            files = validation_result.get('file_list', [])
            input_type = validation_result.get('input_type', 'pdf')
            
            processed_items = []
            
            if input_type == 'pdf':
                # 处理PDF文件
                for pdf_file in files:
                    try:
                        print(f"     处理PDF文件: {os.path.basename(pdf_file)}")
                        
                        # 1. 使用MinerU解析PDF
                        mineru_result = self._call_mineru_api(pdf_file)
                        if not mineru_result.get('success'):
                            print(f"     ⚠️  MinerU解析失败: {pdf_file}")
                            continue
                        
                        # 2. 获取对应的JSON文件路径（从MinerU输出目录中查找）
                        mineru_output_dir = self.config_manager.get_path('mineru_output_dir')
                        json_file = self._find_json_file_for_pdf(pdf_file, mineru_output_dir)
                        if not json_file:
                            print(f"     ⚠️  未找到对应的JSON文件: {pdf_file}")
                            continue
                        
                        # 3. 使用ContentProcessor处理文档内容
                        doc_name = os.path.splitext(os.path.basename(pdf_file))[0]
                        content_result = self.content_processor.process_document_content(json_file, doc_name)
                        
                        # 4. 使用VectorizationManager进行向量化
                        vectorization_result = self.vectorization_manager.vectorize_all_content(content_result)
                        
                        # 5. 构建处理结果
                        processed_item = {
                            'pdf_path': pdf_file,
                            'json_path': json_file,
                            'doc_name': doc_name,
                            'content_result': content_result,
                            'vectorization_result': vectorization_result,
                            'status': 'success',
                            'processing_timestamp': int(time.time())
                        }
                        
                        processed_items.append(processed_item)
                        print(f"     ✅ 文档处理完成: {doc_name}")
                        
                    except Exception as e:
                        error_msg = f"处理PDF文件失败: {pdf_file}, 错误: {e}"
                        print(f"     ❌ {error_msg}")
                        logging.error(error_msg)
                        
                        # 记录失败信息
                        self.failure_handler.record_failure(pdf_file, 'pdf_processing', str(e))
                        
                        # 添加失败项
                        processed_items.append({
                            'pdf_path': pdf_file,
                            'status': 'failed',
                            'error': str(e),
                            'processing_timestamp': int(time.time())
                        })
                        
            elif input_type == 'mineru_output':
                # 直接处理MinerU输出文件（JSON/MD），跳过MinerU解析步骤
                print(f"     ⚡ 跳过MinerU解析，直接处理 {len(files)} 个文件")
                
                for file_path in files:
                    try:
                        print(f"     处理文件: {os.path.basename(file_path)}")
                        
                        # 1. 直接使用ContentProcessor处理文档内容
                        doc_name = os.path.splitext(os.path.basename(file_path))[0]
                        content_result = self.content_processor.process_document_content(file_path, doc_name)
                        
                        # 2. 使用VectorizationManager进行向量化
                        vectorization_result = self.vectorization_manager.vectorize_all_content(content_result)
                        
                        # 3. 构建处理结果
                        processed_item = {
                            'file_path': file_path,
                            'doc_name': doc_name,
                            'content_result': content_result,
                            'vectorization_result': vectorization_result,
                            'status': 'success',
                            'processing_timestamp': int(time.time())
                        }
                        
                        processed_items.append(processed_item)
                        print(f"     ✅ 文档处理完成: {doc_name}")
                        
                    except Exception as e:
                        error_msg = f"处理文件失败: {file_path}, 错误: {e}"
                        print(f"     ❌ {error_msg}")
                        logging.error(error_msg)
                        
                        # 记录失败信息
                        self.failure_handler.record_failure(file_path, 'file_processing', str(e))
                        
                        # 添加失败项
                        processed_items.append({
                            'file_path': file_path,
                            'status': 'failed',
                            'error': str(e),
                            'processing_timestamp': int(time.time())
                        })
            
            # 统计处理结果
            successful_items = [item for item in processed_items if item.get('status') == 'success']
            failed_items = [item for item in processed_items if item.get('status') == 'failed']
            
            result = {
                'processed_items': processed_items,
                'total_files': len(files),
                'successful_files': len(successful_items),
                'failed_files': len(failed_items),
                'status': 'success' if successful_items else 'failed',
                'processing_timestamp': int(time.time())
            }
            
            print(f"   📊 文档处理完成: 成功 {len(successful_items)} 个，失败 {len(failed_items)} 个")
            return result
            
        except Exception as e:
            error_msg = f"新建模式文档处理失败: {e}"
            logging.error(error_msg)
            self.failure_handler.record_failure('document_processing', 'new_mode', str(e))
            
            return {
                'processed_items': [],
                'total_files': 0,
                'status': 'failed',
                'error': str(e)
            }
    
    def _find_json_file_for_pdf(self, pdf_file: str, mineru_output_dir: str) -> Optional[str]:
        """
        为PDF文件找到对应的JSON文件
        
        :param pdf_file: PDF文件路径
        :param mineru_output_dir: MinerU输出目录
        :return: JSON文件路径或None
        """
        pdf_name = os.path.splitext(os.path.basename(pdf_file))[0]
        
        # 在MinerU输出目录中查找对应的JSON文件
        for item in Path(mineru_output_dir).iterdir():
            if item.is_file() and item.suffix.lower() == '.json':
                if pdf_name in item.name:
                    return str(item)
        
        return None

    def _process_documents_incremental(self, validation_result: Dict[str, Any], existing_docs: List[str] = None) -> Dict[str, Any]:
        """
        增量模式文档处理
        
        功能：
        - 检测新增的文档
        - 只处理新增内容
        - 增量更新向量数据库
        - 保持现有数据完整性
        """
        try:
            print("   📄 增量模式：处理新增文档内容...")
            
            # 获取文件列表和输入类型
            files = validation_result.get('file_list', [])
            input_type = validation_result.get('input_type', 'pdf')
            
            if not files:
                print("     没有文件需要处理")
                return {
                    'processed_items': [],
                    'new_files': 0,
                    'incremental_updates': 0,
                    'status': 'success',
                    'message': '没有文件需要处理'
                }
            
            # 检测新增文档（不在现有数据库中的文档）
            new_files = []
            for file_path in files:
                file_name = os.path.basename(file_path)
                # 检查文件名是否在现有文档中
                is_new = True
                for existing_doc in (existing_docs or []):
                    if existing_doc in file_name or file_name in existing_doc:
                        is_new = False
                        break
                
                if is_new:
                    new_files.append({
                        'path': file_path,
                        'name': file_name,
                        'type': input_type
                    })
            
            if not new_files:
                print("     没有新增文档需要处理")
                return {
                    'processed_items': [],
                    'new_files': 0,
                    'incremental_updates': 0,
                    'status': 'success',
                    'message': '没有新增文档'
                }
            
            print(f"     检测到 {len(new_files)} 个新增文档")
            
            # 增量处理新增文档
            processed_items = []
            successful_items = []
            failed_items = []
            
            for file_info in new_files:
                try:
                    print(f"     🔄 处理新增文档: {file_info.get('name', 'unknown')}")
                    
                    # 使用新建模式的处理逻辑来处理单个文档
                    # 这样可以复用现有的处理流程
                    single_validation = {
                        'file_list': [file_info['path']],
                        'input_type': file_info['type'],
                        'file_count': 1
                    }
                    
                    item_result = self._process_documents_new(single_validation)
                    
                    # 修复：检查 'status' 字段而不是 'success' 字段
                    if item_result.get('status') == 'success':
                        successful_items.append({
                            'file_info': file_info,
                            'status': 'success',
                            'result': item_result,
                            'processing_timestamp': int(time.time())
                        })
                        processed_items.append(item_result)
                        print(f"       ✅ 处理成功")
                    else:
                        failed_items.append({
                            'file_info': file_info,
                            'status': 'failed',
                            'error': '处理失败',
                            'processing_timestamp': int(time.time())
                        })
                        print(f"       ❌ 处理失败")
                        
                except Exception as e:
                    error_msg = f"处理新增文档失败: {file_info.get('name', 'unknown')}, 错误: {e}"
                    logging.error(error_msg)
                    
                    failed_item = {
                        'file_info': file_info,
                        'status': 'failed',
                        'error': str(e),
                        'processing_timestamp': int(time.time())
                    }
                    failed_items.append(failed_item)
                    processed_items.append(failed_item)
                    
                    # 记录失败
                    self.failure_handler.record_failure(file_info, 'incremental_processing', str(e))
            
            # 更新向量数据库（这里暂时返回0，因为我们在处理时已经更新了）
            incremental_updates = len(successful_items)
            
            # 生成结果
            result = {
                'mode': 'incremental',
                'processed_items': processed_items,
                'successful_items': successful_items,
                'failed_items': failed_items,
                'new_files': len(new_files),
                'incremental_updates': incremental_updates,
                'total_vectors_added': sum(item.get('vector_count', 0) for item in successful_items),
                'status': 'success' if successful_items else 'failed',
                'processing_timestamp': int(time.time())
            }
            
            print(f"   📊 增量处理完成: 成功 {len(successful_items)} 个，失败 {len(failed_items)} 个")
            print(f"     新增向量: {result['total_vectors_added']} 个")
            
            return result
            
        except Exception as e:
            error_msg = f"增量模式文档处理失败: {e}"
            logging.error(error_msg)
            self.failure_handler.record_failure('document_processing', 'incremental_mode', str(e))
            
            return {
                'processed_items': [],
                'new_files': 0,
                'incremental_updates': 0,
                'status': 'failed',
                'error': str(e)
            }

    def _load_existing_vector_db(self, vector_db_path: str) -> bool:
        """
        加载现有向量数据库
        
        :param vector_db_path: 向量数据库路径
        :return: 是否加载成功
        """
        try:
            if not vector_db_path or not os.path.exists(vector_db_path):
                logging.warning(f"向量数据库路径不存在: {vector_db_path}")
                return False
            
            # 检查数据库文件
            index_dir = os.path.join(vector_db_path, 'index')
            metadata_dir = os.path.join(vector_db_path, 'metadata')
            
            if not os.path.exists(index_dir) or not os.path.exists(metadata_dir):
                logging.warning(f"向量数据库结构不完整: {vector_db_path}")
                return False
            
            # 尝试加载现有数据库
            if self.vector_store_manager.load_existing_database(vector_db_path):
                logging.info(f"成功加载现有向量数据库: {vector_db_path}")
                return True
            else:
                logging.warning(f"加载现有向量数据库失败: {vector_db_path}")
                return False
                
        except Exception as e:
            logging.error(f"加载现有向量数据库失败: {e}")
            return False

    def _process_single_document_incremental(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        增量处理单个文档
        
        :param file_info: 文件信息
        :return: 处理结果
        """
        try:
            file_path = file_info.get('path', '')
            file_type = file_info.get('type', '')
            file_name = file_info.get('name', '')
            
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 根据文件类型选择处理方式
            if file_type == 'pdf':
                return self._process_pdf_incremental(file_path, file_name)
            elif file_type == 'json':
                return self._process_json_incremental(file_path, file_name)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
                
        except Exception as e:
            logging.error(f"增量处理单个文档失败: {e}")
            return {
                'file_info': file_info,
                'status': 'failed',
                'error': str(e),
                'processing_timestamp': int(time.time())
            }

    def _process_pdf_incremental(self, pdf_path: str, pdf_name: str) -> Dict[str, Any]:
        """
        增量处理PDF文档
        
        :param pdf_path: PDF文件路径
        :param pdf_name: PDF文件名
        :return: 处理结果
        """
        try:
            print(f"       📄 处理PDF: {pdf_name}")
            
            # 1. 调用MinerU API处理PDF
            mineru_result = self._call_mineru_api(pdf_path)
            if not mineru_result.get('success'):
                raise RuntimeError(f"MinerU处理失败: {mineru_result.get('error', '未知错误')}")
            
            # 2. 从MinerU输出处理内容
            json_path = mineru_result.get('json_path', '')
            if not json_path or not os.path.exists(json_path):
                raise FileNotFoundError(f"MinerU输出JSON文件不存在: {json_path}")
            
            # 3. 处理文档内容
            content_result = self.content_processor.process_document_content(json_path, pdf_name)
            
            # 4. 增量向量化
            vectorization_result = self._vectorize_content_incremental(content_result)
            
            # 5. 生成结果
            result = {
                'file_info': {
                    'path': pdf_path,
                    'name': pdf_name,
                    'type': 'pdf'
                },
                'status': 'success',
                'mineru_result': mineru_result,
                'content_result': content_result,
                'vectorization_result': vectorization_result,
                'vector_count': self._count_vectors(vectorization_result),
                'processing_timestamp': int(time.time())
            }
            
            return result
            
        except Exception as e:
            logging.error(f"增量处理PDF失败: {pdf_path}, 错误: {e}")
            return {
                'file_info': {
                    'path': pdf_path,
                    'name': pdf_name,
                    'type': 'pdf'
                },
                'status': 'failed',
                'error': str(e),
                'processing_timestamp': int(time.time())
            }

    def _process_json_incremental(self, json_path: str, json_name: str) -> Dict[str, Any]:
        """
        增量处理JSON文档
        
        :param json_path: JSON文件路径
        :param json_name: JSON文件名
        :return: 处理结果
        """
        try:
            print(f"       📋 处理JSON: {json_name}")
            
            # 1. 处理文档内容
            content_result = self.content_processor.process_document_content(json_path, json_name)
            
            # 2. 增量向量化
            vectorization_result = self._vectorize_content_incremental(content_result)
            
            # 3. 生成结果
            result = {
                'file_info': {
                    'path': json_path,
                    'name': json_name,
                    'type': 'json'
                },
                'status': 'success',
                'content_result': content_result,
                'vectorization_result': vectorization_result,
                'vector_count': self._count_vectors(vectorization_result),
                'processing_timestamp': int(time.time())
            }
            
            return result
            
        except Exception as e:
            logging.error(f"增量处理JSON失败: {json_path}, 错误: {e}")
            return {
                'file_info': {
                    'path': json_path,
                    'name': json_name,
                    'type': 'json'
                },
                'status': 'failed',
                'error': str(e),
                'processing_timestamp': int(time.time())
            }

    def _vectorize_content_incremental(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        增量向量化内容
        
        :param content_result: 内容处理结果
        :return: 向量化结果
        """
        try:
            # 只向量化新增内容，避免重复处理
            vectorization_result = {
                'text_vectors': [],
                'image_vectors': [],
                'table_vectors': [],
                'incremental_mode': True
            }
            
            # 向量化文本（只处理新文本）
            if content_result.get('text_chunks'):
                text_vectors = self.vectorization_manager.vectorize_content(
                    content_result['text_chunks'], 'text'
                )
                vectorization_result['text_vectors'] = text_vectors
            
            # 向量化表格（只处理新表格）
            if content_result.get('tables'):
                table_vectors = self.vectorization_manager.vectorize_content(
                    content_result['tables'], 'table'
                )
                vectorization_result['table_vectors'] = table_vectors
            
            # 图片向量化在ImageProcessor中已完成，这里收集结果
            if content_result.get('images'):
                image_vectors = []
                for image in content_result['images']:
                    if image.get('image_embedding') and image.get('description_embedding'):
                        # 修复：复制完整的图片对象，保留所有metadata，与新建模式保持一致
                        image_vector = image.copy()  # 保留完整的metadata
                        
                        # 更新向量化相关字段
                        image_vector.update({
                            'status': 'success',
                            'vectorization_status': 'success',
                            'embedding_model': 'multimodal-embedding-one-peace-v1',
                            'vectorization_timestamp': int(time.time())
                        })
                        
                        image_vectors.append(image_vector)
                vectorization_result['image_vectors'] = image_vectors
            
            return vectorization_result
            
        except Exception as e:
            logging.error(f"增量向量化失败: {e}")
            return {
                'text_vectors': [],
                'image_vectors': [],
                'table_vectors': [],
                'incremental_mode': True,
                'status': 'failed',
                'error': str(e)
            }

    def _update_vector_database_incremental(self, successful_items: List[Dict[str, Any]]) -> int:
        """
        增量更新向量数据库
        
        :param successful_items: 成功处理的项目列表
        :return: 更新的向量数量
        """
        try:
            print("     🔄 增量更新向量数据库...")
            
            total_vectors_added = 0
            
            for item in successful_items:
                vectorization_result = item.get('vectorization_result', {})
                
                # 收集所有向量
                all_vectors = []
                all_metadata = []
                
                # 文本向量
                for tv in vectorization_result.get('text_vectors', []):
                    if tv.get('vectorization_status') == 'success':
                        all_vectors.append(tv.get('vector', []))
                        
                        # 从tv对象中提取metadata，与新建模式保持一致
                        metadata = tv.get('metadata', {})
                        all_metadata.append({
                            'type': 'text',
                            'chunk_type': 'text',
                            'source': item.get('file_info', {}).get('name', '') or metadata.get('document_name', ''),
                            'document_name': metadata.get('document_name', ''),
                            'page_number': metadata.get('page_number', 1),
                            'chunk_id': metadata.get('chunk_id', ''),
                            'text': metadata.get('text', ''),
                            'text_length': metadata.get('text_length', 0),
                            'text_level': metadata.get('text_level', 0),
                            'chunk_size': metadata.get('chunk_size', 0),
                            'chunk_overlap': metadata.get('chunk_overlap', 0),
                            'chunk_position': metadata.get('chunk_position', {}),
                            'related_images': metadata.get('related_images', []),
                            'related_tables': metadata.get('related_tables', []),
                            'text_embedding': tv.get('vector', []),  # 保存实际的text embedding向量
                            'text_embedding_model': tv.get('text_embedding_model', 'text-embedding-v1'),  # 保存embedding模型信息
                            'vector_type': 'text_embedding',
                            'vectorization_status': 'success',
                            'vectorization_timestamp': int(time.time()),
                            'incremental_update': True,
                            'update_timestamp': int(time.time())
                        })
                        total_vectors_added += 1
                
                # 图像向量
                for iv in vectorization_result.get('image_vectors', []):
                    if iv.get('vectorization_status') == 'success':
                        all_vectors.append(iv.get('image_embedding', []))
                        
                        # 从iv对象中提取metadata，与新建模式保持一致
                        metadata = iv.get('metadata', {})
                        all_metadata.append({
                            'type': 'image',
                            'chunk_type': 'image',
                            'source': item.get('file_info', {}).get('name', '') or iv.get('document_name', ''),
                            'document_name': iv.get('document_name', ''),
                            'page_number': metadata.get('page_number', 1),
                            'chunk_id': metadata.get('chunk_id', ''),
                            'image_id': metadata.get('image_id', ''),
                            'image_path': metadata.get('image_path', ''),
                            'image_filename': metadata.get('image_filename', ''),
                            'image_type': metadata.get('image_type', 'general'),
                            'image_format': metadata.get('image_format', 'UNKNOWN'),
                            'image_dimensions': metadata.get('image_dimensions', {}),
                            'basic_description': metadata.get('basic_description', ''),
                            'enhanced_description': metadata.get('enhanced_description', ''),
                            'layered_descriptions': metadata.get('layered_descriptions', {}),
                            'structured_info': metadata.get('structured_info', {}),
                            'img_caption': metadata.get('img_caption', []),
                            'img_footnote': metadata.get('img_footnote', []),
                            'enhancement_enabled': metadata.get('enhancement_enabled', True),
                            'enhancement_model': metadata.get('enhancement_model', ''),
                            'enhancement_status': metadata.get('enhancement_status', 'success'),
                            'enhancement_timestamp': metadata.get('enhancement_timestamp'),
                            'image_embedding': iv.get('image_embedding', []),
                            'description_embedding': iv.get('description_embedding', []),
                            'image_embedding_model': iv.get('embedding_model', ''),
                            'description_embedding_model': iv.get('embedding_model', ''),
                            'related_text_chunks': metadata.get('related_text_chunks', []),
                            'related_table_chunks': metadata.get('related_table_chunks', []),
                            'parent_document_id': metadata.get('parent_document_id', ''),
                            'copy_status': metadata.get('copy_status', 'success'),
                            'vectorization_status': 'success',
                            'vector_type': 'visual_embedding',
                            'vectorization_timestamp': int(time.time()),
                            'incremental_update': True,
                            'update_timestamp': int(time.time())
                        })
                        total_vectors_added += 1
                
                # 表格向量
                for tv in vectorization_result.get('table_vectors', []):
                    if tv.get('vectorization_status') == 'success':
                        all_vectors.append(tv.get('vector', []))
                        
                        # 从tv对象中提取metadata，与新建模式保持一致
                        metadata = tv.get('metadata', {})
                        all_metadata.append({
                            'type': 'table',
                            'chunk_type': 'table',
                            'source': item.get('file_info', {}).get('name', '') or metadata.get('document_name', ''),
                            'document_name': metadata.get('document_name', ''),
                            'page_number': metadata.get('page_number', 1),
                            'chunk_id': metadata.get('chunk_id', ''),
                            'table_id': metadata.get('table_id', ''),
                            'table_type': metadata.get('table_type', 'data_table'),
                            'table_title': metadata.get('table_title', ''),
                            'table_summary': metadata.get('table_summary', ''),
                            'table_headers': metadata.get('table_headers', []),
                            'table_row_count': metadata.get('table_rows', 0),
                            'table_column_count': metadata.get('table_columns', 0),
                            'table_body': metadata.get('table_body', ''),
                            'table_content': metadata.get('table_content', ''),
                            'table_caption': metadata.get('table_caption', []),
                            'table_footnote': metadata.get('table_footnote', []),
                            'is_subtable': metadata.get('is_subtable', False),
                            'parent_table_id': metadata.get('parent_table_id'),
                            'subtable_index': metadata.get('subtable_index'),
                            'chunk_start_row': metadata.get('chunk_start_row', 0),
                            'chunk_end_row': metadata.get('chunk_end_row', 0),
                            'related_text': metadata.get('related_text', ''),
                            'related_images': metadata.get('related_images', []),
                            'related_text_chunks': metadata.get('related_text_chunks', []),
                            'table_context': metadata.get('table_context', ''),
                            'table_embedding': tv.get('vector', []),  # 保存实际的table embedding向量
                            'table_embedding_model': tv.get('table_embedding_model', 'text-embedding-v1'),  # 保存embedding模型信息
                            'vector_type': 'text_embedding',
                            'vectorization_status': 'success',
                            'vectorization_timestamp': int(time.time()),
                            'incremental_update': True,
                            'update_timestamp': int(time.time())
                        })
                        total_vectors_added += 1
            
            # 批量添加到向量数据库
            if all_vectors and all_metadata:
                success = self.vector_store_manager.add_vectors(all_vectors, all_metadata)
                if success:
                    print(f"       ✅ 成功添加 {total_vectors_added} 个向量到数据库")
                else:
                    print(f"       ❌ 添加向量到数据库失败")
                    total_vectors_added = 0
            
            return total_vectors_added
            
        except Exception as e:
            logging.error(f"增量更新向量数据库失败: {e}")
            return 0

    def _count_vectors(self, vectorization_result: Dict[str, Any]) -> int:
        """
        计算向量数量
        
        :param vectorization_result: 向量化结果
        :return: 向量总数
        """
        try:
            count = 0
            
            # 文本向量
            count += len([v for v in vectorization_result.get('text_vectors', []) if v.get('status') == 'success'])
            
            # 图像向量
            count += len([v for v in vectorization_result.get('image_vectors', []) if v.get('status') == 'success'])
            
            # 表格向量
            count += len([v for v in vectorization_result.get('table_vectors', []) if v.get('status') == 'success'])
            
            return count
            
        except Exception as e:
            logging.error(f"计算向量数量失败: {e}")
            return 0

    def _store_results(self, processing_result: Dict[str, Any], target_vector_db: str) -> Dict[str, Any]:
        """存储处理结果"""
        try:
            print("   💾 存储处理结果...")
            
            # 确保目标目录存在
            os.makedirs(target_vector_db, exist_ok=True)
            
            # 获取处理的项目
            processed_items = processing_result.get('processed_items', [])
            if not processed_items:
                print("     没有需要存储的内容")
                return {
                    'stored_items': 0,
                    'storage_path': target_vector_db,
                    'status': 'success',
                    'message': '没有需要存储的内容'
                }
            
            # 统计向量数量
            total_vectors = 0
            total_metadata = 0
            
            # 收集所有向量和元数据
            all_vectors = []
            all_metadata = []
            
            for item in processed_items:
                if item.get('status') == 'success':
                    vectorization_result = item.get('vectorization_result', {})
                    
                    # 收集文本向量
                    text_vectors = vectorization_result.get('text_vectors', [])
                    for tv in text_vectors:
                        if tv.get('vectorization_status') == 'success':
                            all_vectors.append(tv['vector'])
                            # 保存完整的文本元数据，符合设计文档规范
                            metadata = tv.get('metadata', {})
                            logging.info(f"文本向量tv的metadata字段: {'metadata' in tv}")
                            if 'metadata' in tv:
                                logging.info(f"文本metadata内容: {tv['metadata']}")

                            text_metadata = {
                                'type': 'text',
                                'chunk_type': 'text',
                                'source': item.get('pdf_path'),
                                'document_name': metadata.get('document_name', ''),
                                'page_number': metadata.get('page_number', 1),
                                'chunk_id': metadata.get('chunk_id', ''),
                                'text': metadata.get('text', ''),
                                'text_length': metadata.get('text_length', 0),
                                'text_level': metadata.get('text_level', 0),
                                'chunk_size': metadata.get('chunk_size', 0),
                                'chunk_overlap': metadata.get('chunk_overlap', 0),
                                'chunk_position': metadata.get('chunk_position', {}),
                                'related_images': metadata.get('related_images', []),
                                'related_tables': metadata.get('related_tables', []),
                                'text_embedding': tv['vector'],  # 保存实际的text embedding向量
                                'text_embedding_model': tv.get('text_embedding_model', 'text-embedding-v1'),  # 保存embedding模型信息
                                'vector_type': 'text_embedding',
                                'vectorization_status': 'success',
                                'vectorization_timestamp': int(time.time())
                            }
                            all_metadata.append(text_metadata)
                            total_vectors += 1
                    
                    # 收集图像向量
                    image_vectors = vectorization_result.get('image_vectors', [])
                    for iv in image_vectors:
                        if iv.get('vectorization_status') == 'success':
                            all_vectors.append(iv['image_embedding'])
                            # 保存完整的图片元数据，符合设计文档规范
                            logging.info(f"图像向量iv的结构: {list(iv.keys())}")
                            logging.info(f"图像向量iv的metadata字段: {'metadata' in iv}")
                            if 'metadata' in iv:
                                logging.info(f"图像metadata内容: {iv['metadata']}")

                            # 获取metadata
                            metadata = iv.get('metadata', {})
                            image_metadata = {
                                'type': 'image',
                                'chunk_type': 'image',
                                'source': item.get('pdf_path'),
                                'document_name': metadata.get('document_name', ''),
                                'page_number': metadata.get('page_number', 1),
                                'chunk_id': metadata.get('chunk_id', ''),
                                'image_id': metadata.get('image_id', ''),
                                'image_path': metadata.get('image_path', ''),
                                'image_filename': metadata.get('image_filename', ''),
                                'image_type': metadata.get('image_type', 'general'),
                                'image_format': metadata.get('image_format', 'UNKNOWN'),
                                'image_dimensions': metadata.get('image_dimensions', {}),
                                'basic_description': metadata.get('basic_description', ''),
                                'enhanced_description': metadata.get('enhanced_description', ''),
                                'layered_descriptions': metadata.get('layered_descriptions', {}),
                                'structured_info': metadata.get('structured_info', {}),
                                'img_caption': metadata.get('img_caption', []),
                                'img_footnote': metadata.get('img_footnote', []),
                                'enhancement_enabled': metadata.get('enhancement_enabled', True),
                                'enhancement_model': metadata.get('enhancement_model', ''),
                                'enhancement_status': metadata.get('enhancement_status', 'success'),
                                'enhancement_timestamp': metadata.get('enhancement_timestamp'),
                                'image_embedding': iv.get('image_embedding', []),
                                'description_embedding': iv.get('description_embedding', []),
                                'image_embedding_model': iv.get('embedding_model', ''),
                                'description_embedding_model': iv.get('embedding_model', ''),
                                'related_text_chunks': metadata.get('related_text_chunks', []),
                                'related_table_chunks': metadata.get('related_table_chunks', []),
                                'parent_document_id': metadata.get('parent_document_id', ''),
                                'copy_status': metadata.get('copy_status', 'success'),
                                'vectorization_status': 'success',
                                'vector_type': 'visual_embedding',
                                'vectorization_timestamp': int(time.time())
                            }
                            all_metadata.append(image_metadata)
                            total_vectors += 1
                    
                    # 收集表格向量
                    table_vectors = vectorization_result.get('table_vectors', [])
                    for tv in table_vectors:
                        if tv.get('vectorization_status') == 'success':
                            all_vectors.append(tv['vector'])
                            # 保存完整的表格元数据，符合设计文档规范
                            metadata = tv.get('metadata', {})
                            logging.info(f"表格向量tv的metadata字段: {'metadata' in tv}")
                            if 'metadata' in tv:
                                logging.info(f"表格metadata内容: {tv['metadata']}")

                            table_metadata = {
                                'type': 'table',
                                'chunk_type': 'table',
                                'source': item.get('pdf_path'),
                                'document_name': metadata.get('document_name', ''),
                                'page_number': metadata.get('page_number', 1),
                                'chunk_id': metadata.get('chunk_id', ''),
                                'table_id': metadata.get('table_id', ''),
                                'table_type': metadata.get('table_type', 'data_table'),
                                'table_title': metadata.get('table_title', ''),
                                'table_summary': metadata.get('table_summary', ''),
                                'table_headers': metadata.get('table_headers', []),
                                'table_row_count': metadata.get('table_rows', 0),
                                'table_column_count': metadata.get('table_columns', 0),
                                'table_body': metadata.get('table_body', ''),
                                'table_content': metadata.get('table_content', ''),
                                'table_caption': metadata.get('table_caption', []),
                                'table_footnote': metadata.get('table_footnote', []),
                                'is_subtable': metadata.get('is_subtable', False),
                                'parent_table_id': metadata.get('parent_table_id'),
                                'subtable_index': metadata.get('subtable_index'),
                                'chunk_start_row': metadata.get('chunk_start_row', 0),
                                'chunk_end_row': metadata.get('chunk_end_row', 0),
                                'related_text': metadata.get('related_text', ''),
                                'related_images': metadata.get('related_images', []),
                                'related_text_chunks': metadata.get('related_text_chunks', []),
                                'table_context': metadata.get('table_context', ''),
                                'table_embedding': tv['vector'],  # 保存实际的table embedding向量
                                'table_embedding_model': tv.get('table_embedding_model', 'text-embedding-v1'),  # 保存embedding模型信息
                                'vector_type': 'text_embedding',
                                'vectorization_status': 'success',
                                'vectorization_timestamp': int(time.time())
                            }
                            all_metadata.append(table_metadata)
                            total_vectors += 1
            
            # 存储到向量数据库
            if all_vectors:
                print(f"     存储 {len(all_vectors)} 个向量到数据库...")
                
                # 使用向量存储管理器存储
                success = self.vector_store_manager.add_vectors(all_vectors, all_metadata)
                
                if success:
                    print(f"     ✅ 向量存储成功")
                    
                    # 保存向量数据库到磁盘
                    print(f"     💾 保存向量数据库到磁盘...")
                    if self.vector_store_manager.save():
                        print(f"     ✅ 向量数据库保存成功")
                    else:
                        print(f"     ⚠️  向量数据库保存失败")
                    
                    # 创建元数据文件
                    logs_dir = self.config_manager.get_path('logs_dir')
                    metadata_file = os.path.join(logs_dir, 'processing_metadata.json')
                    metadata_summary = {
                        'total_vectors': total_vectors,
                        'total_files': len(processed_items),
                        'success_count': sum(1 for item in processed_items if item.get('status') == 'success'),
                        'failed_count': sum(1 for item in processed_items if item.get('status') == 'failed'),
                        'vector_types': {
                            'text': sum(1 for m in all_metadata if m['type'] == 'text'),
                            'image': sum(1 for m in all_metadata if m['type'] == 'image'),
                            'table': sum(1 for m in all_metadata if m['type'] == 'table')
                        },
                        'processing_timestamp': int(time.time()),
                        'vector_db_path': target_vector_db,  # 添加向量数据库路径信息
                        'items': processed_items
                    }
                    
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata_summary, f, ensure_ascii=False, indent=2)
                    
                    print(f"     📄 元数据已保存到: {metadata_file}")
                    
                    return {
                        'stored_items': total_vectors,
                        'storage_path': target_vector_db,
                        'metadata_file': metadata_file,
                        'status': 'success'
                    }
                else:
                    print(f"     ❌ 向量存储失败")
                    return {
                        'stored_items': 0,
                        'storage_path': target_vector_db,
                        'status': 'failed',
                        'error': '向量存储失败'
                    }
            else:
                print("     没有有效的向量需要存储")
                return {
                    'stored_items': 0,
                    'storage_path': target_vector_db,
                    'status': 'success',
                    'message': '没有有效的向量需要存储'
                }
                
        except Exception as e:
            logging.error(f"存储处理结果失败: {e}")
            print(f"     ❌ 存储失败: {e}")
            return {
                'stored_items': 0,
                'storage_path': target_vector_db,
                'status': 'failed',
                'error': str(e)
            }

    def _process_vectorization_result(self, item: Dict[str, Any], updated_vectors: List, updated_metadata: List, 
                                    text_updates: int, image_updates: int, table_updates: int) -> None:
        """
        处理向量化结果，提取向量和元数据
        
        :param item: 处理项目
        :param updated_vectors: 更新的向量列表
        :param updated_metadata: 更新的元数据列表
        :param text_updates: 文本更新计数
        :param image_updates: 图像更新计数
        :param table_updates: 表格更新计数
        """
        try:
            # 获取向量化结果
            vectorization_result = item.get('vectorization_result', {})
            
            # 更新文本向量
            text_vectors = vectorization_result.get('text_vectors', [])
            for tv in text_vectors:
                if tv.get('vectorization_status') == 'success':  # 修复：使用 vectorization_status 与新建模式一致
                    # 修复：使用正确的字段名，参考新建模式的实现
                    vector_data = tv.get('vector', [])
                    if vector_data:  # 确保向量数据存在
                        updated_vectors.append(vector_data)
                        
                        # 从tv对象中提取metadata，与新建模式保持一致
                        metadata = tv.get('metadata', {})
                        updated_metadata.append({
                            'type': 'text',
                            'chunk_type': 'text',
                            'source': item.get('file_info', {}).get('name', '') or metadata.get('document_name', ''),
                            'document_name': metadata.get('document_name', ''),
                            'page_number': metadata.get('page_number', 1),
                            'chunk_id': metadata.get('chunk_id', ''),
                            'text': metadata.get('text', ''),
                            'text_length': metadata.get('text_length', 0),
                            'text_level': metadata.get('text_level', 0),
                            'chunk_size': metadata.get('chunk_size', 0),
                            'chunk_overlap': metadata.get('chunk_overlap', 0),
                            'chunk_position': metadata.get('chunk_position', {}),
                            'related_images': metadata.get('related_images', []),
                            'related_tables': metadata.get('related_tables', []),
                            'text_embedding': vector_data,  # 添加text_embedding字段
                            'text_embedding_model': tv.get('text_embedding_model', 'text-embedding-v1'),  # 添加模型信息
                            'vector_type': 'text_embedding',
                            'vectorization_status': 'success',
                            'vectorization_timestamp': int(time.time()),
                            'update_type': 'content_update',
                            'update_timestamp': int(time.time()),
                            'incremental_update': True
                        })
                        text_updates += 1
            
            # 更新图像向量
            image_vectors = vectorization_result.get('image_vectors', [])
            for iv in image_vectors:
                if iv.get('vectorization_status') == 'success':  # 修复：使用 vectorization_status 与新建模式一致
                    # 修复：图像向量使用 'image_embedding' 字段，参考新建模式
                    vector_data = iv.get('image_embedding', [])
                    if vector_data:  # 确保向量数据存在
                        updated_vectors.append(vector_data)
                        
                        # 从iv对象中提取metadata，与新建模式保持一致
                        metadata = iv.get('metadata', {})
                        updated_metadata.append({
                            'type': 'image',
                            'chunk_type': 'image',
                            'source': item.get('file_info', {}).get('name', '') or metadata.get('document_name', ''),
                            'document_name': metadata.get('document_name', ''),
                            'page_number': metadata.get('page_number', 1),
                            'chunk_id': metadata.get('chunk_id', ''),
                            'image_id': metadata.get('image_id', ''),
                            'image_path': metadata.get('image_path', ''),
                            'image_filename': metadata.get('image_filename', ''),
                            'image_type': metadata.get('image_type', 'general'),
                            'image_format': metadata.get('image_format', 'UNKNOWN'),
                            'image_dimensions': metadata.get('image_dimensions', {}),
                            'basic_description': metadata.get('basic_description', ''),
                            'enhanced_description': metadata.get('enhanced_description', ''),
                            'layered_descriptions': metadata.get('layered_descriptions', {}),
                            'structured_info': metadata.get('structured_info', {}),
                            'img_caption': metadata.get('img_caption', []),
                            'img_footnote': metadata.get('img_footnote', []),
                            'enhancement_enabled': metadata.get('enhancement_enabled', True),
                            'enhancement_model': metadata.get('enhancement_model', ''),
                            'enhancement_status': metadata.get('enhancement_status', 'success'),
                            'enhancement_timestamp': metadata.get('enhancement_timestamp'),
                            'image_embedding': iv.get('image_embedding', []),
                            'description_embedding': iv.get('description_embedding', []),
                            'image_embedding_model': iv.get('embedding_model', ''),
                            'description_embedding_model': iv.get('embedding_model', ''),
                            'related_text_chunks': metadata.get('related_text_chunks', []),
                            'related_table_chunks': metadata.get('related_table_chunks', []),
                            'parent_document_id': metadata.get('parent_document_id', ''),
                            'copy_status': metadata.get('copy_status', 'success'),
                            'vectorization_status': 'success',
                            'vector_type': 'visual_embedding',
                            'vectorization_timestamp': int(time.time()),
                            'update_type': 'content_update',
                            'update_timestamp': int(time.time()),
                            'incremental_update': True
                        })
                        image_updates += 1
            
            # 更新表格向量
            table_vectors = vectorization_result.get('table_vectors', [])
            for tv in table_vectors:
                if tv.get('vectorization_status') == 'success':  # 修复：使用 vectorization_status 与新建模式一致
                    # 修复：使用正确的字段名，参考新建模式的实现
                    vector_data = tv.get('vector', [])
                    if vector_data:  # 确保向量数据存在
                        updated_vectors.append(vector_data)
                        
                        # 从tv对象中提取metadata，与新建模式保持一致
                        metadata = tv.get('metadata', {})
                        updated_metadata.append({
                            'type': 'table',
                            'chunk_type': 'table',
                            'source': item.get('file_info', {}).get('name', '') or metadata.get('document_name', ''),
                            'document_name': metadata.get('document_name', ''),
                            'page_number': metadata.get('page_number', 1),
                            'chunk_id': metadata.get('chunk_id', ''),
                            'table_id': metadata.get('table_id', ''),
                            'table_type': metadata.get('table_type', 'data_table'),
                            'table_title': metadata.get('table_title', ''),
                            'table_summary': metadata.get('table_summary', ''),
                            'table_headers': metadata.get('table_headers', []),
                            'table_row_count': metadata.get('table_rows', 0),
                            'table_column_count': metadata.get('table_columns', 0),
                            'table_body': metadata.get('table_body', ''),
                            'table_content': metadata.get('table_content', ''),
                            'table_caption': metadata.get('table_caption', []),
                            'table_footnote': metadata.get('table_footnote', []),
                            'is_subtable': metadata.get('is_subtable', False),
                            'parent_table_id': metadata.get('parent_table_id'),
                            'subtable_index': metadata.get('subtable_index'),
                            'chunk_start_row': metadata.get('chunk_start_row', 0),
                            'chunk_end_row': metadata.get('chunk_end_row', 0),
                            'related_text': metadata.get('related_text', ''),
                            'related_images': metadata.get('related_images', []),
                            'related_text_chunks': metadata.get('related_text_chunks', []),
                            'table_context': metadata.get('table_context', ''),
                            'table_embedding': vector_data,  # 添加table_embedding字段
                            'table_embedding_model': tv.get('table_embedding_model', 'text-embedding-v1'),  # 添加模型信息
                            'vector_type': 'text_embedding',
                            'vectorization_status': 'success',
                            'vectorization_timestamp': int(time.time()),
                            'update_type': 'content_update',
                            'update_timestamp': int(time.time()),
                            'incremental_update': True
                        })
                        table_updates += 1
                    
        except Exception as e:
            logging.error(f"处理向量化结果失败: {e}")
            raise

    def _update_results(self, processing_result: Dict[str, Any], target_vector_db: str) -> Dict[str, Any]:
        """
        更新处理结果
        
        功能：
        - 更新向量数据库中的现有内容
        - 处理内容更新和修改
        - 维护数据一致性
        - 提供详细的更新统计
        """
        try:
            print("   🔄 更新向量数据库...")
            
            # 确保目标目录存在
            os.makedirs(target_vector_db, exist_ok=True)
            
            # 获取处理的项目
            processed_items = processing_result.get('processed_items', [])
            if not processed_items:
                print("     没有需要更新的内容")
                return {
                    'updated_items': 0,
                    'storage_path': target_vector_db,
                    'status': 'success',
                    'message': '没有需要更新的内容'
                }
            
            # 统计更新信息
            total_updated = 0
            text_updates = 0
            image_updates = 0
            table_updates = 0
            failed_updates = 0
            
            # 收集需要更新的向量和元数据
            updated_vectors = []
            updated_metadata = []
            
            for item in processed_items:
                if item.get('status') == 'success':
                    try:
                        # 处理数据结构嵌套问题
                        # 增量模式返回的是嵌套结构，新建模式返回的是直接结构
                        if 'processed_items' in item:
                            # 处理嵌套结构（增量模式）
                            print(f"     检测到增量模式数据结构，处理嵌套项...")
                            for sub_item in item['processed_items']:
                                if sub_item.get('status') == 'success':
                                    self._process_vectorization_result(
                                        sub_item, updated_vectors, updated_metadata,
                                        text_updates, image_updates, table_updates
                                    )
                                    total_updated += 1
                        else:
                            # 处理直接结构（新建模式）
                            self._process_vectorization_result(
                                item, updated_vectors, updated_metadata,
                                text_updates, image_updates, table_updates
                            )
                            total_updated += 1
                        
                    except Exception as e:
                        logging.error(f"处理项目更新失败: {e}")
                        failed_updates += 1
                        continue
                else:
                    failed_updates += 1
            
            # 执行数据库更新
            if updated_vectors and updated_metadata:
                print(f"     准备更新 {len(updated_vectors)} 个向量...")
                
                # 使用向量存储管理器更新
                update_success = self.vector_store_manager.update_vectors(
                    updated_vectors, updated_metadata
                )
                
                if update_success:
                    print(f"     ✅ 成功更新 {len(updated_vectors)} 个向量")
                else:
                    print(f"     ❌ 向量数据库更新失败")
                    return {
                        'updated_items': 0,
                        'storage_path': target_vector_db,
                        'status': 'failed',
                        'error': '向量数据库更新失败'
                    }
            
            # 更新元数据管理器
            self._update_metadata_manager(updated_metadata)
            
            # 生成更新结果
            result = {
                'updated_items': total_updated,
                'storage_path': target_vector_db,
                'status': 'success',
                'update_statistics': {
                    'total_vectors_updated': len(updated_vectors),
                    'text_updates': text_updates,
                    'image_updates': image_updates,
                    'table_updates': table_updates,
                    'failed_updates': failed_updates
                },
                'update_timestamp': int(time.time()),
                'update_type': 'content_update'
            }
            
            print(f"   📊 更新完成: 成功更新 {total_updated} 个项目，{len(updated_vectors)} 个向量")
            return result
            
        except Exception as e:
            error_msg = f"更新处理结果失败: {e}"
            logging.error(error_msg)
            self.failure_handler.record_failure('update_results', 'content_update', str(e))
            
            return {
                'updated_items': 0,
                'storage_path': target_vector_db,
                'status': 'failed',
                'error': str(e)
            }

    def _update_metadata_manager(self, updated_metadata: List[Dict[str, Any]]):
        """
        更新元数据管理器
        
        :param updated_metadata: 更新的元数据列表
        """
        try:
            if not updated_metadata:
                return
            
            # 更新元数据管理器中的相关记录
            for metadata in updated_metadata:
                chunk_id = metadata.get('chunk_id') or metadata.get('image_id') or metadata.get('table_id')
                if chunk_id:
                    # 查找现有元数据并更新
                    existing_metadata = self.metadata_manager.get_metadata_by_id(chunk_id)
                    if existing_metadata:
                        # 更新元数据
                        updates = {
                            'updated_timestamp': int(time.time()),
                            'vectorization_status': 'updated',
                            'update_type': metadata.get('update_type', 'content_update'),
                            'update_timestamp': metadata.get('update_timestamp')
                        }
                        self.metadata_manager.update_metadata(chunk_id, updates)
            
            logging.info(f"元数据管理器更新完成: {len(updated_metadata)} 条记录")
            
        except Exception as e:
            logging.error(f"更新元数据管理器失败: {e}")

    def _generate_final_report(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终报告"""
        report = {
            'success': result.get('success', False),
            'mode': result.get('mode', 'unknown'),
            'timestamp': None,  # 将在下面设置
            'system_info': self._get_system_info(),
            'processing_stats': self._get_processing_stats(result)
        }
        
        # 保留原始的storage_path字段
        if 'storage_path' in result:
            report['storage_path'] = result['storage_path']
        elif 'target_vector_db' in result:
            report['storage_path'] = result['target_vector_db']

        # 设置时间戳
        import time
        report['timestamp'] = int(time.time())

        # 添加模式特定的信息
        if result.get('mode') == 'new':
            report['database_status'] = 'created'
        elif result.get('mode') == 'incremental':
            report['database_status'] = 'updated'

        # 添加失败处理统计
        if hasattr(self, 'failure_handler') and self.failure_handler:
            report['failure_stats'] = self.failure_handler.get_failure_summary()

        return report

    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import platform

        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'system': platform.system(),
            'processor': platform.processor()
        }

    def _get_processing_stats(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = {
            'mode': result.get('mode', 'unknown'),
            'success': result.get('success', False)
        }

        # 添加处理结果统计
        processing_result = result.get('processing_result', {})
        if processing_result:
            stats.update({
                'total_files': processing_result.get('total_files', 0),
                'processed_items': len(processing_result.get('processed_items', []))
            })

        # 添加存储结果统计
        storage_result = result.get('storage_result', {})
        if storage_result:
            stats.update({
                'stored_items': storage_result.get('stored_items', 0),
                'storage_path': storage_result.get('storage_path', '')
            })

        return stats

    def _get_pdf_files(self, input_path: str) -> List[str]:
        """获取PDF文件列表"""
        try:
            if not os.path.exists(input_path):
                return []
            
            pdf_files = []
            for file in os.listdir(input_path):
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(input_path, file))
            
            return sorted(pdf_files)
            
        except Exception as e:
            logging.error(f"获取PDF文件列表失败: {e}")
            return []

    def _parse_pdf_with_mineru(self, pdf_path: str, output_dir: str) -> Dict[str, Any]:
        """使用minerU解析PDF"""
        try:
            # 导入minerU集成模块
            from utils.mineru_integration import MinerUIntegration
            
            # 创建minerU集成实例
            mineru = MinerUIntegration(self.config_manager)
            
            # 使用配置文件中的mineru_output_dir，而不是传入的output_dir
            mineru_output_dir = self.config_manager.get_path('mineru_output_dir')
            
            # 解析PDF到正确的MinerU输出目录
            result = mineru.parse_pdf_document(pdf_path, mineru_output_dir)
            
            return result
            
        except Exception as e:
            logging.error(f"minerU解析PDF失败: {pdf_path}, 错误: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # 注意：_vectorize_parsed_content方法已被删除
    # 图片向量化现在通过ImageProcessor -> ImageVectorizer统一处理
    # 文本和表格向量化通过VectorizationManager统一处理

    def _call_mineru_api(self, pdf_path: str) -> Dict[str, Any]:
        """
        调用MinerU API处理PDF文档
        
        :param pdf_path: PDF文件路径
        :return: MinerU处理结果
        """
        try:
            if not pdf_path or not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            # 获取MinerU配置
            mineru_config = self.config_manager.get('mineru', {})
            api_key = mineru_config.get('api_key') or os.getenv('MINERU_API_KEY')
            output_dir = mineru_config.get('output_dir', './document/md')
            
            if not api_key:
                raise RuntimeError("缺少MinerU API密钥")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 调用MinerU集成模块
            from utils.mineru_integration import MinerUIntegration
            mineru = MinerUIntegration(self.config_manager)
            
            # 解析PDF到正确的MinerU输出目录
            result = mineru.parse_pdf_document(pdf_path, output_dir)
            
            return result
            
        except Exception as e:
            logging.error(f"minerU解析PDF失败: {pdf_path}, 错误: {e}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    # 测试V3MainProcessor
    try:
        processor = V3MainProcessor()

        # 测试默认处理
        result = processor.process_documents()
        print(f"\n处理结果: {'成功' if result.get('success') else '失败'}")

        if not result.get('success'):
            print(f"错误: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"V3MainProcessor测试失败: {e}")
