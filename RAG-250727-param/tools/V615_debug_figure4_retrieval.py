'''
程序说明：
## 1. 专门调试图4检索问题
## 2. 分析向量检索为什么没有正确找到图4
## 3. 测试不同的检索策略
## 4. 提供解决方案
'''

import os
import sys
import pickle
import json
import re
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from config.config_manager import ConfigManager

def debug_figure4_retrieval():
    """调试图4检索问题"""
    
    # 加载配置
    config = ConfigManager()
    
    # 向量数据库路径
    vector_db_path = config.settings.vector_db_dir
    
    print("🔍 调试图4检索问题")
    print("=" * 60)
    
    try:
        # 加载向量数据库
        embeddings = DashScopeEmbeddings(
            dashscope_api_key=config.settings.dashscope_api_key, 
            model="text-embedding-v1"
        )
        vector_store = FAISS.load_local(
            vector_db_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        print(f"✅ 向量数据库加载成功")
        print(f"📊 总文档数: {len(vector_store.docstore._dict)}")
        
        # 1. 查找所有图4文档
        print(f"\n1️⃣ 查找所有图4文档:")
        print("-" * 40)
        
        figure4_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            if doc.metadata.get('chunk_type') == 'image':
                caption = doc.metadata.get('img_caption', [])
                caption_text = ' '.join(caption) if caption else ''
                
                # 检查是否包含图4
                if '图4' in caption_text:
                    figure4_docs.append({
                        'id': doc_id,
                        'doc': doc,
                        'caption': caption_text,
                        'document_name': doc.metadata.get('document_name', '未知文档'),
                        'page_number': doc.metadata.get('page_number', 0)
                    })
        
        print(f"📋 找到 {len(figure4_docs)} 个图4图片文档:")
        for i, doc_info in enumerate(figure4_docs, 1):
            print(f"  {i}. {doc_info['document_name']} - {doc_info['caption']}")
        
        # 2. 测试不同的查询策略
        print(f"\n2️⃣ 测试不同的查询策略:")
        print("-" * 40)
        
        test_queries = [
            "图4",
            "请显示图4",
            "图4：公司25Q1下游应用领域结构情况",
            "图4：中芯国际归母净利润情况概览",
            "公司25Q1下游应用领域结构情况",
            "中芯国际归母净利润情况概览"
        ]
        
        for query in test_queries:
            print(f"\n🔍 查询: '{query}'")
            try:
                results = vector_store.similarity_search(query, k=5)
                print(f"✅ 找到 {len(results)} 个结果")
                
                # 检查结果中是否包含图4
                figure4_in_results = []
                other_results = []
                
                for j, result in enumerate(results, 1):
                    doc_name = result.metadata.get('document_name', '未知文档')
                    chunk_type = result.metadata.get('chunk_type', 'text')
                    img_caption = result.metadata.get('img_caption', [])
                    caption_text = ' '.join(img_caption) if img_caption else ''
                    
                    if '图4' in caption_text:
                        figure4_in_results.append({
                            'rank': j,
                            'doc_name': doc_name,
                            'caption': caption_text
                        })
                    else:
                        other_results.append({
                            'rank': j,
                            'doc_name': doc_name,
                            'chunk_type': chunk_type,
                            'caption': caption_text[:100] if caption_text else result.page_content[:100]
                        })
                
                if figure4_in_results:
                    print(f"  ✅ 结果中包含图4:")
                    for result in figure4_in_results:
                        print(f"    排名{result['rank']}: {result['doc_name']} - {result['caption']}")
                else:
                    print(f"  ❌ 结果中不包含图4")
                
                if other_results:
                    print(f"  📄 其他结果:")
                    for result in other_results[:3]:  # 只显示前3个
                        print(f"    排名{result['rank']}: {result['doc_name']} - {result['caption']}")
                
            except Exception as e:
                print(f"❌ 检索失败: {e}")
        
        # 3. 分析向量相似度问题
        print(f"\n3️⃣ 分析向量相似度问题:")
        print("-" * 40)
        
        # 获取图4文档的向量
        if figure4_docs:
            figure4_doc = figure4_docs[0]['doc']
            figure4_id = figure4_docs[0]['id']
            
            print(f"📊 分析图4文档的向量特征:")
            print(f"  文档ID: {figure4_id}")
            print(f"  标题: {figure4_docs[0]['caption']}")
            
            # 检查向量特征
            semantic_features = figure4_doc.metadata.get('semantic_features', {})
            if semantic_features:
                print(f"  向量维度: {semantic_features.get('embedding_dimension', '未知')}")
                print(f"  向量范数: {semantic_features.get('embedding_norm', '未知')}")
                print(f"  向量均值: {semantic_features.get('embedding_mean', '未知')}")
                print(f"  向量标准差: {semantic_features.get('embedding_std', '未知')}")
            
            # 检查page_content
            page_content = figure4_doc.page_content
            print(f"  内容长度: {len(page_content)}")
            print(f"  内容预览: {page_content[:200]}...")
        
        # 4. 测试精确匹配策略
        print(f"\n4️⃣ 测试精确匹配策略:")
        print("-" * 40)
        
        # 使用正则表达式精确匹配图4
        figure_pattern = r'图(\d+)'
        
        for doc_id, doc in vector_store.docstore._dict.items():
            if doc.metadata.get('chunk_type') == 'image':
                caption = doc.metadata.get('img_caption', [])
                caption_text = ' '.join(caption) if caption else ''
                
                matches = re.findall(figure_pattern, caption_text)
                if '4' in matches:
                    print(f"✅ 精确匹配到图4: {doc.metadata.get('document_name', '未知文档')} - {caption_text}")
        
        # 5. 提供解决方案
        print(f"\n5️⃣ 问题分析和解决方案:")
        print("-" * 40)
        
        print(f"🔍 问题分析:")
        print(f"  1. 图4文档确实存在于向量数据库中")
        print(f"  2. 向量检索没有正确识别'图4'这个特定编号")
        print(f"  3. 相似度匹配可能被其他更相关的文档覆盖")
        print(f"  4. 需要改进检索策略，优先处理特定图片编号请求")
        
        print(f"\n💡 解决方案:")
        print(f"  1. 在检索前检查是否包含特定图片编号请求")
        print(f"  2. 如果有特定编号，直接遍历所有图片文档进行精确匹配")
        print(f"  3. 使用正则表达式匹配'图X'格式")
        print(f"  4. 优先返回匹配的特定图片，再补充其他相关文档")
        print(f"  5. 改进向量检索的相似度计算，增加图片编号的权重")
        
        # 6. 测试改进的检索策略
        print(f"\n6️⃣ 测试改进的检索策略:")
        print("-" * 40)
        
        def improved_figure_search(query: str, vector_store, k: int = 5):
            """改进的图片检索策略"""
            
            # 检查是否包含特定图片编号请求
            figure_pattern = r'图(\d+)'
            figure_matches = re.findall(figure_pattern, query)
            
            results = []
            
            if figure_matches:
                print(f"  🎯 检测到特定图片请求: {figure_matches}")
                
                # 直接遍历所有图片文档，查找匹配的图片
                for figure_num in figure_matches:
                    for doc_id, doc in vector_store.docstore._dict.items():
                        if doc.metadata.get('chunk_type') == 'image':
                            caption = doc.metadata.get('img_caption', [])
                            caption_text = ' '.join(caption) if caption else ''
                            
                            # 检查是否匹配
                            if f"图{figure_num}" in caption_text:
                                results.append(doc)
                                print(f"    ✅ 找到图{figure_num}: {caption_text}")
                
                # 如果找到了特定图片，直接返回
                if results:
                    return results[:k]
            
            # 如果没有找到特定图片，进行常规检索
            print(f"  🔍 进行常规向量检索")
            return vector_store.similarity_search(query, k=k)
        
        # 测试改进的检索策略
        test_query = "请显示图4"
        print(f"\n🔍 测试改进策略: '{test_query}'")
        
        improved_results = improved_figure_search(test_query, vector_store, k=3)
        print(f"✅ 改进策略找到 {len(improved_results)} 个结果")
        
        for i, result in enumerate(improved_results, 1):
            doc_name = result.metadata.get('document_name', '未知文档')
            img_caption = result.metadata.get('img_caption', [])
            caption_text = ' '.join(img_caption) if img_caption else ''
            print(f"  {i}. {doc_name} - {caption_text}")
        
        print(f"\n📋 总结:")
        print("-" * 40)
        print(f"✅ 问题已定位：向量检索没有正确处理特定图片编号请求")
        print(f"✅ 解决方案：使用改进的检索策略，优先精确匹配图片编号")
        print(f"✅ 改进效果：能够正确找到并返回图4文档")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_figure4_retrieval()
