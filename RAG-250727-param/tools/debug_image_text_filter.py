'''
程序说明：
## 1. 专门调试image_text filter搜索问题
## 2. 检查为什么image_text文档无法通过filter搜索到
## 3. 分析filter机制和文档类型标记
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key


def debug_image_text_filter():
    """调试image_text filter搜索问题"""
    print("🔍 调试image_text filter搜索问题")
    print("=" * 80)
    
    try:
        # 1. 初始化
        api_key = get_dashscope_api_key()
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        vector_db_path = "../central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print("✅ 向量数据库加载成功")
        
        # 2. 检查数据库中的image_text文档
        print("\n📊 检查数据库中的image_text文档")
        if hasattr(vector_store, 'docstore') and hasattr(vector_store.docstore, '_dict'):
            docs = vector_store.docstore._dict
            print(f"总文档数量: {len(docs)}")
            
            # 统计文档类型
            chunk_types = {}
            image_text_docs = []
            
            for doc_id, doc in docs.items():
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                if chunk_type == 'image_text':
                    image_text_docs.append((doc_id, doc))
            
            print("文档类型分布:")
            for chunk_type, count in sorted(chunk_types.items()):
                print(f"  - {chunk_type}: {count} 个")
            
            print(f"\n找到 {len(image_text_docs)} 个image_text文档")
            
            # 检查前几个image_text文档的内容
            if image_text_docs:
                print("\n📋 前5个image_text文档内容:")
                for i, (doc_id, doc) in enumerate(image_text_docs[:5]):
                    print(f"\n{i+1}. 文档ID: {doc_id}")
                    print(f"   类型: {doc.metadata.get('chunk_type')}")
                    print(f"   内容: {doc.page_content[:200]}...")
                    
                    # 检查是否包含目标内容
                    if "图4：中芯国际归母净利润情况概览" in doc.page_content:
                        print("   ✅ 包含目标内容！")
                    else:
                        print("   ❌ 不包含目标内容")
        
        # 3. 测试filter搜索
        query = "图4：中芯国际归母净利润情况概览"
        print(f"\n🔍 测试查询: '{query}'")
        
        # 3.1 不使用filter的搜索
        print("\n📋 步骤1：不使用filter的搜索（k=100）")
        all_results = vector_store.similarity_search(query, k=100)
        print(f"搜索到 {len(all_results)} 个结果")
        
        # 查找包含目标内容的文档
        target_docs = []
        for i, doc in enumerate(all_results):
            if "图4：中芯国际归母净利润情况概览" in doc.page_content:
                target_docs.append((i+1, doc))
        
        print(f"找到 {len(target_docs)} 个包含目标内容的文档:")
        for rank, doc in target_docs:
            print(f"  排名{rank}: 类型={doc.metadata.get('chunk_type')}, 内容={doc.page_content[:100]}...")
        
        # 3.2 使用filter搜索image_text
        print(f"\n📋 步骤2：使用filter搜索image_text（k=100）")
        try:
            image_text_results = vector_store.similarity_search(
                query, 
                k=100,
                filter={'chunk_type': 'image_text'}
            )
            print(f"filter搜索到 {len(image_text_results)} 个image_text结果")
            
            # 检查filter结果中是否包含目标内容
            filter_target_found = False
            for i, doc in enumerate(image_text_results):
                if "图4：中芯国际归母净利润情况概览" in doc.page_content:
                    filter_target_found = True
                    print(f"✅ 在filter结果中找到目标文档！位置: 第{i+1}位")
                    print(f"   内容: {doc.page_content[:200]}...")
                    break
            
            if not filter_target_found:
                print("❌ 在filter结果中没有找到目标文档")
                
        except Exception as e:
            print(f"❌ filter搜索失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
        
        # 4. 测试不同的filter条件
        print(f"\n📋 步骤3：测试不同的filter条件")
        
        # 4.1 搜索text类型
        try:
            text_results = vector_store.similarity_search(
                query, 
                k=50,
                filter={'chunk_type': 'text'}
            )
            print(f"filter搜索text类型: {len(text_results)} 个结果")
            
            for i, doc in enumerate(text_results):
                if "图4：中芯国际归母净利润情况概览" in doc.page_content:
                    print(f"✅ 在text类型中找到目标文档！位置: 第{i+1}位")
                    break
                    
        except Exception as e:
            print(f"❌ text filter搜索失败: {e}")
        
        # 4.2 搜索所有类型
        try:
            all_types_results = vector_store.similarity_search(
                query, 
                k=50,
                filter={'chunk_type': ['image_text', 'text', 'image']}
            )
            print(f"filter搜索所有相关类型: {len(all_types_results)} 个结果")
            
        except Exception as e:
            print(f"❌ 多类型filter搜索失败: {e}")
        
        # 5. 分析问题
        print("\n" + "=" * 80)
        print("🎯 问题分析")
        print("=" * 80)
        
        if target_docs:
            print("✅ 目标文档确实存在于数据库中")
            print("❌ 但是无法通过image_text filter搜索到")
            print("\n可能的原因:")
            print("1. 文档类型标记错误 - 应该标记为image_text但实际是text")
            print("2. Filter机制有问题 - FAISS的filter功能可能不工作")
            print("3. 查询内容匹配问题 - 虽然包含关键词但相似度不够")
            
            print("\n建议解决方案:")
            print("1. 检查文档类型标记，确保图表相关内容标记为image_text")
            print("2. 在image_engine中添加对text类型文档的搜索")
            print("3. 或者扩大搜索范围，不使用filter")
        else:
            print("❌ 目标文档不存在于数据库中")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_image_text_filter()
