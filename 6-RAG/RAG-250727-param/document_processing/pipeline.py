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
from .markdown_processor import MarkdownProcessor
from .image_extractor import ImageExtractor
from .document_chunker import DocumentChunker
from .table_processor import TableProcessor
from .vector_generator import VectorGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessingPipeline:
    """
    统一的文档处理管道
    从PDF到向量数据库的完整流程
    """
    
    def __init__(self, config):
        """
        初始化文档处理管道
        :param config: 配置对象
        """
        self.config = config
        self.pdf_processor = PDFProcessor(config)
        self.markdown_processor = MarkdownProcessor(config)
        self.image_extractor = ImageExtractor(config)
        self.document_chunker = DocumentChunker(config)
        self.table_processor = TableProcessor(config)
        self.vector_generator = VectorGenerator(config)
        
        # 处理状态
        self.processing_status = {
            'pdf_conversion': False,
            'image_extraction': False,
            'document_chunking': False,
            'table_processing': False,
            'vector_generation': False,
            'image_vector_addition': False
        }
    
    def process_pipeline(self, pdf_dir: str, output_dir: str, vector_db_path: str) -> Dict[str, Any]:
        """
        完整的文档处理流程
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
            logger.info("开始文档处理流程...")
            
            # 步骤1: PDF转Markdown
            logger.info("步骤1: 开始PDF转Markdown处理...")
            md_files = self.pdf_processor.convert_pdfs(pdf_dir, output_dir)
            if md_files:
                self.processing_status['pdf_conversion'] = True
                result['steps']['pdf_conversion'] = {
                    'status': 'success',
                    'files_processed': len(md_files),
                    'files': md_files
                }
                logger.info(f"PDF转换完成，生成了 {len(md_files)} 个Markdown文件")
            else:
                result['errors'].append("PDF转换失败")
                logger.error("PDF转换失败")
                return result
            
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
            
            # 步骤3: 文档分块
            logger.info("步骤3: 开始文档分块处理...")
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
            
            # 步骤4: 表格处理
            logger.info("步骤4: 开始表格处理...")
            table_chunks = self.table_processor.process_tables(chunks)
            if table_chunks is not None:
                self.processing_status['table_processing'] = True
                result['steps']['table_processing'] = {
                    'status': 'success',
                    'table_chunks_processed': len(table_chunks)
                }
                logger.info(f"表格处理完成，处理了 {len(table_chunks)} 个表格分块")
            else:
                logger.warning("表格处理失败或没有表格")
            
            # 步骤5: 生成向量数据库
            logger.info("步骤5: 开始生成向量数据库...")
            all_chunks = chunks + (table_chunks if table_chunks else [])
            vector_store = self.vector_generator.create_vector_store(all_chunks, vector_db_path)
            if vector_store:
                self.processing_status['vector_generation'] = True
                result['steps']['vector_generation'] = {
                    'status': 'success',
                    'vector_store_path': vector_db_path
                }
                logger.info("向量数据库生成完成")
            else:
                result['errors'].append("向量数据库生成失败")
                logger.error("向量数据库生成失败")
                return result
            
            # 步骤6: 添加图片向量
            if all_image_files and self.processing_status['image_extraction']:
                logger.info("步骤6: 开始添加图片向量...")
                success = self.vector_generator.add_images_to_store(vector_store, all_image_files, vector_db_path)
                if success:
                    self.processing_status['image_vector_addition'] = True
                    result['steps']['image_vector_addition'] = {
                        'status': 'success',
                        'images_added': len(all_image_files)
                    }
                    logger.info(f"图片向量添加完成，添加了 {len(all_image_files)} 张图片")
                else:
                    logger.warning("图片向量添加失败")
            
            # 生成统计信息
            result['statistics'] = self._generate_statistics(result['steps'])
            result['success'] = True
            
            logger.info("文档处理流程完成！")
            return result
            
        except Exception as e:
            error_msg = f"文档处理流程失败: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
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