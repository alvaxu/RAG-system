"""
程序说明：
## 1. 改进的检索策略，确保文档来源的平衡
## 2. 不仅按chunk_type平衡，还要按document_name平衡
## 3. 测试新的检索策略效果
"""

import os
import json
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.schema import Document

def improved_retrieval_strategy(vector_store: FAISS, question: str, k: int = 10) -> List[Document]:
    """
    改进的检索策略
    :param vector_store: 向量存储
    :param question: 查询问题
    :param k: 检索数量
    :return: 检索到的文档
    """
    print(f"🔍 改进检索策略测试: '{question}'")
    
    # 第一步：获取所有文档的文档名称
    doc_names = set()
    for doc in vector_store.docstore._dict.values():
        doc_name = doc.metadata.get('document_name', '未知文档')
        doc_names.add(doc_name)
    
    print(f"📚 可用文档: {list(doc_names)}")
    
    # 第二步：为每个文档分配检索配额
    total_docs = len(doc_names)
    base_k_per_doc = max(1, k // total_docs)  # 每个文档至少检索1个
    remaining_k = k - (base_k_per_doc * total_docs)
    
    print(f"📊 检索配额: 每个文档 {base_k_per_doc} 个，剩余 {remaining_k} 个")
    
    # 第三步：分别从每个文档检索
    all_docs = []
    doc_results = {}
    
    for doc_name in doc_names:
        try:
            # 为每个文档检索指定数量的文档
            docs = vector_store.similarity_search(
                question, 
                k=base_k_per_doc,
                filter={"document_name": doc_name}
            )
            doc_results[doc_name] = len(docs)
            all_docs.extend(docs)
            print(f"  {doc_name}: 检索到 {len(docs)} 个文档")
        except Exception as e:
            print(f"  {doc_name}: 检索失败 - {e}")
            doc_results[doc_name] = 0
    
    # 第四步：如果还有剩余配额，按相似度补充
    if remaining_k > 0 and len(all_docs) < k:
        try:
            # 获取所有文档，按相似度排序
            all_available_docs = vector_store.similarity_search(question, k=k*2)
            
            # 过滤掉已经选中的文档
            selected_doc_ids = {doc.page_content for doc in all_docs}
            additional_docs = []
            
            for doc in all_available_docs:
                if doc.page_content not in selected_doc_ids and len(additional_docs) < remaining_k:
                    additional_docs.append(doc)
                    selected_doc_ids.add(doc.page_content)
            
            all_docs.extend(additional_docs)
            print(f"  📈 补充检索: 新增 {len(additional_docs)} 个文档")
            
        except Exception as e:
            print(f"  ❌ 补充检索失败: {e}")
    
    # 第五步：统计最终结果
    final_doc_sources = {}
    for doc in all_docs[:k]:
        doc_name = doc.metadata.get('document_name', '未知文档')
        final_doc_sources[doc_name] = final_doc_sources.get(doc_name, 0) + 1
    
    print(f"📋 最终检索结果分布: {final_doc_sources}")
    print(f"📊 总计检索到: {len(all_docs[:k])} 个文档")
    
    return all_docs[:k]

def test_improved_retrieval():
    """
    测试改进的检索策略
    """
    print("=== 测试改进的检索策略 ===")
    
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
        
        # 测试查询
        test_queries = [
            "中芯国际的主要业务",
            "中芯国际的产能利用率",
            "中芯国际的毛利率",
            "中芯国际的市场地位",
            "中芯国际的财务表现"
        ]
        
        for query in test_queries:
            print(f"\n{'='*50}")
            improved_retrieval_strategy(vector_store, query, k=8)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_improved_retrieval() 