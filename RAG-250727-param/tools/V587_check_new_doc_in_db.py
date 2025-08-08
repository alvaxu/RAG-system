"""
程序说明：
## 1. 检查新增文档是否在向量数据库中
## 2. 验证文档检索功能是否正常
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.settings import Settings

def check_new_doc_in_db():
    """检查新增文档是否在向量数据库中"""
    print("🔍 检查新增文档是否在向量数据库中...")
    print("=" * 60)
    
    # 加载配置
    settings = Settings.load_from_file("config.json")
    api_key = settings.dashscope_api_key
    
    if not api_key or api_key == '你的APIKEY':
        print("❌ 错误: 未配置DashScope API密钥")
        return
    
    # 加载向量数据库
    vector_db_path = "./central/vector_db"
    
    try:
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model="text-embedding-v1")
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print("✅ 向量数据库加载成功")
        print(f"📊 总文档数: {len(vector_store.docstore._dict)}")
        
        # 检查新增文档
        target_doc_name = "【上海证券】中芯国际深度研究报告：晶圆制造龙头，领航国产芯片新征程"
        
        print(f"\n🔍 查找文档: {target_doc_name}")
        print("-" * 60)
        
        found_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            doc_name = doc.metadata.get('document_name', '')
            if target_doc_name in doc_name:
                found_docs.append({
                    'id': doc_id,
                    'content': doc.page_content[:100] + "...",
                    'metadata': doc.metadata
                })
        
        print(f"📋 找到 {len(found_docs)} 个相关文档")
        
        if found_docs:
            print("\n📄 文档详情:")
            for i, doc in enumerate(found_docs[:5], 1):
                print(f"  文档 {i}:")
                print(f"    ID: {doc['id']}")
                print(f"    内容: {doc['content']}")
                print(f"    类型: {doc['metadata'].get('chunk_type', 'text')}")
                print(f"    页码: {doc['metadata'].get('page_number', '未知')}")
                print()
        else:
            print("❌ 未找到新增文档")
        
        # 测试检索功能
        print("\n🧪 测试检索功能...")
        print("-" * 40)
        
        test_queries = [
            "中芯国际产能利用率",
            "晶圆制造",
            "上海证券",
            "投资建议"
        ]
        
        for query in test_queries:
            print(f"\n🔍 查询: {query}")
            try:
                results = vector_store.similarity_search(query, k=3)
                print(f"✅ 找到 {len(results)} 个结果")
                
                for j, result in enumerate(results, 1):
                    doc_name = result.metadata.get('document_name', '未知文档')
                    chunk_type = result.metadata.get('chunk_type', 'text')
                    print(f"   结果 {j}: {doc_name} ({chunk_type})")
                    print(f"   内容: {result.page_content[:80]}...")
                    
            except Exception as e:
                print(f"❌ 检索失败: {e}")
        
    except Exception as e:
        print(f"❌ 加载向量数据库失败: {e}")

if __name__ == "__main__":
    check_new_doc_in_db() 