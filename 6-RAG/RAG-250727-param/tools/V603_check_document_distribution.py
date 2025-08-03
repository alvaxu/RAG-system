"""
程序说明：
## 1. 检查向量数据库中两个文档的分布情况
## 2. 分析为什么第二个文档没有被使用
## 3. 验证文档检索的平衡性
"""

import os
import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings

def check_document_distribution():
    """
    检查向量数据库中文档的分布情况
    """
    print("=== 检查向量数据库文档分布 ===")
    
    # 配置API密钥
    api_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
    if not api_key or api_key == '你的APIKEY':
        print("❌ 未配置有效的DashScope API密钥")
        return
    
    embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model="text-embedding-v1")
    
    # 加载向量数据库
    vector_db_path = "central/vector_db"
    if not os.path.exists(vector_db_path):
        print(f"❌ 向量数据库路径不存在: {vector_db_path}")
        return
    
    try:
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        print(f"✅ 向量数据库加载成功")
        
        # 统计文档分布
        doc_sources = {}
        chunk_types = {}
        
        for doc_id, doc in vector_store.docstore._dict.items():
            doc_name = doc.metadata.get('document_name', '未知文档')
            chunk_type = doc.metadata.get('chunk_type', 'text')
            
            if doc_name not in doc_sources:
                doc_sources[doc_name] = {'text': 0, 'image': 0, 'table': 0, 'total': 0}
            
            doc_sources[doc_name][chunk_type] += 1
            doc_sources[doc_name]['total'] += 1
            
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        print(f"\n📊 文档分布统计:")
        print(f"总文档数: {len(vector_store.docstore._dict)}")
        print(f"文档类型分布: {chunk_types}")
        
        print(f"\n📋 各文档详细统计:")
        for doc_name, stats in doc_sources.items():
            print(f"  {doc_name}:")
            print(f"    总chunks: {stats['total']}")
            print(f"    文本chunks: {stats['text']}")
            print(f"    图片chunks: {stats['image']}")
            print(f"    表格chunks: {stats['table']}")
        
        # 测试检索
        print(f"\n🔍 检索测试:")
        test_queries = [
            "中芯国际的主要业务",
            "中芯国际的产能利用率",
            "中芯国际的毛利率",
            "中芯国际的市场地位"
        ]
        
        for query in test_queries:
            print(f"\n查询: '{query}'")
            docs = vector_store.similarity_search(query, k=5)
            
            # 统计检索结果中的文档来源
            result_sources = {}
            for doc in docs:
                doc_name = doc.metadata.get('document_name', '未知文档')
                result_sources[doc_name] = result_sources.get(doc_name, 0) + 1
            
            print(f"  检索结果分布: {result_sources}")
        
        # 检查是否有第二个文档
        second_doc_name = "【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评"
        if second_doc_name in doc_sources:
            print(f"\n✅ 第二个文档存在于向量数据库中")
            print(f"  文档chunks数: {doc_sources[second_doc_name]['total']}")
        else:
            print(f"\n❌ 第二个文档不存在于向量数据库中")
            
            # 检查是否有类似的文档名
            similar_docs = [name for name in doc_sources.keys() if "中原证券" in name]
            if similar_docs:
                print(f"  发现类似文档: {similar_docs}")
            else:
                print(f"  没有发现中原证券相关的文档")
        
    except Exception as e:
        print(f"❌ 加载向量数据库失败: {e}")

if __name__ == "__main__":
    check_document_distribution() 