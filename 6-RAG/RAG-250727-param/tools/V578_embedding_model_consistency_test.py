'''
程序说明：
## 1. 验证数据库生成和查询时使用的嵌入模型一致性
## 2. 检查向量数据库的嵌入维度
## 3. 测试不同嵌入模型的兼容性
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
import numpy as np

def test_embedding_model_consistency():
    """测试嵌入模型一致性"""
    print("="*60)
    print("🔍 验证嵌入模型一致性")
    print("="*60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        print(f"✅ 配置加载成功")
        
        # 获取配置中的嵌入模型
        text_embedding_model = config.to_dict().get('vector_store', {}).get('text_embedding_model', 'text-embedding-v4')
        print(f"   配置的文本嵌入模型: {text_embedding_model}")
        
        # 检查向量数据库路径
        vector_db_path = config.vector_db_dir
        if not os.path.exists(vector_db_path):
            print(f"❌ 向量数据库路径不存在: {vector_db_path}")
            return
        
        print(f"✅ 向量数据库路径存在: {vector_db_path}")
        
        # 测试不同嵌入模型
        models_to_test = [
            'text-embedding-v4',
            'text-embedding-v3',
            'text-embedding-v2',
            'text-embedding-v1'
        ]
        
        for model in models_to_test:
            print(f"\n🔍 测试模型: {model}")
            try:
                # 创建嵌入模型
                embeddings = DashScopeEmbeddings(
                    dashscope_api_key=config.dashscope_api_key, 
                    model=model
                )
                
                # 尝试加载向量存储
                vector_store = FAISS.load_local(
                    vector_db_path, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                
                print(f"✅ 成功加载向量存储")
                print(f"   文档数量: {len(vector_store.docstore._dict)}")
                print(f"   索引大小: {vector_store.index.ntotal}")
                print(f"   索引维度: {vector_store.index.d}")
                
                # 测试检索
                results = vector_store.similarity_search("中芯国际", k=3)
                print(f"✅ 检索成功，找到 {len(results)} 个结果")
                
                # 检查第一个结果的嵌入维度
                if results:
                    # 获取第一个文档的嵌入向量
                    doc_id = list(vector_store.docstore._dict.keys())[0]
                    embedding = vector_store.index.reconstruct(doc_id)
                    print(f"   嵌入向量维度: {len(embedding)}")
                
                # 如果当前模型与配置模型一致，标记为推荐
                if model == text_embedding_model:
                    print(f"   🎯 这是配置中指定的模型")
                
            except Exception as e:
                print(f"❌ 模型 {model} 加载失败: {e}")
        
        # 特别测试配置中的模型
        print(f"\n🎯 特别测试配置中的模型: {text_embedding_model}")
        try:
            embeddings = DashScopeEmbeddings(
                dashscope_api_key=config.dashscope_api_key, 
                model=text_embedding_model
            )
            
            vector_store = FAISS.load_local(
                vector_db_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            
            print(f"✅ 配置模型加载成功")
            print(f"   文档数量: {len(vector_store.docstore._dict)}")
            print(f"   索引维度: {vector_store.index.d}")
            
            # 测试检索
            results = vector_store.similarity_search("中芯国际", k=3)
            print(f"✅ 配置模型检索成功，找到 {len(results)} 个结果")
            
            if results:
                for i, doc in enumerate(results):
                    print(f"   结果 {i+1}: {doc.page_content[:50]}...")
            
        except Exception as e:
            print(f"❌ 配置模型测试失败: {e}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding_model_consistency() 