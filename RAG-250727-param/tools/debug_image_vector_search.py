#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 深度诊断图片向量搜索问题
## 2. 确定是向量化问题还是查询逻辑问题
## 3. 逐步排查每个可能的问题点
"""

import sys
import os
import logging

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings

# 导入统一的API密钥管理模块
from config.api_key_manager import get_dashscope_api_key

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_image_vector_search():
    """深度诊断图片向量搜索问题"""
    print("🔍 深度诊断图片向量搜索问题")
    print("=" * 60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        vector_db_path = config.vector_db_dir
        
        print(f"📁 向量数据库路径: {vector_db_path}")
        
        # 获取API密钥
        config_key = config.dashscope_api_key
        api_key = get_dashscope_api_key(config_key)
        
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return
        
        # 初始化embeddings
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        print("✅ DashScope embeddings初始化成功")
        
        # 加载向量存储
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        print(f"✅ 向量存储加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
        
        # 深度诊断开始
        print("\n🔍 开始深度诊断...")
        
        # 诊断1：检查文档分布
        print("\n📊 诊断1：检查文档分布")
        docstore = vector_store.docstore._dict
        chunk_type_count = {}
        doc_details = {}
        
        for doc_id, doc in docstore.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                chunk_type_count[chunk_type] = chunk_type_count.get(chunk_type, 0) + 1
                
                # 记录前几个文档的详细信息
                if chunk_type in ['image', 'image_text'] and chunk_type not in doc_details:
                    doc_details[chunk_type] = {
                        'doc_id': doc_id,
                        'doc': doc,
                        'metadata': doc.metadata
                    }
        
        print("📋 文档类型分布:")
        for chunk_type, count in sorted(chunk_type_count.items()):
            print(f"  {chunk_type}: {count} 个")
        
        # 诊断2：检查image_text文档的详细信息
        print("\n📊 诊断2：检查image_text文档详细信息")
        if 'image_text' in doc_details:
            doc_info = doc_details['image_text']
            doc = doc_info['doc']
            metadata = doc_info['metadata']
            
            print(f"📄 文档ID: {doc_info['doc_id']}")
            print(f"📄 文档类型: {type(doc)}")
            print(f"📄 是否有page_content: {hasattr(doc, 'page_content')}")
            
            if hasattr(doc, 'page_content'):
                print(f"📄 page_content长度: {len(doc.page_content)}")
                print(f"📄 page_content预览: {doc.page_content[:200]}...")
            
            print(f"📄 metadata字段: {list(metadata.keys())}")
            print(f"📄 chunk_type: {metadata.get('chunk_type', 'N/A')}")
            print(f"📄 enhanced_description长度: {len(metadata.get('enhanced_description', ''))}")
            
            # 检查关键字段
            key_fields = ['enhanced_description', 'image_id', 'document_name', 'page_number']
            for field in key_fields:
                value = metadata.get(field, 'N/A')
                if isinstance(value, str) and len(value) > 100:
                    print(f"📄 {field}: {value[:100]}...")
                else:
                    print(f"📄 {field}: {value}")
        
        # 诊断3：检查image文档的详细信息
        print("\n📊 诊断3：检查image文档详细信息")
        if 'image' in doc_details:
            doc_info = doc_details['image']
            doc = doc_info['doc']
            metadata = doc_info['metadata']
            
            print(f"🖼️ 文档ID: {doc_info['doc_id']}")
            print(f"🖼️ 文档类型: {type(doc)}")
            print(f"🖼️ 是否有page_content: {hasattr(doc, 'page_content')}")
            
            if hasattr(doc, 'page_content'):
                print(f"🖼️ page_content长度: {len(doc.page_content)}")
                print(f"🖼️ page_content预览: {doc.page_content[:200]}...")
            
            print(f"🖼️ metadata字段: {list(metadata.keys())}")
            print(f"🖼️ chunk_type: {metadata.get('chunk_type', 'N/A')}")
            print(f"🖼️ img_caption: {metadata.get('img_caption', 'N/A')}")
            print(f"🖼️ image_id: {metadata.get('image_id', 'N/A')}")
        
        # 诊断4：测试不同的查询方式
        print("\n📊 诊断4：测试不同的查询方式")
        test_queries = [
            "中芯国际净利润",
            "股价相对走势",
            "图片",
            "图表"
        ]
        
        for query in test_queries:
            print(f"\n🔍 测试查询: {query}")
            
            # 测试无filter搜索
            try:
                results = vector_store.similarity_search(query, k=3)
                print(f"  无filter: 返回 {len(results)} 个结果")
                for i, doc in enumerate(results[:2]):
                    chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') else 'unknown'
                    print(f"    结果{i+1}: {chunk_type}")
            except Exception as e:
                print(f"  无filter: 失败 - {e}")
            
            # 测试image_text搜索
            try:
                image_text_results = vector_store.similarity_search(
                    query, 
                    k=3,
                    filter={'chunk_type': 'image_text'}
                )
                print(f"  image_text filter: 返回 {len(image_text_results)} 个结果")
            except Exception as e:
                print(f"  image_text filter: 失败 - {e}")
            
            # 测试image搜索
            try:
                image_results = vector_store.similarity_search(
                    query, 
                    k=3,
                    filter={'chunk_type': 'image'}
                )
                print(f"  image filter: 返回 {len(image_results)} 个结果")
            except Exception as e:
                print(f"  image filter: 失败 - {e}")
        
        # 诊断5：检查向量索引
        print("\n📊 诊断5：检查向量索引")
        try:
            # 检查FAISS索引
            faiss_index = vector_store.index
            print(f"🔢 FAISS索引类型: {type(faiss_index)}")
            print(f"🔢 向量维度: {faiss_index.d}")
            print(f"🔢 向量数量: {faiss_index.ntotal}")
            
            # 检查是否有向量数据
            if hasattr(faiss_index, 'get_xb'):
                try:
                    vectors = faiss_index.get_xb()
                    print(f"🔢 向量数据类型: {type(vectors)}")
                    if hasattr(vectors, 'shape'):
                        print(f"🔢 向量数据形状: {vectors.shape}")
                        print(f"🔢 前3个向量的前5维: {vectors[:3, :5]}")
                except Exception as e:
                    print(f"🔢 无法获取向量数据: {e}")
            
        except Exception as e:
            print(f"❌ 检查向量索引失败: {e}")
        
        # 诊断6：检查filter参数
        print("\n📊 诊断6：检查filter参数")
        print("🔍 测试不同的filter组合...")
        
        filter_tests = [
            {},  # 无filter
            {'chunk_type': 'image_text'},  # 精确匹配
            {'chunk_type': 'image'},  # 精确匹配
            {'chunk_type': {'$in': ['image_text', 'image']}},  # 包含匹配
        ]
        
        for i, filter_param in enumerate(filter_tests):
            try:
                results = vector_store.similarity_search("中芯国际", k=5, filter=filter_param)
                print(f"  Filter {i+1} {filter_param}: 返回 {len(results)} 个结果")
                
                # 显示结果的chunk_type分布
                chunk_types = {}
                for doc in results:
                    chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') else 'unknown'
                    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                for chunk_type, count in chunk_types.items():
                    print(f"    {chunk_type}: {count} 个")
                    
            except Exception as e:
                print(f"  Filter {i+1} {filter_param}: 失败 - {e}")
        
        print("\n✅ 深度诊断完成！")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_image_vector_search()
