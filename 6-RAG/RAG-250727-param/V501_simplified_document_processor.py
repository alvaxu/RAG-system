'''
程序说明：
## 1. 简化版的统一文档处理器，使用新的配置管理
## 2. 简化命令行参数，支持配置文件
## 3. 提供更友好的用户界面
## 4. 保持与现有系统的兼容性
'''

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入配置管理
from config import ConfigManager
# 导入文档处理管道
from document_processing import DocumentProcessingPipeline

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class SimplifiedDocumentProcessor:
    """
    简化版文档处理器
    """
    
    def __init__(self, config_file: str = None):
        """
        初始化简化版文档处理器
        :param config_file: 配置文件路径
        """
        self.config_manager = ConfigManager(config_file)
        self.pipeline = DocumentProcessingPipeline(self.config_manager.get_config_for_processing())
    
    def process_from_pdf(self, pdf_dir: str = None, output_dir: str = None, vector_db_path: str = None) -> bool:
        """
        从PDF开始处理文档
        :param pdf_dir: PDF文件目录
        :param output_dir: 输出目录
        :param vector_db_path: 向量数据库路径
        :return: 是否成功
        """
        try:
            # 使用配置中的路径，如果参数提供则覆盖
            pdf_dir = pdf_dir or self.config_manager.settings.pdf_dir
            output_dir = output_dir or self.config_manager.settings.output_dir
            vector_db_path = vector_db_path or self.config_manager.settings.get_vector_db_path()
            
            logger.info("开始从PDF处理文档...")
            logger.info(f"PDF目录: {pdf_dir}")
            logger.info(f"输出目录: {output_dir}")
            logger.info(f"向量数据库: {vector_db_path}")
            
            # 执行完整的处理流程
            result = self.pipeline.process_from_pdf(pdf_dir, output_dir, vector_db_path)
            
            if result['success']:
                logger.info("文档处理成功！")
                self._print_processing_report(result)
                return True
            else:
                logger.error("文档处理失败！")
                for error in result['errors']:
                    logger.error(f"错误: {error}")
                return False
                
        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            return False
    
    def process_from_markdown(self, md_dir: str = None, vector_db_path: str = None) -> bool:
        """
        从Markdown开始处理文档
        :param md_dir: Markdown文件目录
        :param vector_db_path: 向量数据库路径
        :return: 是否成功
        """
        try:
            # 使用配置中的路径，如果参数提供则覆盖
            md_dir = md_dir or self.config_manager.settings.md_dir
            vector_db_path = vector_db_path or self.config_manager.settings.get_vector_db_path()
            
            logger.info("开始从Markdown处理文档...")
            logger.info(f"Markdown目录: {md_dir}")
            logger.info(f"向量数据库: {vector_db_path}")
            
            # 直接调用pipeline的markdown处理流程
            result = self.pipeline.process_from_markdown(md_dir, vector_db_path)
            
            if result['success']:
                logger.info("文档处理成功！")
                self._print_processing_report(result)
                return True
            else:
                logger.error("文档处理失败！")
                for error in result['errors']:
                    logger.error(f"错误: {error}")
                return False
                
        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            return False
    
    def _extract_document_name_from_image_path(self, image_path: str, md_files: List[str]) -> str:
        """
        从图片路径提取文档名称
        :param image_path: 图片路径
        :param md_files: Markdown文件列表
        :return: 文档名称
        """
        try:
            # 从图片路径推断文档名称
            image_dir = Path(image_path).parent
            for md_file in md_files:
                md_path = Path(md_file)
                if md_path.parent == image_dir.parent:
                    return md_path.stem
            return "未知文档"
        except Exception as e:
            logger.warning(f"提取文档名称失败: {e}")
            return "未知文档"
    
    def _extract_page_number_from_image_path(self, image_path: str) -> int:
        """
        从图片路径提取页码
        :param image_path: 图片路径
        :return: 页码
        """
        try:
            # 从图片文件名中提取页码信息
            image_name = Path(image_path).stem
            # 这里可以根据实际的文件命名规则来提取页码
            # 暂时返回默认值
            return 1
        except Exception as e:
            logger.warning(f"提取页码失败: {e}")
            return 1
    
    def _enhance_image_metadata_from_json(self, image_files: List[Dict[str, Any]], md_files: List[str]) -> List[Dict[str, Any]]:
        """
        从JSON文件中增强图片元信息
        :param image_files: 图片文件列表
        :param md_files: Markdown文件列表
        :return: 增强的图片文件列表
        """
        enhanced_files = []
        
        for image_file in image_files:
            # 检查是否来自JSON提取（包含完整元数据）
            has_json_metadata = (
                image_file.get('img_caption') or 
                image_file.get('img_footnote') or 
                image_file.get('source_zip') == 'json_extraction'
            )
            
            if has_json_metadata:
                # 从JSON中提取的图片信息已经包含完整元数据
                enhanced_file = {
                    **image_file,
                    'document_name': image_file.get('document_name', '未知文档'),
                    'page_number': image_file.get('page_number', 1),
                    'img_caption': image_file.get('img_caption', []),
                    'img_footnote': image_file.get('img_footnote', []),
                    'page_idx': image_file.get('page_number', 1) - 1,  # 转换为0索引
                    'image_filename': image_file.get('image_filename', ''),
                    'extension': image_file.get('extension', ''),
                    'source_zip': image_file.get('source_zip', '')
                }
                logger.info(f"使用JSON元数据: {image_file.get('image_filename', 'unknown')} - caption: {len(image_file.get('img_caption', []))} - footnote: {len(image_file.get('img_footnote', []))}")
            else:
                # 从图片路径推断信息
                image_path = image_file.get('image_path', '')
                document_name = self._extract_document_name_from_image_path(image_path, md_files)
                page_number = self._extract_page_number_from_image_path(image_path)
                
                enhanced_file = {
                    **image_file,
                    'document_name': document_name,
                    'page_number': page_number,
                    'img_caption': image_file.get('img_caption', []),
                    'img_footnote': image_file.get('img_footnote', []),
                    'page_idx': page_number - 1,
                    'image_filename': image_file.get('image_filename', ''),
                    'extension': image_file.get('extension', ''),
                    'source_zip': image_file.get('source_zip', '')
                }
                logger.info(f"使用推断元数据: {image_file.get('image_filename', 'unknown')}")
            
            enhanced_files.append(enhanced_file)
        
        return enhanced_files
    
    def _print_processing_report(self, result: dict):
        """
        打印处理报告
        :param result: 处理结果
        """
        print("\n" + "="*60)
        print("文档处理报告")
        print("="*60)
        
        if result['success']:
            print("✅ 处理状态: 成功")
            
            # 打印步骤信息
            print("\n处理步骤:")
            for step_name, step_info in result['steps'].items():
                status = "✅" if step_info.get('status') == 'success' else "❌"
                print(f"  {status} {step_name}")
                
                if step_name == 'pdf_conversion':
                    print(f"     - 处理文件数: {step_info.get('files_processed', 0)}")
                elif step_name == 'image_extraction':
                    print(f"     - 提取图片数: {step_info.get('images_extracted', 0)}")
                elif step_name == 'document_chunking':
                    print(f"     - 总分块数: {step_info.get('total_chunks', 0)}")
                    print(f"     - 文本分块: {step_info.get('text_chunks', 0)}")
                    print(f"     - 表格分块: {step_info.get('table_chunks', 0)}")
                elif step_name == 'table_processing':
                    print(f"     - 表格分块数: {step_info.get('table_chunks_processed', 0)}")
                elif step_name == 'vector_generation':
                    print(f"     - 向量存储路径: {step_info.get('vector_store_path', '')}")
                elif step_name == 'image_vector_addition':
                    print(f"     - 添加图片数: {step_info.get('images_added', 0)}")
            
            # 打印统计信息
            if 'statistics' in result:
                stats = result['statistics']
                print(f"\n统计信息:")
                print(f"  - 处理文件数: {stats.get('total_files_processed', 0)}")
                print(f"  - 生成分块数: {stats.get('total_chunks_generated', 0)}")
                print(f"  - 提取图片数: {stats.get('total_images_extracted', 0)}")
                print(f"  - 成功步骤数: {stats.get('successful_steps', 0)}")
                print(f"  - 失败步骤数: {stats.get('failed_steps', 0)}")
        else:
            print("❌ 处理状态: 失败")
            print("\n错误信息:")
            for error in result.get('errors', []):
                print(f"  - {error}")
        
        print("="*60)


def main():
    """
    主函数
    """
    # 创建参数解析器
    parser = ConfigManager.create_arg_parser()
    args = parser.parse_args()
    
    try:
        # 创建处理器
        processor = SimplifiedDocumentProcessor(args.config)
        
        # 配置管理功能（优先级最高）
        if args.show_config:
            processor.config_manager.print_config_summary()
            return
        
        if args.validate:
            validation_results = processor.config_manager.validate_config()
            print("\n配置验证结果:")
            for key, result in validation_results.items():
                status = "✅" if result else "❌"
                print(f"  {status} {key}: {'通过' if result else '失败'}")
            return
        
        if args.save_config:
            processor.config_manager.save_config()
            return
        
        # 文档处理功能（只需要mode参数）
        if not args.mode:
            print("错误: 文档处理需要指定 --mode 参数")
            print("示例:")
            print("  python V501_simplified_document_processor.py --mode pdf")
            print("  python V501_simplified_document_processor.py --mode markdown")
            print("\n配置管理命令:")
            print("  python V501_simplified_document_processor.py --show-config")
            print("  python V501_simplified_document_processor.py --validate")
            print("  python V501_simplified_document_processor.py --save-config")
            sys.exit(1)
        
        # 更新配置
        processor.config_manager.update_from_args(args)
        
        # 根据模式执行处理（使用配置文件中的路径）
        if args.mode == 'pdf':
            # 使用命令行参数覆盖配置（如果提供）
            pdf_dir = args.input if args.input else None
            output_dir = args.output if args.output else None
            vector_db_path = args.vector_db if args.vector_db else None
            success = processor.process_from_pdf(pdf_dir, output_dir, vector_db_path)
        else:  # markdown
            # 使用命令行参数覆盖配置（如果提供）
            md_dir = args.input if args.input else None
            vector_db_path = args.vector_db if args.vector_db else None
            success = processor.process_from_markdown(md_dir, vector_db_path)
        
        if success:
            print("\n✅ 文档处理完成！")
            sys.exit(0)
        else:
            print("\n❌ 文档处理失败！")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"\n❌ 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 