'''
程序说明：
## 1. 调试QA系统的向量数据库加载
## 2. 检查向量存储是否正确加载
## 3. 测试检索功能
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.enhanced_qa_system import load_enhanced_qa_system
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings

def debug_qa_system():
    """调试QA系统"""
    print("="*60)
    print("🔍 调试QA系统向量数据库加载")
    print("="*60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        print(f"✅ 配置加载成功")
        print(f"   向量数据库路径: {config.vector_db_dir}")
        print(f"   API密钥: {'已配置' if config.dashscope_api_key and config.dashscope_api_key != '你的DashScope API密钥' else '未配置'}")
        
        # 检查路径是否存在
        import os
        if os.path.exists(config.vector_db_dir):
            print(f"✅ 向量数据库路径存在")
            
            # 检查文件
            files = os.listdir(config.vector_db_dir)
            print(f"   目录内容: {files}")
        else:
            print(f"❌ 向量数据库路径不存在")
            return
        
        # 尝试直接加载向量存储
        print(f"\n🔍 尝试直接加载向量存储...")
        try:
            embeddings = DashScopeEmbeddings(
                dashscope_api_key=config.dashscope_api_key, 
                model='text-embedding-v4'
            )
            vector_store = FAISS.load_local(
                config.vector_db_dir, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            print(f"✅ 向量存储直接加载成功")
            print(f"   文档数量: {len(vector_store.docstore._dict)}")
            print(f"   索引大小: {vector_store.index.ntotal}")
            
            # 测试检索
            print(f"\n🔍 测试检索功能...")
            results = vector_store.similarity_search("中芯国际", k=3)
            print(f"✅ 检索成功，找到 {len(results)} 个结果")
            
            for i, doc in enumerate(results):
                print(f"   结果 {i+1}:")
                print(f"     内容: {doc.page_content[:100]}...")
                print(f"     元数据: {doc.metadata}")
            
        except Exception as e:
            print(f"❌ 向量存储直接加载失败: {e}")
            return
        
        # 测试QA系统加载
        print(f"\n🔍 测试QA系统加载...")
        try:
            qa_system = load_enhanced_qa_system(
                config.vector_db_dir, 
                config.dashscope_api_key, 
                None, 
                config.to_dict()
            )
            
            if qa_system:
                print(f"✅ QA系统加载成功")
                print(f"   向量存储: {'已加载' if qa_system.vector_store else '未加载'}")
                
                # 测试QA系统检索
                print(f"\n🔍 测试QA系统检索...")
                result = qa_system.answer_question("中芯国际", k=3)
                print(f"   检索结果: {result}")
                
            else:
                print(f"❌ QA系统加载失败")
                
        except Exception as e:
            print(f"❌ QA系统加载失败: {e}")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")

if __name__ == "__main__":
    debug_qa_system() 