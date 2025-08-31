#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：

## 1. 调试脚本：检查实际向量数据库状态
## 2. 分析为什么显示33张未完成图片
## 3. 对比设计文档要求与实际状态

"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.vector_store_manager import LangChainVectorStoreManager
from config.config_manager import ConfigManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_vector_db_status():
    """调试向量数据库状态"""
    try:
        print("🔍 开始调试向量数据库状态...")
        
        # 初始化配置管理器
        config_manager = ConfigManager()
        
        # 初始化向量存储管理器
        vector_store_manager = LangChainVectorStoreManager(config_manager)
        
        # 尝试加载向量数据库
        print("📂 尝试加载向量数据库...")
        load_success = vector_store_manager.load()
        
        if not load_success:
            print("❌ 无法加载向量数据库")
            return
        
        print("✅ 向量数据库加载成功")
        
        # 获取数据库状态
        status = vector_store_manager.get_status()
        print(f"\n📊 数据库状态:")
        print(f"  - 是否初始化: {status.get('is_initialized')}")
        print(f"  - 向量总数: {status.get('total_vectors')}")
        print(f"  - 索引类型: {status.get('index_type')}")
        print(f"  - 索引向量数: {status.get('index_ntotal')}")
        
        # 检查向量存储对象
        if not vector_store_manager.vector_store:
            print("❌ 向量存储对象为空")
            return
        
        # 检查docstore中的内容
        docstore = vector_store_manager.vector_store.docstore
        if not hasattr(docstore, '_dict'):
            print("❌ docstore没有_dict属性")
            return
        
        docstore_dict = docstore._dict
        print(f"\n📚 Docstore内容:")
        print(f"  - 文档总数: {len(docstore_dict)}")
        
        # 统计不同类型的chunk
        chunk_types = {}
        image_chunks = []
        
        for doc_id, doc in docstore_dict.items():
            metadata = getattr(doc, 'metadata', {}) if hasattr(doc, 'metadata') else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            
            # 统计chunk类型
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            # 收集图片chunk的详细信息
            if chunk_type == 'image':
                image_info = {
                    'doc_id': doc_id,
                    'image_path': metadata.get('image_path', ''),
                    'image_id': metadata.get('image_id', ''),
                    'document_name': metadata.get('document_name', ''),
                    'enhancement_status': metadata.get('enhancement_status', 'unknown'),
                    'vectorization_status': metadata.get('vectorization_status', 'unknown'),
                    'enhanced_description': metadata.get('enhanced_description', ''),
                    'image_embedding': metadata.get('image_embedding', []),
                    'description_embedding': metadata.get('description_embedding', [])
                }
                image_chunks.append(image_info)
        
        print(f"\n📊 Chunk类型统计:")
        for chunk_type, count in chunk_types.items():
            print(f"  - {chunk_type}: {count}")
        
        print(f"\n🖼️ 图片Chunk详细信息 (共{len(image_chunks)}张):")
        for i, img in enumerate(image_chunks):
            print(f"  图片 {i+1}:")
            print(f"    - ID: {img['image_id']}")
            print(f"    - 文档: {img['document_name']}")
            print(f"    - 增强状态: {img['enhancement_status']}")
            print(f"    - 向量化状态: {img['vectorization_status']}")
            print(f"    - 增强描述: {'有' if img['enhanced_description'] else '无'}")
            print(f"    - 图片向量: {'有' if img['image_embedding'] else '无'}")
            print(f"    - 描述向量: {'有' if img['description_embedding'] else '无'}")
            print()
        
        # 分析未完成的原因
        print("🔍 分析未完成原因:")
        enhancement_pending = sum(1 for img in image_chunks if img['enhancement_status'] != 'success')
        vectorization_pending = sum(1 for img in image_chunks if img['vectorization_status'] != 'success')
        no_enhanced_desc = sum(1 for img in image_chunks if not img['enhanced_description'])
        no_image_embedding = sum(1 for img in image_chunks if not img['image_embedding'])
        no_desc_embedding = sum(1 for img in image_chunks if not img['description_embedding'])
        
        print(f"  - 增强状态不是'success': {enhancement_pending}")
        print(f"  - 向量化状态不是'success': {vectorization_pending}")
        print(f"  - 缺少增强描述: {no_enhanced_desc}")
        print(f"  - 缺少图片向量: {no_image_embedding}")
        print(f"  - 缺少描述向量: {no_desc_embedding}")
        
        # 检查get_unfinished_images的逻辑
        print(f"\n🔍 测试get_unfinished_images逻辑:")
        unfinished_images = vector_store_manager.get_unfinished_images()
        print(f"  - get_unfinished_images返回: {len(unfinished_images)} 张")
        
        if unfinished_images:
            print(f"  - 第一张未完成图片的状态:")
            first_unfinished = unfinished_images[0]
            print(f"    - 需要增强: {first_unfinished.get('needs_enhancement')}")
            print(f"    - 需要向量化: {first_unfinished.get('needs_vectorization')}")
            print(f"    - 元数据: {first_unfinished.get('metadata', {})}")
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_vector_db_status()
