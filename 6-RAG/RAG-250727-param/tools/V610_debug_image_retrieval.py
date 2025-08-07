'''
程序说明：
## 1. 调试图片检索过程
## 2. 分析为什么没有检索到图4
'''

import pickle
import os
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS

def debug_image_retrieval():
    """调试图片检索过程"""
    
    # 加载向量数据库
    db_path = 'central/vector_db'
    embeddings = DashScopeEmbeddings(dashscope_api_key="test", model="text-embedding-v1")
    
    try:
        vector_store = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        print(f'向量数据库加载成功，包含 {len(vector_store.docstore._dict)} 个文档')
    except Exception as e:
        print(f'加载向量数据库失败: {e}')
        return
    
    # 测试查询
    question = "请显示图4"
    
    print(f'\n测试查询: "{question}"')
    print('=' * 50)
    
    # 1. 测试普通检索
    print('\n1. 普通检索结果:')
    try:
        docs = vector_store.similarity_search(question, k=5)
        for i, doc in enumerate(docs):
            chunk_type = doc.metadata.get('chunk_type', 'text')
            caption = doc.metadata.get('img_caption', ['无标题'])
            caption_text = caption[0] if caption else '无标题'
            print(f'{i+1}. 类型: {chunk_type}, 标题: {caption_text}')
    except Exception as e:
        print(f'普通检索失败: {e}')
    
    # 2. 测试图片类型过滤检索
    print('\n2. 图片类型过滤检索结果:')
    try:
        image_docs = vector_store.similarity_search(
            question, 
            k=5,
            filter={"chunk_type": "image"}
        )
        for i, doc in enumerate(image_docs):
            caption = doc.metadata.get('img_caption', ['无标题'])
            caption_text = caption[0] if caption else '无标题'
            print(f'{i+1}. 标题: {caption_text}')
    except Exception as e:
        print(f'图片类型过滤检索失败: {e}')
    
    # 3. 测试特定文档过滤检索
    print('\n3. 特定文档过滤检索结果:')
    try:
        specific_docs = vector_store.similarity_search(
            question, 
            k=5,
            filter={"document_name": "【上海证券】中芯国际深度研究报告：晶圆制造龙头，领航国产芯片新征程"}
        )
        for i, doc in enumerate(specific_docs):
            chunk_type = doc.metadata.get('chunk_type', 'text')
            caption = doc.metadata.get('img_caption', ['无标题'])
            caption_text = caption[0] if caption else '无标题'
            print(f'{i+1}. 类型: {chunk_type}, 标题: {caption_text}')
    except Exception as e:
        print(f'特定文档过滤检索失败: {e}')
    
    # 4. 测试包含"图4"的检索
    print('\n4. 包含"图4"的检索结果:')
    try:
        figure4_docs = vector_store.similarity_search("图4", k=5)
        for i, doc in enumerate(figure4_docs):
            chunk_type = doc.metadata.get('chunk_type', 'text')
            caption = doc.metadata.get('img_caption', ['无标题'])
            caption_text = caption[0] if caption else '无标题'
            print(f'{i+1}. 类型: {chunk_type}, 标题: {caption_text}')
    except Exception as e:
        print(f'包含"图4"的检索失败: {e}')

if __name__ == '__main__':
    debug_image_retrieval() 