'''
程序说明：
## 1. PDF处理器，整合minerU功能
## 2. 统一PDF到Markdown的转换接口
## 3. 提供错误处理和状态反馈
## 4. 保持与现有minerU_batch_local_files.py的兼容性
'''

import os
import logging
from typing import List, Optional
from pathlib import Path
from minerU_batch_local_files import run_mineru_batch_export

# 导入统一的API密钥管理模块
from config.api_key_manager import get_mineru_api_key

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    PDF处理器，负责PDF文件的转换和处理
    """
    
    def __init__(self, config: dict):
        """
        初始化PDF处理器
        
        :param config: 配置字典
        """
        self.config = config
        
        # 使用统一的API密钥管理模块获取API密钥
        self.api_key = get_mineru_api_key(config.get('mineru_api_key', ''))
        
        if not self.api_key:
            logger.warning("未配置有效的minerU API密钥，PDF转换功能将受限")
    
    def _get_api_key(self) -> str:
        """
        获取minerU API密钥
        :return: API密钥
        """
        # 使用统一的API密钥管理模块
        return get_mineru_api_key(self.config.get('mineru_api_key', ''))
    
    def convert_pdfs(self, pdf_dir: str, output_dir: str) -> Optional[List[str]]:
        """
        将PDF文件转换为Markdown文件
        :param pdf_dir: PDF文件目录
        :param output_dir: 输出目录
        :return: 生成的Markdown文件列表
        """
        try:
            # 检查输入目录
            pdf_path = Path(pdf_dir)
            if not pdf_path.exists():
                logger.error(f"PDF目录不存在: {pdf_dir}")
                return None
            
            # 检查输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 检查API密钥
            if not self.api_key:
                logger.error("minerU API密钥未配置，无法进行PDF转换")
                return None
            
            logger.info(f"开始PDF转换，输入目录: {pdf_dir}")
            logger.info(f"输出目录: {output_dir}")
            
            # 调用现有的minerU功能
            run_mineru_batch_export(
                pdf_dir=pdf_dir,
                output_dir=output_dir,
                api_key=self.api_key,
                language='ch'
            )
            
            # 检查生成的Markdown文件
            md_files = []
            for md_file in output_path.glob("*.md"):
                md_files.append(str(md_file))
            
            if md_files:
                logger.info(f"PDF转换完成，生成了 {len(md_files)} 个Markdown文件")
                return md_files
            else:
                logger.warning("PDF转换完成，但未找到生成的Markdown文件")
                return None
                
        except Exception as e:
            logger.error(f"PDF转换失败: {e}")
            return None
    
    # 注释原因：
    # 以下两个函数主要用于调试和状态检查，不是核心流程的一部分
    # def validate_pdf_files(self, pdf_dir: str) -> bool:
    #     """
    #     验证PDF文件
    #     :param pdf_dir: PDF文件目录
    #     :return: 验证结果
    #     """
    #     try:
    #         pdf_path = Path(pdf_dir)
    #         if not pdf_path.exists():
    #             logger.error(f"PDF目录不存在: {pdf_dir}")
    #             return False
            
    #         pdf_files = list(pdf_path.glob("*.pdf"))
    #         if not pdf_files:
    #             logger.warning(f"PDF目录中没有找到PDF文件: {pdf_dir}")
    #             return False
            
    #         logger.info(f"找到 {len(pdf_files)} 个PDF文件")
    #         return True
            
    #     except Exception as e:
    #         logger.error(f"验证PDF文件失败: {e}")
    #         return False
    
    # def get_conversion_status(self, output_dir: str) -> dict:
    #     """
    #     获取转换状态
    #     :param output_dir: 输出目录
    #     :return: 转换状态信息
    #     """
    #     try:
    #         output_path = Path(output_dir)
    #         if not output_path.exists():
    #             return {
    #                 'status': 'not_started',
    #                 'message': '输出目录不存在'
    #             }
            
    #         md_files = list(output_path.glob("*.md"))
    #         json_files = list(output_path.glob("*.json"))
            
    #         return {
    #             'status': 'completed' if md_files else 'failed',
    #             'markdown_files': len(md_files),
    #             'json_files': len(json_files),
    #             'files': [str(f) for f in md_files]
    #         }
            
    #     except Exception as e:
    #         return {
    #             'status': 'error',
    #             'message': str(e)
    #         } 