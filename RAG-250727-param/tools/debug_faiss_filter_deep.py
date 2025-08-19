'''
程序说明：
## 1. 深入调试FAISS filter机制
## 2. 检查为什么filter对image_text类型不工作
## 3. 分析FAISS索引配置和filter支持
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key


def debug_faiss_filter_deep():
    """深入调试FAISS filter机制"""
    print("🔍 深入调试FAISS filter机制")
    print("=" * 80)
    
    try:
        # 1. 初始化
        api_key = get_dashscope_api_key()
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        vector_db_path = "../central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print("✅ 向量数据库加载成功")
        
        # 2. 检查FAISS索引信息
        print("\n📊 检查FAISS索引信息")
        if hasattr(vector_store, 'index'):
            faiss_index = vector_store.index
            print(f"FAISS索引类型: {type(faiss_index).__name__}")
            print(f"索引维度: {faiss_index.d}")
            print(f"索引大小: {faiss_index.ntotal}")
            
            # 检查是否有filter相关属性
            print("\n🔍 检查filter相关属性:")
            for attr in dir(faiss_index):
                if 'filter' in attr.lower() or 'metadata' in attr.lower():
                    try:
                        value = getattr(faiss_index, attr)
                        print(f"  {attr}: {value}")
                    except:
                        print(f"  {attr}: <无法获取>")
        else:
            print("❌ 无法获取FAISS索引信息")
        
        # 3. 检查文档元数据结构
        print(f"\n📋 检查文档元数据结构")
        if hasattr(vector_store, 'docstore') and hasattr(vector_store.docstore, '_dict'):
            docs = vector_store.docstore._dict
            sample_docs = list(docs.values())[:3]  # 取前3个文档作为样本
            
            for i, doc in enumerate(sample_docs):
                print(f"\n文档 {i+1}:")
                print(f"  类型: {type(doc)}")
                print(f"  属性: {dir(doc)}")
                if hasattr(doc, 'metadata'):
                    print(f"  元数据: {doc.metadata}")
                    print(f"  元数据类型: {type(doc.metadata)}")
                    if doc.metadata:
                        for key, value in doc.metadata.items():
                            print(f"    {key}: {value} (类型: {type(value)})")
                else:
                    print("  无metadata属性")
        
        # 4. 测试不同的filter语法
        print(f"\n🧪 测试不同的filter语法")
        query = "图4：中芯国际归母净利润情况概览"
        
        # 4.1 测试基本filter
        print("\n📋 测试1：基本filter语法")
        try:
            results1 = vector_store.similarity_search(
                query, k=10, filter={'chunk_type': 'image_text'}
            )
            print(f"  结果数量: {len(results1)}")
        except Exception as e:
            print(f"  失败: {e}")
        
        # 4.2 测试字符串filter
        print("\n📋 测试2：字符串filter语法")
        try:
            results2 = vector_store.similarity_search(
                query, k=10, filter="chunk_type == 'image_text'"
            )
            print(f"  结果数量: {len(results2)}")
        except Exception as e:
            print(f"  失败: {e}")
        
        # 4.3 测试列表filter
        print("\n📋 测试3：列表filter语法")
        try:
            results3 = vector_store.similarity_search(
                query, k=10, filter={'chunk_type': ['image_text']}
            )
            print(f"  结果数量: {len(results3)}")
        except Exception as e:
            print(f"  失败: {e}")
        
        # 4.4 测试无filter
        print("\n📋 测试4：无filter")
        try:
            results4 = vector_store.similarity_search(query, k=10)
            print(f"  结果数量: {len(results4)}")
            
            # 检查返回的文档类型
            image_text_count = 0
            for doc in results4:
                if hasattr(doc, 'metadata') and doc.metadata:
                    chunk_type = doc.metadata.get('chunk_type')
                    if chunk_type == 'image_text':
                        image_text_count += 1
            
            print(f"  其中image_text类型: {image_text_count} 个")
            
        except Exception as e:
            print(f"  失败: {e}")
        
        # 5. 检查LangChain版本和配置
        print(f"\n📦 检查LangChain版本和配置")
        try:
            import langchain_community
            print(f"LangChain版本: {langchain_community.__version__}")
        except:
            print("无法获取LangChain版本")
        
        # 6. 分析问题
        print("\n" + "=" * 80)
        print("🎯 问题分析")
        print("=" * 80)
        
        print("\n可能的原因:")
        print("1. FAISS索引不支持filter功能")
        print("2. Filter语法不正确")
        print("3. 文档元数据格式问题")
        print("4. LangChain版本兼容性问题")
        print("5. 向量数据库构建时的配置问题")
        
        print("\n建议下一步:")
        print("1. 检查FAISS索引是否支持filter")
        print("2. 尝试不同的filter语法")
        print("3. 检查文档元数据格式")
        print("4. 考虑升级或降级LangChain版本")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_faiss_filter_deep()
