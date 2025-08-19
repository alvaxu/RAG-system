#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 诊断FAISS filter不工作的根本原因
## 2. 检查向量数据库结构和chunk_type字段
## 3. 测试不同的filter语法和FAISS支持情况
## 4. 分析向量化模型和数据类型
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

def debug_faiss_filter():
    """诊断FAISS filter不工作的根本原因"""
    print("🔍 诊断FAISS filter不工作的根本原因")
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
        
        # 加载向量数据库
        print("📚 正在加载向量数据库...")
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        print(f"✅ 向量数据库加载成功")
        
        # 1. 检查FAISS版本和配置
        print("\n🔍 1. 检查FAISS版本和配置")
        print("-" * 40)
        try:
            import faiss
            print(f"FAISS版本: {faiss.__version__}")
            print(f"FAISS编译信息: {faiss.get_compile_options()}")
        except Exception as e:
            print(f"❌ 获取FAISS信息失败: {e}")
        
        # 2. 分析向量数据库结构
        print("\n🔍 2. 分析向量数据库结构")
        print("-" * 40)
        
        docstore = vector_store.docstore
        docstore_dict = docstore._dict
        print(f"总文档数量: {len(docstore_dict)}")
        
        # 统计chunk_type分布
        chunk_type_stats = {}
        metadata_fields = set()
        
        for doc_id, doc in docstore_dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
                
                # 收集所有metadata字段
                metadata_fields.update(doc.metadata.keys())
                
                # 检查前几个文档的详细信息
                if len(chunk_type_stats) <= 5:
                    print(f"文档 {doc_id}: chunk_type={chunk_type}")
                    print(f"  metadata字段: {list(doc.metadata.keys())}")
                    if 'chunk_type' in doc.metadata:
                        print(f"  chunk_type值: '{doc.metadata['chunk_type']}' (类型: {type(doc.metadata['chunk_type'])})")
        
        print(f"\nchunk_type分布:")
        for chunk_type, count in sorted(chunk_type_stats.items()):
            print(f"  {chunk_type}: {count} 个")
        
        print(f"\n所有metadata字段: {sorted(metadata_fields)}")
        
        # 3. 测试不同的filter语法
        print("\n🔍 3. 测试不同的filter语法")
        print("-" * 40)
        
        test_query = "中芯国际净利润"
        test_filters = [
            None,  # 无filter
            {'chunk_type': 'image'},
            {'chunk_type': 'image_text'},
            {'chunk_type': 'text'},
            {'chunk_type': 'table'},
            {'metadata.chunk_type': 'image'},
            {'metadata.chunk_type': 'image_text'},
            {'chunk_type': 1},  # 数值化测试
            {'chunk_type': 'image', 'document_name': '中芯国际'},
            {'chunk_type': 'image_text', 'document_name': '中芯国际'},
        ]
        
        for filter_dict in test_filters:
            try:
                if filter_dict is None:
                    results = vector_store.similarity_search(test_query, k=5)
                    print(f"无filter: {len(results)} 个结果")
                else:
                    results = vector_store.similarity_search(test_query, k=5, filter=filter_dict)
                    print(f"Filter {filter_dict}: {len(results)} 个结果")
                    
                    # 显示结果的chunk_type
                    if results:
                        chunk_types = [r.metadata.get('chunk_type', 'N/A') for r in results]
                        print(f"  结果chunk_type: {chunk_types}")
                        
            except Exception as e:
                print(f"Filter {filter_dict}: 错误 - {e}")
        
        # 4. 分析向量化模型
        print("\n🔍 4. 分析向量化模型")
        print("-" * 40)
        
        # 检查image和image_text文档的向量化信息
        image_docs = []
        image_text_docs = []
        
        for doc_id, doc in docstore_dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', '')
                if chunk_type == 'image':
                    image_docs.append(doc)
                elif chunk_type == 'image_text':
                    image_text_docs.append(doc)
        
        print(f"image文档数量: {len(image_docs)}")
        print(f"image_text文档数量: {len(image_text_docs)}")
        
        # 检查前几个文档的详细信息
        if image_docs:
            print(f"\n第一个image文档:")
            doc = image_docs[0]
            metadata = doc.metadata
            print(f"  chunk_type: {metadata.get('chunk_type')}")
            print(f"  image_id: {metadata.get('image_id')}")
            print(f"  enhanced_description: {metadata.get('enhanced_description', '')[:100]}...")
            print(f"  semantic_features: {'有' if 'semantic_features' in metadata else '无'}")
        
        if image_text_docs:
            print(f"\n第一个image_text文档:")
            doc = image_text_docs[0]
            metadata = doc.metadata
            print(f"  chunk_type: {metadata.get('chunk_type')}")
            print(f"  image_id: {metadata.get('image_id')}")
            print(f"  enhanced_description: {metadata.get('enhanced_description', '')[:100]}...")
            print(f"  semantic_features: {'有' if 'semantic_features' in metadata else '无'}")
        
        # 5. 测试向量搜索的相似度分数
        print("\n🔍 5. 测试向量搜索的相似度分数")
        print("-" * 40)
        
        try:
            # 使用similarity_search_with_score获取分数
            results_with_score = vector_store.similarity_search_with_score(test_query, k=10)
            print(f"前10个结果的相似度分数:")
            
            for i, (doc, score) in enumerate(results_with_score):
                chunk_type = doc.metadata.get('chunk_type', 'N/A') if hasattr(doc, 'metadata') else 'N/A'
                print(f"  结果{i+1}: chunk_type={chunk_type}, score={score:.4f}")
                
                if i >= 4:  # 只显示前5个
                    break
                    
        except Exception as e:
            print(f"❌ 获取相似度分数失败: {e}")
        
        print("\n✅ FAISS filter诊断完成！")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_faiss_filter()
