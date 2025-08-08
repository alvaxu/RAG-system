'''
程序说明：
## 1. 检查图片文档的完整结构
## 2. 分析图片文档的内容字段
'''

import pickle
import os
import json

def check_image_content():
    """检查图片文档的完整结构"""
    
    # 加载元数据
    metadata_file = 'central/vector_db/metadata.pkl'
    
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        print(f'总文档数: {len(metadata)}')
    except Exception as e:
        print(f'加载metadata.pkl失败: {e}')
        return
    
    # 查找图4的图片文档
    figure4_docs = []
    for doc in metadata:
        if doc.get('chunk_type') == 'image':
            caption = doc.get('img_caption', [''])
            caption_text = ' '.join(caption) if caption else ''
            if '图4' in caption_text:
                figure4_docs.append(doc)
    
    if not figure4_docs:
        print('未找到图4的图片文档')
        return
    
    print(f'找到 {len(figure4_docs)} 个图4图片文档')
    
    # 检查第一个图4文档的完整结构
    doc = figure4_docs[0]
    print('\n图4文档的完整结构:')
    print('=' * 50)
    
    for key, value in doc.items():
        if key == 'page_content':
            print(f'{key}: {repr(value)} (长度: {len(str(value))})')
        elif isinstance(value, list) and len(value) > 0:
            print(f'{key}: {value[:3]}... (共{len(value)}项)')
        else:
            print(f'{key}: {value}')
    
    print('\n' + '=' * 50)
    
    # 检查所有图片文档的page_content
    print('\n检查所有图片文档的page_content:')
    image_docs = [doc for doc in metadata if doc.get('chunk_type') == 'image']
    
    empty_content_count = 0
    non_empty_content_count = 0
    
    for i, doc in enumerate(image_docs[:5]):  # 只检查前5个
        content = doc.get('page_content', '')
        caption = doc.get('img_caption', ['无标题'])
        caption_text = caption[0] if caption else '无标题'
        
        print(f'{i+1}. {caption_text}')
        print(f'   page_content长度: {len(str(content))}')
        print(f'   page_content内容: {repr(content)[:100]}...')
        
        if not content or len(str(content).strip()) == 0:
            empty_content_count += 1
        else:
            non_empty_content_count += 1
        print()
    
    print(f'空内容图片文档: {empty_content_count}')
    print(f'有内容图片文档: {non_empty_content_count}')

if __name__ == '__main__':
    check_image_content() 