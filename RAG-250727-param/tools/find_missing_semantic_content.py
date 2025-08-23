#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 专门用于找出缺少语义化内容的表格文档
## 2. 分析为什么某些表格没有语义化内容
"""

import sys
import os
import json
from pathlib import Path

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key

def load_vector_store(vector_db_path):
    """加载向量存储"""
    try:
        config = Settings.load_from_file('config.json')
        
        # 使用统一的API密钥管理模块获取API密钥
        config_key = config.dashscope_api_key
        api_key = get_dashscope_api_key(config_key)
        
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return None
        
        # 初始化DashScope embeddings
        try:
            embedding_model = config.text_embedding_model
        except Exception as e:
            print(f"⚠️ 无法加载配置，使用默认embedding模型: {e}")
            embedding_model = 'text-embedding-v1'
        
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model=embedding_model)
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        print(f"✅ 向量存储加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
        return vector_store
    except Exception as e:
        print(f"❌ 加载向量存储失败: {e}")
        return None

def analyze_semantic_content_missing(vector_store):
    """分析缺少语义化内容的表格文档"""
    print("🔍 分析缺少语义化内容的表格文档")
    print("=" * 60)
    
    if not vector_store or not hasattr(vector_store, 'docstore') or not hasattr(vector_store.docstore, '_dict'):
        print("❌ 向量存储结构异常")
        return None
    
    docstore = vector_store.docstore._dict
    table_docs = []
    
    # 找出所有表格文档
    for doc_id, doc in docstore.items():
        if hasattr(doc, 'metadata') and doc.metadata and doc.metadata.get('chunk_type') == 'table':
            table_docs.append((doc_id, doc))
    
    print(f"📊 找到 {len(table_docs)} 个表格文档")
    
    # 分析每个表格文档的语义化内容
    missing_semantic = []
    has_semantic = []
    
    for i, (doc_id, doc) in enumerate(table_docs):
        doc_info = {
            'index': i + 1,
            'doc_id': doc_id,
            'document_name': doc.metadata.get('document_name', 'N/A'),
            'page_number': doc.metadata.get('page_number', 'N/A'),
            'table_id': doc.metadata.get('table_id', 'N/A'),
            'table_type': doc.metadata.get('table_type', 'N/A'),
            'has_html': False,
            'has_semantic': False,
            'semantic_fields': [],
            'html_content_length': 0,
            'semantic_content_length': 0
        }
        
        # 检查HTML内容
        if 'page_content' in doc.metadata and doc.metadata['page_content']:
            html_content = doc.metadata['page_content']
            doc_info['html_content_length'] = len(html_content)
            if '<table' in str(html_content).lower() or '<tr' in str(html_content).lower() or '<td' in str(html_content).lower():
                doc_info['has_html'] = True
        
        # 检查语义化内容
        semantic_fields = []
        semantic_content = ""
        
        # 主要语义化字段 - 只检查processed_table_content
        if 'processed_table_content' in doc.metadata and doc.metadata['processed_table_content']:
            semantic_fields.append('processed_table_content')
            semantic_content = doc.metadata['processed_table_content']
        
        # 备用语义化字段 - 仅作为参考，不参与主要统计
        alt_semantic_fields = []
        for alt_key in ['table_summary', 'table_title', 'related_text']:
            if alt_key in doc.metadata and doc.metadata[alt_key] and len(str(doc.metadata[alt_key])) > 0:
                alt_semantic_fields.append(alt_key)
        
        doc_info['semantic_fields'] = semantic_fields
        doc_info['alt_semantic_fields'] = alt_semantic_fields  # 备用字段
        doc_info['semantic_content_length'] = len(semantic_content)
        
        # 只有processed_table_content存在才算有语义化内容
        if semantic_fields:
            doc_info['has_semantic'] = True
            has_semantic.append(doc_info)
        else:
            missing_semantic.append(doc_info)
    
    # 显示统计结果
    print(f"\n📊 语义化内容统计:")
    print(f"  有语义化内容的表格: {len(has_semantic)}")
    print(f"  缺少语义化内容的表格: {len(missing_semantic)}")
    
    # 显示缺少语义化内容的表格详情
    if missing_semantic:
        print(f"\n❌ 缺少语义化内容的表格 ({len(missing_semantic)}个):")
        print("=" * 60)
        for doc_info in missing_semantic:
            print(f"\n📄 表格 {doc_info['index']}:")
            print(f"  文档名: {doc_info['document_name']}")
            print(f"  页码: {doc_info['page_number']}")
            print(f"  表格ID: {doc_info['table_id']}")
            print(f"  表格类型: {doc_info['table_type']}")
            print(f"  有HTML内容: {'✅' if doc_info['has_html'] else '❌'}")
            print(f"  HTML内容长度: {doc_info['html_content_length']}")
            print(f"  主要语义化字段: {doc_info['semantic_fields']}")
            print(f"  备用语义化字段: {doc_info['alt_semantic_fields']}")
            
            # 显示元数据中的所有字段
            doc = next(doc for doc_id, doc in table_docs if doc_id == doc_info['doc_id'])
            print(f"  所有元数据字段: {list(doc.metadata.keys())}")
            
            # 显示关键字段的值
            for field in ['processed_table_content', 'table_summary', 'table_title', 'related_text']:
                if field in doc.metadata:
                    value = doc.metadata[field]
                    if value is None:
                        print(f"    {field}: None")
                    elif value == "":
                        print(f"    {field}: (空字符串)")
                    else:
                        print(f"    {field}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                else:
                    print(f"    {field}: (字段不存在)")
    
    # 显示有语义化内容的表格统计
    if has_semantic:
        print(f"\n✅ 有语义化内容的表格 ({len(has_semantic)}个):")
        print("=" * 60)
        
        # 统计语义化字段的分布
        field_stats = {}
        for doc_info in has_semantic:
            for field in doc_info['semantic_fields']:
                field_stats[field] = field_stats.get(field, 0) + 1
        
        print("语义化字段分布:")
        for field, count in sorted(field_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {field}: {count}个表格")
        
        # 显示前几个有语义化内容的表格
        print(f"\n前3个有语义化内容的表格示例:")
        for i, doc_info in enumerate(has_semantic[:3]):
            print(f"\n📄 表格 {doc_info['index']}:")
            print(f"  文档名: {doc_info['document_name']}")
            print(f"  页码: {doc_info['page_number']}")
            print(f"  表格ID: {doc_info['table_id']}")
            print(f"  主要语义化字段: {doc_info['semantic_fields']}")
            print(f"  备用语义化字段: {doc_info['alt_semantic_fields']}")
            print(f"  语义化内容长度: {doc_info['semantic_content_length']}")
    
    return {
        'total_table_docs': len(table_docs),
        'has_semantic': len(has_semantic),
        'missing_semantic': len(missing_semantic),
        'missing_details': missing_semantic,
        'has_details': has_semantic
    }

def main():
    """主函数"""
    print("🔍 查找缺少语义化内容的表格文档")
    print("=" * 60)
    
    try:
        config = Settings.load_from_file('config.json')
        vector_db_path = config.vector_db_dir
        
        print(f"📁 向量数据库路径: {vector_db_path}")
        
        # 检查路径是否存在，如果不存在尝试其他可能的路径
        if not os.path.exists(vector_db_path):
            possible_paths = [
                "./central/vector_db",
                "./vector_db",
                "./central/vector_db_test",
                "./vector_db_test"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    vector_db_path = path
                    print(f"✅ 找到向量数据库路径: {vector_db_path}")
                    break
            else:
                print(f"❌ 向量数据库路径不存在，尝试过的路径:")
                for path in possible_paths:
                    print(f"   - {path}")
                return
        
        # 加载向量存储
        vector_store = load_vector_store(vector_db_path)
        if not vector_store:
            print("❌ 无法加载向量存储")
            return
        
        # 分析语义化内容缺失情况
        analysis_result = analyze_semantic_content_missing(vector_store)
        
        # 保存分析结果
        output_file = "semantic_content_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 分析结果已保存到: {output_file}")
        
        print("\n✅ 语义化内容缺失分析完成！")
        
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
