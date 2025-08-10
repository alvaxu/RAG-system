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
        # DashScope API限制：最大2048字符
        self.max_chunk_length = 2048
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""],
            chunk_size=min(chunk_size, self.max_chunk_length),  # 确保不超过API限制
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
                    # 验证并截断分块内容
                    validated_content = self._validate_and_truncate_chunk(chunk_text, "文本")
                    
                    chunk = EnhancedDocumentChunk(
                        content=validated_content,
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
                # 直接处理表格内容，使用智能分块
                validated_content = self._validate_and_truncate_chunk(table_body, "表格")
                
                chunk = EnhancedDocumentChunk(
                    content=validated_content,
                    document_name=doc_name,
                    page_number=page_number,
                    chunk_index=chunk_index_offset,
                    chunk_type="table",
                    table_id=f"table_{hash(table_body) % 1000000}",  # 生成简单的表格ID
                    table_type="数据表格"
                )
                chunks.append(chunk)
                chunk_index_offset += 1
                        
            except Exception as e:
                print(f"处理表格时出错: {e}")
                # 如果表格解析失败，将原始HTML作为文本处理（与老代码一致）
                # 验证并截断内容
                fallback_content = f"表格内容（解析失败）: {table_body}"
                validated_content = self._validate_and_truncate_chunk(fallback_content, "表格")
                
                chunk = EnhancedDocumentChunk(
                    content=validated_content,
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

    # 以下两个函数都是从老代码移植过来的，但在当前实现中都没有被使用
    # 简化实现：当前的分块实现直接从JSON数据中获取page_idx，然后转换为页码
    # 不需要复杂映射：因为JSON数据已经包含了每个文本块和表格块的页码信息
    # def _build_page_mapping(self, text_with_pages: List[Dict[str, Any]]) -> Dict[Tuple[int, int], int]:
    #     """
    #     构建文本位置到页码的映射（从老代码移植）
    #     :param text_with_pages: 包含页码信息的文本列表
    #     :return: 位置到页码的映射字典
    #     """
    #     page_mapping = {}
    #     current_pos = 0
        
    #     for item in text_with_pages:
    #         text = item.get('text', '')
    #         page = item.get('page', 0)
    #         text_length = len(text)
            
    #         # 为文本的每个字符位置分配页码
    #         for i in range(text_length):
    #             page_mapping[(current_pos + i, current_pos + i + 1)] = page
            
    #         current_pos += text_length
        
    #     return page_mapping
    
    # def _find_most_frequent_page(self, chunk: str, full_text: str, page_mapping: Dict[Tuple[int, int], int]) -> int:
    #     """
    #     找到分块中出现最频繁的页码（从老代码移植）
    #     :param chunk: 分块内容
    #     :param full_text: 完整文本
    #     :param page_mapping: 页码映射
    #     :return: 最频繁的页码
    #     """
    #     chunk_start = full_text.find(chunk)
    #     if chunk_start == -1:
    #         return 0
        
    #     chunk_end = chunk_start + len(chunk)
    #     page_counts = {}
        
    #     # 统计分块中每个字符位置对应的页码
    #     for pos in range(chunk_start, chunk_end):
    #         for (start, end), page in page_mapping.items():
    #             if start <= pos < end:
    #                 page_counts[page] = page_counts.get(page, 0) + 1
    #                 break
        
    #     # 返回出现次数最多的页码
    #     if page_counts:
    #         return max(page_counts.items(), key=lambda x: x[1])[0]
    #     return 0

    def _validate_and_truncate_chunk(self, content: str, content_type: str) -> str:
        """
        验证并智能处理分块内容，避免简单截断导致的信息丢失
        
        :param content: 原始内容
        :param content_type: 内容类型（文本/表格）
        :return: 处理后的内容
        """
        original_length = len(content)
        
        if original_length <= self.max_chunk_length:
            return content
        
        # 记录处理信息
        print(f"📊 检测到超长{content_type}内容: {original_length}字符 > {self.max_chunk_length}字符限制")
        print(f"🔧 开始进行智能处理...")
        
        if content_type == "表格":
            result = self._smart_table_chunking(content)
        else:
            result = self._smart_text_chunking(content)
        
        # 记录处理结果
        processed_length = len(result)
        print(f"✅ {content_type}处理完成: {original_length}字符 → {processed_length}字符")
        
        return result
    
    def _smart_table_chunking(self, table_content: str) -> str:
        """
        智能表格分块：将大表格分解为多个逻辑相关的子表格
        
        :param table_content: 原始表格内容
        :return: 处理后的表格内容
        """
        table_length = len(table_content)
        threshold = self.max_chunk_length * 1.5
        
        print(f"📋 表格长度分析: {table_length}字符")
        print(f"🔍 处理策略判断: 阈值 = {threshold}字符")
        
        # 如果表格内容不是特别长，尝试优化格式
        if table_length <= threshold:
            print(f"📝 选择格式优化策略 (≤ {threshold}字符)")
            return self._optimize_table_format(table_content)
        
        # 对于超长表格，进行智能分块
        print(f"✂️ 选择截断处理策略 (> {threshold}字符)")
        return self._split_large_table(table_content)
    
    def _smart_text_chunking(self, text_content: str) -> str:
        """
        智能文本分块：在合适的位置截断，保持语义完整性
        
        :param text_content: 原始文本内容
        :return: 处理后的文本内容
        """
        if len(text_content) <= self.max_chunk_length:
            return text_content
        
        # 尝试在句号、换行符等位置截断
        for separator in ["。", "！", "？", ".", "!", "?", "\n\n", "\n"]:
            last_sep_pos = text_content[:self.max_chunk_length].rfind(separator)
            if last_sep_pos > self.max_chunk_length * 0.8:  # 在80%位置之后找到分隔符
                truncated_text = text_content[:last_sep_pos + len(separator)]
                # 添加截断标记
                return truncated_text + f"\n[内容已截断，原始长度: {len(text_content)} 字符]"
        
        # 如果没找到合适的分隔符，直接截断并添加标记
        return text_content[:self.max_chunk_length] + f"\n[内容已截断，原始长度: {len(text_content)} 字符]"
    
    def _optimize_table_format(self, table_content: str) -> str:
        """
        优化表格格式，去除冗余信息，保持核心数据
        
        :param table_content: 原始表格内容
        :return: 优化后的表格内容
        """
        original_length = len(table_content)
        print(f"🔧 开始表格格式优化...")
        
        # 简化表格结构说明
        lines = table_content.split('\n')
        optimized_lines = []
        optimized_count = 0
        
        for line in lines:
            # 保留关键信息，简化冗长的描述
            if line.startswith('表格类型:') or line.startswith('表格ID:'):
                optimized_lines.append(line)
            elif line.startswith('行数:') or line.startswith('列数:'):
                optimized_lines.append(line)
            elif line.startswith('列标题（字段定义）:'):
                # 简化列标题描述
                if len(line) > 100:
                    optimized_lines.append(line[:100] + "...")
                    optimized_count += 1
                else:
                    optimized_lines.append(line)
            elif line.startswith('数据记录:'):
                optimized_lines.append(line)
            elif line.startswith('  记录'):
                # 保留数据记录，但限制长度
                if len(line) > 150:
                    optimized_lines.append(line[:150] + "...")
                    optimized_count += 1
                else:
                    optimized_lines.append(line)
            else:
                # 其他行直接保留
                optimized_lines.append(line)
        
        result = '\n'.join(optimized_lines)
        result_length = len(result)
        
        print(f"📝 格式优化完成: {original_length}字符 → {result_length}字符")
        if optimized_count > 0:
            print(f"✨ 优化了 {optimized_count} 行内容")
        
        # 添加优化标记
        if result_length < original_length:
            result += f"\n[表格格式已优化，原始长度: {original_length} 字符]"
        
        return result
    
    def _split_large_table(self, table_content: str) -> str:
        """
        将大表格分割为多个子表格
        
        :param table_content: 原始表格内容
        :return: 分割后的表格内容
        """
        original_length = len(table_content)
        print(f"✂️ 开始大表格截断处理...")
        
        lines = table_content.split('\n')
        
        # 提取表格头部信息
        header_lines = []
        data_lines = []
        in_data_section = False
        
        for line in lines:
            if line.startswith('数据记录:'):
                in_data_section = True
                header_lines.append(line)
                continue
            
            if in_data_section:
                data_lines.append(line)
            else:
                header_lines.append(line)
        
        print(f"📊 表格结构分析: 头部{len(header_lines)}行，数据{len(data_lines)}行")
        
        # 初始化截断标记和处理信息
        truncation_mark = ""
        processing_info = f"\n[表格已进行智能截断处理，原始长度: {original_length} 字符]"
        
        # 如果数据行太多，只保留前几行和后几行
        if len(data_lines) > 20:
            total_data_rows = len(data_lines)
            kept_rows = 15  # 前10行 + 后5行
            truncated_rows = total_data_rows - kept_rows
            
            print(f"⚠️ 数据行过多({total_data_rows}行)，进行截断处理:")
            print(f"   - 保留前10行数据")
            print(f"   - 保留后5行数据")
            print(f"   - 截断中间{truncated_rows}行数据")
            
            # 保留前10行和后5行
            selected_data = data_lines[:10] + [f'  ... (中间{truncated_rows}行数据省略) ...'] + data_lines[-5:]
            data_lines = selected_data
            
            # 设置截断处理标记
            truncation_mark = f"\n[表格数据行已截断处理: 原始{total_data_rows}行 → 保留{kept_rows}行，截断{truncated_rows}行]"
        else:
            print(f"✅ 数据行数量适中({len(data_lines)}行)，无需行数截断")
        
        # 重新组合
        result_lines = header_lines + data_lines
        result_content = '\n'.join(result_lines)
        
        # 总是添加处理信息标记
        result_content += processing_info
        
        # 如果有行数截断，也添加行数截断标记
        if truncation_mark:
            result_content += truncation_mark
        
        result_length = len(result_content)
        print(f"📋 截断处理完成: {original_length}字符 → {result_length}字符")
        
        # 如果仍然超长，进行最终截断
        if result_length > self.max_chunk_length:
            print(f"⚠️ 处理后仍超长，进行最终截断...")
            final_length = self.max_chunk_length
            
            # 计算可以保留的标记长度
            # 保留处理信息标记和行数截断标记（如果有的话）
            marks_to_keep = processing_info
            if truncation_mark:
                marks_to_keep += truncation_mark
            
            marks_length = len(marks_to_keep)
            available_length = final_length - marks_length
            
            # 截断主要内容，保留标记
            if available_length > 0:
                result_content = result_content[:available_length] + marks_to_keep
                # 添加最终截断标记
                result_content += f"\n[表格内容已截断处理，原始长度: {original_length} 字符]"
            else:
                # 如果标记太长，只保留最终截断标记
                result_content = result_content[:final_length] + f"\n[表格内容已截断处理，原始长度: {original_length} 字符]"
            
            print(f"🔚 最终处理完成: {original_length}字符 → {len(result_content)}字符")
        
        return result_content 

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