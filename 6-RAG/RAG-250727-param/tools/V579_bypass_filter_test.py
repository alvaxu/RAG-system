'''
程序说明：
## 1. 绕过过滤引擎直接测试向量检索
## 2. 检查各个过滤步骤的影响
## 3. 验证检索功能是否正常
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.enhanced_qa_system import load_enhanced_qa_system
from core.memory_manager import MemoryManager

def test_bypass_filters():
    """绕过过滤测试检索"""
    print("="*60)
    print("🔍 绕过过滤引擎测试检索")
    print("="*60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        print(f"✅ 配置加载成功")
        
        # 初始化记忆管理器
        memory_manager = MemoryManager(config.memory_db_dir)
        
        # 加载QA系统
        qa_system = load_enhanced_qa_system(
            config.vector_db_dir, 
            config.dashscope_api_key, 
            memory_manager, 
            config.to_dict()
        )
        
        if not qa_system or not qa_system.vector_store:
            print(f"❌ QA系统或向量存储加载失败")
            return
        
        print(f"✅ QA系统加载成功")
        print(f"   向量存储文档数: {len(qa_system.vector_store.docstore._dict)}")
        
        # 测试问题
        test_questions = [
            "中芯国际",
            "中芯国际的财务数据",
            "产能利用率",
            "财务报表"
        ]
        
        for question in test_questions:
            print(f"\n🔍 测试问题: {question}")
            
            # 1. 直接向量检索（绕过所有过滤）
            try:
                k = config.to_dict().get('vector_store', {}).get('similarity_top_k', 5)
                direct_results = qa_system.vector_store.similarity_search(question, k=k)
                print(f"✅ 直接检索成功，找到 {len(direct_results)} 个结果")
                
                for i, doc in enumerate(direct_results[:2]):  # 只显示前2个
                    print(f"   结果 {i+1}: {doc.page_content[:100]}...")
                    
            except Exception as e:
                print(f"❌ 直接检索失败: {e}")
            
            # 2. 测试初始检索（只绕过后续过滤）
            try:
                initial_docs = qa_system._initial_retrieval(question, k)
                print(f"✅ 初始检索成功，找到 {len(initial_docs)} 个结果")
                
            except Exception as e:
                print(f"❌ 初始检索失败: {e}")
            
            # 3. 测试完整流程
            try:
                result = qa_system.answer_question(question, k=k)
                print(f"✅ 完整流程成功")
                print(f"   最终源数量: {len(result.get('sources', []))}")
                print(f"   答案长度: {len(result.get('answer', ''))}")
                
            except Exception as e:
                print(f"❌ 完整流程失败: {e}")
        
        # 4. 检查过滤配置
        print(f"\n🔍 检查过滤配置:")
        processing_config = config.to_dict().get('processing', {})
        vector_config = config.to_dict().get('vector_store', {})
        qa_config = config.to_dict().get('qa_system', {})
        
        print(f"   智能过滤启用: {processing_config.get('enable_smart_filtering', True)}")
        print(f"   语义相似度阈值: {processing_config.get('semantic_similarity_threshold', 0.2)}")
        print(f"   内容相关性阈值: {processing_config.get('content_relevance_threshold', 0.02)}")
        print(f"   最大过滤结果: {processing_config.get('max_filtered_results', 5)}")
        print(f"   相似度阈值: {vector_config.get('similarity_threshold', 0.3)}")
        print(f"   最小相似度阈值: {vector_config.get('min_similarity_threshold', 0.01)}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bypass_filters() 