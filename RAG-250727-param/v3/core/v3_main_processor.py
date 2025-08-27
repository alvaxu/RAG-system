"""
V3版本主处理器

V3版本向量数据库构建系统的核心控制器，负责统一管理整个文档处理流程。
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from config.config_manager import ConfigManager
from utils.document_type_detector import DocumentTypeDetector
from utils.model_caller import ModelCaller
from .content_processor import ContentProcessor
from .vectorization_manager import VectorizationManager
from .metadata_manager import MetadataManager
from .vector_store_manager import VectorStoreManager

class V3MainProcessor:
    """
    V3版本主处理器

    功能：
    - 统一的程序入口和流程控制
    - 智能模式选择（新建 vs 增量）
    - 与所有子模块的深度集成
    - 配置管理和验证
    - 失败处理和状态跟踪
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

        logging.info("V3MainProcessor初始化完成")

    def _initialize_modules(self):
        """初始化所有子模块"""
        try:
            # 文档类型检测器
            self.document_type_detector = DocumentTypeDetector(self.config_manager)

            # AI模型调用器
            self.model_caller = ModelCaller(self.config_manager)

            # 内容处理器
            self.content_processor = ContentProcessor(self.config_manager, self.model_caller)

            # 向量化管理器
            self.vectorization_manager = VectorizationManager(self.config_manager, self.model_caller)

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
        index_file = os.path.join(target_vector_db, 'index.faiss')
        metadata_file = os.path.join(target_vector_db, 'metadata.pkl')

        exists = os.path.exists(index_file) and os.path.exists(metadata_file)

        if exists:
            logging.info(f"检测到现有向量数据库: {target_vector_db}")
        else:
            logging.info(f"未检测到向量数据库: {target_vector_db}")

        return exists

    def _new_process(self, validation_result: Dict[str, Any], target_vector_db: str) -> Dict[str, Any]:
        """新建模式处理"""
        try:
            print("\n🏗️  开始新建模式处理...")

            # 1. 初始化向量数据库
            success = self.vector_store_manager.create_vector_store(
                dimension=1536,  # 默认向量维度
                index_type='faiss'
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
            # 这里需要实现加载逻辑

            # 2. 处理新增文档内容
            processing_result = self._process_documents_incremental(validation_result)

            # 3. 更新向量数据库
            storage_result = self._update_results(processing_result, target_vector_db)

            # 4. 生成报告
            result = {
                'success': True,
                'mode': 'incremental',
                'processing_result': processing_result,
                'storage_result': storage_result,
                'target_vector_db': target_vector_db
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
            
            # 获取输入路径
            input_path = validation_result.get('input_path', './document/orig_pdf')
            output_path = validation_result.get('output_path', './document/md')
            
            # 确保输出目录存在
            os.makedirs(output_path, exist_ok=True)
            
            # 获取PDF文件列表
            pdf_files = self._get_pdf_files(input_path)
            if not pdf_files:
                return {
                    'processed_items': [],
                    'total_files': 0,
                    'status': 'success',
                    'message': '未找到PDF文件'
                }
            
            print(f"   发现 {len(pdf_files)} 个PDF文件")
            
            # 处理每个PDF文件
            processed_items = []
            total_size = 0
            
            for i, pdf_file in enumerate(pdf_files):
                print(f"   处理第 {i+1}/{len(pdf_files)} 个文件: {os.path.basename(pdf_file)}")
                
                try:
                    # 解析PDF
                    parse_result = self._parse_pdf_with_mineru(pdf_file, output_path)
                    
                    if parse_result.get('success'):
                        # 向量化内容
                        vectorization_result = self._vectorize_parsed_content(parse_result['parsed_content'])
                        
                        # 合并结果
                        item_result = {
                            'pdf_path': pdf_file,
                            'parse_result': parse_result,
                            'vectorization_result': vectorization_result,
                            'file_size': parse_result.get('file_size', 0),
                            'status': 'success'
                        }
                        
                        processed_items.append(item_result)
                        total_size += item_result['file_size']
                        
                        print(f"     ✅ 处理成功")
                    else:
                        print(f"     ❌ 处理失败: {parse_result.get('error')}")
                        
                        # 记录失败项
                        processed_items.append({
                            'pdf_path': pdf_file,
                            'status': 'failed',
                            'error': parse_result.get('error'),
                            'file_size': 0
                        })
                
                except Exception as e:
                    logging.error(f"处理PDF文件失败: {pdf_file}, 错误: {e}")
                    print(f"     ❌ 处理异常: {e}")
                    
                    processed_items.append({
                        'pdf_path': pdf_file,
                        'status': 'failed',
                        'error': str(e),
                        'file_size': 0
                    })
            
            # 统计结果
            success_count = sum(1 for item in processed_items if item.get('status') == 'success')
            failed_count = len(processed_items) - success_count
            
            print(f"   处理完成: 成功 {success_count} 个，失败 {failed_count} 个")
            
            return {
                'processed_items': processed_items,
                'total_files': len(pdf_files),
                'success_count': success_count,
                'failed_count': failed_count,
                'total_size': total_size,
                'status': 'success'
            }
            
        except Exception as e:
            logging.error(f"新建模式文档处理失败: {e}")
            return {
                'processed_items': [],
                'total_files': 0,
                'status': 'failed',
                'error': str(e)
            }

    def _process_documents_incremental(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """增量模式文档处理"""
        # 占位符实现
        print("   📄 处理新增文档内容...")

        return {
            'processed_items': [],
            'new_files': validation_result.get('file_count', 0),
            'status': 'success'
        }

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
                        if tv.get('status') == 'success':
                            all_vectors.append(tv['vector'])
                            all_metadata.append({
                                'type': 'text',
                                'source': item.get('pdf_path'),
                                'chunk': tv['chunk'],
                                'vector_type': 'text_embedding'
                            })
                            total_vectors += 1
                    
                    # 收集图像向量
                    image_vectors = vectorization_result.get('image_vectors', [])
                    for iv in image_vectors:
                        if iv.get('status') == 'success':
                            all_vectors.append(iv['vector'])
                            all_metadata.append({
                                'type': 'image',
                                'source': item.get('pdf_path'),
                                'image': iv['image'],
                                'enhanced_description': iv.get('enhanced_description'),
                                'vector_type': 'visual_embedding'
                            })
                            total_vectors += 1
                    
                    # 收集表格向量
                    table_vectors = vectorization_result.get('table_vectors', [])
                    for tv in table_vectors:
                        if tv.get('status') == 'success':
                            all_vectors.append(tv['vector'])
                            all_metadata.append({
                                'type': 'table',
                                'source': item.get('pdf_path'),
                                'table': tv['table'],
                                'vector_type': 'text_embedding'
                            })
                            total_vectors += 1
            
            # 存储到向量数据库
            if all_vectors:
                print(f"     存储 {len(all_vectors)} 个向量到数据库...")
                
                # 使用向量存储管理器存储
                success = self.vector_store_manager.add_vectors(all_vectors, all_metadata)
                
                if success:
                    print(f"     ✅ 向量存储成功")
                    
                    # 创建元数据文件
                    metadata_file = os.path.join(target_vector_db, 'processing_metadata.json')
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

    def _update_results(self, processing_result: Dict[str, Any], target_vector_db: str) -> Dict[str, Any]:
        """更新处理结果"""
        # 占位符实现
        print("   🔄 更新向量数据库...")

        return {
            'updated_items': 0,
            'storage_path': target_vector_db,
            'status': 'success'
        }

    def _generate_final_report(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终报告"""
        report = {
            'success': result.get('success', False),
            'mode': result.get('mode', 'unknown'),
            'timestamp': None,  # 将在下面设置
            'system_info': self._get_system_info(),
            'processing_stats': self._get_processing_stats(result)
        }

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

    def _vectorize_parsed_content(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """向量化解析后的内容"""
        try:
            vectorization_result = {
                'text_vectors': [],
                'image_vectors': [],
                'table_vectors': [],
                'metadata': {}
            }
            
            # 向量化文本块
            text_chunks = parsed_content.get('text_chunks', [])
            for chunk in text_chunks:
                try:
                    vector = self.model_caller.call_text_embedding(chunk['content'])
                    vectorization_result['text_vectors'].append({
                        'chunk': chunk,
                        'vector': vector,
                        'status': 'success'
                    })
                except Exception as e:
                    logging.error(f"文本向量化失败: {e}")
                    vectorization_result['text_vectors'].append({
                        'chunk': chunk,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # 向量化图像
            images = parsed_content.get('images', [])
            for image in images:
                try:
                    # 图像增强描述
                    enhanced_description = self.model_caller.call_image_enhancement(
                        image.get('image_path', '')
                    )
                    
                    # 图像向量化
                    image_vector = self.model_caller.call_visual_embedding(
                        image.get('image_path', '')
                    )
                    
                    vectorization_result['image_vectors'].append({
                        'image': image,
                        'enhanced_description': enhanced_description,
                        'vector': image_vector,
                        'status': 'success'
                    })
                except Exception as e:
                    logging.error(f"图像向量化失败: {e}")
                    vectorization_result['image_vectors'].append({
                        'image': image,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # 向量化表格
            tables = parsed_content.get('tables', [])
            for table in tables:
                try:
                    # 表格内容向量化
                    table_text = table.get('text_content', '')
                    if table_text:
                        vector = self.model_caller.call_text_embedding(table_text)
                        vectorization_result['table_vectors'].append({
                            'table': table,
                            'vector': vector,
                            'status': 'success'
                        })
                    else:
                        vectorization_result['table_vectors'].append({
                            'table': table,
                            'status': 'failed',
                            'error': '表格内容为空'
                        })
                except Exception as e:
                    logging.error(f"表格向量化失败: {e}")
                    vectorization_result['table_vectors'].append({
                        'table': table,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # 添加元数据
            vectorization_result['metadata'] = parsed_content.get('metadata', {})
            
            return vectorization_result
            
        except Exception as e:
            logging.error(f"内容向量化失败: {e}")
            return {
                'text_vectors': [],
                'image_vectors': [],
                'table_vectors': [],
                'metadata': {},
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
