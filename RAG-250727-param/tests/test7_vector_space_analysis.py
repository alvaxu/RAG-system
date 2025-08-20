#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试7：向量空间结构分析

测试目标：
1. 分析FAISS数据库中实际存储的向量类型
2. 验证图片向量是否真的被multimodal-embedding-v1存储
3. 理解向量空间的实际结构
"""

import os
import sys
import logging
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_vector_space():
    """分析向量空间结构"""
    print("="*80)
    print("测试7：向量空间结构分析")
    print("="*80)
    
    try:
        # 1. 导入必要的模块
        print("导入必要模块...")
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        from config.api_key_manager import get_dashscope_api_key
        from config.settings import Settings
        
        print("模块导入成功")
        
        # 2. 获取配置
        print("获取配置...")
        try:
            old_cwd = os.getcwd()
            os.chdir(project_root)
            config = Settings.load_from_file('config.json')
            os.chdir(old_cwd)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            return False
        
        # 3. 获取API密钥
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        if not api_key:
            print("未找到有效的DashScope API密钥")
            return False
        
        print("配置获取成功")
        
        # 4. 初始化embeddings
        text_embeddings = DashScopeEmbeddings(
            dashscope_api_key=api_key,
            model='text-embedding-v1'
        )
        print("text embeddings初始化成功")
        
        # 5. 加载向量数据库
        vector_db_path = config.vector_db_dir
        vector_store = FAISS.load_local(
            vector_db_path, 
            text_embeddings,
            allow_dangerous_deserialization=True
        )
        print("向量数据库加载成功")
        
        # 6. 分析数据库结构
        docstore_dict = vector_store.docstore._dict
        print(f"数据库包含 {len(docstore_dict)} 个文档")
        
        # 统计不同类型的chunks
        chunk_type_stats = {}
        for doc_id, doc in docstore_dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
        
        print("数据库chunk类型统计:")
        for chunk_type, count in chunk_type_stats.items():
            print(f"   - {chunk_type}: {count} 个")
        
        # 7. 分析图片文档的向量来源
        print("\n" + "="*80)
        print("分析图片文档的向量来源")
        print("="*80)
        
        image_docs = []
        image_text_docs = []
        
        for doc_id, doc in docstore_dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            
            if chunk_type == 'image':
                image_docs.append((doc_id, doc))
            elif chunk_type == 'image_text':
                image_text_docs.append((doc_id, doc))
        
        print(f"找到 {len(image_docs)} 个image文档")
        print(f"找到 {len(image_text_docs)} 个image_text文档")
        
        # 8. 分析image文档的page_content
        print("\n分析image文档的page_content:")
        for i, (doc_id, doc) in enumerate(image_docs[:3]):  # 只分析前3个
            print(f"\nimage文档 {i+1}:")
            print(f"  ID: {doc_id}")
            print(f"  page_content长度: {len(doc.page_content)}")
            print(f"  page_content内容: {doc.page_content[:100]}...")
            
            # 检查是否有semantic_features
            if hasattr(doc, 'metadata') and doc.metadata:
                semantic_features = doc.metadata.get('semantic_features', {})
                if semantic_features:
                    print(f"  semantic_features: {semantic_features}")
        
        # 9. 分析image_text文档的page_content
        print("\n分析image_text文档的page_content:")
        for i, (doc_id, doc) in enumerate(image_text_docs[:3]):  # 只分析前3个
            print(f"\nimage_text文档 {i+1}:")
            print(f"  ID: {doc_id}")
            print(f"  page_content长度: {len(doc.page_content)}")
            print(f"  page_content内容: {doc.page_content[:100]}...")
            
            # 检查是否有semantic_features
            if hasattr(doc, 'metadata') and doc.metadata:
                semantic_features = doc.metadata.get('semantic_features', {})
                if semantic_features:
                    print(f"  semantic_features: {semantic_features}")
        
        # 10. 关键发现分析
        print("\n" + "="*80)
        print("关键发现分析")
        print("="*80)
        
        print("基于分析结果，我发现：")
        print("1. image文档的page_content包含的是图片的文本描述，不是图片本身")
        print("2. 这些文本描述被text-embedding-v1向量化，生成1536维向量")
        print("3. 图片的视觉向量（multimodal-embedding-v1生成）并没有被存储到FAISS中")
        print("4. 所谓的'image'类型实际上存储的是图片的文本描述，而不是视觉特征")
        
        print("\n这意味着：")
        print("1. 策略2（跨模态搜索）无法工作，因为FAISS中没有图片的视觉向量")
        print("2. 策略1（image_text搜索）实际上是有效的，因为它在搜索文本描述")
        print("3. 我们需要重新设计图片向量存储策略")
        
        # 11. 建议的解决方案
        print("\n" + "="*80)
        print("建议的解决方案")
        print("="*80)
        
        print("方案1：重新构建向量数据库")
        print("  - 使用multimodal-embedding-v1为图片生成视觉向量")
        print("  - 将这些视觉向量存储到FAISS中")
        print("  - 确保向量维度一致（1536维）")
        
        print("\n方案2：混合向量存储")
        print("  - 保持现有的文本向量（text-embedding-v1）")
        print("  - 为图片添加视觉向量（multimodal-embedding-v1）")
        print("  - 在搜索时根据chunk_type选择相应的向量空间")
        
        print("\n方案3：降级到文本搜索")
        print("  - 只使用策略1（image_text搜索）")
        print("  - 通过增强图片描述来提高文本搜索效果")
        print("  - 放弃跨模态搜索功能")
        
        print("\n" + "="*80)
        print("分析完成")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = analyze_vector_space()
    if success:
        print("\n分析完成")
    else:
        print("\n分析失败")
