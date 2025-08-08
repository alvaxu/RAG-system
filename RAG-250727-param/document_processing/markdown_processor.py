'''
程序说明：
## 1. Markdown处理器，处理Markdown文件的基本操作
## 2. 提供Markdown文件的读取、验证和预处理功能
## 3. 统一Markdown处理接口
## 4. 为后续的文档分块和图片提取提供基础
'''

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)


class MarkdownProcessor:
    """
    Markdown处理器，处理Markdown文件的基本操作
    """
    
    def __init__(self, config):
        """
        初始化Markdown处理器
        :param config: 配置对象
        """
        self.config = config
    
    def load_markdown_files(self, md_dir: str) -> Optional[List[Dict[str, Any]]]:
        """
        加载Markdown文件
        :param md_dir: Markdown文件目录
        :return: 包含文件内容和元数据的字典列表
        """
        try:
            md_path = Path(md_dir)
            if not md_path.exists():
                logger.error(f"Markdown目录不存在: {md_dir}")
                return None
            
            documents = []
            
            # 遍历所有Markdown文件
            for md_file in md_path.glob("*.md"):
                try:
                    # 读取Markdown内容
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 查找对应的JSON文件
                    json_file = md_file.with_name(f"{md_file.stem}_1.json")
                    json_data = None
                    
                    if json_file.exists():
                        import json
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                    
                    documents.append({
                        'name': md_file.stem,
                        'file_path': str(md_file),
                        'content': content,
                        'json_data': json_data,
                        'file_size': md_file.stat().st_size
                    })
                    
                except Exception as e:
                    logger.warning(f"读取文件 {md_file} 失败: {e}")
                    continue
            
            if documents:
                logger.info(f"成功加载 {len(documents)} 个Markdown文件")
                return documents
            else:
                logger.warning("未找到有效的Markdown文件")
                return None
                
        except Exception as e:
            logger.error(f"加载Markdown文件失败: {e}")
            return None
    
    def validate_markdown_content(self, content: str) -> bool:
        """
        验证Markdown内容
        :param content: Markdown内容
        :return: 验证结果
        """
        if not content or not content.strip():
            return False
        
        # 检查是否包含基本的内容结构
        lines = content.split('\n')
        if len(lines) < 3:  # 至少应该有3行内容
            return False
        
        return True
    
    def extract_metadata(self, content: str, json_data: Dict = None) -> Dict[str, Any]:
        """
        从Markdown内容中提取元数据
        :param content: Markdown内容
        :param json_data: JSON元数据
        :return: 提取的元数据
        """
        metadata = {
            'content_length': len(content),
            'line_count': len(content.split('\n')),
            'has_tables': '|' in content and '\n' in content,
            'has_images': '![' in content,
            'has_links': '[' in content and '](' in content
        }
        
        # 如果有JSON数据，合并元数据
        if json_data:
            metadata.update({
                'json_metadata': True,
                'json_keys': list(json_data.keys()) if isinstance(json_data, dict) else []
            })
        
        return metadata
    
    def preprocess_content(self, content: str) -> str:
        """
        预处理Markdown内容
        :param content: 原始Markdown内容
        :return: 预处理后的内容
        """
        if not content:
            return content
        
        # 移除多余的空白字符
        content = content.strip()
        
        # 统一换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除多余的空行
        lines = content.split('\n')
        processed_lines = []
        prev_empty = False
        
        for line in lines:
            if line.strip():
                processed_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                processed_lines.append('')
                prev_empty = True
        
        return '\n'.join(processed_lines)
    
    def get_file_statistics(self, md_dir: str) -> Dict[str, Any]:
        """
        获取文件统计信息
        :param md_dir: Markdown文件目录
        :return: 统计信息
        """
        try:
            md_path = Path(md_dir)
            if not md_path.exists():
                return {'error': '目录不存在'}
            
            md_files = list(md_path.glob("*.md"))
            json_files = list(md_path.glob("*.json"))
            
            total_size = sum(f.stat().st_size for f in md_files)
            
            return {
                'markdown_files': len(md_files),
                'json_files': len(json_files),
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'files': [str(f) for f in md_files]
            }
            
        except Exception as e:
            return {'error': str(e)} 