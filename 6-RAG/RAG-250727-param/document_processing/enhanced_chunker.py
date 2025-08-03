'''
程序说明：
## 1. 独立的增强文档分块器模块
## 2. 从V310_enhanced_document_chunker.py中提取核心功能
## 3. 统一文档分块接口
## 4. 支持文本和表格的分块处理
'''

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 导入表格处理器
from .table_processor import ConfigurableTableProcessor as TableProcessor, ConfigurableTableChunkGenerator as TableChunkGenerator


@dataclass
class EnhancedDocumentChunk:
    """
    增强版文档分块数据结构
    :param content: 分块内容
    :param document_name: 文档名称
    :param page_number: 页码
    :param chunk_index: 分块索引
    :param chunk_type: 分块类型（text/table）
    :param table_id: 表格ID（如果是表格分块）
    :param table_type: 表格类型（如果是表格分块）
    """
    content: str
    document_name: str
    page_number: int
    chunk_index: int
    chunk_type: str = "text"
    table_id: str = None
    table_type: str = None


class EnhancedDocumentLoader:
    """
    增强版文档加载器类，用于加载markdown和JSON文件
    """
    
    def __init__(self, md_dir: str):
        """
        初始化增强版文档加载器
        :param md_dir: markdown文件目录路径
        """
        self.md_dir = Path(md_dir)
        
    def load_documents(self) -> List[Dict[str, Any]]:
        """
        加载所有文档的markdown和JSON文件
        :return: 包含文档内容和元数据的字典列表
        """
        documents = []
        
        # 遍历所有markdown文件
        for md_file in self.md_dir.glob("*.md"):
            doc_name = md_file.stem  # 获取不带扩展名的文件名
            
            # 查找对应的JSON文件
            json_file = md_file.with_name(f"{doc_name}_1.json")
            
            if not json_file.exists():
                print(f"警告: 找不到 {doc_name} 对应的JSON文件")
                continue
                
            # 读取markdown内容
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
                
            # 读取JSON元数据
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
            documents.append({
                'name': doc_name,
                'md_content': md_content,
                'json_data': json_data
            })
            
        return documents


class EnhancedSemanticChunker:
    """
    增强版语义分块器类，用于对文档内容进行语义分块处理，包括表格处理
    """
    
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        """
        初始化增强版语义分块器
        :param chunk_size: 分块大小
        :param chunk_overlap: 分块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def chunk_document(self, document: Dict[str, Any]) -> List[EnhancedDocumentChunk]:
        """
        对单个文档进行分块处理
        :param document: 文档数据
        :return: 文档分块列表
        """
        chunks = []
        doc_name = document['name']
        md_content = document['md_content']
        json_data = document['json_data']
        
        # 提取文本内容
        text_content = self._extract_text_content(json_data)
        
        # 提取表格内容
        table_content = self._extract_table_content(json_data)
        
        # 处理文本分块
        text_chunks = self._process_text_chunks(text_content, doc_name)
        chunks.extend(text_chunks)
        
        # 处理表格分块
        table_chunks = self._process_table_chunks(table_content, doc_name)
        chunks.extend(table_chunks)
        
        return chunks
    
    def _extract_text_content(self, json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取文本内容
        :param json_data: JSON数据
        :return: 文本内容列表
        """
        text_content = []
        for item in json_data:
            if item.get("type") == "text":
                text_content.append(item)
        return text_content
    
    def _extract_table_content(self, json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取表格内容
        :param json_data: JSON数据
        :return: 表格内容列表
        """
        table_content = []
        for item in json_data:
            if item.get("type") == "table":
                table_content.append(item)
        return table_content
    
    def _process_text_chunks(self, text_content: List[Dict[str, Any]], doc_name: str) -> List[EnhancedDocumentChunk]:
        """
        处理文本分块
        :param text_content: 文本内容
        :param doc_name: 文档名称
        :return: 文本分块列表
        """
        chunks = []
        chunk_index_offset = 0  # 使用偏移量管理索引（与老代码一致）
        
        for item in text_content:
            text = item.get("text", "")
            # 将0索引的page_idx转换为1索引的页码（与老代码一致）
            page_idx = item.get("page_idx", 0)
            page_number = page_idx + 1
            
            # 使用文本分割器进行分块
            text_chunks = self.text_splitter.split_text(text)
            
            for i, chunk_text in enumerate(text_chunks):
                if chunk_text.strip():  # 跳过空分块
                    chunk = EnhancedDocumentChunk(
                        content=chunk_text,
                        document_name=doc_name,
                        page_number=page_number,
                        chunk_index=chunk_index_offset + i,
                        chunk_type="text"
                    )
                    chunks.append(chunk)
            
            chunk_index_offset += len(text_chunks)
        
        return chunks
    
    def _process_table_chunks(self, table_content: List[Dict[str, Any]], doc_name: str) -> List[EnhancedDocumentChunk]:
        """
        处理表格分块
        :param table_content: 表格内容
        :param doc_name: 文档名称
        :return: 表格分块列表
        """
        chunks = []
        chunk_index_offset = 0  # 使用偏移量管理索引（与老代码一致）
        
        for item in table_content:
            # 将0索引的page_idx转换为1索引的页码（与老代码一致）
            page_idx = item.get("page_idx", 0)
            page_number = page_idx + 1
            table_body = item.get("table_body", "")
            
            try:
                # 使用表格处理器处理表格
                table_processor = TableProcessor()
                table_info = table_processor.parse_html_table(table_body, "数据表格")
                
                # 使用表格分块生成器生成智能分块
                chunk_generator = TableChunkGenerator()
                table_chunks = chunk_generator.generate_table_chunks(table_info)
                
                for i, chunk_text in enumerate(table_chunks):
                    if chunk_text.strip():
                        chunk = EnhancedDocumentChunk(
                            content=chunk_text,
                            document_name=doc_name,
                            page_number=page_number,
                            chunk_index=chunk_index_offset + i,
                            chunk_type="table",
                            table_id=table_info.table_id,
                            table_type=table_info.table_type
                        )
                        chunks.append(chunk)
                
                chunk_index_offset += len(table_chunks)
                        
            except Exception as e:
                print(f"处理表格时出错: {e}")
                # 如果表格解析失败，将原始HTML作为文本处理（与老代码一致）
                chunk = EnhancedDocumentChunk(
                    content=f"表格内容（解析失败）: {table_body}",
                    document_name=doc_name,
                    page_number=page_number,
                    chunk_index=chunk_index_offset,
                    chunk_type="text"
                )
                chunks.append(chunk)
                chunk_index_offset += 1
                continue
        
        return chunks
    
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[EnhancedDocumentChunk]:
        """
        对多个文档进行分块处理
        :param documents: 文档列表
        :return: 所有文档的分块列表
        """
        all_chunks = []
        for document in documents:
            chunks = self.chunk_document(document)
            all_chunks.extend(chunks)
        return all_chunks

    def _build_page_mapping(self, text_with_pages: List[Dict[str, Any]]) -> Dict[Tuple[int, int], int]:
        """
        构建文本位置到页码的映射（从老代码移植）
        :param text_with_pages: 包含页码信息的文本列表
        :return: 位置到页码的映射字典
        """
        page_mapping = {}
        current_pos = 0
        
        for item in text_with_pages:
            text = item.get('text', '')
            page = item.get('page', 0)
            text_length = len(text)
            
            # 为文本的每个字符位置分配页码
            for i in range(text_length):
                page_mapping[(current_pos + i, current_pos + i + 1)] = page
            
            current_pos += text_length
        
        return page_mapping
    
    def _find_most_frequent_page(self, chunk: str, full_text: str, page_mapping: Dict[Tuple[int, int], int]) -> int:
        """
        找到分块中出现最频繁的页码（从老代码移植）
        :param chunk: 分块内容
        :param full_text: 完整文本
        :param page_mapping: 页码映射
        :return: 最频繁的页码
        """
        chunk_start = full_text.find(chunk)
        if chunk_start == -1:
            return 0
        
        chunk_end = chunk_start + len(chunk)
        page_counts = {}
        
        # 统计分块中每个字符位置对应的页码
        for pos in range(chunk_start, chunk_end):
            for (start, end), page in page_mapping.items():
                if start <= pos < end:
                    page_counts[page] = page_counts.get(page, 0) + 1
                    break
        
        # 返回出现次数最多的页码
        if page_counts:
            return max(page_counts.items(), key=lambda x: x[1])[0]
        return 0


def process_documents_with_tables(md_dir: str = None, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[EnhancedDocumentChunk]:
    """
    处理文档并包含表格的完整流程
    :param md_dir: markdown文件目录
    :param chunk_size: 分块大小
    :param chunk_overlap: 分块重叠大小
    :return: 增强文档分块列表
    """
    if not md_dir:
        print("错误: 未指定markdown文件目录")
        return []
    
    try:
        # 加载文档
        loader = EnhancedDocumentLoader(md_dir)
        documents = loader.load_documents()
        
        if not documents:
            print(f"警告: 在目录 {md_dir} 中没有找到有效的文档")
            return []
        
        # 分块处理
        chunker = EnhancedSemanticChunker(chunk_size, chunk_overlap)
        chunks = chunker.chunk_documents(documents)
        
        print(f"成功处理 {len(documents)} 个文档，生成 {len(chunks)} 个分块")
        
        # 统计分块类型
        text_chunks = [c for c in chunks if c.chunk_type == "text"]
        table_chunks = [c for c in chunks if c.chunk_type == "table"]
        
        print(f"  - 文本分块: {len(text_chunks)} 个")
        print(f"  - 表格分块: {len(table_chunks)} 个")
        
        return chunks
        
    except Exception as e:
        print(f"处理文档失败: {e}")
        return [] 