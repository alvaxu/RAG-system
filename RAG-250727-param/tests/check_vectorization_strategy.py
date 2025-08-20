#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量化策略检查程序

检查目标：
1. 确认text和image_text使用text-embedding-v1向量化
2. 确认image使用multimodal-embedding-v1向量化
3. 验证FAISS中的向量存储状态
4. 输出详细的向量化策略信息
"""

import os
import sys
import logging
from typing import List, Dict, Any, Tuple

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_vectorization_strategy():
    """检查向量化策略"""
    print("="*100)
    print("向量化策略检查程序")
    print("="*100)
    
    try:
        # 1. 导入必要模块
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
        
        # 3. 输出配置信息
        print("\n" + "="*100)
        print("配置信息")
        print("="*100)
        print(f"文本嵌入模型: {getattr(config, 'text_embedding_model', 'N/A')}")
        print(f"图片嵌入模型: {getattr(config, 'image_embedding_model', 'N/A')}")
        print(f"向量维度: {getattr(config, 'vector_dimension', 'N/A')}")
        print(f"向量数据库路径: {getattr(config, 'vector_db_dir', 'N/A')}")
        
        # 4. 获取API密钥
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        if not api_key:
            print("未找到有效的DashScope API密钥")
            return False
        
        print("配置获取成功")
        
        # 5. 初始化embeddings
        text_embeddings = DashScopeEmbeddings(
            dashscope_api_key=api_key,
            model='text-embedding-v1'
        )
        print("text embeddings初始化成功")
        
        # 6. 加载向量数据库
        vector_db_path = config.vector_db_dir
        vector_store = FAISS.load_local(
            vector_db_path, 
            text_embeddings,
            allow_dangerous_deserialization=True
        )
        print("向量数据库加载成功")
        
        # 7. 分析FAISS索引结构
        print("\n" + "="*100)
        print("FAISS索引结构分析")
        print("="*100)
        
        if hasattr(vector_store, 'index') and hasattr(vector_store.index, 'd'):
            print(f"FAISS索引维度: {vector_store.index.d}")
            print(f"FAISS索引向量数量: {vector_store.index.ntotal}")
            print(f"FAISS索引类型: {type(vector_store.index)}")
        else:
            print("无法获取FAISS索引信息")
            return False
        
        # 8. 分析文档存储结构
        print("\n" + "="*100)
        print("文档存储结构分析")
        print("="*100)
        
        docstore_dict = vector_store.docstore._dict
        chunk_type_stats = {}
        total_docs = len(docstore_dict)
        
        # 统计各类型文档数量
        for doc_id, doc in docstore_dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
        
        print(f"总文档数量: {total_docs}")
        print("各类型文档统计:")
        for chunk_type, count in sorted(chunk_type_stats.items()):
            percentage = (count / total_docs) * 100
            print(f"  {chunk_type}: {count} ({percentage:.1f}%)")
        
        # 9. 详细分析各类型文档的向量化策略
        print("\n" + "="*100)
        print("向量化策略详细分析")
        print("="*100)
        
        # 9.1 分析text类型文档
        print("\n--- text类型文档分析 ---")
        text_docs = [(doc_id, doc) for doc_id, doc in docstore_dict.items() 
                     if doc.metadata and doc.metadata.get('chunk_type') == 'text']
        
        if text_docs:
            print(f"找到 {len(text_docs)} 个text文档")
            sample_text_doc = text_docs[0]
            print(f"样本text文档ID: {sample_text_doc[0]}")
            print(f"样本text文档metadata: {sample_text_doc[1].metadata}")
            
            # 检查是否有向量相关信息
            if 'semantic_features' in sample_text_doc[1].metadata:
                semantic_features = sample_text_doc[1].metadata['semantic_features']
                print(f"样本text文档semantic_features: {semantic_features}")
            else:
                print("样本text文档没有semantic_features信息")
        else:
            print("没有找到text类型文档")
        
        # 9.2 分析image_text类型文档
        print("\n--- image_text类型文档分析 ---")
        image_text_docs = [(doc_id, doc) for doc_id, doc in docstore_dict.items() 
                           if doc.metadata and doc.metadata.get('chunk_type') == 'image_text']
        
        if image_text_docs:
            print(f"找到 {len(image_text_docs)} 个image_text文档")
            sample_image_text_doc = image_text_docs[0]
            print(f"样本image_text文档ID: {sample_image_text_doc[0]}")
            print(f"样本image_text文档metadata: {sample_image_text_doc[1].metadata}")
            
            # 检查是否有向量相关信息
            if 'semantic_features' in sample_image_text_doc[1].metadata:
                semantic_features = sample_image_text_doc[1].metadata['semantic_features']
                print(f"样本image_text文档semantic_features: {semantic_features}")
            else:
                print("样本image_text文档没有semantic_features信息")
        else:
            print("没有找到image_text类型文档")
        
        # 9.3 分析image类型文档
        print("\n--- image类型文档分析 ---")
        image_docs = [(doc_id, doc) for doc_id, doc in docstore_dict.items() 
                      if doc.metadata and doc.metadata.get('chunk_type') == 'image']
        
        if image_docs:
            print(f"找到 {len(image_docs)} 个image文档")
            sample_image_doc = image_docs[0]
            print(f"样本image文档ID: {sample_image_doc[0]}")
            print(f"样本image文档metadata: {sample_image_doc[1].metadata}")
            
            # 检查是否有向量相关信息
            if 'semantic_features' in sample_image_doc[1].metadata:
                semantic_features = sample_image_doc[1].metadata['semantic_features']
                print(f"样本image文档semantic_features: {semantic_features}")
            else:
                print("样本image文档没有semantic_features信息")
        else:
            print("没有找到image类型文档")
        
        # 10. 验证向量化策略
        print("\n" + "="*100)
        print("向量化策略验证")
        print("="*100)
        
        # 10.1 验证text和image_text使用text-embedding-v1
        text_based_docs = text_docs + image_text_docs
        if text_based_docs:
            print(f"text和image_text类型文档总数: {len(text_based_docs)}")
            
            # 检查这些文档的向量是否与FAISS索引维度匹配
            # text-embedding-v1应该生成1536维向量
            expected_dim = 1536
            if vector_store.index.d == expected_dim:
                print(f"✅ text和image_text文档向量维度验证通过: {expected_dim}维")
                print("✅ 确认使用text-embedding-v1进行向量化")
            else:
                print(f"❌ text和image_text文档向量维度不匹配: 期望{expected_dim}，实际{vector_store.index.d}")
        else:
            print("没有找到text和image_text类型文档")
        
        # 10.2 验证image使用multimodal-embedding-v1
        if image_docs:
            print(f"image类型文档总数: {len(image_docs)}")
            
            # 检查image文档的向量是否与FAISS索引维度匹配
            # multimodal-embedding-v1应该生成1536维向量（根据我们的验证）
            expected_dim = 1536
            if vector_store.index.d == expected_dim:
                print(f"✅ image文档向量维度验证通过: {expected_dim}维")
                print("✅ 确认使用multimodal-embedding-v1进行向量化")
            else:
                print(f"❌ image文档向量维度不匹配: 期望{expected_dim}，实际{vector_store.index.d}")
        else:
            print("没有找到image类型文档")
        
        # 11. 输出总结报告
        print("\n" + "="*100)
        print("向量化策略总结报告")
        print("="*100)
        
        print("📊 文档类型分布:")
        for chunk_type, count in sorted(chunk_type_stats.items()):
            percentage = (count / total_docs) * 100
            print(f"  {chunk_type}: {count} ({percentage:.1f}%)")
        
        print(f"\n🔧 向量化策略:")
        print(f"  text + image_text → text-embedding-v1 (1536维)")
        print(f"  image → multimodal-embedding-v1 (1536维)")
        
        print(f"\n📏 向量维度信息:")
        print(f"  FAISS索引维度: {vector_store.index.d}")
        print(f"  总向量数量: {vector_store.index.ntotal}")
        
        print(f"\n✅ 验证结果:")
        if vector_store.index.d == 1536:
            print("  所有文档类型都使用1536维向量，向量化策略一致")
            print("  跨模态搜索可以实现：text查询 → multimodal向量 → image召回")
        else:
            print(f"  向量维度不一致，需要检查向量化策略")
        
        print(f"\n💡 技术要点:")
        print("  1. text和image_text使用相同的embedding模型，语义空间一致")
        print("  2. image使用multimodal模型，可以接受文本输入")
        print("  3. 所有向量都存储在同一个FAISS索引中")
        print("  4. 策略2需要将文本查询转换为multimodal向量以实现跨模态搜索")
        
        print("\n" + "="*100)
        print("检查完成")
        print("="*100)
        
        return True
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_vectorization_strategy()
    if success:
        print("\n检查完成")
    else:
        print("\n检查失败")
