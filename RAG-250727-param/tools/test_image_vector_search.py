#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试图片向量搜索功能
## 2. 验证image_text和image两种搜索策略
## 3. 检查向量搜索API是否正常工作
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

def test_image_vector_search():
    """测试图片向量搜索功能"""
    print("🔍 开始测试图片向量搜索功能")
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
        
        # 测试查询
        test_query = "中芯国际净利润"
        print(f"\n🔍 测试查询: {test_query}")
        
        # 测试1：无filter的向量搜索
        print("\n📊 测试1：无filter的向量搜索")
        try:
            results = vector_store.similarity_search(test_query, k=5)
            print(f"✅ 无filter搜索成功，返回 {len(results)} 个结果")
            
            # 显示前3个结果的chunk_type
            for i, doc in enumerate(results[:3]):
                chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') else 'unknown'
                score = getattr(doc, 'score', 'N/A')
                print(f"  结果{i+1}: chunk_type={chunk_type}, score={score}")
                
        except Exception as e:
            print(f"❌ 无filter搜索失败: {e}")
        
        # 测试2：搜索image_text chunks
        print("\n📊 测试2：搜索image_text chunks")
        try:
            image_text_results = vector_store.similarity_search(
                test_query, 
                k=10,
                filter={'chunk_type': 'image_text'}
            )
            print(f"✅ image_text搜索成功，返回 {len(image_text_results)} 个结果")
            
            # 显示结果详情
            for i, doc in enumerate(image_text_results[:3]):
                if hasattr(doc, 'metadata') and doc.metadata:
                    chunk_type = doc.metadata.get('chunk_type', 'N/A')
                    score = getattr(doc, 'score', 'N/A')
                    enhanced_desc = doc.metadata.get('enhanced_description', '')[:100] + '...' if len(doc.metadata.get('enhanced_description', '')) > 100 else doc.metadata.get('enhanced_description', '')
                    print(f"  结果{i+1}: chunk_type={chunk_type}, score={score}")
                    print(f"    描述: {enhanced_desc}")
                else:
                    print(f"  结果{i+1}: 无metadata")
                    
        except Exception as e:
            print(f"❌ image_text搜索失败: {e}")
        
        # 测试3：搜索image chunks
        print("\n📊 测试3：搜索image chunks")
        try:
            image_results = vector_store.similarity_search(
                test_query, 
                k=10,
                filter={'chunk_type': 'image'}
            )
            print(f"✅ image搜索成功，返回 {len(image_results)} 个结果")
            
            # 显示结果详情
            for i, doc in enumerate(image_results[:3]):
                if hasattr(doc, 'metadata') and doc.metadata:
                    chunk_type = doc.metadata.get('chunk_type', 'N/A')
                    score = getattr(doc, 'score', 'N/A')
                    img_caption = doc.metadata.get('img_caption', 'N/A')
                    print(f"  结果{i+1}: chunk_type={chunk_type}, score={score}")
                    print(f"    标题: {img_caption}")
                else:
                    print(f"  结果{i+1}: 无metadata")
                    
        except Exception as e:
            print(f"❌ image搜索失败: {e}")
        
        # 测试4：检查向量数据
        print("\n📊 测试4：检查向量数据")
        try:
            # 获取一个image_text文档
            docstore = vector_store.docstore._dict
            image_text_docs = []
            
            for doc_id, doc in docstore.items():
                if hasattr(doc, 'metadata') and doc.metadata and doc.metadata.get('chunk_type') == 'image_text':
                    image_text_docs.append(doc)
                    if len(image_text_docs) >= 3:
                        break
            
            print(f"找到 {len(image_text_docs)} 个image_text文档")
            
            if image_text_docs:
                # 检查第一个文档的向量
                doc = image_text_docs[0]
                print(f"第一个文档ID: {list(docstore.keys())[list(docstore.values()).index(doc)]}")
                print(f"文档类型: {type(doc)}")
                print(f"是否有page_content: {hasattr(doc, 'page_content')}")
                if hasattr(doc, 'page_content'):
                    print(f"page_content长度: {len(doc.page_content)}")
                    print(f"page_content预览: {doc.page_content[:100]}...")
                
                # 检查metadata
                if hasattr(doc, 'metadata') and doc.metadata:
                    print(f"metadata字段: {list(doc.metadata.keys())}")
                    enhanced_desc = doc.metadata.get('enhanced_description', '')
                    print(f"enhanced_description长度: {len(enhanced_desc)}")
                    print(f"enhanced_description预览: {enhanced_desc[:100]}...")
                    
                    # 检查semantic_features
                    semantic_features = doc.metadata.get('semantic_features', {})
                    if semantic_features:
                        print(f"semantic_features: {semantic_features}")
                    else:
                        print("❌ 没有semantic_features")
                else:
                    print("❌ 没有metadata")
                    
        except Exception as e:
            print(f"❌ 检查向量数据失败: {e}")
        
        print("\n✅ 图片向量搜索测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_vector_search()
