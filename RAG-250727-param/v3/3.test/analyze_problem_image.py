#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析问题图片的详细信息
"""

import pickle
import os
import sys

# 添加项目路径
sys.path.append('.')

from core.vector_store_manager import LangChainVectorStoreManager
from config.config_manager import ConfigManager

def analyze_problem_image():
    """分析问题图片的详细信息"""
    
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        
        # 使用向量存储管理器加载数据库
        vector_store_manager = LangChainVectorStoreManager(config_manager)
        success = vector_store_manager.load('./central/vector_db')
        
        if not success:
            print('无法加载向量数据库')
            return
        
        # 获取向量存储
        vector_store = vector_store_manager.vector_store
        if not vector_store or not hasattr(vector_store, 'docstore'):
            print('向量存储结构异常')
            return
        
        # 查找问题图片
        target_image_id = "f821c43d-d9ba-4d81-b071-112c7f9efd72"  # 新出现的问题图片
        
        if hasattr(vector_store.docstore, '_dict'):
            docstore = vector_store.docstore._dict
        else:
            docstore = vector_store.docstore
            
        if target_image_id in docstore:
            doc = docstore[target_image_id]
            print(f'找到问题图片文档: {target_image_id}')
            print(f'文档类型: {type(doc)}')
            
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
                print(f'\n=== 完整元数据 ===')
                for key, value in metadata.items():
                                    print(f'{key}: {value}')
                
                print(f'\n=== 关键字段分析 ===')
                print(f'chunk_type: {metadata.get("chunk_type", "N/A")}')
                print(f'source: {metadata.get("source", "N/A")}')
                print(f'image_id: {metadata.get("image_id", "N/A")}')
                print(f'update_timestamp: {metadata.get("update_timestamp", "N/A")}')
                print(f'update_type: {metadata.get("update_type", "N/A")}')
                print(f'vector_type: {metadata.get("vector_type", "N/A")}')
                print(f'type: {metadata.get("type", "N/A")}')
                
                # 检查关键信息
                print(f'\n=== 关键字段分析 ===')
                print(f'chunk_id: {metadata.get("chunk_id", "N/A")}')
                print(f'document_name: {metadata.get("document_name", "N/A")}')
                print(f'image_id: {metadata.get("image_id", "N/A")}')
                print(f'enhanced_description: {metadata.get("enhanced_description", "N/A")[:100] if metadata.get("enhanced_description") else "N/A"}...')
                
                # 检查是否是增量模式添加的
                if 'update_timestamp' in metadata:
                    print(f'\n这是一个增量更新的向量')
                    print(f'更新时间: {metadata.get("update_timestamp")}')
                else:
                    print(f'\n这不是增量更新的向量')
                    
            else:
                print('没有元数据')
        else:
            print(f'未找到ID: {target_image_id}')
            
    except Exception as e:
        print(f'分析失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    analyze_problem_image()
