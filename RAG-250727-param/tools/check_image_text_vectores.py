#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 检查FAISS索引中image_text文档的向量化状态
## 2. 分析image_text文档是否真的有对应的向量
## 3. 确认向量化存储的完整性
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

def check_image_text_vectors():
    """检查FAISS索引中image_text文档的向量化状态"""
    print("🔍 检查FAISS索引中image_text文档的向量化状态")
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
        
        # 检查FAISS索引状态
        print("\n🔍 1. 检查FAISS索引状态")
        print("-" * 40)
        
        # 获取FAISS索引信息
        index = vector_store.index
        print(f"FAISS索引类型: {type(index)}")
        print(f"FAISS索引维度: {index.d}")
        print(f"FAISS索引向量数量: {index.ntotal}")
        
        # 检查docstore
        docstore = vector_store.docstore
        docstore_dict = docstore._dict
        print(f"docstore文档数量: {len(docstore_dict)}")
        
        # 2. 分析image_text文档状态
        print("\n🔍 2. 分析image_text文档状态")
        print("-" * 40)
        
        image_text_docs = []
        image_docs = []
        text_docs = []
        table_docs = []
        
        for doc_id, doc in docstore_dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', '')
                if chunk_type == 'image_text':
                    image_text_docs.append((doc_id, doc))
                elif chunk_type == 'image':
                    image_docs.append((doc_id, doc))
                elif chunk_type == 'text':
                    text_docs.append((doc_id, doc))
                elif chunk_type == 'table':
                    table_docs.append((doc_id, doc))
        
        print(f"image_text文档数量: {len(image_text_docs)}")
        print(f"image文档数量: {len(image_docs)}")
        print(f"text文档数量: {len(text_docs)}")
        print(f"table文档数量: {len(table_docs)}")
        
        # 3. 检查image_text文档的详细信息
        print("\n�� 3. 检查image_text文档的详细信息")
        print("-" * 40)
        
        if image_text_docs:
            print("前5个image_text文档:")
            for i, (doc_id, doc) in enumerate(image_text_docs[:5]):
                metadata = doc.metadata
                print(f"  文档{i+1}: {doc_id}")
                print(f"    chunk_type: {metadata.get('chunk_type')}")
                print(f"    image_id: {metadata.get('image_id')}")
                print(f"    related_image_id: {metadata.get('related_image_id')}")
                print(f"    enhanced_description长度: {len(metadata.get('enhanced_description', ''))}")
                print(f"    page_content长度: {len(doc.page_content)}")
                print(f"    page_content前100字符: {doc.page_content[:100]}...")
                print()
        else:
            print("❌ 没有找到image_text文档")
        
        # 4. 检查向量索引的完整性
        print("\n🔍 4. 检查向量索引的完整性")
        print("-" * 40)
        
        # 检查FAISS索引中的向量数量是否与docstore匹配
        if index.ntotal != len(docstore_dict):
            print(f"⚠️ 向量数量不匹配!")
            print(f"  FAISS索引向量数量: {index.ntotal}")
            print(f"  docstore文档数量: {len(docstore_dict)}")
            print(f"  差异: {abs(index.ntotal - len(docstore_dict))}")
        else:
            print(f"✅ 向量数量匹配: {index.ntotal}")
        
        # 5. 测试image_text的向量搜索
        print("\n�� 5. 测试image_text的向量搜索")
        print("-" * 40)
        
        if image_text_docs:
            # 使用第一个image_text文档的enhanced_description进行搜索
            test_doc = image_text_docs[0][1]
            test_query = test_doc.page_content[:100]  # 使用前100字符作为查询
            
            print(f"测试查询: {test_query[:50]}...")
            
            try:
                # 无filter搜索
                results_no_filter = vector_store.similarity_search(test_query, k=5)
                print(f"无filter搜索: {len(results_no_filter)} 个结果")
                
                # 有filter搜索
                results_with_filter = vector_store.similarity_search(test_query, k=5, filter={'chunk_type': 'image_text'})
                print(f"Filter {{'chunk_type': 'image_text'}}: {len(results_with_filter)} 个结果")
                
                # 检查结果
                if results_with_filter:
                    print("Filter搜索结果:")
                    for i, result in enumerate(results_with_filter):
                        chunk_type = result.metadata.get('chunk_type', 'N/A')
                        print(f"  结果{i+1}: chunk_type={chunk_type}")
                else:
                    print("⚠️ Filter搜索没有返回结果")
                    
            except Exception as e:
                print(f"❌ 向量搜索失败: {e}")
        else:
            print("❌ 没有image_text文档可以测试")
        
        # 6. 检查向量存储的保存状态
        print("\n🔍 6. 检查向量存储的保存状态")
        print("-" * 40)
        
        # 检查向量数据库文件
        import glob
        faiss_files = glob.glob(os.path.join(vector_db_path, "*.faiss"))
        pkl_files = glob.glob(os.path.join(vector_db_path, "*.pkl"))
        
        print(f"FAISS索引文件: {len(faiss_files)} 个")
        for f in faiss_files:
            file_size = os.path.getsize(f) / (1024 * 1024)  # MB
            print(f"  {os.path.basename(f)}: {file_size:.2f} MB")
        
        print(f"元数据文件: {len(pkl_files)} 个")
        for f in pkl_files:
            file_size = os.path.getsize(f) / (1024 * 1024)  # MB
            print(f"  {os.path.basename(f)}: {file_size:.2f} MB")
        
        print("\n✅ image_text向量化状态检查完成！")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_image_text_vectors()