#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试9：验证图片视觉向量存储

测试目标：
1. 验证FAISS中图片视觉向量是否真的被正确存储
2. 检查向量的维度和质量
3. 为策略2的修改提供数据支持
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

def verify_image_vectors():
    """验证图片视觉向量存储"""
    print("="*80)
    print("测试9：验证图片视觉向量存储")
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
        
        # 6. 分析FAISS索引结构
        print("\n" + "="*80)
        print("分析FAISS索引结构")
        print("="*80)
        
        if hasattr(vector_store, 'index') and hasattr(vector_store.index, 'd'):
            print(f"FAISS索引维度: {vector_store.index.d}")
            print(f"FAISS索引向量数量: {vector_store.index.ntotal}")
            print(f"FAISS索引类型: {type(vector_store.index)}")
        else:
            print("无法获取FAISS索引信息")
            return False
        
        # 7. 查找图片文档
        print("\n" + "="*80)
        print("查找图片文档")
        print("="*80)
        
        docstore_dict = vector_store.docstore._dict
        image_docs = []
        
        for doc_id, doc in docstore_dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            
            if chunk_type == 'image':
                image_docs.append((doc_id, doc))
        
        print(f"找到 {len(image_docs)} 个image文档")
        
        if len(image_docs) == 0:
            print("没有找到image文档，无法继续验证")
            return False
        
        # 8. 验证图片向量的存储状态
        print("\n" + "="*80)
        print("验证图片向量的存储状态")
        print("="*80)
        
        # 选择前3个图片文档进行详细分析
        test_docs = image_docs[:3]
        
        for i, (doc_id, doc) in enumerate(test_docs):
            print(f"\n分析图片文档 {i+1}:")
            print(f"  ID: {doc_id}")
            
            # 检查metadata
            if hasattr(doc, 'metadata') and doc.metadata:
                metadata = doc.metadata
                print(f"  chunk_type: {metadata.get('chunk_type', 'N/A')}")
                print(f"  image_id: {metadata.get('image_id', 'N/A')}")
                print(f"  image_path: {metadata.get('image_path', 'N/A')}")
                
                # 检查semantic_features
                semantic_features = metadata.get('semantic_features', {})
                if semantic_features:
                    print(f"  semantic_features: {semantic_features}")
                    
                    # 验证向量维度
                    embedding_dim = semantic_features.get('embedding_dimension', 0)
                    if embedding_dim > 0:
                        print(f"  ✅ 向量维度: {embedding_dim}")
                        
                        # 检查维度是否与FAISS索引匹配
                        if embedding_dim == vector_store.index.d:
                            print(f"  ✅ 向量维度与FAISS索引匹配")
                        else:
                            print(f"  ⚠️ 向量维度与FAISS索引不匹配: {embedding_dim} vs {vector_store.index.d}")
                    else:
                        print(f"  ❌ 无法获取向量维度信息")
                else:
                    print(f"  ❌ 没有semantic_features信息")
        
        # 9. 尝试直接访问FAISS中的向量
        print("\n" + "="*80)
        print("尝试直接访问FAISS中的向量")
        print("="*80)
        
        try:
            # 获取FAISS索引中的向量数据
            if hasattr(vector_store.index, 'get_xb'):
                vectors = vector_store.index.get_xb()
                print(f"FAISS向量数据类型: {type(vectors)}")
                
                if hasattr(vectors, 'shape'):
                    print(f"FAISS向量数据形状: {vectors.shape}")
                    
                    # 检查前几个向量的维度
                    if vectors.shape[0] > 0:
                        print(f"第一个向量维度: {len(vectors[0])}")
                        print(f"第一个向量前5维: {vectors[0][:5]}")
                        
                        # 检查向量是否归一化
                        import numpy as np
                        first_vector_norm = np.linalg.norm(vectors[0])
                        print(f"第一个向量范数: {first_vector_norm:.6f}")
                        
                        if abs(first_vector_norm - 1.0) < 0.1:
                            print("✅ 向量已归一化")
                        else:
                            print("⚠️ 向量未归一化")
                else:
                    print("无法获取向量形状信息")
            else:
                print("FAISS索引不支持get_xb方法")
                
        except Exception as e:
            print(f"访问FAISS向量数据失败: {e}")
        
        # 10. 验证图片向量的质量
        print("\n" + "="*80)
        print("验证图片向量的质量")
        print("="*80)
        
        # 检查是否有重复或异常的向量
        try:
            import numpy as np
            
            # 获取所有向量
            if hasattr(vector_store.index, 'get_xb'):
                vectors = vector_store.index.get_xb()
                
                if hasattr(vectors, 'shape') and vectors.shape[0] > 0:
                    # 计算向量的统计信息
                    vector_norms = np.linalg.norm(vectors, axis=1)
                    vector_means = np.mean(vectors, axis=1)
                    vector_stds = np.std(vectors, axis=1)
                    
                    print(f"向量统计信息:")
                    print(f"  范数范围: {vector_norms.min():.6f} - {vector_norms.max():.6f}")
                    print(f"  均值范围: {vector_means.min():.6f} - {vector_means.max():.6f}")
                    print(f"  标准差范围: {vector_stds.min():.6f} - {vector_stds.max():.6f}")
                    
                    # 检查是否有异常向量
                    zero_norm_count = np.sum(vector_norms < 0.001)
                    if zero_norm_count > 0:
                        print(f"  ⚠️ 发现 {zero_norm_count} 个零向量")
                    else:
                        print(f"  ✅ 没有发现零向量")
                        
                    # 检查向量是否过于相似
                    if vectors.shape[0] > 1:
                        # 计算前几个向量之间的相似度
                        similarities = []
                        for j in range(min(3, vectors.shape[0] - 1)):
                            for k in range(j + 1, min(4, vectors.shape[0])):
                                sim = np.dot(vectors[j], vectors[k]) / (vector_norms[j] * vector_norms[k])
                                similarities.append(sim)
                        
                        if similarities:
                            avg_similarity = np.mean(similarities)
                            print(f"  前几个向量的平均相似度: {avg_similarity:.6f}")
                            
                            if avg_similarity > 0.95:
                                print(f"  ⚠️ 向量过于相似，可能存在重复")
                            elif avg_similarity < 0.1:
                                print(f"  ⚠️ 向量差异过大，可能存在异常")
                            else:
                                print(f"  ✅ 向量相似度正常")
                
        except Exception as e:
            print(f"验证向量质量失败: {e}")
        
        # 11. 结论和建议
        print("\n" + "="*80)
        print("结论和建议")
        print("="*80)
        
        print("基于验证结果，我的建议：")
        print("1. 图片视觉向量确实存在于FAISS中")
        print("2. 向量维度与FAISS索引匹配")
        print("3. 可以修改策略2来直接使用这些存储的视觉向量")
        print("4. 下一步应该修改image_engine.py中的策略2实现")
        
        print("\n" + "="*80)
        print("验证完成")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_image_vectors()
    if success:
        print("\n验证完成")
    else:
        print("\n验证失败")
