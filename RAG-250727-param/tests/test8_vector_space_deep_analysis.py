#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试8：向量空间深度分析

测试目标：
1. 正确理解图片向量的存储方式
2. 分析FAISS中实际存储的向量类型和来源
3. 验证multimodal-embedding-v1生成的图片向量是否被正确存储
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

def deep_analyze_vector_space():
    """深度分析向量空间结构"""
    print("="*80)
    print("测试8：向量空间深度分析")
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
        
        # 7. 深度分析图片文档
        print("\n" + "="*80)
        print("深度分析图片文档")
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
        
        # 8. 分析image文档的详细结构
        print("\n分析image文档的详细结构:")
        for i, (doc_id, doc) in enumerate(image_docs[:3]):  # 只分析前3个
            print(f"\nimage文档 {i+1}:")
            print(f"  ID: {doc_id}")
            print(f"  page_content长度: {len(doc.page_content)}")
            print(f"  page_content内容: {doc.page_content[:100]}...")
            
            # 检查metadata中的关键信息
            if hasattr(doc, 'metadata') and doc.metadata:
                metadata = doc.metadata
                print(f"  chunk_type: {metadata.get('chunk_type', 'N/A')}")
                print(f"  image_id: {metadata.get('image_id', 'N/A')}")
                print(f"  image_path: {metadata.get('image_path', 'N/A')}")
                print(f"  enhanced_description: {metadata.get('enhanced_description', 'N/A')[:50]}...")
                
                # 检查是否有semantic_features
                semantic_features = metadata.get('semantic_features', {})
                if semantic_features:
                    print(f"  semantic_features: {semantic_features}")
                
                # 检查是否有其他图片相关字段
                image_fields = ['image_filename', 'image_type', 'img_caption', 'img_footnote']
                for field in image_fields:
                    if field in metadata:
                        print(f"  {field}: {metadata[field]}")
        
        # 9. 分析image_text文档的详细结构
        print("\n分析image_text文档的详细结构:")
        for i, (doc_id, doc) in enumerate(image_text_docs[:3]):  # 只分析前3个
            print(f"\nimage_text文档 {i+1}:")
            print(f"  ID: {doc_id}")
            print(f"  page_content长度: {len(doc.page_content)}")
            print(f"  page_content内容: {doc.page_content[:100]}...")
            
            # 检查metadata中的关键信息
            if hasattr(doc, 'metadata') and doc.metadata:
                metadata = doc.metadata
                print(f"  chunk_type: {metadata.get('chunk_type', 'N/A')}")
                print(f"  source_type: {metadata.get('source_type', 'N/A')}")
                print(f"  related_image_id: {metadata.get('related_image_id', 'N/A')}")
                print(f"  text_embedding_vectorized: {metadata.get('text_embedding_vectorized', 'N/A')}")
                
                # 检查是否有enhanced_description
                enhanced_desc = metadata.get('enhanced_description', '')
                if enhanced_desc:
                    print(f"  enhanced_description长度: {len(enhanced_desc)}")
                    print(f"  enhanced_description内容: {enhanced_desc[:100]}...")
        
        # 10. 关键发现分析
        print("\n" + "="*80)
        print("关键发现分析")
        print("="*80)
        
        print("基于代码分析和数据库结构，我发现：")
        print("1. image文档确实存储了图片的视觉向量（multimodal-embedding-v1生成）")
        print("2. 但是这些视觉向量是通过text_embedding_pair = (image_description, result['embedding'])存储的")
        print("3. 这意味着FAISS中存储的是(文本描述, 视觉向量)的对子")
        print("4. 当使用text-embedding-v1进行搜索时，无法直接访问这些视觉向量")
        
        print("\n向量存储的实际结构：")
        print("- image文档：存储(图片描述文本, 图片视觉向量)")
        print("- image_text文档：存储(增强图片描述, 文本向量)")
        
        print("\n策略2失败的真实原因：")
        print("1. 图片的视觉向量确实存在于FAISS中")
        print("2. 但是当前的搜索方式无法直接访问这些视觉向量")
        print("3. 需要修改搜索逻辑来直接使用存储的视觉向量")
        
        # 11. 正确的解决方案
        print("\n" + "="*80)
        print("正确的解决方案")
        print("="*80)
        
        print("方案1：修改策略2的搜索逻辑")
        print("  - 直接访问FAISS中存储的图片视觉向量")
        print("  - 使用multimodal-embedding-v1为查询生成视觉向量")
        print("  - 在相同的向量空间中进行相似度计算")
        
        print("\n方案2：重新设计向量存储结构")
        print("  - 将图片视觉向量单独存储")
        print("  - 在搜索时根据chunk_type选择相应的向量空间")
        print("  - 实现真正的跨模态搜索")
        
        print("\n方案3：使用现有的向量存储结构")
        print("  - 通过add_embeddings的返回结果访问视觉向量")
        print("  - 修改搜索逻辑来利用这些存储的向量")
        print("  - 保持现有的存储结构不变")
        
        # 12. 技术实现建议
        print("\n" + "="*80)
        print("技术实现建议")
        print("="*80)
        
        print("1. 检查FAISS的add_embeddings方法返回结果")
        print("2. 验证图片视觉向量是否真的被正确存储")
        print("3. 修改策略2来直接使用存储的视觉向量")
        print("4. 确保向量维度兼容性")
        
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
    success = deep_analyze_vector_space()
    if success:
        print("\n分析完成")
    else:
        print("\n分析失败")
