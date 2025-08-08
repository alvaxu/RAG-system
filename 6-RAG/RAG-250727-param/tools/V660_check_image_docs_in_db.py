'''
程序说明：

## 1. 检查向量数据库中的图片文档
## 2. 验证图片检索逻辑是否正确工作
'''

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.settings import Settings

def check_image_docs_in_db():
    """检查向量数据库中的图片文档"""
    
    print("🔍 检查向量数据库中的图片文档")
    print("=" * 60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        embeddings = DashScopeEmbeddings(dashscope_api_key=config.dashscope_api_key, model="text-embedding-v1")
        
        # 加载向量数据库
        vector_db_path = "./central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print(f"向量数据库加载成功")
        
        # 统计所有文档
        all_docs = list(vector_store.docstore._dict.values())
        print(f"总文档数: {len(all_docs)}")
        
        # 统计图片文档
        image_docs = [doc for doc in all_docs if doc.metadata.get('chunk_type') == 'image']
        print(f"图片文档数: {len(image_docs)}")
        
        if image_docs:
            print(f"\n📊 图片文档详情:")
            print("-" * 50)
            
            for i, doc in enumerate(image_docs[:10], 1):  # 只显示前10个
                caption = doc.metadata.get('img_caption', [])
                caption_text = ' '.join(caption) if caption else '无标题'
                doc_name = doc.metadata.get('document_name', '未知文档')
                image_id = doc.metadata.get('image_id', '无ID')
                
                print(f"{i}. 图片ID: {image_id}")
                print(f"   标题: {caption_text}")
                print(f"   文档: {doc_name}")
                print()
            
            if len(image_docs) > 10:
                print(f"... 还有 {len(image_docs) - 10} 个图片文档")
        
        # 测试图片检索
        print(f"\n🔍 测试图片检索:")
        print("-" * 50)
        
        # 测试不同的查询
        test_queries = [
            "图4：公司25Q1下游应用领域结构情况",
            "图4：中芯国际归母净利润情况概览",
            "图4",
            "图1：中芯国际全球部署示意图"
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            try:
                results = vector_store.similarity_search(query, k=5)
                image_results = [doc for doc in results if doc.metadata.get('chunk_type') == 'image']
                print(f"  找到 {len(image_results)} 个图片文档")
                
                for j, doc in enumerate(image_results, 1):
                    caption = doc.metadata.get('img_caption', [])
                    caption_text = ' '.join(caption) if caption else '无标题'
                    print(f"  {j}. {caption_text}")
                    
            except Exception as e:
                print(f"  检索失败: {e}")
        
        print(f"\n✅ 检查完成")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_image_docs_in_db()
