#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查向量数据库中的所有图片文档
特别关注图4的情况
"""

import os
import sys
import pickle
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def check_vector_db():
    """检查向量数据库中的所有图片文档"""
    
    # 向量数据库路径
    vector_db_path = "./central/vector_db"
    
    print("检查向量数据库文件是否存在:")
    print(f"index.pkl: {os.path.exists(os.path.join(vector_db_path, 'index.pkl'))}")
    print(f"metadata.pkl: {os.path.exists(os.path.join(vector_db_path, 'metadata.pkl'))}")
    print()
    
    try:
        # 加载向量数据库
        with open(os.path.join(vector_db_path, 'index.pkl'), 'rb') as f:
            index_data = pickle.load(f)
        
        with open(os.path.join(vector_db_path, 'metadata.pkl'), 'rb') as f:
            metadata_data = pickle.load(f)
        
        print(f"向量数据库加载成功")
        print(f"文档总数: {len(metadata_data)}")
        print()
        
        # 统计图片文档
        image_docs = []
        text_docs = []
        
        # 检查metadata_data的结构
        print(f"metadata_data类型: {type(metadata_data)}")
        if isinstance(metadata_data, list):
            print(f"metadata_data长度: {len(metadata_data)}")
            # 如果是列表，直接遍历
            for i, metadata in enumerate(metadata_data):
                chunk_type = metadata.get('chunk_type', 'text')
                if chunk_type == 'image':
                    image_docs.append((i, metadata))
                else:
                    text_docs.append((i, metadata))
        else:
            # 如果是字典，使用items()
            for doc_id, metadata in metadata_data.items():
                chunk_type = metadata.get('chunk_type', 'text')
                if chunk_type == 'image':
                    image_docs.append((doc_id, metadata))
                else:
                    text_docs.append((doc_id, metadata))
        
        print(f"图片文档总数: {len(image_docs)}")
        print(f"文字文档总数: {len(text_docs)}")
        print()
        
        # 查找所有图4相关的图片
        figure_4_docs = []
        all_figure_docs = []
        
        for doc_id, metadata in image_docs:
            img_caption = metadata.get('img_caption', [])
            caption_text = ' '.join(img_caption) if img_caption else ''
            
            # 检查是否包含图4
            if '图4' in caption_text:
                figure_4_docs.append((doc_id, metadata))
            
            # 检查所有图表编号
            import re
            figure_matches = re.findall(r'图(\d+)', caption_text)
            if figure_matches:
                all_figure_docs.append((doc_id, metadata, figure_matches))
        
        print("=== 图4相关图片 ===")
        if figure_4_docs:
            for i, (doc_id, metadata) in enumerate(figure_4_docs, 1):
                img_caption = metadata.get('img_caption', [])
                caption_text = ' '.join(img_caption) if img_caption else ''
                document_name = metadata.get('document_name', '未知文档')
                page_number = metadata.get('page_number', '未知页码')
                image_id = metadata.get('image_id', '未知ID')
                
                print(f"{i}. 标题: {caption_text}")
                print(f"   文档: {document_name}")
                print(f"   页码: {page_number}")
                print(f"   图片ID: {image_id}")
                print()
        else:
            print("未找到图4相关的图片")
        
        print("=== 所有图表编号统计 ===")
        figure_numbers = {}
        for doc_id, metadata, matches in all_figure_docs:
            for match in matches:
                figure_num = int(match)
                if figure_num not in figure_numbers:
                    figure_numbers[figure_num] = []
                
                img_caption = metadata.get('img_caption', [])
                caption_text = ' '.join(img_caption) if img_caption else ''
                document_name = metadata.get('document_name', '未知文档')
                
                figure_numbers[figure_num].append({
                    'caption': caption_text,
                    'document': document_name,
                    'image_id': metadata.get('image_id', '未知ID')
                })
        
        # 按图表编号排序显示
        for figure_num in sorted(figure_numbers.keys()):
            docs = figure_numbers[figure_num]
            print(f"图{figure_num}: {len(docs)} 个")
            for i, doc in enumerate(docs, 1):
                print(f"  {i}. {doc['caption']} (来自: {doc['document']})")
            print()
        
        print("=== 前10个图片文档详细信息 ===")
        for i, (doc_id, metadata) in enumerate(image_docs[:10], 1):
            img_caption = metadata.get('img_caption', [])
            caption_text = ' '.join(img_caption) if img_caption else ''
            document_name = metadata.get('document_name', '未知文档')
            page_number = metadata.get('page_number', '未知页码')
            image_id = metadata.get('image_id', '未知ID')
            
            print(f"{i}. 标题: {caption_text}")
            print(f"   文档: {document_name}")
            print(f"   页码: {page_number}")
            print(f"   图片ID: {image_id}")
            print()
        
    except Exception as e:
        print(f"检查向量数据库时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vector_db()
