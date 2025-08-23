#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 专门检查table_405084的3个子块的语义化内容
## 2. 验证是否只有部分子块有processed_table_content字段
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

def check_table_405084_chunks():
    """检查table_405084的所有子块"""
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
        
        print("🔍 检查table_405084的所有子块")
        print("=" * 60)
        
        # 获取所有文档
        all_docs = vector_store.docstore._dict
        
        # 找到table_405084相关的所有文档
        table_405084_docs = []
        for doc_id, doc in all_docs.items():
            if hasattr(doc, 'metadata') and doc.metadata.get('table_id'):
                table_id = doc.metadata.get('table_id', '')
                if 'table_405084' in table_id:
                    table_405084_docs.append((doc_id, doc))
        
        print(f"📊 找到 {len(table_405084_docs)} 个table_405084相关的文档")
        print()
        
        for i, (doc_id, doc) in enumerate(table_405084_docs, 1):
            print(f"==== 子块 {i} ====")
            print(f"文档ID: {doc_id}")
            print(f"表格ID: {doc.metadata.get('table_id', 'N/A')}")
            print(f"页码: {doc.metadata.get('page_number', 'N/A')}")
            print(f"分块索引: {doc.metadata.get('chunk_index', 'N/A')}")
            
            # 检查processed_table_content字段
            processed_content = doc.metadata.get('processed_table_content')
            if processed_content:
                print(f"✅ 有processed_table_content: 长度={len(processed_content)}")
                print(f"内容预览: {processed_content[:100]}...")
            else:
                print("❌ 无processed_table_content")
            
            # 检查HTML内容
            html_content = doc.metadata.get('page_content', '')
            if html_content and any(tag in html_content.lower() for tag in ['<table', '<tr', '<td']):
                print(f"✅ 有HTML内容: 长度={len(html_content)}")
                print(f"HTML预览: {html_content[:100]}...")
            else:
                print("❌ 无HTML内容")
            
            # 显示其他相关字段
            table_summary = doc.metadata.get('table_summary', '')
            table_title = doc.metadata.get('table_title', '')
            related_text = doc.metadata.get('related_text', '')
            
            print(f"table_summary: {'有' if table_summary else '无'}")
            print(f"table_title: {'有' if table_title else '无'}")
            print(f"related_text: {'有' if related_text else '无'}")
            print()
        
        print("📈 统计结果:")
        has_processed = sum(1 for _, doc in table_405084_docs 
                          if doc.metadata.get('processed_table_content'))
        has_html = sum(1 for _, doc in table_405084_docs 
                      if doc.metadata.get('page_content') and 
                      any(tag in doc.metadata.get('page_content', '').lower() 
                          for tag in ['<table', '<tr', '<td']))
        
        print(f"总子块数: {len(table_405084_docs)}")
        print(f"有processed_table_content的子块: {has_processed}")
        print(f"有HTML内容的子块: {has_html}")
        
        if has_processed < len(table_405084_docs):
            print(f"⚠️  发现问题：{len(table_405084_docs) - has_processed} 个子块缺少processed_table_content")
        else:
            print("✅ 所有子块都有processed_table_content")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_table_405084_chunks()
