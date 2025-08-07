'''
程序说明：
## 1. 检查向量数据库中的图片文档
## 2. 分析图4相关的图片文档是否存在
'''

import pickle
import os
import json

def check_image_documents():
    """检查向量数据库中的图片文档"""
    
    # 检查向量数据库文件
    db_path = 'central/vector_db'
    index_file = os.path.join(db_path, 'index.pkl')
    metadata_file = os.path.join(db_path, 'metadata.pkl')
    
    print('检查向量数据库文件是否存在:')
    print(f'index.pkl: {os.path.exists(index_file)}')
    print(f'metadata.pkl: {os.path.exists(metadata_file)}')
    
    if not os.path.exists(metadata_file):
        print('错误: metadata.pkl 文件不存在')
        return
    
    # 加载元数据
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        print(f'\n总文档数: {len(metadata)}')
    except Exception as e:
        print(f'加载metadata.pkl失败: {e}')
        return
    
    # 检查图片类型文档
    image_docs = [doc for doc in metadata if doc.get('chunk_type') == 'image']
    print(f'图片文档总数: {len(image_docs)}')
    
    if len(image_docs) == 0:
        print('警告: 没有找到图片类型的文档')
        return
    
    # 显示前10个图片文档的信息
    print('\n前10个图片文档的信息:')
    for i, doc in enumerate(image_docs[:10]):
        caption = doc.get('img_caption', ['无标题'])
        caption_text = caption[0] if caption else '无标题'
        document_name = doc.get('document_name', '未知文档')
        page_number = doc.get('page_number', '未知页码')
        
        print(f'{i+1}. 标题: {caption_text}')
        print(f'   文档: {document_name}')
        print(f'   页码: {page_number}')
        print(f'   图片ID: {doc.get("image_id", "无ID")}')
        print()
    
    # 查找图4相关的图片
    print('查找图4相关的图片:')
    figure4_docs = []
    for doc in image_docs:
        caption = doc.get('img_caption', [''])
        caption_text = ' '.join(caption) if caption else ''
        
        if '图4' in caption_text or '图表4' in caption_text:
            figure4_docs.append(doc)
    
    print(f'找到 {len(figure4_docs)} 个图4相关的图片文档')
    
    for i, doc in enumerate(figure4_docs):
        caption = doc.get('img_caption', ['无标题'])
        caption_text = caption[0] if caption else '无标题'
        document_name = doc.get('document_name', '未知文档')
        page_number = doc.get('page_number', '未知页码')
        
        print(f'{i+1}. 标题: {caption_text}')
        print(f'   文档: {document_name}')
        print(f'   页码: {page_number}')
        print(f'   图片ID: {doc.get("image_id", "无ID")}')
        print()
    
    # 查找中芯国际归母净利润相关的图片
    print('查找中芯国际归母净利润相关的图片:')
    profit_docs = []
    for doc in image_docs:
        caption = doc.get('img_caption', [''])
        caption_text = ' '.join(caption) if caption else ''
        
        if '归母净利润' in caption_text or '净利润' in caption_text:
            profit_docs.append(doc)
    
    print(f'找到 {len(profit_docs)} 个净利润相关的图片文档')
    
    for i, doc in enumerate(profit_docs):
        caption = doc.get('img_caption', ['无标题'])
        caption_text = caption[0] if caption else '无标题'
        document_name = doc.get('document_name', '未知文档')
        page_number = doc.get('page_number', '未知页码')
        
        print(f'{i+1}. 标题: {caption_text}')
        print(f'   文档: {document_name}')
        print(f'   页码: {page_number}')
        print(f'   图片ID: {doc.get("image_id", "无ID")}')
        print()

if __name__ == '__main__':
    check_image_documents() 