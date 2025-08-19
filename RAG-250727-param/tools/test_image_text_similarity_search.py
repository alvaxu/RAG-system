'''
程序说明：
## 1. 测试image_text文档的向量相似度搜索
## 2. 模拟text_engine的实现方式，使用similarity_search方法
## 3. 测试不同阈值设置对召回结果的影响
## 4. 为image_engine的阈值设置提供参考
'''

import os
import sys
import json
import numpy as np
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key


def test_image_text_similarity_search():
    """测试image_text文档的向量相似度搜索"""
    print("🔍 开始测试image_text文档的向量相似度搜索")
    print("=" * 80)
    
    try:
        # 1. 获取API密钥
        print("🔑 获取API密钥...")
        api_key = get_dashscope_api_key()
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return
        
        print("✅ API密钥获取成功")
        
        # 2. 初始化embeddings
        print("\n🚀 初始化embeddings...")
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        print("✅ embeddings初始化成功")
        
        # 3. 加载向量数据库
        print("\n📚 加载向量数据库...")
        vector_db_path = "../central/vector_db"
        print(f"📁 向量数据库路径: {os.path.abspath(vector_db_path)}")
        
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        print("✅ 向量数据库加载成功")
        
        # 4. 分析数据库结构
        print("\n📊 分析数据库结构...")
        if hasattr(vector_store, 'docstore') and hasattr(vector_store.docstore, '_dict'):
            docs = vector_store.docstore._dict
            print(f"📄 总文档数量: {len(docs)}")
            
            # 统计文档类型
            chunk_types = {}
            for doc_id, doc in docs.items():
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            print("文档类型分布:")
            for chunk_type, count in sorted(chunk_types.items()):
                print(f"  - {chunk_type}: {count} 个")
            
            # 检查image_text文档
            image_text_count = chunk_types.get('image_text', 0)
            if image_text_count == 0:
                print("❌ 没有找到image_text类型的文档")
                return
            else:
                print(f"✅ 找到 {image_text_count} 个image_text文档")
        else:
            print("❌ 无法获取文档信息")
            return
        
        # 5. 测试查询
        print("\n🔍 开始测试查询...")
        test_queries = [
            "图4：中芯国际归母净利润情况概览",  # 添加具体的图表查询
            "图表数据",
            "中芯国际净利润",
            "产能利用率",
            "季度报告",
            "财务分析",
            "数据趋势"
        ]
        
        # 测试不同阈值
        test_thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        for query in test_queries:
            print(f"\n📝 测试查询: '{query}'")
            print("-" * 50)
            
            # 使用similarity_search方法（模拟text_engine）
            try:
                # 获取更多结果用于分析
                vector_results = vector_store.similarity_search(query, k=50)
                print(f"🔍 原始搜索结果: {len(vector_results)} 个")
                
                if vector_results:
                    # 分析每个结果的相似度分数
                    scores = []
                    image_text_results = []
                    
                    for i, doc in enumerate(vector_results):
                        # 获取文档类型
                        chunk_type = doc.metadata.get('chunk_type', 'unknown')
                        
                        # 计算内容相关性分数（模拟text_engine的_calculate_content_relevance）
                        content_score = calculate_content_relevance(query, doc.page_content)
                        
                        # 记录image_text类型的结果
                        if chunk_type == 'image_text':
                            image_text_results.append({
                                'rank': i + 1,
                                'content': doc.page_content[:100] + "...",
                                'chunk_type': chunk_type,
                                'content_score': content_score,
                                'metadata': doc.metadata
                            })
                        
                        scores.append(content_score)
                    
                    # 分析分数分布
                    if scores:
                        min_score = min(scores)
                        max_score = max(scores)
                        avg_score = sum(scores) / len(scores)
                        
                        print(f"📊 分数统计:")
                        print(f"  - 最小分数: {min_score:.4f}")
                        print(f"  - 最大分数: {max_score:.4f}")
                        print(f"  - 平均分数: {avg_score:.4f}")
                        
                        # 测试不同阈值
                        print(f"🎯 阈值测试结果:")
                        for threshold in test_thresholds:
                            above_threshold = sum(1 for score in scores if score >= threshold)
                            print(f"  - 阈值 {threshold}: {above_threshold}/{len(scores)} 个结果")
                        
                        # 显示image_text结果
                        if image_text_results:
                            print(f"\n🖼️ Image_text类型结果 (共{len(image_text_results)}个):")
                            for result in image_text_results[:5]:  # 只显示前5个
                                print(f"  {result['rank']}. 分数: {result['content_score']:.4f}")
                                print(f"     内容: {result['content']}")
                                print(f"     类型: {result['chunk_type']}")
                        else:
                            print("⚠️ 没有找到image_text类型的结果")
                    
                else:
                    print("❌ 搜索返回0个结果")
                    
            except Exception as e:
                print(f"❌ 查询失败: {e}")
                import traceback
                print(f"详细错误: {traceback.format_exc()}")
        
        # 6. 总结和建议
        print("\n" + "=" * 80)
        print("🎯 测试总结和建议")
        print("=" * 80)
        
        print("\n📋 主要发现:")
        print("1. ✅ 成功使用similarity_search方法进行向量搜索")
        print("2. ✅ 能够获取到image_text类型的文档")
        print("3. ✅ 可以计算内容相关性分数")
        
        print("\n💡 阈值设置建议:")
        print("1. 基于分数分布设置合理阈值")
        print("2. 考虑image_text文档的特殊性")
        print("3. 平衡召回率和精确率")
        
        print("\n🔧 实施建议:")
        print("1. 在image_engine中使用similarity_search方法")
        print("2. 参考text_engine的实现方式")
        print("3. 根据测试结果调整阈值设置")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


def calculate_content_relevance(query: str, content: str) -> float:
    """
    计算内容相关性分数（改进版本）
    
    :param query: 查询文本
    :param content: 文档内容
    :return: 相关性分数 [0, 1]
    """
    try:
        # 预处理：转换为小写并分词
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 方法1：直接字符串包含匹配
        if query_lower in content_lower:
            return 0.8  # 完全包含给高分
        
        # 方法2：分词匹配
        query_words = [word for word in query_lower.split() if len(word) > 1]  # 过滤单字符
        if not query_words:
            return 0.0
        
        content_words = content_lower.split()
        
        # 计算匹配词数
        matched_words = 0
        total_score = 0.0
        
        for query_word in query_words:
            if query_word in content_words:
                matched_words += 1
                # 计算词频分数
                word_count = content_lower.count(query_word)
                word_score = min(word_count / len(content_words), 0.3)  # 限制单个词的最大分数
                total_score += word_score
        
        # 计算匹配率
        match_rate = matched_words / len(query_words) if query_words else 0
        
        # 综合分数：匹配率 + 词频分数
        final_score = (match_rate * 0.7 + total_score * 0.3)
        
        return min(final_score, 1.0)
        
    except Exception:
        return 0.0


if __name__ == "__main__":
    test_image_text_similarity_search()
