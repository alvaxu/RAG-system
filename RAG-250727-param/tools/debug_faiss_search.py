'''
程序说明：
## 1. 专门调试FAISS搜索问题
## 2. 查看"图4：中芯国际归母净利润情况概览"是否在FAISS搜索结果中
## 3. 分析FAISS搜索的原始结果
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key


def debug_faiss_search():
    """调试FAISS搜索问题"""
    print("🔍 调试FAISS搜索问题")
    print("=" * 80)
    
    try:
        # 1. 初始化
        api_key = get_dashscope_api_key()
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        vector_db_path = "../central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print("✅ 向量数据库加载成功")
        
        # 2. 测试查询
        query = "图4：中芯国际归母净利润情况概览"
        print(f"\n🔍 测试查询: '{query}'")
        
        # 3. 原始FAISS搜索（不使用filter）
        print("\n📋 步骤1：原始FAISS搜索（k=100，无filter）")
        all_results = vector_store.similarity_search(query, k=100)
        print(f"搜索到 {len(all_results)} 个结果")
        
        # 查找目标文档
        target_found = False
        target_position = -1
        
        for i, doc in enumerate(all_results):
            if "图4：中芯国际归母净利润情况概览" in doc.page_content:
                target_found = True
                target_position = i + 1
                print(f"✅ 找到目标文档！位置: 第{target_position}位")
                print(f"   内容: {doc.page_content[:200]}...")
                print(f"   类型: {doc.metadata.get('chunk_type', 'unknown')}")
                break
        
        if not target_found:
            print("❌ 在前100个结果中没有找到目标文档")
            
            # 搜索更多结果
            print("\n📋 步骤2：扩大搜索范围（k=300）")
            more_results = vector_store.similarity_search(query, k=300)
            print(f"搜索到 {len(more_results)} 个结果")
            
            for i, doc in enumerate(more_results):
                if "图4：中芯国际归母净利润情况概览" in doc.page_content:
                    target_found = True
                    target_position = i + 1
                    print(f"✅ 找到目标文档！位置: 第{target_position}位")
                    print(f"   内容: {doc.page_content[:200]}...")
                    print(f"   类型: {doc.metadata.get('chunk_type', 'unknown')}")
                    break
        
        # 4. 使用filter搜索image_text
        print(f"\n📋 步骤3：使用filter搜索image_text（k=100）")
        try:
            image_text_results = vector_store.similarity_search(
                query, 
                k=100,
                filter={'chunk_type': 'image_text'}
            )
            print(f"filter搜索到 {len(image_text_results)} 个image_text结果")
            
            # 查找目标文档
            for i, doc in enumerate(image_text_results):
                if "图4：中芯国际归母净利润情况概览" in doc.page_content:
                    print(f"✅ 在filter结果中找到目标文档！位置: 第{i+1}位")
                    print(f"   内容: {doc.page_content[:200]}...")
                    break
            else:
                print("❌ 在filter结果中没有找到目标文档")
                
        except Exception as e:
            print(f"❌ filter搜索失败: {e}")
        
        # 5. 检查文档是否存在于数据库中
        print(f"\n📋 步骤4：检查目标文档是否存在于数据库中")
        if hasattr(vector_store, 'docstore') and hasattr(vector_store.docstore, '_dict'):
            docs = vector_store.docstore._dict
            found_in_db = False
            
            for doc_id, doc in docs.items():
                if "图4：中芯国际归母净利润情况概览" in doc.page_content:
                    found_in_db = True
                    print(f"✅ 目标文档存在于数据库中")
                    print(f"   文档ID: {doc_id}")
                    print(f"   类型: {doc.metadata.get('chunk_type', 'unknown')}")
                    print(f"   内容: {doc.page_content[:200]}...")
                    break
            
            if not found_in_db:
                print("❌ 目标文档不存在于数据库中")
        
        print("\n" + "=" * 80)
        print("🎯 调试总结")
        print("=" * 80)
        
        if target_found:
            print(f"✅ 目标文档存在，排名: 第{target_position}位")
            if target_position > 60:  # max_results * 2 = 30 * 2 = 60
                print("⚠️ 问题：目标文档排名太靠后，需要增加搜索数量")
            else:
                print("⚠️ 问题：目标文档排名合理，问题可能在其他地方")
        else:
            print("❌ 目标文档不存在或FAISS搜索有问题")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_faiss_search()
