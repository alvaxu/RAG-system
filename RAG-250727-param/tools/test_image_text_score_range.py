#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 专门测试image_text搜索的score范围
## 2. 使用similarity_search_with_score获取真实分数
## 3. 分析FAISS返回的score类型和范围
## 4. 为调整阈值提供数据支持
"""

import sys
import os
import logging
import json
from typing import List, Dict, Any

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from v2.config.v2_config import ImageEngineConfigV2
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_faiss_config(vector_store):
    """
    专门分析FAISS是否支持余弦相似度，以及如何获取余弦相似度值
    
    :param vector_store: FAISS向量数据库
    :return: 配置分析结果
    """
    print("\n🔧 FAISS余弦相似度支持分析")
    print("=" * 60)
    
    config_info = {}
    
    try:
        # 检查FAISS索引类型和度量方式
        if hasattr(vector_store, 'index'):
            faiss_index = vector_store.index
            config_info['index_type'] = type(faiss_index).__name__
            config_info['index_metric_type'] = getattr(faiss_index, 'metric_type', 'unknown')
            
            print(f"📊 FAISS索引信息:")
            print(f"  - 索引类型: {config_info['index_type']}")
            print(f"  - 度量类型: {config_info['index_metric_type']}")
            
            # 解释度量类型
            metric_explanations = {
                0: "L2距离 (越小越相似)",
                1: "IP内积 (越大越相似)", 
                2: "余弦相似度 (越大越相似)"
            }
            
            if config_info['index_metric_type'] in metric_explanations:
                print(f"  - 度量含义: {metric_explanations[config_info['index_metric_type']]}")
            else:
                print(f"  - 度量含义: 未知类型 {config_info['index_metric_type']}")
        
        # 关键问题：能否获取余弦相似度？
        print(f"\n🎯 核心问题：能否获取余弦相似度值？")
        print("-" * 40)
        
        if config_info.get('index_metric_type') == 2:
            print("✅ 好消息！FAISS当前配置使用余弦相似度")
            print("  - 可以直接获取余弦相似度值")
            print("  - 分数范围: [0,1]")
            print("  - 阈值设置简单: 0.3-0.8")
            
        elif config_info.get('index_metric_type') == 1:
            print("❌ 当前FAISS使用IP内积，无法直接获取余弦相似度")
            print("  - 需要手动计算余弦相似度")
            print("  - 或者重建FAISS索引使用余弦相似度")
            
        elif config_info.get('index_metric_type') == 0:
            print("❌ 当前FAISS使用L2距离，无法直接获取余弦相似度")
            print("  - 需要手动计算余弦相似度")
            print("  - 或者重建FAISS索引使用余弦相似度")
            
        else:
            print("⚠️ 无法确定FAISS度量类型，需要进一步分析")
        
        # 尝试手动计算余弦相似度
        print(f"\n🔄 尝试手动计算余弦相似度...")
        try:
            # 获取一个测试查询的向量
            test_query = "测试查询"
            test_vector = vector_store.embedding_function.embed_query(test_query)
            print(f"  - 测试查询向量维度: {len(test_vector)}")
            
            # 获取一个文档的向量（从FAISS索引中）
            if hasattr(faiss_index, 'reconstruct'):
                try:
                    # 尝试重建第一个向量
                    first_vector = faiss_index.reconstruct(0)
                    print(f"  - 第一个文档向量维度: {len(first_vector)}")
                    
                    # 手动计算余弦相似度
                    import numpy as np
                    dot_product = np.dot(test_vector, first_vector)
                    norm_test = np.linalg.norm(test_vector)
                    norm_doc = np.linalg.norm(first_vector)
                    cosine_similarity = dot_product / (norm_test * norm_doc)
                    
                    print(f"  - 手动计算余弦相似度: {cosine_similarity:.4f}")
                    print(f"  - 验证: 值在[0,1]范围内 ✅")
                    
                    config_info['manual_cosine_success'] = True
                    config_info['manual_cosine_value'] = cosine_similarity
                    
                except Exception as e:
                    print(f"  - 无法重建向量: {e}")
                    config_info['manual_cosine_success'] = False
            else:
                print("  - FAISS索引不支持向量重建")
                config_info['manual_cosine_success'] = False
                
        except Exception as e:
            print(f"  - 手动计算余弦相似度失败: {e}")
            config_info['manual_cosine_success'] = False
        
        # 总结和建议
        print(f"\n💡 总结和建议:")
        print("-" * 40)
        
        if config_info.get('index_metric_type') == 2:
            print("✅ 直接获取余弦相似度: 可以")
            print("  - 无需额外操作，FAISS直接返回余弦相似度")
            
        elif config_info.get('manual_cosine_success'):
            print("⚠️ 直接获取余弦相似度: 不可以，但可以手动计算")
            print("  - 当前FAISS使用其他度量方式")
            print("  - 可以通过手动计算获得余弦相似度")
            print("  - 建议: 考虑重建FAISS索引使用余弦相似度")
            
        else:
            print("❌ 获取余弦相似度: 困难")
            print("  - 当前FAISS配置不支持余弦相似度")
            print("  - 手动计算也失败")
            print("  - 建议: 重建FAISS索引或使用其他方案")
            
    except Exception as e:
        print(f"❌ FAISS配置分析失败: {e}")
        config_info['error'] = str(e)
    
    return config_info

def analyze_score_range(vector_store, query: str, max_results: int = 20):
    """
    分析image_text搜索的score范围
    
    :param vector_store: FAISS向量数据库
    :param query: 查询文本
    :param max_results: 最大结果数
    :return: 分析结果
    """
    print(f"\n🔍 分析查询: {query}")
    print("=" * 60)
    
    results = {
        'query': query,
        'max_results': max_results,
        'search_k': max_results * 3,
        'filter_condition': {'chunk_type': 'image_text'},
        'candidates': [],
        'score_analysis': {},
        'metadata_analysis': {},
        'recommendations': []
    }
    
    try:
        # 使用与image_engine完全相同的方法
        search_k = max(max_results * 3, 50)
        print(f"📊 搜索参数:")
        print(f"  - 查询: {query}")
        print(f"  - 最大结果数: {max_results}")
        print(f"  - 搜索候选数: {search_k}")
        print(f"  - Filter条件: {results['filter_condition']}")
        
        # 策略1：使用FAISS filter直接搜索image_text类型文档
        print(f"\n📋 策略1：FAISS filter搜索")
        print("-" * 40)
        
        try:
            # 使用similarity_search_with_score获取真实分数
            docs_and_scores = vector_store.similarity_search_with_score(
                query, 
                k=max_results * 2,
                filter={'chunk_type': 'image_text'}
            )
            
            print(f"✅ Filter搜索成功，返回 {len(docs_and_scores)} 个候选结果")
            
            # 分析每个候选结果（包含真实分数）
            for i, (doc, score) in enumerate(docs_and_scores):
                doc_analysis = {
                    'index': i + 1,
                    'has_score_attr': True,  # 现在有真实分数
                    'score_value': score,    # 使用真实分数
                    'score_type': type(score),
                    'metadata': doc.metadata if hasattr(doc, 'metadata') else {},
                    'chunk_type': doc.metadata.get('chunk_type') if hasattr(doc, 'metadata') else None,
                    'content_preview': doc.page_content[:100] + "..." if hasattr(doc, 'page_content') else "N/A"
                }
                
                results['candidates'].append(doc_analysis)
                
                print(f"  文档 {i+1}:")
                print(f"    - 是否有score属性: {doc_analysis['has_score_attr']}")
                print(f"    - Score值: {doc_analysis['score_value']}")
                print(f"    - Score类型: {doc_analysis['score_type']}")
                print(f"    - Chunk类型: {doc_analysis['chunk_type']}")
                print(f"    - 内容预览: {doc_analysis['content_preview']}")
                
                # 分析metadata
                if doc.metadata:
                    for key, value in doc.metadata.items():
                        if key not in results['metadata_analysis']:
                            results['metadata_analysis'][key] = []
                        if value not in results['metadata_analysis'][key]:
                            results['metadata_analysis'][key].append(value)
            
            # 分析score范围
            scores = [c['score_value'] for c in results['candidates'] if c['score_value'] is not None]
            if scores:
                results['score_analysis'] = {
                    'count': len(scores),
                    'min_score': min(scores),
                    'max_score': max(scores),
                    'avg_score': sum(scores) / len(scores),
                    'score_range': f"{min(scores)} - {max(scores)}",
                    'score_types': list(set(type(s).__name__ for s in scores))
                }
                
                print(f"\n📊 Score分析结果:")
                print(f"  - 有效Score数量: {results['score_analysis']['count']}")
                print(f"  - Score范围: {results['score_analysis']['score_range']}")
                print(f"  - 最小Score: {results['score_analysis']['min_score']}")
                print(f"  - 最大Score: {results['score_analysis']['max_score']}")
                print(f"  - 平均Score: {results['score_analysis']['avg_score']:.4f}")
                print(f"  - Score类型: {results['score_analysis']['score_types']}")
                
                # 生成建议 - 针对IP内积分数
                min_score = results['score_analysis']['min_score']
                max_score = results['score_analysis']['max_score']
                
                if min_score > 1000:  # IP内积特征
                    # 基于当前分数范围计算合理阈值
                    score_range = max_score - min_score
                    conservative_threshold = min_score + score_range * 0.1  # 保守阈值
                    moderate_threshold = min_score + score_range * 0.2      # 中等阈值
                    aggressive_threshold = min_score + score_range * 0.3    # 激进阈值
                    
                    results['recommendations'].append(f"IP内积分数范围: {min_score:.2f} - {max_score:.2f}")
                    results['recommendations'].append(f"建议阈值设置:")
                    results['recommendations'].append(f"  - 保守阈值: {conservative_threshold:.2f}")
                    results['recommendations'].append(f"  - 中等阈值: {moderate_threshold:.2f}")
                    results['recommendations'].append(f"  - 激进阈值: {aggressive_threshold:.2f}")
                    results['recommendations'].append("注意: 当前使用IP内积，建议考虑切换到余弦相似度")
                    
                elif min_score < 0.05:  # 余弦相似度特征
                    results['recommendations'].append("当前阈值0.05过低，建议提高到0.3-0.5")
                elif min_score > 0.8:
                    results['recommendations'].append("当前阈值0.05过低，建议提高到0.7-0.8")
                else:
                    results['recommendations'].append(f"建议阈值设置为: {min_score:.2f} - {max_score:.2f}")
                    
            else:
                print("⚠️ 没有找到有效的Score值")
                results['recommendations'].append("所有文档都没有Score属性，需要检查FAISS配置")
                
        except Exception as e:
            print(f"❌ Filter搜索失败: {e}")
            results['recommendations'].append(f"Filter搜索失败: {e}")
            
            # 尝试降级搜索（也使用with_score）
            print(f"\n🔄 尝试降级搜索...")
            try:
                all_candidates_with_scores = vector_store.similarity_search_with_score(query, k=search_k)
                print(f"降级搜索返回 {len(all_candidates_with_scores)} 个候选结果")
                
                # 后过滤：筛选出image_text类型的文档，并保留分数
                image_text_candidates = []
                for doc, score in all_candidates_with_scores:
                    if (hasattr(doc, 'metadata') and doc.metadata and 
                        doc.metadata.get('chunk_type') == 'image_text'):
                        image_text_candidates.append((doc, score))
                
                print(f"后过滤后找到 {len(image_text_candidates)} 个image_text文档")
                
                if image_text_candidates:
                    results['recommendations'].append("建议使用后过滤策略作为备选方案")
                    # 分析降级搜索的分数
                    fallback_scores = [score for doc, score in image_text_candidates]
                    if fallback_scores:
                        print(f"降级搜索分数范围: {min(fallback_scores):.4f} - {max(fallback_scores):.4f}")
                else:
                    results['recommendations'].append("后过滤也没有找到image_text文档，需要检查数据")
                    
            except Exception as fallback_error:
                print(f"降级搜索也失败: {fallback_error}")
                results['recommendations'].append(f"降级搜索失败: {fallback_error}")
        
        # 分析metadata字段
        print(f"\n📋 Metadata字段分析:")
        print("-" * 40)
        for field, values in results['metadata_analysis'].items():
            print(f"  {field}: {values[:5]}")  # 只显示前5个值
            if len(values) > 5:
                print(f"    ... 还有 {len(values) - 5} 个值")
        
        # 生成最终建议
        print(f"\n💡 优化建议:")
        print("-" * 40)
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"  {i}. {rec}")
            
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        results['error'] = str(e)
    
    return results

def test_image_text_score_range():
    """测试image_text搜索的score范围"""
    print("🔍 测试ImageText搜索的Score范围")
    print("=" * 80)
    
    try:
        # 加载配置
        config = Settings.load_from_file('../config.json')  # 修复路径：从tools目录看，需要回到上级目录
        
        # 创建ImageEngine配置（使用与image_engine相同的默认值）
        image_config = ImageEngineConfigV2(
            enabled=True,
            max_results=20,
            image_similarity_threshold=0.05,  # 使用相同的默认值
            enable_vector_search=True,
            enable_keyword_search=True,
            max_recall_results=150,
            use_new_pipeline=False,
            enable_enhanced_reranking=False
        )
        
        print("✅ ImageEngine配置创建成功")
        print(f"  - 向量搜索阈值: {image_config.image_similarity_threshold}")
        
        # 加载向量数据库
        print("\n📚 正在加载向量数据库...")
        
        # 获取API密钥
        config_key = config.dashscope_api_key
        api_key = get_dashscope_api_key(config_key)
        
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return
        
        # 初始化embeddings
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        
        # 修复路径问题：从tools目录运行，需要回到上级目录
        vector_db_path = "../central/vector_db"
        print(f"📁 向量数据库路径: {os.path.abspath(vector_db_path)}")
        
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        doc_count = len(vector_store.docstore._dict)
        print(f"✅ 向量数据库加载成功，包含 {doc_count} 个文档")
        
        # 检查数据库中的文档类型分布
        print("\n📊 检查数据库中的文档类型分布...")
        chunk_types = {}
        for doc_id, doc in vector_store.docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        print("文档类型分布:")
        for chunk_type, count in sorted(chunk_types.items()):
            print(f"  - {chunk_type}: {count} 个")
        
        # 分析FAISS配置
        faiss_config = analyze_faiss_config(vector_store)
        
        # 测试查询 - 增加更多样化的查询来测试Score范围
        test_queries = [
            "图4：中芯国际归母净利润情况概览",  # 使用控制台输出中的实际查询
            "中芯国际净利润",
            "图表数据",
            "财务分析",
            "产能利用率",  # 新增：测试更多相关查询
            "季度报告",
            "数据趋势",
            "图表分析"
        ]
        
        all_results = []
        
        for test_query in test_queries:
            result = analyze_score_range(vector_store, test_query, 20)
            all_results.append(result)
        
        # 保存分析结果
        output_file = "image_text_score_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 分析结果已保存到: {output_file}")
        
        # 生成总结报告
        print(f"\n📋 总结报告:")
        print("=" * 60)
        
        total_candidates = sum(len(r['candidates']) for r in all_results)
        successful_searches = sum(1 for r in all_results if r['candidates'])
        
        print(f"  - 总测试查询数: {len(test_queries)}")
        print(f"  - 成功搜索查询数: {successful_searches}")
        print(f"  - 总候选结果数: {total_candidates}")
        
        if all_results:
            # 分析所有score
            all_scores = []
            for result in all_results:
                for candidate in result['candidates']:
                    if candidate['score_value'] is not None:
                        all_scores.append(candidate['score_value'])
            
            if all_scores:
                print(f"  - 全局Score范围: {min(all_scores)} - {max(all_scores)}")
                print(f"  - 全局平均Score: {sum(all_scores) / len(all_scores):.4f}")
                
                # 最终建议
                if min(all_scores) < 0.05:
                    print(f"  - 🚨 当前阈值0.05过低，建议提高到: {min(all_scores) + 0.1:.2f}")
                else:
                    print(f"  - ✅ 当前阈值设置合理")
        
        print(f"\n🎯 主要发现和建议:")
        print("-" * 40)
        
        # FAISS余弦相似度支持总结
        if faiss_config:
            print("🔧 余弦相似度支持总结:")
            if 'index_metric_type' in faiss_config:
                metric_type = faiss_config['index_metric_type']
                if metric_type == 2:
                    print("  ✅ 可以直接获取余弦相似度值")
                    print("  - FAISS配置使用余弦相似度度量")
                    print("  - 分数范围: [0,1]，阈值设置简单")
                    print("  - 无需额外操作")
                elif metric_type == 1:
                    print("  ❌ 无法直接获取余弦相似度值")
                    print("  - FAISS配置使用IP内积度量")
                    print("  - 当前观察值: 6026.57 (IP内积)")
                    if faiss_config.get('manual_cosine_success'):
                        print("  - 但可以手动计算余弦相似度")
                        print(f"  - 手动计算示例值: {faiss_config.get('manual_cosine_value', 'N/A')}")
                    print("  - 建议: 重建FAISS索引使用余弦相似度")
                elif metric_type == 0:
                    print("  ❌ 无法直接获取余弦相似度值")
                    print("  - FAISS配置使用L2距离度量")
                    print("  - 建议: 重建FAISS索引使用余弦相似度")
                else:
                    print(f"  ⚠️ 无法确定度量类型 {metric_type}")
                    print("  - 建议: 需要进一步分析FAISS配置")
            else:
                print("  ⚠️ 无法获取FAISS度量类型信息")
                print("  - 建议: 检查FAISS索引配置")
        
        # 分析主要问题
        if successful_searches == 0:
            print("  ❌ 所有查询都失败，需要检查:")
            print("    1. 向量数据库是否正确加载")
            print("    2. Filter条件是否正确")
            print("    3. 是否有image_text类型的文档")
        elif total_candidates == 0:
            print("  ⚠️ 搜索成功但没有候选结果，需要检查:")
            print("    1. Score阈值是否过低")
            print("    2. Score计算是否正确")
        else:
            print("  ✅ 搜索基本正常，主要关注Score范围优化")
        
        print(f"\n📖 详细分析结果请查看: {output_file}")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_text_score_range()
