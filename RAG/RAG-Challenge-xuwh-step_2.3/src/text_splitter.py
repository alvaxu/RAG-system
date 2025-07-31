import json
import tiktoken
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import os
from collections import defaultdict

# 文本分块工具类，支持按页分块、表格插入、token统计等
class TextSplitter():
    def __init__(self, splitter_model_name: str = "qwen-turbo-latest"):
        self.splitter_model_name = splitter_model_name

    def _get_serialized_tables_by_page(self, tables: List[Dict]) -> Dict[int, List[Dict]]:
        """按页分组已序列化表格，便于后续插入到对应页面分块中"""
        tables_by_page = {}
        for table in tables:
            if 'serialized' not in table:
                continue
                
            page = table['page']
            if page not in tables_by_page:
                tables_by_page[page] = []
            
            table_text = "\n".join(
                block["information_block"] 
                for block in table["serialized"]["information_blocks"]
            )
            
            tables_by_page[page].append({
                "page": page,
                "text": table_text,
                "table_id": table["table_id"],
                "length_tokens": self.count_tokens(table_text)
            })
            
        return tables_by_page

    def _split_report(self, file_content: Dict[str, any], serialized_tables_report_path: Optional[Path] = None) -> Dict[str, any]:
        """将报告按页分块，保留markdown表格内容，可选插入序列化表格块。"""
        chunks = []
        chunk_id = 0
        
        tables_by_page = {}
        if serialized_tables_report_path is not None:
            # 加载序列化表格，按页分组
            with open(serialized_tables_report_path, 'r', encoding='utf-8') as f:
                parsed_report = json.load(f)
            tables_by_page = self._get_serialized_tables_by_page(parsed_report.get('tables', []))
        
        for page in file_content['content']['pages']:
            # 普通文本分块
            page_chunks = self._split_page(page)
            for chunk in page_chunks:
                chunk['id'] = chunk_id
                chunk['type'] = 'content'
                chunk_id += 1
                chunks.append(chunk)
            
            # 插入序列化表格分块
            if tables_by_page and page['page'] in tables_by_page:
                for table in tables_by_page[page['page']]:
                    table['id'] = chunk_id
                    table['type'] = 'serialized_table'
                    chunk_id += 1
                    chunks.append(table)
        
        file_content['content']['chunks'] = chunks
        return file_content

    def count_tokens(self, string: str, encoding_name="o200k_base"):
        # 统计字符串的token数，支持自定义编码
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(string)
        token_count = len(tokens)
        return token_count

    def split_with_overlap(self, text, chunk_size=300, chunk_overlap=50):
        """按字符分块，支持overlap"""
        chunks = []
        i = 0
        text_length = len(text)
        while i < text_length:
            chunk = text[i:i+chunk_size]
            chunks.append(chunk)
            if i + chunk_size >= text_length:
                break
            i += chunk_size - chunk_overlap
        return chunks

    def _split_page(self, page: Dict[str, any], chunk_size: int = 300, chunk_overlap: int = 50) -> List[Dict[str, any]]:
        """将单页文本分块，保留原始markdown表格。"""
        chunks = self.split_with_overlap(page['text'], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks_with_meta = []
        for chunk in chunks:
            chunks_with_meta.append({
                "page": page['page'],
                "length_tokens": self.count_tokens(chunk),
                "text": chunk
            })
        return chunks_with_meta

    #对 json 文件分块，输出还是 json
    def split_all_reports(self, all_report_dir: Path, output_dir: Path, serialized_tables_dir: Optional[Path] = None):
        """
        批量处理目录下所有报告（json文件），对每个报告进行文本分块，并输出到目标目录。
        如果提供了序列化表格目录，会尝试将表格内容插入到对应页面的分块中。
        主要用于后续向量化和检索的预处理。
        参数：
            all_report_dir: 存放待处理报告json的目录
            output_dir: 分块后输出的目标目录
            serialized_tables_dir: （可选）存放序列化表格的目录
        """
        # 获取所有报告文件路径
        all_report_paths = list(all_report_dir.glob("*.json"))
        
        # 遍历每个报告文件
        for report_path in all_report_paths:
            serialized_tables_path = None
            # 如果提供了表格序列化目录，查找对应表格文件
            if serialized_tables_dir is not None:
                serialized_tables_path = serialized_tables_dir / report_path.name
                if not serialized_tables_path.exists():
                    print(f"警告：未找到 {report_path.name} 的序列化表格报告")
                
            # 读取报告内容
            with open(report_path, 'r', encoding='utf-8') as file:
                report_data = json.load(file)
                
            # 分块处理，插入表格分块（如有）
            updated_report = self._split_report(report_data, serialized_tables_path)
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 写入分块后的报告到目标目录
            with open(output_dir / report_path.name, 'w', encoding='utf-8') as file:
                json.dump(updated_report, file, indent=2, ensure_ascii=False)
                
        # 输出处理文件数统计
        print(f"已分块处理 {len(all_report_paths)} 个文件")

    def split_markdown_file(self, md_path: Path, chunk_size: int = 30, chunk_overlap: int = 5):
        """
        按行分割 markdown 文件，每个分块记录起止行号和内容。
        :param md_path: markdown 文件路径
        :param chunk_size: 每个分块的最大行数
        :param chunk_overlap: 分块重叠行数
        :return: 分块列表
        """
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        chunks = []
        i = 0
        total_lines = len(lines)
        while i < total_lines:
            start = i
            end = min(i + chunk_size, total_lines)
            chunk_text = ''.join(lines[start:end])
            chunks.append({
                'lines': [start + 1, end],  # 行号从1开始
                'text': chunk_text
            })
            i += chunk_size - chunk_overlap
        return chunks

    def split_markdown_reports(self, all_md_dir: Path, output_dir: Path, chunk_size: int = 30, chunk_overlap: int = 5, subset_csv: Path = None):
        """
        批量处理目录下所有 markdown 文件，分块并输出为 json 文件到目标目录。
        以meta json为主循环，确保每一页（page_idx+1）至少有一个chunk，chunk内容优先匹配md分块，meta信息（type、page、text等）直接来自meta json，metainfo统计量与标准json一致，输出结构严格对齐标准chunked json。
        """
        import re
        # 建立 file_name（不去扩展名）到 company_name、sha1 的映射
        file2company = {}
        file2sha1 = {}
        file2full = {}  # 新增：file_stem -> 原始file_name
        if subset_csv is not None and os.path.exists(subset_csv):
            try:
                df = pd.read_csv(subset_csv, encoding='utf-8')
            except UnicodeDecodeError:
                print('警告：subset.csv 不是 utf-8 编码，自动尝试 gbk 编码...')
                df = pd.read_csv(subset_csv, encoding='gbk')
            if 'file_name' in df.columns:
                for _, row in df.iterrows():
                    file_stem = str(row['file_name'])  # 不去除小数点
                    file2company[file_stem] = row['company_name']
                    if 'sha1' in row:
                        file2sha1[file_stem] = row['sha1']
                    file2full[file_stem] = row['file_name']
            elif 'sha1' in df.columns:
                for _, row in df.iterrows():
                    file_stem = str(row['sha1'])
                    file2company[file_stem] = row['company_name']
                    file2sha1[file_stem] = row['sha1']
                    file2full[file_stem] = row['sha1']
            else:
                raise ValueError('subset.csv 缺少 file_name 或 sha1 列，无法建立文件名到公司名的映射')

        all_md_paths = list(all_md_dir.glob("*.md"))
        output_dir.mkdir(parents=True, exist_ok=True)
        for md_path in all_md_paths:
            file_stem = md_path.stem  # 保留小数点
            # 1. 查找同名meta json（如 xxx_1.json）
            meta_json_path = md_path.parent / f"{file_stem}_1.json"
            if not meta_json_path.exists():
                print(f"警告：未找到meta json: {meta_json_path}")
                continue
            with open(meta_json_path, 'r', encoding='utf-8') as f:
                meta_blocks = json.load(f)
            # 2. 按页分组meta块
            page2blocks = defaultdict(list)
            for block in meta_blocks:
                if isinstance(block, dict):
                    page = block.get('page_idx', 0) + 1
                    page2blocks[page].append(block)
                else:
                    # block为str或其他类型，跳过或可记录日志
                    continue
            # 3. 读取md内容
            with open(md_path, 'r', encoding='utf-8') as f:
                md_lines = f.readlines()
            # 4. 统计页数
            all_pages = sorted(page2blocks.keys())
            # 5. 统计 metainfo
            # 优先用md文件名（去扩展名）精确匹配subset.csv的file_name（去扩展名）
            company_name = file2company.get(file_stem, "")
            sha1 = file2sha1.get(file_stem, "")
            pdf_file_name = file2full.get(file_stem, "")
            # 如果没找到，再用sha1兜底
            if not pdf_file_name and sha1:
                # 取subset.csv中第一个sha1匹配的file_name
                if subset_csv is not None and os.path.exists(subset_csv):
                    if 'file_name' in df.columns:
                        match = df[df['sha1'] == sha1]
                        if not match.empty:
                            pdf_file_name = match.iloc[0]['file_name']
                            print(f"警告：{md_path.name} 未能精确匹配file_name，已用sha1兜底: {pdf_file_name}")
            pages_amount = len(all_pages)
            text_blocks_amount = sum(1 for blocks in page2blocks.values() for b in blocks if b.get('type', 'text') == 'text')
            tables_amount = sum(1 for blocks in page2blocks.values() for b in blocks if b.get('type', '') == 'table')
            pictures_amount = sum(1 for blocks in page2blocks.values() for b in blocks if b.get('type', '') == 'picture')
            equations_amount = sum(1 for blocks in page2blocks.values() for b in blocks if b.get('type', '') == 'equation')
            footnotes_amount = sum(1 for blocks in page2blocks.values() for b in blocks if b.get('type', '') == 'footnote')
            metainfo = {
                "sha1": sha1,
                "sha1_name": sha1,
                "pages_amount": pages_amount,
                "text_blocks_amount": text_blocks_amount,
                "tables_amount": tables_amount,
                "pictures_amount": pictures_amount,
                "equations_amount": equations_amount,
                "footnotes_amount": footnotes_amount,
                "company_name": company_name,
                "file_name": pdf_file_name
            }
            # 6. 以meta为主循环，保证每页至少有一个chunk
            chunks = []
            chunk_id = 0
            for page in all_pages:
                blocks = page2blocks[page]
                for block in blocks:
                    chunk_text = block.get('text', '')
                    chunk_type = block.get('type', 'content')
                    # 对文本型block做overlap分块
                    if chunk_type == 'text' and chunk_text:
                        sub_chunks = self.split_with_overlap(chunk_text, chunk_size=300, chunk_overlap=50)
                        for sub in sub_chunks:
                            length_tokens = self.count_tokens(sub)
                            chunks.append({
                                "page": page,
                                "length_tokens": length_tokens,
                                "text": sub,
                                "id": chunk_id,
                                "type": chunk_type
                            })
                            chunk_id += 1
                    else:
                        # 非文本型block直接保留
                        length_tokens = self.count_tokens(chunk_text)
                        chunks.append({
                            "page": page,
                            "length_tokens": length_tokens,
                            "text": chunk_text,
                            "id": chunk_id,
                            "type": chunk_type
                        })
                        chunk_id += 1
            # 7. 按page升序排序
            chunks = sorted(chunks, key=lambda x: (x['page'], x['id']))
            # 8. 输出json
            output_json_path = output_dir / (md_path.stem + ".json")
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump({"metainfo": metainfo, "content": {"chunks": chunks}}, f, ensure_ascii=False, indent=2)
            print(f"已处理: {md_path.name} -> {output_json_path.name}")
        print(f"共分割 {len(all_md_paths)} 个 markdown 文件")
