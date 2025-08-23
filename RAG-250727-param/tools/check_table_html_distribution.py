#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查表格文档中HTML内容的分布情况
"""

import os
import sys
import pickle
import faiss
from pathlib import Path

def check_table_html_distribution():
    """检查表格文档中HTML内容的分布情况"""
    
    # 向量数据库路径
    vector_db_path = "central/vector_db"
    
    if not os.path.exists(vector_db_path):
        print(f"❌ 向量数据库路径不存在: {vector_db_path}")
        return
    
    # 加载索引元数据
    try:
        with open(os.path.join(vector_db_path, "index.pkl"), "rb") as f:
            index_data = pickle.load(f)
        print(f"✅ 索引元数据加载成功")
    except Exception as e:
        print(f"❌ 索引元数据加载失败: {e}")
        return
    
    if len(index_data) >= 2:
        docstore = index_data[0]
        
        # 统计表格文档
        table_docs = []
        html_content_docs = []
        no_html_content_docs = []
        
        for doc_id, doc in docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', '')
                if chunk_type == 'table':
                    table_docs.append(doc)
                    
                    # 检查是否有HTML内容
                    page_content = getattr(doc, 'page_content', '')
                    if page_content and page_content.startswith('<table'):
                        html_content_docs.append(doc)
                    else:
                        no_html_content_docs.append(doc)
        
        print(f"\n📊 表格文档统计:")
        print(f"总表格文档数量: {len(table_docs)}")
        print(f"有HTML内容的文档数量: {len(html_content_docs)}")
        print(f"没有HTML内容的文档数量: {len(no_html_content_docs)}")
        
        # 分析有HTML内容的文档
        if html_content_docs:
            print(f"\n✅ 有HTML内容的文档:")
            for i, doc in enumerate(html_content_docs[:5]):  # 只显示前5个
                doc_name = doc.metadata.get('document_name', '未知文档')
                page_num = doc.metadata.get('page_number', 'N/A')
                table_id = doc.metadata.get('table_id', 'N/A')
                page_content = getattr(doc, 'page_content', '')
                html_preview = page_content[:100] + "..." if len(page_content) > 100 else page_content
                
                print(f"  {i+1}. {doc_name} - 第{page_num}页 - {table_id}")
                print(f"     HTML预览: {html_preview}")
                print()
        
        # 分析没有HTML内容的文档
        if no_html_content_docs:
            print(f"\n❌ 没有HTML内容的文档:")
            for i, doc in enumerate(no_html_content_docs[:5]):  # 只显示前5个
                doc_name = doc.metadata.get('document_name', '未知文档')
                page_num = doc.metadata.get('page_number', 'N/A')
                table_id = doc.metadata.get('table_id', 'N/A')
                page_content = getattr(doc, 'page_content', '')
                content_preview = page_content[:100] + "..." if len(page_content) > 100 else page_content
                
                print(f"  {i+1}. {doc_name} - 第{page_num}页 - {table_id}")
                print(f"     内容预览: {content_preview}")
                print()
        
        # 分析可能的原因
        print(f"\n🔍 分析可能的原因:")
        
        # 检查文档来源
        html_doc_names = set()
        no_html_doc_names = set()
        
        for doc in html_content_docs:
            doc_name = doc.metadata.get('document_name', '')
            if doc_name:
                html_doc_names.add(doc_name)
        
        for doc in no_html_content_docs:
            doc_name = doc.metadata.get('document_name', '')
            if doc_name:
                no_html_doc_names.add(doc_name)
        
        print(f"有HTML内容的文档来源: {len(html_doc_names)} 个不同文档")
        print(f"没有HTML内容的文档来源: {len(no_html_doc_names)} 个不同文档")
        
        # 检查是否有重叠
        overlap = html_doc_names.intersection(no_html_doc_names)
        if overlap:
            print(f"⚠️  发现重叠文档（既有HTML内容又没有HTML内容）: {len(overlap)} 个")
            for doc_name in list(overlap)[:3]:
                print(f"    - {doc_name}")
        else:
            print(f"✅ 没有重叠文档，HTML内容分布清晰")
        
        # 检查处理时间差异
        print(f"\n⏰ 检查处理时间差异:")
        html_docs_with_time = [doc for doc in html_content_docs if hasattr(doc, 'processing_time')]
        no_html_docs_with_time = [doc for doc in no_html_content_docs if hasattr(doc, 'processing_time')]
        
        if html_docs_with_time:
            avg_html_time = sum(getattr(doc, 'processing_time', 0) for doc in html_docs_with_time) / len(html_docs_with_time)
            print(f"有HTML内容的文档平均处理时间: {avg_html_time:.2f}s")
        
        if no_html_docs_with_time:
            avg_no_html_time = sum(getattr(doc, 'processing_time', 0) for doc in no_html_docs_with_time) / len(no_html_docs_with_time)
            print(f"没有HTML内容的文档平均处理时间: {avg_no_html_time:.2f}s")
        
        # 总结
        print(f"\n📋 总结:")
        if len(html_content_docs) == 12 and len(no_html_content_docs) == 78:
            print(f"✅ 数据与诊断结果一致: 12个有HTML内容，78个没有HTML内容")
        
        if not overlap:
            print(f"✅ HTML内容分布清晰，没有重叠文档")
            print(f"   可能原因: 不同批次的文档处理使用了不同的处理策略")
        else:
            print(f"⚠️  发现重叠文档，需要进一步调查")
        
        print(f"\n💡 建议:")
        print(f"1. 检查文档处理的时间线，看是否在不同时期使用了不同的处理策略")
        print(f"2. 检查enhanced_chunker.py中表格处理的逻辑，看是否有条件分支")
        print(f"3. 检查JSON源文件，看是否所有文档都包含table_body字段")

if __name__ == "__main__":
    check_table_html_distribution()
