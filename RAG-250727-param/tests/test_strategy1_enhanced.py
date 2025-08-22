'''
程序说明：
## 1. 测试修复后的table_engine策略1
## 2. 验证扩大搜索范围是否能突破FAISS filter限制
## 3. 对比策略1和策略2的效果
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

def test_strategy1_enhanced():
    """测试修复后的策略1"""
    print("🔍 测试修复后的table_engine策略1")
    print("=" * 80)
    
    try:
        # 1. 加载table_engine配置
        from v2.config.v2_config import TableEngineConfigV2
        config = TableEngineConfigV2()
        print("✅ 成功加载table_engine配置")
        
        # 2. 测试查询
        test_query = "中芯国际的营业收入从2017年到2024年的变化趋势 如何？"
        print(f"测试查询: {test_query}")
        
        # 3. 测试策略1：FAISS filter（标准范围）
        print("\n📋 策略1：FAISS filter（标准范围）")
        print("-" * 40)
        
        try:
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
            
            # 标准范围filter搜索
            filter_search_k = 200
            standard_filter_results = vector_store.similarity_search(
                test_query, 
                k=filter_search_k,
                filter={'chunk_type': 'table'}
            )
            print(f"标准范围filter结果数量: {len(standard_filter_results)}")
            
            if len(standard_filter_results) > 0:
                print("✅ 标准范围filter成功！")
                for i, doc in enumerate(standard_filter_results[:3]):
                    chunk_type = doc.metadata.get('chunk_type', 'N/A') if hasattr(doc, 'metadata') and doc.metadata else 'N/A'
                    print(f"  结果{i+1}: chunk_type={chunk_type}")
            else:
                print("⚠️ 标准范围filter返回0个结果，尝试扩大搜索范围...")
                
                # 扩大搜索范围
                extended_filter_results = vector_store.similarity_search(
                    test_query, 
                    k=filter_search_k * 3,  # 扩大3倍
                    filter={'chunk_type': 'table'}
                )
                print(f"扩大范围后filter结果数量: {len(extended_filter_results)}")
                
                if len(extended_filter_results) > 0:
                    print("✅ 扩大范围后filter成功！")
                    for i, doc in enumerate(extended_filter_results[:3]):
                        chunk_type = doc.metadata.get('chunk_type', 'N/A') if hasattr(doc, 'metadata') and doc.metadata else 'N/A'
                        print(f"  结果{i+1}: chunk_type={chunk_type}")
                else:
                    print("❌ 即使扩大范围，filter仍然返回0个结果")
                    
        except Exception as e:
            print(f"策略1测试失败: {e}")
        
        # 4. 测试策略2：无filter + 手动筛选（对比）
        print("\n📋 策略2：无filter + 手动筛选（对比）")
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
            print(f"策略2测试失败: {e}")
        
        # 5. 分析结果
        print("\n🎯 分析结果")
        print("-" * 40)
        
        print("基于测试结果:")
        if 'standard_filter_results' in locals() and len(standard_filter_results) > 0:
            print("✅ 策略1（标准范围filter）成功工作")
        elif 'extended_filter_results' in locals() and len(extended_filter_results) > 0:
            print("✅ 策略1（扩大范围filter）成功工作")
        else:
            print("❌ 策略1（filter）完全失败")
            
        if 'table_candidates' in locals() and len(table_candidates) > 0:
            print("✅ 策略2（post-filter）成功工作")
        else:
            print("❌ 策略2（post-filter）失败")
        
        # 6. 结论
        print("\n💡 结论和建议")
        print("-" * 40)
        
        if ('extended_filter_results' in locals() and len(extended_filter_results) > 0) or \
           ('standard_filter_results' in locals() and len(standard_filter_results) > 0):
            print("✅ 策略1可以通过扩大搜索范围来突破FAISS filter限制")
            print("建议：在table_engine中实现自适应搜索范围调整")
        else:
            print("❌ 策略1即使扩大搜索范围也无法工作")
            print("建议：完全依赖策略2（post-filter），或者进一步调查FAISS filter机制")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strategy1_enhanced()
