#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查FAISS索引的实际结构，确认图片视觉向量的存储情况
"""

import pickle
import numpy as np
from pathlib import Path

def check_faiss_structure():
    """检查FAISS索引的实际结构"""
    
    # 检查index.pkl中的文档结构
    index_path = Path('central/vector_db/index.pkl')
    faiss_path = Path('central/vector_db/index.faiss')
    
    print("🔍 检查FAISS索引结构:")
    print("=" * 60)
    
    if not index_path.exists():
        print(f"❌ 索引文件不存在: {index_path}")
        return
    
    if not faiss_path.exists():
        print(f"❌ FAISS文件不存在: {faiss_path}")
        return
    
    try:
        # 加载文档索引
        with open(index_path, 'rb') as f:
            index_data = pickle.load(f)
        
        docstore = index_data[0]
        
        if not hasattr(docstore, '_dict'):
            print("❌ docstore没有_dict属性")
            return
        
        print(f"📊 文档总数: {len(docstore._dict)}")
        
        # 检查图片文档的向量存储情况
        print("\n🔍 检查图片文档的向量存储:")
        image_docs = []
        for doc_id, doc in docstore._dict.items():
            if (hasattr(doc, 'metadata') and 
                'chunk_type' in doc.metadata and 
                doc.metadata['chunk_type'] == 'image'):
                image_docs.append((doc_id, doc))
        
        print(f"📷 找到 {len(image_docs)} 个图片文档")
        
        # 检查前3个图片文档的详细情况
        for i, (doc_id, doc) in enumerate(image_docs[:3]):
            print(f"\n📷 图片文档 {i+1}:")
            print(f"  ID: {doc_id}")
            print(f"  page_content长度: {len(doc.page_content) if hasattr(doc, 'page_content') else 'N/A'}")
            
            # 检查是否有向量相关的属性
            vector_attrs = []
            for attr in dir(doc):
                if 'vector' in attr.lower() or 'embedding' in attr.lower():
                    vector_attrs.append(attr)
            
            if vector_attrs:
                print(f"  向量相关属性: {vector_attrs}")
            else:
                print("  向量相关属性: 无")
            
            # 检查metadata中的semantic_features
            if hasattr(doc, 'metadata') and 'semantic_features' in doc.metadata:
                semantic = doc.metadata['semantic_features']
                print(f"  semantic_features: {semantic}")
            else:
                print("  semantic_features: 无")
        
        # 检查FAISS文件大小
        faiss_size = faiss_path.stat().st_size
        print(f"\n📏 FAISS文件大小: {faiss_size} bytes")
        
        # 尝试加载FAISS索引
        try:
            import faiss
            index = faiss.read_index(str(faiss_path))
            print(f"🔢 FAISS索引信息:")
            print(f"  向量维度: {index.d}")
            print(f"  向量数量: {index.ntotal}")
            print(f"  索引类型: {type(index)}")
            
            # 检查是否有向量数据
            if hasattr(index, 'get_xb'):
                try:
                    vectors = index.get_xb()
                    print(f"  向量数据类型: {type(vectors)}")
                    if hasattr(vectors, 'shape'):
                        print(f"  向量数据形状: {vectors.shape}")
                    
                    # 检查前几个向量
                    if vectors.shape[0] > 0:
                        print(f"  第一个向量: {vectors[0][:5]}... (前5维)")
                        print(f"  向量范数范围: {np.linalg.norm(vectors, axis=1).min():.4f} - {np.linalg.norm(vectors, axis=1).max():.4f}")
                except Exception as e:
                    print(f"  无法获取向量数据: {e}")
            
        except ImportError:
            print("❌ 无法导入faiss库")
        except Exception as e:
            print(f"❌ 加载FAISS索引失败: {e}")
        
        # 关键问题分析
        print(f"\n🤔 关键问题分析:")
        print(f"1. 图片文档的page_content包含文本描述，这些文本会被text-embedding-v1向量化")
        print(f"2. 图片的视觉内容是否真的被multimodal-embedding-v1向量化并存储到FAISS中？")
        print(f"3. 如果存储了，这些视觉向量在检索中是否被使用？")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    check_faiss_structure()
