'''
程序说明：
## 1. 统一的文档处理管道，整合从PDF到向量数据库的完整流程
## 2. 整合现有的所有文档处理功能
## 3. 统一接口和错误处理
## 4. 提供清晰的处理步骤和状态反馈
## 5. 解决向量存储ID映射问题
'''

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# 导入各个处理器
from .pdf_processor import PDFProcessor
from .image_extractor import ImageExtractor
from .document_chunker import DocumentChunker
from .vector_generator import VectorGenerator
from .markdown_processor import MarkdownProcessor

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key, get_mineru_api_key

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessingPipeline:
    """
    文档处理管道，整合PDF处理、Markdown处理和向量生成
    """
    
    def __init__(self, config):
        """
        初始化文档处理管道
        
        :param config: 配置对象
        """
        self.config = config
        
        # 初始化各个处理器
        if hasattr(self.config, '__dict__'):
            config_dict = self.config.__dict__
        else:
            config_dict = self.config
        
        self.pdf_processor = PDFProcessor(config_dict)
        self.markdown_processor = MarkdownProcessor(config_dict)
        self.vector_generator = VectorGenerator(config_dict)
        
        # 处理状态跟踪
        self.processing_status = {
            'pdf_conversion': False,
            'markdown_processing': False,
            'vector_generation': False
        }
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """
        验证配置的完整性
        """
        try:
            # 使用统一的API密钥管理模块检查API密钥
            dashscope_key = getattr(self.config, 'dashscope_api_key', '')
            dashscope_status = get_dashscope_api_key(dashscope_key)
            if dashscope_status:
                logger.info("DashScope API密钥已配置")
            else:
                logger.warning("DashScope API密钥未配置，向量生成功能可能受限")
            
            mineru_key = getattr(self.config, 'mineru_api_key', '')
            mineru_status = get_mineru_api_key(mineru_key)
            if mineru_status:
                logger.info("minerU API密钥已配置")
            else:
                logger.warning("minerU API密钥未配置，PDF转换功能可能受限")
            
            # 检查必需的路径配置
            required_paths = [
                'pdf_dir', 'output_dir', 'md_dir', 'vector_db_dir', 'central_images_dir'
            ]
            
            for path_name in required_paths:
                path_value = getattr(self.config, path_name, None)
                if not path_value:
                    logger.warning(f"缺少路径配置: {path_name}")
            
            # 检查处理参数
            if self.config.chunk_size <= 0:
                logger.warning("chunk_size配置无效，使用默认值1000")
                self.config.chunk_size = 1000
            
            if self.config.chunk_overlap < 0:
                logger.warning("chunk_overlap配置无效，使用默认值200")
                self.config.chunk_overlap = 200
            
            logger.info("配置验证完成")
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
    
    def process_from_pdf(self, pdf_dir: str, output_dir: str, vector_db_path: str) -> Dict[str, Any]:
        """
        从PDF开始的完整文档处理流程
        :param pdf_dir: PDF文件目录
        :param output_dir: 输出目录
        :param vector_db_path: 向量数据库路径
        :return: 处理结果和统计信息
        """
        result = {
            'success': False,
            'steps': {},
            'statistics': {},
            'errors': []
        }
        
        try:
            logger.info("开始从PDF处理文档...")
            
            # 步骤1: PDF转换
            logger.info("步骤1: 开始PDF转换...")
            conversion_result = self.pdf_processor.convert_pdfs(pdf_dir, output_dir)
            if conversion_result:
                self.processing_status['pdf_conversion'] = True
                result['steps']['pdf_conversion'] = {
                    'status': 'success',
                    'files_processed': len(conversion_result)
                }
                logger.info(f"PDF转换完成，处理了 {len(conversion_result)} 个文件")
            else:
                result['errors'].append("PDF转换失败")
                logger.error("PDF转换失败")
                return result
            
            # 获取现有的Markdown文件
            md_files = list(Path(output_dir).glob("*.md"))
            md_files = [str(f) for f in md_files]
            
            if not md_files:
                result['errors'].append("没有找到Markdown文件")
                logger.error("没有找到Markdown文件")
                return result
            
            logger.info(f"找到 {len(md_files)} 个现有Markdown文件")
            
            # 调用从markdown开始的处理流程
            markdown_result = self._process_from_markdown_files(md_files, vector_db_path)
            
            # 合并结果
            result['steps'].update(markdown_result['steps'])
            result['errors'].extend(markdown_result['errors'])
            result['success'] = markdown_result['success']
            
            if result['success']:
                result['statistics'] = self._generate_statistics(result['steps'])
                logger.info("从PDF开始的文档处理流程完成！")
            
            return result
            
        except Exception as e:
            error_msg = f"从PDF开始的文档处理流程失败: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
    def process_from_markdown(self, md_dir: str, vector_db_path: str) -> Dict[str, Any]:
        """
        从Markdown开始的文档处理流程
        :param md_dir: Markdown文件目录
        :param vector_db_path: 向量数据库路径
        :return: 处理结果和统计信息
        """
        result = {
            'success': False,
            'steps': {},
            'statistics': {},
            'errors': []
        }
        
        try:
            logger.info("开始从Markdown处理文档...")
            
            # 获取Markdown文件列表
            md_files = list(Path(md_dir).glob("*.md"))
            if not md_files:
                result['errors'].append("没有找到Markdown文件")
                logger.error("没有找到Markdown文件")
                return result
            
            md_file_paths = [str(f) for f in md_files]
            logger.info(f"找到 {len(md_file_paths)} 个Markdown文件")
            
            # 调用内部处理方法
            result = self._process_from_markdown_files(md_file_paths, vector_db_path)
            
            if result['success']:
                result['statistics'] = self._generate_statistics(result['steps'])
                logger.info("从Markdown开始的文档处理流程完成！")
            
            return result
            
        except Exception as e:
            error_msg = f"从Markdown开始的文档处理流程失败: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
    def _process_from_markdown_files(self, md_files: List[str], vector_db_path: str) -> Dict[str, Any]:
        """
        从Markdown文件列表开始处理（内部方法）
        :param md_files: Markdown文件路径列表
        :param vector_db_path: 向量数据库路径
        :return: 处理结果和统计信息
        """
        result = {
            'success': False,
            'steps': {},
            'statistics': {},
            'errors': []
        }
        
        try:
            # 步骤2: 提取图片
            logger.info("步骤2: 开始图片提取...")
            # 优先从JSON文件中提取图片信息（包含更完整的metadata）
            json_image_files = self.image_extractor.extract_images_from_json_files(md_files)
            
            # 如果JSON中没有图片信息，再从Markdown文件中提取
            if not json_image_files:
                image_files = self.image_extractor.extract_images(md_files)
                all_image_files = image_files if image_files else []
            else:
                all_image_files = json_image_files
            
            if all_image_files:
                self.processing_status['image_extraction'] = True
                result['steps']['image_extraction'] = {
                    'status': 'success',
                    'images_extracted': len(all_image_files),
                    'images': all_image_files
                }
                logger.info(f"图片提取完成，提取了 {len(all_image_files)} 张图片")
            else:
                logger.warning("图片提取失败或没有图片")
            
            # 步骤3: 文档分块（文本分块+增强表格处理）
            logger.info("步骤3: 开始文档分块处理（文本分块+增强表格处理）...")
            chunks = self.document_chunker.process_documents(md_files)
            if chunks:
                self.processing_status['document_chunking'] = True
                result['steps']['document_chunking'] = {
                    'status': 'success',
                    'total_chunks': len(chunks),
                    'text_chunks': len([c for c in chunks if c.metadata.get('chunk_type') == 'text']),
                    'table_chunks': len([c for c in chunks if c.metadata.get('chunk_type') == 'table'])
                }
                logger.info(f"文档分块完成，生成了 {len(chunks)} 个分块")
            else:
                result['errors'].append("文档分块失败")
                logger.error("文档分块失败")
                return result
            
            # 步骤4: 生成向量数据库
            logger.info("步骤4: 开始生成向量数据库...")
            vector_store = self.vector_generator.create_vector_store(chunks, vector_db_path)
            if vector_store:
                self.processing_status['vector_generation'] = True
                result['steps']['vector_generation'] = {
                    'status': 'success',
                    'vector_store_path': vector_db_path,
                    'total_chunks': len(chunks)
                }
                logger.info("向量数据库生成完成")
            else:
                result['errors'].append("向量数据库生成失败")
                logger.error("向量数据库生成失败")
                return result
            
            # 步骤5: 添加图片向量
            if all_image_files and self.processing_status['image_extraction']:
                logger.info("步骤5: 开始添加图片向量...")
                success = self.vector_generator.add_images_to_store(vector_store, all_image_files, vector_db_path)
                if success:
                    self.processing_status['image_vector_addition'] = True
                    # 获取实际的添加结果
                    total_processed = len(all_image_files)
                    # 从向量生成器获取实际添加的图片数量
                    actual_added = self.vector_generator.get_last_image_addition_result()
                    failed_count = total_processed - actual_added if actual_added is not None else 0
                    
                    result['steps']['image_vector_addition'] = {
                        'status': 'success',
                        'images_added': actual_added or total_processed,
                        'images_failed': failed_count,
                        'total_images_processed': total_processed
                    }
                    logger.info(f"图片向量添加完成，处理了 {total_processed} 张图片，成功添加 {actual_added or total_processed} 张，失败 {failed_count} 张")
                else:
                    logger.warning("图片向量添加失败")
            
            result['success'] = True
            return result
            
        except Exception as e:
            error_msg = f"Markdown文件处理失败: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
    def process_pipeline(self, pdf_dir: str, output_dir: str, vector_db_path: str) -> Dict[str, Any]:
        """
        完整的文档处理流程（保持向后兼容）
        :param pdf_dir: PDF文件目录
        :param output_dir: 输出目录
        :param vector_db_path: 向量数据库路径
        :return: 处理结果和统计信息
        """
        return self.process_from_pdf(pdf_dir, output_dir, vector_db_path)
    
    def _generate_statistics(self, steps: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成处理统计信息
        :param steps: 处理步骤信息
        :return: 统计信息
        """
        stats = {
            'total_files_processed': 0,
            'total_chunks_generated': 0,
            'total_images_extracted': 0,
            'processing_time': 0,
            'successful_steps': 0,
            'failed_steps': 0
        }
        
        for step_name, step_info in steps.items():
            if step_info.get('status') == 'success':
                stats['successful_steps'] += 1
                
                if step_name == 'pdf_conversion':
                    stats['total_files_processed'] = step_info.get('files_processed', 0)
                elif step_name == 'document_chunking':
                    stats['total_chunks_generated'] = step_info.get('total_chunks', 0)
                elif step_name == 'image_extraction':
                    stats['total_images_extracted'] = step_info.get('images_extracted', 0)
                elif step_name == 'vector_generation':
                    # 向量生成步骤，从步骤信息中获取分块数
                    stats['total_chunks_generated'] = step_info.get('total_chunks', 0)
                elif step_name == 'image_vector_addition':
                    stats['total_images_extracted'] = step_info.get('images_added', 0)
            else:
                stats['failed_steps'] += 1
        
        return stats
    
    def get_processing_status(self) -> Dict[str, bool]:
        """
        获取处理状态
        :return: 处理状态字典
        """
        return self.processing_status.copy()
    
    def reset_status(self):
        """
        重置处理状态
        """
        for key in self.processing_status:
            self.processing_status[key] = False 