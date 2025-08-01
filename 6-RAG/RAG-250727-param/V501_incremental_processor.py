'''
程序说明：
## 1. 增量文档处理器主入口，专门处理新增文档的增量更新
## 2. 复用V501_simplified_document_processor.py的框架结构
## 3. 支持从PDF和Markdown两种方式的新增文档处理
## 4. 使用配置管理，避免硬编码
## 5. 提供友好的用户界面和错误处理
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
from config.settings import Settings
# 导入增量处理管道
from document_processing.incremental_pipeline import IncrementalPipeline

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('incremental_processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class IncrementalDocumentProcessor:
    """
    增量文档处理器
    专门处理新增文档的增量更新
    """
    
    def __init__(self, config_file: str = None):
        """
        初始化增量文档处理器
        :param config_file: 配置文件路径
        """
        self.config = Settings.load_from_file(config_file or 'config.json')
        self.pipeline = IncrementalPipeline(self.config)
    
    def process_incremental_from_pdf(self, pdf_dir: str = None, output_dir: str = None, vector_db_path: str = None) -> bool:
        """
        从PDF开始处理新增文档
        :param pdf_dir: PDF文件目录
        :param output_dir: 输出目录
        :param vector_db_path: 向量数据库路径
        :return: 是否成功
        """
        try:
            # 使用配置中的路径，如果参数提供则覆盖
            pdf_dir = pdf_dir or self.config.add_pdf_dir
            output_dir = output_dir or self.config.add_output_dir
            vector_db_path = vector_db_path or self.config.get_vector_db_path()
            
            logger.info("开始从PDF处理新增文档...")
            logger.info(f"PDF目录: {pdf_dir}")
            logger.info(f"输出目录: {output_dir}")
            logger.info(f"向量数据库: {vector_db_path}")
            
            # 执行增量处理流程
            result = self.pipeline.process_from_pdf(pdf_dir, output_dir, vector_db_path)
            
            if result['success']:
                logger.info("新增文档处理成功！")
                self._print_processing_report(result)
                return True
            else:
                logger.error("新增文档处理失败！")
                for error in result['errors']:
                    logger.error(f"错误: {error}")
                return False
                
        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            return False
    
    def process_incremental_from_markdown(self, md_dir: str = None, vector_db_path: str = None) -> bool:
        """
        从Markdown开始处理新增文档
        :param md_dir: Markdown文件目录
        :param vector_db_path: 向量数据库路径
        :return: 是否成功
        """
        try:
            # 使用配置中的路径，如果参数提供则覆盖
            md_dir = md_dir or self.config.add_md_dir
            vector_db_path = vector_db_path or self.config.get_vector_db_path()
            
            logger.info("开始从Markdown处理新增文档...")
            logger.info(f"Markdown目录: {md_dir}")
            logger.info(f"向量数据库: {vector_db_path}")
            
            # 执行增量处理流程
            result = self.pipeline.process_from_markdown(md_dir, vector_db_path)
            
            if result['success']:
                logger.info("新增文档处理成功！")
                self._print_processing_report(result)
                return True
            else:
                logger.error("新增文档处理失败！")
                for error in result['errors']:
                    logger.error(f"错误: {error}")
                return False
                
        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            return False
    
    def _print_processing_report(self, result: dict):
        """
        打印处理报告
        :param result: 处理结果
        """
        print("\n" + "="*60)
        print("增量文档处理报告")
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
                elif step_name == 'vector_incremental_update':
                    print(f"     - 增量更新分块数: {step_info.get('total_chunks', 0)}")
                elif step_name == 'image_vector_addition':
                    print(f"     - 添加图片数: {step_info.get('images_added', 0)}")
                    if step_info.get('images_failed', 0) > 0:
                        print(f"     - 失败图片数: {step_info.get('images_failed', 0)}")
                    if step_info.get('total_images_processed', 0) > 0:
                        print(f"     - 处理图片数: {step_info.get('total_images_processed', 0)}")
            
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
    parser = argparse.ArgumentParser(description='增量文档处理器')
    
    # 添加配置管理参数
    parser.add_argument('--config', type=str, default='config.json', help='配置文件路径')
    parser.add_argument('--show-config', action='store_true', help='显示配置信息')
    parser.add_argument('--validate', action='store_true', help='验证配置')
    parser.add_argument('--save-config', action='store_true', help='保存配置')
    
    # 添加处理参数
    parser.add_argument('--mode', type=str, choices=['pdf', 'markdown'], help='处理模式')
    parser.add_argument('--input', type=str, help='输入目录（覆盖配置文件中的路径）')
    parser.add_argument('--output', type=str, help='输出目录（仅PDF模式）')
    parser.add_argument('--vector-db', type=str, help='向量数据库路径')
    
    args = parser.parse_args()
    
    try:
        # 创建处理器
        processor = IncrementalDocumentProcessor(args.config)
        
        # 配置管理功能（优先级最高）
        if args.show_config:
            print("配置信息:")
            print(f"  - PDF目录: {processor.config.add_pdf_dir}")
            print(f"  - Markdown目录: {processor.config.add_md_dir}")
            print(f"  - 输出目录: {processor.config.add_output_dir}")
            print(f"  - 向量数据库: {processor.config.vector_db_dir}")
            print(f"  - 图片目录: {processor.config.central_images_dir}")
            return
        
        if args.validate:
            print("\n配置验证结果:")
            # 检查必需的路径
            required_paths = ['add_pdf_dir', 'add_md_dir', 'add_output_dir', 'vector_db_dir', 'central_images_dir']
            for path_name in required_paths:
                path_value = getattr(processor.config, path_name, None)
                status = "✅" if path_value else "❌"
                print(f"  {status} {path_name}: {'已配置' if path_value else '未配置'}")
            return
        
        if args.save_config:
            processor.config.save_to_file('config.json')
            print("配置已保存到 config.json")
            return
        
        # 增量文档处理功能（只需要mode参数）
        if not args.mode:
            print("错误: 增量文档处理需要指定 --mode 参数")
            print("示例:")
            print("  python V501_incremental_processor.py --mode pdf")
            print("  python V501_incremental_processor.py --mode markdown")
            print("\n配置管理命令:")
            print("  python V501_incremental_processor.py --show-config")
            print("  python V501_incremental_processor.py --validate")
            print("  python V501_incremental_processor.py --save-config")
            sys.exit(1)
        
        # 配置已通过Settings加载，无需更新
        
        # 根据模式执行增量处理（使用配置文件中的路径）
        if args.mode == 'pdf':
            # 使用命令行参数覆盖配置（如果提供）
            pdf_dir = args.input if args.input else None
            output_dir = args.output if args.output else None
            vector_db_path = args.vector_db if args.vector_db else None
            success = processor.process_incremental_from_pdf(pdf_dir, output_dir, vector_db_path)
        else:  # markdown
            # 使用命令行参数覆盖配置（如果提供）
            md_dir = args.input if args.input else None
            vector_db_path = args.vector_db if args.vector_db else None
            success = processor.process_incremental_from_markdown(md_dir, vector_db_path)
        
        if success:
            print("\n✅ 增量文档处理完成！")
            sys.exit(0)
        else:
            print("\n❌ 增量文档处理失败！")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"\n❌ 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 