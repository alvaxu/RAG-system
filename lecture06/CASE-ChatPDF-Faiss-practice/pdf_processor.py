"""
PDF处理模块
"""
from PyPDF2 import PdfReader
from typing import List, Dict, Tuple
import re
from config import CHUNK_SIZE, CHUNK_OVERLAP

class PDFProcessor:
    """
    功能：处理PDF文档，提取文本和元数据
    参数：
        pdf_path: PDF文件路径
    返回：
        chunks: 文本块列表
        metadata: 元数据列表
    """
    def __init__(self):
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP

    def process_pdf(self, pdf_path: str) -> Tuple[List[str], List[Dict]]:
        """
        处理PDF文件，返回文本块和元数据
        """
        # 读取PDF
        reader = PdfReader(pdf_path)
        chunks = []
        metadata = []
        
        # 逐页处理
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                # 对每页文本进行分块
                page_chunks = self._split_text(page_text)
                # 为每个文本块创建对应的元数据
                for chunk in page_chunks:
                    chunks.append(chunk)
                    metadata.append({
                        "page": page_num,
                        "source": pdf_path
                    })
        
        return chunks, metadata

    def _split_text(self, text: str) -> List[str]:
        """
        将文本分割成块
        """
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks 