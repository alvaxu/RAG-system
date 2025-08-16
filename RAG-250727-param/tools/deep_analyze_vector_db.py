#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
程序说明：
深度分析向量数据库，特别关注图片的语义描述存储方式
'''

import pickle
import os
import sys

def deep_analyze_vector_db():
    """深度分析向量数据库结构"""
    print("🔍 深度分析向量数据库结构...")
    print("=" * 60)
    
    # 检查文件
    vector_db_dir = "central/vector_db"
    metadata_file = os.path.join(vector_db_dir, "metadata.pkl")
    index_file = os.path.join(vector_db_dir, "index.pkl")
    
    print("📋 分析metadata.pkl的详细内容:")
    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        print(f"  元数据总数量: {len(metadata)}")
        
        if len(metadata) > 0:
            first_doc = metadata[0]
            print(f"\n  第一个文档的详细信息:")
            print(f"    chunk_type: {first_doc.get('chunk_type')}")
            print(f"    image_id: {first_doc.get('image_id')}")
            print(f"    img_caption: {first_doc.get('img_caption')}")
            print(f"    enhanced_description: {first_doc.get('enhanced_description', 'N/A')[:200]}...")
            print(f"    semantic_features: {first_doc.get('semantic_features')}")
            
            # 检查是否有其他字段包含语义信息
            print(f"\n  其他可能包含语义信息的字段:")
            for key, value in first_doc.items():
                if isinstance(value, str) and len(value) > 50:
                    print(f"    {key}: {value[:100]}...")
                elif key not in ['image_id', 'image_path', 'image_filename', 'chunk_type', 'page_number', 'page_idx', 'extension', 'source_zip']:
                    print(f"    {key}: {value}")
    except Exception as e:
        print(f"  读取metadata.pkl失败: {e}")
    
    print("\n" + "=" * 60)
    
    print("📊 分析index.pkl的详细内容:")
    try:
        with open(index_file, 'rb') as f:
            index_data = pickle.load(f)
        print(f"  index.pkl类型: {type(index_data)}")
        print(f"  index.pkl长度: {len(index_data)}")
        
        if len(index_data) > 0:
            print(f"\n  第一个元素类型: {type(index_data[0])}")
            if hasattr(index_data[0], '__dict__'):
                print(f"  第一个元素的属性: {list(index_data[0].__dict__.keys())}")
            
            if len(index_data) > 1:
                print(f"\n  第二个元素类型: {type(index_data[1])}")
                if hasattr(index_data[1], '__dict__'):
                    print(f"  第二个元素的属性: {list(index_data[1].__dict__.keys())}")
                    
                    # 尝试获取文档内容
                    if hasattr(index_data[1], 'page_content'):
                        content = index_data[1].page_content
                        print(f"  第二个元素的page_content: {content[:200] if content else 'N/A'}...")
                    
                    if hasattr(index_data[1], 'metadata'):
                        meta = index_data[1].metadata
                        print(f"  第二个元素的metadata: {meta}")
    except Exception as e:
        print(f"  读取index.pkl失败: {e}")
    
    print("\n" + "=" * 60)
    
    print("🔍 分析FAISS索引的向量内容:")
    try:
        import faiss
        faiss_file = os.path.join(vector_db_dir, "index.faiss")
        index = faiss.read_index(faiss_file)
        print(f"  FAISS索引类型: {type(index)}")
        print(f"  向量维度: {index.d}")
        print(f"  向量数量: {index.ntotal}")
        
        # 尝试获取前几个向量
        if index.ntotal > 0:
            vectors = index.reconstruct_n(0, min(3, index.ntotal))
            print(f"\n  前{min(3, index.ntotal)}个向量的统计信息:")
            for i in range(min(3, index.ntotal)):
                vector = vectors[i]
                print(f"    向量{i}: 形状={vector.shape}, 均值={vector.mean():.6f}, 标准差={vector.std():.6f}")
    except ImportError:
        print("  FAISS未安装，无法分析")
    except Exception as e:
        print(f"  读取FAISS索引失败: {e}")

if __name__ == "__main__":
    deep_analyze_vector_db()
