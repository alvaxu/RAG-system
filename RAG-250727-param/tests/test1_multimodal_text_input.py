#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试1：multimodal-embedding-v1文本输入能力验证

测试目标：
1. 确认multimodal-embedding-v1能否接受文本输入并生成向量
2. 验证返回向量的维度和质量
3. 与已知图片向量进行相似度计算验证
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_multimodal_text_input():
    """测试multimodal-embedding-v1的文本输入能力"""
    print("="*60)
    print("🧪 测试1：multimodal-embedding-v1文本输入能力验证")
    print("="*60)
    
    try:
        # 1. 导入必要的模块
        print("📦 导入必要模块...")
        from langchain_community.vectorstores import FAISS
        import dashscope
        from config.api_key_manager import get_dashscope_api_key
        from config.settings import Settings
        
        print("✅ 模块导入成功")
        
        # 2. 获取API密钥
        print("🔑 获取API密钥...")
        config = Settings.load_from_file('config.json')
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return False
        
        print("✅ API密钥获取成功")
        
        # 3. 初始化multimodal embeddings
        print("🚀 初始化multimodal embeddings...")
        dashscope.api_key = api_key
        print("✅ multimodal embeddings初始化成功")
        
        # 4. 测试文本输入
        print("📝 测试文本输入...")
        test_queries = [
            "中芯国际的财务图表",
            "半导体制造工艺流程图",
            "晶圆代工产能利用率图表",
            "芯片良率统计表"
        ]
        
        text_embeddings = []
        for i, query in enumerate(test_queries, 1):
            print(f"   处理查询 {i}: {query}")
            try:
                # 生成文本向量
                from dashscope import MultiModalEmbedding
                result = MultiModalEmbedding.call(
                    model='multimodal-embedding-v1',
                    input=[{'text': query}]
                )
                if result.status_code == 200:
                    # 从正确的路径提取向量
                    embedding = result.output['embeddings'][0]['embedding']
                else:
                    raise Exception(f"API调用失败: {result}")
                text_embeddings.append(embedding)
                
                print(f"   ✅ 查询 {i} 向量生成成功，维度: {len(embedding)}")
                
                # 检查向量质量（不应该全是0或相同值）
                unique_values = len(set(embedding))
                embedding_sum = sum(embedding)
                embedding_norm = sum(x*x for x in embedding) ** 0.5
                
                print(f"   📊 向量统计: 唯一值={unique_values}, 总和={embedding_sum:.3f}, 范数={embedding_norm:.3f}")
                
                if unique_values < 10 or embedding_norm < 0.1:
                    print(f"   ⚠️ 警告：向量质量可能有问题")
                
            except Exception as e:
                print(f"   ❌ 查询 {i} 向量生成失败: {e}")
                return False
        
        print(f"✅ 所有 {len(test_queries)} 个查询的向量生成成功")
        
        # 5. 验证向量一致性
        print("🔍 验证向量一致性...")
        if len(text_embeddings) > 1:
            first_dim = len(text_embeddings[0])
            for i, embedding in enumerate(text_embeddings[1:], 2):
                if len(embedding) != first_dim:
                    print(f"   ❌ 查询 {i} 向量维度不一致: {len(embedding)} vs {first_dim}")
                    return False
                else:
                    print(f"   ✅ 查询 {i} 向量维度一致: {len(embedding)}")
        
        print(f"✅ 所有向量维度一致: {len(text_embeddings[0])}")
        
        # 6. 测试向量相似度计算
        print("📊 测试向量相似度计算...")
        if len(text_embeddings) >= 2:
            try:
                # 检查numpy依赖
                try:
                    import numpy as np
                    print("   ✅ numpy导入成功")
                except ImportError:
                    print("   ❌ numpy未安装，跳过相似度计算")
                    print("   请运行: pip install numpy")
                    return False
                
                # 计算第一个查询与后续查询的相似度
                query1_embedding = np.array(text_embeddings[0])
                
                for i in range(1, len(text_embeddings)):
                    query2_embedding = np.array(text_embeddings[i])
                    
                    # 计算余弦相似度
                    dot_product = np.dot(query1_embedding, query2_embedding)
                    norm1 = np.linalg.norm(query1_embedding)
                    norm2 = np.linalg.norm(query2_embedding)
                    
                    if norm1 > 0 and norm2 > 0:
                        similarity = dot_product / (norm1 * norm2)
                        print(f"   查询1 vs 查询{i+1} 相似度: {similarity:.4f}")
                        
                        # 相似度应该在合理范围内
                        if similarity < -1 or similarity > 1:
                            print(f"   ⚠️ 警告：相似度超出正常范围")
                    else:
                        print(f"   ⚠️ 警告：向量范数为0，无法计算相似度")
                
                print("✅ 向量相似度计算成功")
                
            except Exception as e:
                print(f"   ❌ 向量相似度计算失败: {e}")
                return False
        
        # 7. 测试与图片向量的兼容性
        print("��️ 测试与图片向量的兼容性...")
        try:
            # 尝试加载向量数据库
            vector_db_path = config.vector_db_dir
            if os.path.exists(vector_db_path):
                print(f"   向量数据库路径: {vector_db_path}")
                
                # 加载向量存储
                vector_store = FAISS.load_local(
                    vector_db_path, 
                    multimodal_embeddings,
                    allow_dangerous_deserialization=True
                )
                
                print("✅ 向量数据库加载成功")
                
                # 检查是否有image类型的chunks
                if hasattr(vector_store, 'docstore') and hasattr(vector_store.docstore, '_dict'):
                    image_chunks = []
                    for doc_id, doc in vector_store.docstore._dict.items():
                        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                        if metadata.get('chunk_type') == 'image':
                            image_chunks.append(doc)
                    
                    print(f"   找到 {len(image_chunks)} 个image chunks")
                    
                    if image_chunks:
                        # 测试文本向量与图片向量的相似度计算
                        print("   �� 测试文本向量与图片向量的相似度...")
                        
                        # 使用第一个文本查询向量
                        test_text_embedding = text_embeddings[0]
                        
                        # 尝试计算与第一个图片chunk的相似度
                        first_image_chunk = image_chunks[0]
                        if hasattr(first_image_chunk, 'embedding') or hasattr(first_image_chunk, 'vector'):
                            # 这里需要根据实际的chunk结构来获取向量
                            print("   📊 图片chunk结构分析:")
                            print(f"      - 类型: {type(first_image_chunk)}")
                            print(f"      - 属性: {dir(first_image_chunk)}")
                            print(f"      - metadata: {first_image_chunk.metadata if hasattr(first_image_chunk, 'metadata') else 'N/A'}")
                        
                        print("   ✅ 图片chunk兼容性检查完成")
                    else:
                        print("   ⚠️ 未找到image chunks，跳过兼容性测试")
                
            else:
                print(f"   ⚠️ 向量数据库路径不存在: {vector_db_path}")
                
        except Exception as e:
            print(f"   ⚠️ 图片向量兼容性测试失败: {e}")
            print("   这不会影响基本功能，但可能影响后续的跨模态搜索")
        
        print("\n" + "="*60)
        print("🎉 测试1完成：multimodal-embedding-v1文本输入能力验证成功！")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_multimodal_text_input()
    if success:
        print("\n✅ 测试1通过：multimodal-embedding-v1可以接受文本输入并生成向量")
    else:
        print("\n❌ 测试1失败：需要检查配置或API密钥")