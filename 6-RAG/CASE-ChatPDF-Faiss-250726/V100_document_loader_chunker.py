'''
程序说明：
## 1. 该模块实现了文档加载器和语义分块器功能，用于处理多个PDF转换后的markdown和JSON文件
## 2. 支持保留文档出处信息（文档名）和页码信息，为后续RAG系统提供结构化数据
## 3. 与现有minerU_batch_local_files.py配合使用，完成从PDF到结构化数据的完整流程
'''

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter


@dataclass
class DocumentChunk:
    """
    文档分块数据结构
    :param content: 分块内容
    :param document_name: 文档名称
    :param page_number: 页码
    :param chunk_index: 分块索引
    """
    content: str
    document_name: str
    page_number: int
    chunk_index: int


class DocumentLoader:
    """
    文档加载器类，用于加载markdown和JSON文件
    """
    
    def __init__(self, md_dir: str):
        """
        初始化文档加载器
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


class SemanticChunker:
    """
    语义分块器类，用于对文档内容进行语义分块处理
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化语义分块器
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
        
    def chunk_document(self, document: Dict[str, Any]) -> List[DocumentChunk]:
        """
        对单个文档进行分块处理
        :param document: 包含文档内容和元数据的字典
        :return: 文档分块列表
        """
        chunks = []
        doc_name = document['name']
        json_data = document['json_data']
        
        # 提取所有文本内容及其页码
        text_with_pages = []
        for item in json_data:
            if item['type'] == 'text':
                text_with_pages.append({
                    'text': item['text'],
                    'page_idx': item.get('page_idx', 0) + 1  # 页码从1开始
                })
        
        # 将所有文本合并为一个字符串，同时记录每个段落的页码
        full_text = "\n".join([item['text'] for item in text_with_pages])
        
        # 创建一个映射，记录原始文本段落的位置与页码的关系
        page_mapping = {}
        current_pos = 0
        for item in text_with_pages:
            text_len = len(item['text'])
            page_mapping[(current_pos, current_pos + text_len)] = item['page_idx']
            current_pos += text_len + 1  # +1 for newline character
        
        # 使用文本分割器进行分块
        text_chunks = self.text_splitter.split_text(full_text)
        
        # 为每个分块创建DocumentChunk对象
        for i, chunk in enumerate(text_chunks):
            # 确定分块的页码：找到分块内容在原始文本中的位置
            chunk_start = full_text.find(chunk)
            chunk_end = chunk_start + len(chunk)
            
            # 根据位置确定页码
            page_number = 1
            for (start, end), page in page_mapping.items():
                if chunk_start >= start and chunk_start < end:
                    page_number = page
                    break
            
            chunks.append(DocumentChunk(
                content=chunk,
                document_name=doc_name,
                page_number=page_number,
                chunk_index=i
            ))
            
        return chunks
        
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """
        对多个文档进行分块处理
        :param documents: 文档列表
        :return: 所有文档的分块列表
        """
        all_chunks = []
        
        for document in documents:
            chunks = self.chunk_document(document)
            all_chunks.extend(chunks)
            print(f"文档 {document['name']} 分块完成，共 {len(chunks)} 个分块")
            
        return all_chunks


def process_documents(md_dir: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[DocumentChunk]:
    """
    处理文档的主函数：加载文档并进行分块
    :param md_dir: markdown文件目录路径
    :param chunk_size: 分块大小
    :param chunk_overlap: 分块重叠大小
    :return: 文档分块列表
    """
    # 创建文档加载器
    loader = DocumentLoader(md_dir)
    
    # 加载文档
    print("正在加载文档...")
    documents = loader.load_documents()
    print(f"共加载 {len(documents)} 个文档")
    
    # 创建语义分块器
    chunker = SemanticChunker(chunk_size, chunk_overlap)
    
    # 对文档进行分块
    print("正在对文档进行分块处理...")
    chunks = chunker.chunk_documents(documents)
    print(f"文档分块处理完成，共生成 {len(chunks)} 个分块")
    
    return chunks


# 调试和测试代码
if __name__ == "__main__":
    # 测试代码
    chunks = process_documents("md")
    
    # 显示前几个分块作为示例
    print("\n前3个分块示例:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"分块 {i+1}:")
        print(f"  文档名: {chunk.document_name}")
        print(f"  页码: {chunk.page_number}")
        print(f"  内容: {chunk.content[:100]}...")
        print()