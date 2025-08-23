#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 精确找出缺少processed_table_content字段的表格
## 2. 列出具体的表格ID和详细信息
"""

import sys
import os
from pathlib import Path

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key

def find_missing_processed_content():
    """找出缺少processed_table_content的表格"""
    try:
        config = Settings.load_from_file('config.json')
        
        # 使用统一的API密钥管理模块获取API密钥
        config_key = config.dashscope_api_key
        api_key = get_dashscope_api_key(config_key)
        
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return
        
        # 创建embedding实例
        embeddings = DashScopeEmbeddings(
            model=config.text_embedding_model,
            dashscope_api_key=api_key
        )
        
        # 加载向量存储
        vector_store = FAISS.load_local(
            "central/vector_db", 
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        print("🔍 查找缺少processed_table_content的表格")
        print("=" * 60)
        
        # 获取所有文档
        all_docs = vector_store.docstore._dict
        
        # 找到所有表格文档
        table_docs = []
        missing_docs = []
        
        for doc_id, doc in all_docs.items():
            if hasattr(doc, 'metadata') and doc.metadata.get('chunk_type') == 'table':
                table_docs.append((doc_id, doc))
                
                # 检查是否缺少processed_table_content
                processed_content = doc.metadata.get('processed_table_content')
                if not processed_content or len(str(processed_content).strip()) == 0:
                    missing_docs.append((doc_id, doc))
        
        print(f"📊 总表格文档数: {len(table_docs)}")
        print(f"❌ 缺少processed_table_content的文档数: {len(missing_docs)}")
        print()
        
        if missing_docs:
            print("🔍 缺少processed_table_content的表格详情:")
            print("-" * 60)
            
            for i, (doc_id, doc) in enumerate(missing_docs, 1):
                print(f"==== 缺失表格 {i} ====")
                print(f"文档ID: {doc_id}")
                print(f"表格ID: {doc.metadata.get('table_id', 'N/A')}")
                print(f"页码: {doc.metadata.get('page_number', 'N/A')}")
                print(f"分块索引: {doc.metadata.get('chunk_index', 'N/A')}")
                print(f"表格类型: {doc.metadata.get('table_type', 'N/A')}")
                print(f"表格标题: {doc.metadata.get('table_title', 'N/A')}")
                
                # 检查processed_table_content的具体情况
                processed_content = doc.metadata.get('processed_table_content')
                print(f"processed_table_content值: {repr(processed_content)}")
                
                # 检查其他语义化字段
                table_summary = doc.metadata.get('table_summary', '')
                table_title = doc.metadata.get('table_title', '')
                related_text = doc.metadata.get('related_text', '')
                
                print(f"table_summary: {'有' if table_summary else '无'} ({len(str(table_summary))} 字符)")
                print(f"table_title: {'有' if table_title else '无'} ({len(str(table_title))} 字符)")
                print(f"related_text: {'有' if related_text else '无'} ({len(str(related_text))} 字符)")
                
                # 检查HTML内容
                html_content = doc.metadata.get('page_content', '')
                if html_content and any(tag in html_content.lower() for tag in ['<table', '<tr', '<td']):
                    print(f"✅ 有HTML内容: 长度={len(html_content)}")
                    print(f"HTML预览: {html_content[:100]}...")
                else:
                    print("❌ 无HTML内容")
                
                print()
        else:
            print("✅ 所有表格都有processed_table_content字段")
        
        # 同时检查有processed_table_content的表格统计
        has_processed = len(table_docs) - len(missing_docs)
        print(f"📈 统计汇总:")
        print(f"总表格数: {len(table_docs)}")
        print(f"有processed_table_content: {has_processed}")
        print(f"缺少processed_table_content: {len(missing_docs)}")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_missing_processed_content()
