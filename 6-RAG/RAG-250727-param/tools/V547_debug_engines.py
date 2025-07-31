'''
程序说明：
## 1. 引擎调试脚本
## 2. 查看具体的分数计算过程
## 3. 分析过滤逻辑
## 4. 找出过度过滤的原因
'''

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.reranking_engine import RerankingEngine
from core.source_filter_engine import SourceFilterEngine
from core.smart_filter_engine import SmartFilterEngine


def debug_reranking_engine():
    """调试重排序引擎"""
    print("=" * 60)
    print("🔍 调试重排序引擎")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        vector_config = {
            'enable_reranking': settings.enable_reranking,
            'reranking_method': settings.reranking_method,
            'semantic_weight': settings.semantic_weight,
            'keyword_weight': settings.keyword_weight,
            'min_similarity_threshold': settings.min_similarity_threshold
        }
        
        print(f"配置参数: {vector_config}")
        
        # 初始化重排序引擎
        reranking_engine = RerankingEngine(vector_config)
        print("✅ 重排序引擎初始化成功")
        
        # 测试数据
        query = "中芯国际的主要业务是什么？"
        documents = [
            {
                'content': '中芯国际是中国大陆最大的晶圆代工企业，主要从事晶圆代工业务。',
                'metadata': {'source': 'doc1'},
                'score': 0.8
            },
            {
                'content': '公司专注于集成电路制造，为客户提供晶圆代工服务。',
                'metadata': {'source': 'doc2'},
                'score': 0.7
            },
            {
                'content': '中芯国际在2024年第一季度业绩表现良好，营收增长显著。',
                'metadata': {'source': 'doc3'},
                'score': 0.6
            }
        ]
        
        print(f"查询: {query}")
        print(f"原始文档数量: {len(documents)}")
        
        # 执行重排序
        reranked_docs = reranking_engine.rerank_results(query, documents)
        
        print(f"重排序后文档数量: {len(reranked_docs)}")
        
        # 显示详细的分数信息
        print("\n📊 详细分数信息:")
        for i, doc in enumerate(documents):
            print(f"文档 {i+1}:")
            print(f"  内容: {doc['content']}")
            print(f"  语义分数: {doc.get('semantic_score', 'N/A')}")
            print(f"  关键词分数: {doc.get('keyword_score', 'N/A')}")
            print(f"  重排序分数: {doc.get('rerank_score', 'N/A')}")
            print(f"  是否保留: {'是' if doc in reranked_docs else '否'}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 重排序引擎调试失败: {e}")
        return False


def debug_source_filter_engine():
    """调试源过滤引擎"""
    print("\n" + "=" * 60)
    print("🔍 调试源过滤引擎")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        qa_config = {
            'enable_sources_filtering': settings.enable_sources_filtering,
            'min_relevance_score': settings.min_relevance_score,
            'enable_keyword_matching': settings.enable_keyword_matching,
            'enable_image_id_matching': settings.enable_image_id_matching,
            'enable_similarity_filtering': settings.enable_similarity_filtering
        }
        
        print(f"配置参数: {qa_config}")
        
        # 初始化源过滤引擎
        source_filter_engine = SourceFilterEngine(qa_config)
        print("✅ 源过滤引擎初始化成功")
        
        # 测试数据
        llm_answer = "中芯国际主要从事晶圆代工业务，为客户提供集成电路制造服务。"
        sources = [
            {
                'content': '中芯国际是中国大陆最大的晶圆代工企业，专注于集成电路制造。',
                'metadata': {'source': 'doc1'},
                'score': 0.8
            },
            {
                'content': '公司2024年第一季度营收增长显著，产能利用率提升。',
                'metadata': {'source': 'doc2'},
                'score': 0.7
            },
            {
                'content': '晶圆代工是半导体产业链的重要环节，中芯国际在该领域具有优势。',
                'metadata': {'source': 'doc3'},
                'score': 0.6
            }
        ]
        
        print(f"LLM回答: {llm_answer}")
        print(f"原始源数量: {len(sources)}")
        
        # 执行源过滤
        filtered_sources = source_filter_engine.filter_sources(llm_answer, sources)
        
        print(f"过滤后源数量: {len(filtered_sources)}")
        
        # 显示详细的分数信息
        print("\n📊 详细分数信息:")
        for i, source in enumerate(sources):
            print(f"源 {i+1}:")
            print(f"  内容: {source['content']}")
            print(f"  相关性分数: {source.get('relevance_score', 'N/A')}")
            print(f"  是否保留: {'是' if source in filtered_sources else '否'}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 源过滤引擎调试失败: {e}")
        return False


def debug_smart_filter_engine():
    """调试智能过滤引擎"""
    print("\n" + "=" * 60)
    print("🔍 调试智能过滤引擎")
    print("=" * 60)
    
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        processing_config = {
            'enable_smart_filtering': settings.enable_smart_filtering,
            'semantic_similarity_threshold': settings.semantic_similarity_threshold,
            'content_relevance_threshold': settings.content_relevance_threshold,
            'max_filtered_results': settings.max_filtered_results
        }
        
        print(f"配置参数: {processing_config}")
        
        # 初始化智能过滤引擎
        smart_filter_engine = SmartFilterEngine(processing_config)
        print("✅ 智能过滤引擎初始化成功")
        
        # 测试数据
        query = "中芯国际的业绩表现如何？"
        documents = [
            {
                'content': '中芯国际2024年第一季度营收增长显著，产能利用率提升至80%以上。',
                'metadata': {'source': 'doc1'},
                'score': 0.8
            },
            {
                'content': '公司晶圆代工业务表现良好，客户需求稳定增长。',
                'metadata': {'source': 'doc2'},
                'score': 0.7
            },
            {
                'content': '中芯国际在先进制程技术方面持续投入，研发进展顺利。',
                'metadata': {'source': 'doc3'},
                'score': 0.6
            },
            {
                'content': '半导体行业整体景气度回升，带动公司业绩改善。',
                'metadata': {'source': 'doc4'},
                'score': 0.5
            }
        ]
        
        print(f"查询: {query}")
        print(f"原始文档数量: {len(documents)}")
        
        # 执行智能过滤
        filtered_docs = smart_filter_engine.smart_filter(query, documents)
        
        print(f"过滤后文档数量: {len(filtered_docs)}")
        
        # 显示详细的分数信息
        print("\n📊 详细分数信息:")
        for i, doc in enumerate(documents):
            scores = doc.get('smart_filter_scores', {})
            print(f"文档 {i+1}:")
            print(f"  内容: {doc['content']}")
            print(f"  内容分数: {scores.get('content_score', 'N/A')}")
            print(f"  语义分数: {scores.get('semantic_score', 'N/A')}")
            print(f"  上下文分数: {scores.get('context_score', 'N/A')}")
            print(f"  意图分数: {scores.get('intent_score', 'N/A')}")
            print(f"  综合分数: {scores.get('final_score', 'N/A')}")
            print(f"  是否保留: {'是' if doc in filtered_docs else '否'}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 智能过滤引擎调试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始引擎调试...")
    
    tests = [
        ("重排序引擎调试", debug_reranking_engine),
        ("源过滤引擎调试", debug_source_filter_engine),
        ("智能过滤引擎调试", debug_smart_filter_engine)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 调试结果总结")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 调试通过率: {passed}/{total} ({passed/total*100:.1f}%)")


if __name__ == "__main__":
    main() 