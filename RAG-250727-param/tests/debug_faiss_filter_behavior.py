'''
程序说明：
## 1. 深入分析FAISS filter的行为差异
## 2. 对比filter策略和post-filter策略的结果差异
## 3. 找出为什么相同阈值下filter策略失败而post-filter成功
'''

import os
import sys
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def debug_faiss_filter_behavior():
    """深入分析FAISS filter的行为差异"""
    print("🔍 深入分析FAISS filter的行为差异")
    print("=" * 80)
    
    try:
        # 1. 加载向量数据库
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        from config.api_key_manager import get_dashscope_api_key
        
        # 初始化embeddings
        api_key = get_dashscope_api_key()
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        
        # 加载向量数据库
        vector_db_path = "central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        print("✅ 向量数据库加载成功")
        
        # 2. 测试查询
        test_query = "中芯国际的营业收入从2017年到2024年的变化趋势 如何？"
        print(f"测试查询: {test_query}")
        
        # 3. 测试策略1：FAISS filter
        print("\n📋 策略1：FAISS filter测试")
        print("-" * 40)
        
        try:
            # 使用与table_engine相同的参数
            filter_search_k = 200
            filter_results = vector_store.similarity_search(
                test_query, 
                k=filter_search_k,
                filter={'chunk_type': 'table'}
            )
            print(f"FAISS filter结果数量: {len(filter_results)}")
            
            if filter_results:
                print("FAISS filter结果示例:")
                for i, doc in enumerate(filter_results[:3]):
                    chunk_type = doc.metadata.get('chunk_type', 'N/A') if hasattr(doc, 'metadata') and doc.metadata else 'N/A'
                    print(f"  结果{i+1}: chunk_type={chunk_type}")
            else:
                print("⚠️ FAISS filter返回0个结果")
                
        except Exception as e:
            print(f"FAISS filter失败: {e}")
        
        # 4. 测试策略2：无filter + 手动筛选
        print("\n📋 策略2：无filter + 手动筛选测试")
        print("-" * 40)
        
        try:
            search_k = 150
            all_candidates = vector_store.similarity_search(
                test_query, 
                k=search_k
            )
            print(f"无filter搜索结果数量: {len(all_candidates)}")
            
            # 手动筛选table类型
            table_candidates = []
            for doc in all_candidates:
                if (hasattr(doc, 'metadata') and doc.metadata and 
                    doc.metadata.get('chunk_type') == 'table'):
                    table_candidates.append(doc)
            
            print(f"手动筛选后table文档数量: {len(table_candidates)}")
            
            if table_candidates:
                print("手动筛选结果示例:")
                for i, doc in enumerate(table_candidates[:3]):
                    chunk_type = doc.metadata.get('chunk_type', 'N/A')
                    print(f"  结果{i+1}: chunk_type={chunk_type}")
                    
        except Exception as e:
            print(f"无filter搜索失败: {e}")
        
        # 5. 分析差异原因
        print("\n🔍 分析差异原因")
        print("-" * 40)
        
        print("可能的原因:")
        print("1. FAISS filter可能对向量相似度有额外的限制")
        print("2. Filter可能只返回相似度最高的结果，而我们的查询与table文档相似度较低")
        print("3. FAISS filter的实现可能与预期不同")
        print("4. 可能存在索引配置问题")
        
        # 6. 测试不同相似度阈值下的filter行为
        print("\n📋 测试不同相似度阈值下的filter行为")
        print("-" * 40)
        
        # 检查是否有similarity_search_with_score方法
        if hasattr(vector_store, 'similarity_search_with_score'):
            try:
                print("使用similarity_search_with_score分析相似度分布...")
                docs_and_scores = vector_store.similarity_search_with_score(
                    test_query, 
                    k=50
                )
                
                # 分析相似度分布
                scores = [score for _, score in docs_and_scores]
                if scores:
                    min_score = min(scores)
                    max_score = max(scores)
                    avg_score = sum(scores) / len(scores)
                    print(f"相似度分布: 最小={min_score:.4f}, 最大={max_score:.4f}, 平均={avg_score:.4f}")
                    
                    # 检查table文档的相似度
                    table_scores = []
                    for doc, score in docs_and_scores:
                        if (hasattr(doc, 'metadata') and doc.metadata and 
                            doc.metadata.get('chunk_type') == 'table'):
                            table_scores.append(score)
                    
                    if table_scores:
                        table_min = min(table_scores)
                        table_max = max(table_scores)
                        table_avg = sum(table_scores) / len(table_scores)
                        print(f"Table文档相似度: 最小={table_min:.4f}, 最大={table_max:.4f}, 平均={table_avg:.4f}")
                        
                        # 检查是否有table文档的相似度足够高
                        high_similarity_table = [s for s in table_scores if s > 0.5]
                        print(f"相似度>0.5的table文档数量: {len(high_similarity_table)}")
                    else:
                        print("没有找到table文档")
                        
            except Exception as e:
                print(f"similarity_search_with_score失败: {e}")
        else:
            print("❌ 不支持similarity_search_with_score方法")
        
        # 7. 结论和建议
        print("\n🎯 结论和建议")
        print("-" * 40)
        
        print("基于测试结果，建议:")
        print("1. 检查FAISS filter的实现机制")
        print("2. 考虑调整filter策略的搜索参数")
        print("3. 可能需要结合filter和post-filter的混合策略")
        print("4. 进一步分析向量相似度的分布特征")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_faiss_filter_behavior()
