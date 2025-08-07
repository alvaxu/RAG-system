'''
程序说明：
## 1. 检查图4的向量化情况
## 2. 分析图4文档的完整信息
'''

import pickle
import os
import numpy as np

def check_figure4_vector():
    """检查图4的向量化情况"""
    
    # 加载元数据
    metadata_file = 'central/vector_db/metadata.pkl'
    index_file = 'central/vector_db/index.pkl'
    
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        print(f'总文档数: {len(metadata)}')
    except Exception as e:
        print(f'加载metadata.pkl失败: {e}')
        return
    
    # 查找图4文档
    figure4_docs = []
    for i, doc in enumerate(metadata):
        if doc.get('chunk_type') == 'image':
            caption = doc.get('img_caption', [''])
            caption_text = ' '.join(caption) if caption else ''
            if '图4' in caption_text:
                figure4_docs.append((i, doc))
    
    if not figure4_docs:
        print('未找到图4文档')
        return
    
    print(f'找到 {len(figure4_docs)} 个图4文档')
    
    # 检查图4文档的详细信息
    for idx, (doc_idx, doc) in enumerate(figure4_docs):
        print(f'\n图4文档 #{idx+1} (索引: {doc_idx}):')
        print('=' * 50)
        
        # 基本信息
        print(f'文档索引: {doc_idx}')
        print(f'图片ID: {doc.get("image_id", "无ID")}')
        print(f'文档名称: {doc.get("document_name", "未知")}')
        print(f'页码: {doc.get("page_number", "未知")}')
        
        # 标题和描述
        caption = doc.get('img_caption', [''])
        caption_text = ' '.join(caption) if caption else ''
        print(f'图片标题: {caption_text}')
        
        enhanced_desc = doc.get('enhanced_description', '')
        print(f'增强描述: {enhanced_desc}')
        
        # 检查向量化信息
        semantic_features = doc.get('semantic_features', {})
        if semantic_features:
            print(f'向量维度: {semantic_features.get("embedding_dimension", "未知")}')
            print(f'向量范数: {semantic_features.get("embedding_norm", "未知")}')
            print(f'向量均值: {semantic_features.get("embedding_mean", "未知")}')
            print(f'向量标准差: {semantic_features.get("embedding_std", "未知")}')
        
        # 检查page_content
        page_content = doc.get('page_content', '')
        print(f'page_content长度: {len(str(page_content))}')
        print(f'page_content内容: {repr(page_content)}')
        
        print()
    
    # 检查所有图片文档的标题
    print('\n所有图片文档的标题:')
    print('=' * 50)
    image_docs = [doc for doc in metadata if doc.get('chunk_type') == 'image']
    
    for i, doc in enumerate(image_docs):
        caption = doc.get('img_caption', ['无标题'])
        caption_text = caption[0] if caption else '无标题'
        print(f'{i+1:2d}. {caption_text}')
    
    # 检查向量索引
    try:
        with open(index_file, 'rb') as f:
            index = pickle.load(f)
        print(f'\n向量索引信息:')
        print(f'索引类型: {type(index)}')
        if hasattr(index, 'ntotal'):
            print(f'总向量数: {index.ntotal}')
        if hasattr(index, 'd'):
            print(f'向量维度: {index.d}')
    except Exception as e:
        print(f'加载向量索引失败: {e}')

if __name__ == '__main__':
    check_figure4_vector() 