#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
分析向量数据库的结构，了解embedding的存储方式
'''

import pickle
import os
import sys

def analyze_vector_db():
    """分析向量数据库结构"""
    print("🔍 分析向量数据库结构...")
    print("=" * 60)
    
    # 检查文件
    vector_db_dir = "central/vector_db"
    metadata_file = os.path.join(vector_db_dir, "metadata.pkl")
    index_file = os.path.join(vector_db_dir, "index.pkl")
    faiss_file = os.path.join(vector_db_dir, "index.faiss")
    
    print("📁 向量数据库文件:")
    print(f"  metadata.pkl: {os.path.getsize(metadata_file)} bytes")
    print(f"  index.pkl: {os.path.getsize(index_file)} bytes")
    print(f"  index.faiss: {os.path.getsize(faiss_file)} bytes")
    
    print("\n" + "=" * 60)
    
    # 分析metadata.pkl
    print("📋 分析metadata.pkl:")
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        print(f"  类型: {type(metadata)}")
        print(f"  长度: {len(metadata)}")
        
        if len(metadata) > 0:
            print(f"  第一个元素类型: {type(metadata[0])}")
            if isinstance(metadata[0], dict):
                print(f"  第一个元素键: {list(metadata[0].keys())}")
                if 'chunk_type' in metadata[0]:
                    print(f"  第一个元素chunk_type: {metadata[0]['chunk_type']}")
                if 'semantic_features' in metadata[0]:
                    print(f"  第一个元素semantic_features: {metadata[0]['semantic_features']}")
    except Exception as e:
        print(f"  读取metadata.pkl失败: {e}")
    
    print("\n" + "=" * 60)
    
    # 分析index.pkl
    print("📊 分析index.pkl:")
    try:
        with open(index_file, 'rb') as f:
            index_data = pickle.load(f)
        print(f"  类型: {type(index_data)}")
        print(f"  长度: {len(index_data)}")
        
        if len(index_data) > 0:
            print(f"  第一个元素类型: {type(index_data[0])}")
            if hasattr(index_data[0], 'shape'):
                print(f"  第一个元素形状: {index_data[0].shape}")
            if hasattr(index_data[0], 'dtype'):
                print(f"  第一个元素数据类型: {index_data[0].dtype}")
    except Exception as e:
        print(f"  读取index.pkl失败: {e}")
    
    print("\n" + "=" * 60)
    
    # 分析FAISS索引
    print("🔍 分析FAISS索引:")
    try:
        import faiss
        index = faiss.read_index(faiss_file)
        print(f"  FAISS索引类型: {type(index)}")
        print(f"  向量维度: {index.d}")
        print(f"  向量数量: {index.ntotal}")
        print(f"  索引类型: {faiss.index_type(index)}")
    except ImportError:
        print("  FAISS未安装，无法分析")
    except Exception as e:
        print(f"  读取FAISS索引失败: {e}")

if __name__ == "__main__":
    analyze_vector_db()
