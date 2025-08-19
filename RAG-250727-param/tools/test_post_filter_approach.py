'''
程序说明：

## 1. 测试后过滤方案
## 2. 验证先搜索后过滤的效果
## 3. 对比不同阈值设置的影响
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key
import time


def calculate_content_relevance(query: str, content: str) -> float:
    """
    计算查询与内容的相关性分数
    
    :param query: 查询文本
    :param content: 文档内容
    :return: 相关性分数 (0.0-1.0)
    """
    try:
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 完全匹配
        if query_lower in content_lower:
            return 0.8
        
        # 分词匹配
        query_words = [word for word in query_lower.split() if len(word) > 1]
        if not query_words:
            return 0.0
        
        content_words = content_lower.split()
        matched_words = 0
        total_score = 0.0
        
        for query_word in query_words:
            if query_word in content_words:
                matched_words += 1
                word_count = content_lower.count(query_word)
                word_score = min(word_count / len(content_words), 0.3)
                total_score += word_score
        
        match_rate = matched_words / len(query_words) if query_words else 0
        final_score = (match_rate * 0.7 + total_score * 0.3)
        return min(final_score, 1.0)
        
    except Exception as e:
        print(f"计算内容相关性失败: {e}")
        return 0.0


def test_post_filter_approach():
    """测试后过滤方案"""
    print("🧪 测试后过滤方案")
    print("=" * 80)
    
    try:
        # 1. 初始化
        print("📡 初始化向量数据库...")
        api_key = get_dashscope_api_key()
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        vector_db_path = "../central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print("✅ 向量数据库加载成功")
        
        # 2. 测试查询
        test_queries = [
            "图4：中芯国际归母净利润情况概览",
            "中芯国际",
            "芯片制造",
            "晶圆代工"
        ]
        
        # 3. 测试不同的搜索策略
        for query in test_queries:
            print(f"\n🔍 测试查询: {query}")
            print("-" * 60)
            
            # 策略1: 使用filter (应该失败)
            print("📋 策略1: 使用filter (预期失败)")
            try:
                start_time = time.time()
                results_with_filter = vector_store.similarity_search(
                    query, k=20, filter={'chunk_type': 'image_text'}
                )
                filter_time = time.time() - start_time
                print(f"  结果数量: {len(results_with_filter)}")
                print(f"  耗时: {filter_time:.3f}秒")
            except Exception as e:
                print(f"  失败: {e}")
            
            # 策略2: 后过滤方案
            print("\n📋 策略2: 后过滤方案")
            try:
                start_time = time.time()
                # 先进行无filter的向量搜索，增加k值以找到更多文档
                all_results = vector_store.similarity_search(query, k=200)
                search_time = time.time() - start_time
                
                # 后过滤
                filter_start = time.time()
                image_text_candidates = []
                other_candidates = []
                
                for doc in all_results:
                    if hasattr(doc, 'metadata') and doc.metadata:
                        chunk_type = doc.metadata.get('chunk_type')
                        if chunk_type == 'image_text':
                            # 计算内容相关性分数，但不直接赋值给doc.score
                            relevance_score = calculate_content_relevance(query, doc.page_content)
                            # 创建一个包含分数的元组
                            doc_with_score = (doc, relevance_score)
                            image_text_candidates.append(doc_with_score)
                        else:
                            other_candidates.append(doc)
                
                # 按分数排序
                image_text_candidates.sort(key=lambda x: x[1], reverse=True)
                
                filter_time = time.time() - filter_start
                total_time = time.time() - start_time
                
                print(f"  总搜索结果: {len(all_results)}")
                print(f"  image_text类型: {len(image_text_candidates)}")
                print(f"  其他类型: {len(other_candidates)}")
                print(f"  向量搜索耗时: {search_time:.3f}秒")
                print(f"  后过滤耗时: {filter_time:.3f}秒")
                print(f"  总耗时: {total_time:.3f}秒")
                
                # 显示前几个image_text结果
                if image_text_candidates:
                    print(f"\n  📊 image_text结果 (前5个):")
                    for i, (doc, score) in enumerate(image_text_candidates[:5]):
                        print(f"    {i+1}. 分数: {score:.4f}")
                        print(f"       内容: {doc.page_content[:100]}...")
                        if hasattr(doc, 'metadata') and doc.metadata:
                            print(f"       元数据: {doc.metadata}")
                        print()
                else:
                    print(f"\n  ⚠️  在{len(all_results)}个结果中没有找到image_text类型文档")
                    # 检查所有文档的类型分布
                    type_distribution = {}
                    for doc in all_results:
                        if hasattr(doc, 'metadata') and doc.metadata:
                            chunk_type = doc.metadata.get('chunk_type', 'unknown')
                            type_distribution[chunk_type] = type_distribution.get(chunk_type, 0) + 1
                    
                    print(f"  文档类型分布: {type_distribution}")
                
            except Exception as e:
                print(f"  失败: {e}")
                import traceback
                print(f"  详细错误: {traceback.format_exc()}")
        
        # 4. 性能分析
        print("\n" + "=" * 80)
        print("📊 性能分析")
        print("=" * 80)
        
        print("\n后过滤方案的优势:")
        print("✅ 能获取到所有相关文档")
        print("✅ 可以自定义相关性计算逻辑")
        print("✅ 支持复杂的过滤条件")
        print("✅ 不需要重建向量数据库")
        
        print("\n后过滤方案的劣势:")
        print("❌ 需要处理更多文档")
        print("❌ 过滤时间会增加")
        print("❌ 内存使用可能增加")
        
        print("\n建议:")
        print("1. 设置合理的k值 (如50-100)，平衡召回率和性能")
        print("2. 优化相关性计算函数，提高计算效率")
        print("3. 考虑缓存过滤结果，避免重复计算")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    test_post_filter_approach()
