#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 专门调试FAISS不返回score的问题
## 2. 测试多种FAISS搜索方法
## 3. 检查FAISS配置和版本信息
## 4. 找出score缺失的根本原因
"""

import sys
import os
import logging
import json
from typing import List, Dict, Any

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_faiss_methods(vector_store, query: str, max_results: int = 10):
    """
    调试FAISS的各种搜索方法，找出score缺失的原因
    
    :param vector_store: FAISS向量数据库
    :param query: 查询文本
    :param max_results: 最大结果数
    :return: 调试结果
    """
    print(f"\n🔍 调试查询: {query}")
    print("=" * 80)
    
    results = {
        'query': query,
        'max_results': max_results,
        'methods_tested': [],
        'faiss_info': {},
        'search_results': {},
        'recommendations': []
    }
    
    try:
        # 1. 检查FAISS基本信息
        print("📋 1. 检查FAISS基本信息")
        print("-" * 50)
        
        faiss_info = {
            'vector_store_type': type(vector_store).__name__,
            'has_index': hasattr(vector_store, 'index'),
            'has_docstore': hasattr(vector_store, 'docstore'),
            'has_embedding_function': hasattr(vector_store, 'embedding_function'),
            'docstore_size': len(vector_store.docstore._dict) if hasattr(vector_store, 'docstore') else 0
        }
        
        if hasattr(vector_store, 'index'):
            index = vector_store.index
            faiss_info.update({
                'index_type': type(index).__name__,
                'index_ntotal': getattr(index, 'ntotal', 'N/A'),
                'index_d': getattr(index, 'd', 'N/A'),
                'index_metric_type': getattr(index, 'metric_type', 'N/A'),
                'index_is_trained': getattr(index, 'is_trained', 'N/A')
            })
        
        results['faiss_info'] = faiss_info
        
        for key, value in faiss_info.items():
            print(f"  {key}: {value}")
        
        # 2. 检查可用的搜索方法
        print(f"\n📋 2. 检查可用的搜索方法")
        print("-" * 50)
        
        available_methods = []
        for method_name in dir(vector_store):
            if 'search' in method_name.lower() and callable(getattr(vector_store, method_name)):
                available_methods.append(method_name)
        
        print(f"可用的搜索方法: {available_methods}")
        results['available_methods'] = available_methods
        
        # 3. 测试方法1: similarity_search (当前使用的方法)
        print(f"\n📋 3. 测试方法1: similarity_search")
        print("-" * 50)
        
        try:
            candidates = vector_store.similarity_search(
                query, 
                k=max_results,
                filter={'chunk_type': 'image_text'}
            )
            
            print(f"✅ similarity_search成功，返回 {len(candidates)} 个结果")
            
            # 检查第一个结果的属性
            if candidates:
                first_doc = candidates[0]
                print(f"\n第一个文档的属性分析:")
                print(f"  - 类型: {type(first_doc)}")
                print(f"  - 所有属性: {[attr for attr in dir(first_doc) if not attr.startswith('_')]}")
                print(f"  - 是否有score: {hasattr(first_doc, 'score')}")
                print(f"  - 是否有metadata: {hasattr(first_doc, 'metadata')}")
                
                if hasattr(first_doc, 'metadata'):
                    print(f"  - metadata内容: {first_doc.metadata}")
                
                # 尝试获取score
                score = getattr(first_doc, 'score', None)
                print(f"  - getattr(doc, 'score', None): {score}")
                
                # 尝试从metadata获取score
                if hasattr(first_doc, 'metadata') and first_doc.metadata:
                    metadata_score = first_doc.metadata.get('score', None)
                    print(f"  - doc.metadata.get('score'): {metadata_score}")
                
                results['search_results']['similarity_search'] = {
                    'success': True,
                    'count': len(candidates),
                    'first_doc_analysis': {
                        'has_score': hasattr(first_doc, 'score'),
                        'score_value': score,
                        'metadata_score': metadata_score if 'metadata_score' in locals() else None,
                        'attributes': [attr for attr in dir(first_doc) if not attr.startswith('_')]
                    }
                }
            else:
                print("⚠️ 没有返回结果")
                results['search_results']['similarity_search'] = {
                    'success': True,
                    'count': 0,
                    'first_doc_analysis': None
                }
                
        except Exception as e:
            print(f"❌ similarity_search失败: {e}")
            results['search_results']['similarity_search'] = {
                'success': False,
                'error': str(e)
            }
        
        # 4. 测试方法2: similarity_search_with_score
        print(f"\n📋 4. 测试方法2: similarity_search_with_score")
        print("-" * 50)
        
        try:
            if hasattr(vector_store, 'similarity_search_with_score'):
                docs_and_scores = vector_store.similarity_search_with_score(
                    query, 
                    k=max_results,
                    filter={'chunk_type': 'image_text'}
                )
                
                print(f"✅ similarity_search_with_score成功，返回 {len(docs_and_scores)} 个结果")
                
                if docs_and_scores:
                    first_result = docs_and_scores[0]
                    print(f"\n第一个结果分析:")
                    print(f"  - 类型: {type(first_result)}")
                    print(f"  - 长度: {len(first_result)}")
                    print(f"  - 内容: {first_result}")
                    
                    if len(first_result) == 2:
                        doc, score = first_result
                        print(f"  - 文档类型: {type(doc)}")
                        print(f"  - 分数类型: {type(score)}")
                        print(f"  - 分数值: {score}")
                        
                        # 检查文档是否有score属性
                        print(f"  - doc.score: {getattr(doc, 'score', '不存在')}")
                
                results['search_results']['similarity_search_with_score'] = {
                    'success': True,
                    'count': len(docs_and_scores),
                    'first_result_analysis': {
                        'type': type(docs_and_scores[0]) if docs_and_scores else None,
                        'length': len(docs_and_scores[0]) if docs_and_scores else None,
                        'has_score': len(docs_and_scores[0]) == 2 if docs_and_scores else False
                    }
                }
            else:
                print("❌ 不支持similarity_search_with_score方法")
                results['search_results']['similarity_search_with_score'] = {
                    'success': False,
                    'error': '方法不存在'
                }
                
        except Exception as e:
            print(f"❌ similarity_search_with_score失败: {e}")
            results['search_results']['similarity_search_with_score'] = {
                'success': False,
                'error': str(e)
            }
        
        # 5. 测试方法3: 直接调用FAISS索引
        print(f"\n📋 5. 测试方法3: 直接调用FAISS索引")
        print("-" * 50)
        
        try:
            if hasattr(vector_store, 'index') and hasattr(vector_store, 'embedding_function'):
                # 获取查询向量
                query_embedding = vector_store.embedding_function.embed_query(query)
                print(f"✅ 查询向量生成成功，维度: {len(query_embedding)}")
                
                # 直接调用FAISS索引搜索
                if hasattr(vector_store.index, 'search'):
                    # 搜索最近的向量
                    distances, indices = vector_store.index.search(
                        [query_embedding], 
                        max_results
                    )
                    
                    print(f"✅ 直接FAISS搜索成功")
                    print(f"  - 距离: {distances[0]}")
                    print(f"  - 索引: {indices[0]}")
                    print(f"  - 距离类型: {type(distances[0][0])}")
                    print(f"  - 距离范围: {distances[0].min():.4f} - {distances[0].max():.4f}")
                    
                    # 检查距离是否合理
                    if distances[0].min() < 0.1:
                        print(f"  - 🚨 距离值过小，可能是相似度分数")
                    elif distances[0].max() > 10:
                        print(f"  - 🚨 距离值过大，可能需要转换")
                    else:
                        print(f"  - ✅ 距离值在合理范围内")
                    
                    results['search_results']['direct_faiss_search'] = {
                        'success': True,
                        'distances': distances[0].tolist(),
                        'indices': indices[0].tolist(),
                        'distance_range': f"{distances[0].min():.4f} - {distances[0].max():.4f}"
                    }
                else:
                    print("❌ FAISS索引不支持search方法")
                    results['search_results']['direct_faiss_search'] = {
                        'success': False,
                        'error': '索引不支持search方法'
                    }
            else:
                print("❌ 无法直接调用FAISS索引")
                results['search_results']['direct_faiss_search'] = {
                    'success': False,
                    'error': '缺少必要的属性'
                }
                
        except Exception as e:
            print(f"❌ 直接FAISS搜索失败: {e}")
            results['search_results']['direct_faiss_search'] = {
                'success': False,
                'error': str(e)
            }
        
        # 6. 测试方法4: 检查文档存储
        print(f"\n📋 6. 测试方法4: 检查文档存储")
        print("-" * 50)
        
        try:
            if hasattr(vector_store, 'docstore') and hasattr(vector_store.docstore, '_dict'):
                docstore = vector_store.docstore._dict
                print(f"✅ 文档存储检查成功")
                print(f"  - 文档总数: {len(docstore)}")
                
                # 检查前几个文档
                sample_docs = list(docstore.values())[:3]
                for i, doc in enumerate(sample_docs):
                    print(f"\n  样本文档 {i+1}:")
                    print(f"    - 类型: {type(doc)}")
                    print(f"    - 属性: {[attr for attr in dir(doc) if not attr.startswith('_')]}")
                    print(f"    - 是否有score: {hasattr(doc, 'score')}")
                    
                    if hasattr(doc, 'metadata'):
                        print(f"    - metadata keys: {list(doc.metadata.keys())}")
                        if 'score' in doc.metadata:
                            print(f"    - metadata.score: {doc.metadata['score']}")
                
                results['search_results']['docstore_check'] = {
                    'success': True,
                    'total_docs': len(docstore),
                    'sample_docs_analysis': [
                        {
                            'has_score': hasattr(doc, 'score'),
                            'metadata_keys': list(doc.metadata.keys()) if hasattr(doc, 'metadata') else []
                        }
                        for doc in sample_docs
                    ]
                }
            else:
                print("❌ 无法检查文档存储")
                results['search_results']['docstore_check'] = {
                    'success': False,
                    'error': '缺少docstore属性'
                }
                
        except Exception as e:
            print(f"❌ 文档存储检查失败: {e}")
            results['search_results']['docstore_check'] = {
                'success': False,
                'error': str(e)
            }
        
        # 7. 生成诊断建议
        print(f"\n📋 7. 诊断建议")
        print("-" * 50)
        
        # 分析问题
        if results['search_results'].get('similarity_search_with_score', {}).get('success'):
            results['recommendations'].append("✅ 建议使用similarity_search_with_score方法，它会返回分数")
        else:
            results['recommendations'].append("❌ similarity_search_with_score不可用，需要其他解决方案")
        
        if results['search_results'].get('direct_faiss_search', {}).get('success'):
            distances = results['search_results']['direct_faiss_search'].get('distances', [])
            if distances:
                min_dist = min(distances)
                max_dist = max(distances)
                if min_dist < 0.1:
                    results['recommendations'].append("🚨 FAISS返回的是相似度分数，不是距离")
                elif max_dist > 10:
                    results['recommendations'].append("🚨 FAISS返回的距离值过大，需要转换")
                else:
                    results['recommendations'].append("✅ FAISS返回的距离值在合理范围内")
        
        # 检查是否有score属性
        similarity_search_result = results['search_results'].get('similarity_search', {})
        if similarity_search_result.get('success') and similarity_search_result.get('first_doc_analysis'):
            if not similarity_search_result['first_doc_analysis']['has_score']:
                results['recommendations'].append("❌ similarity_search不返回score属性，这是问题的根源")
        
        # 输出建议
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"  {i}. {rec}")
            
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        results['error'] = str(e)
    
    return results

def test_faiss_score_issue():
    """测试FAISS score问题"""
    print("🔍 调试FAISS Score缺失问题")
    print("=" * 80)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        
        # 加载向量数据库
        print("📚 正在加载向量数据库...")
        
        # 获取API密钥
        config_key = config.dashscope_api_key
        api_key = get_dashscope_api_key(config_key)
        
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return
        
        # 初始化embeddings
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        vector_db_path = config.vector_db_dir
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        print(f"✅ 向量数据库加载成功")
        
        # 测试查询
        test_queries = [
            "图4：中芯国际归母净利润情况概览",  # 控制台输出中的实际查询
            "中芯国际净利润"
        ]
        
        all_results = []
        
        for test_query in test_queries:
            result = debug_faiss_methods(vector_store, test_query, 10)
            all_results.append(result)
        
        # 保存调试结果
        output_file = "faiss_score_debug_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 调试结果已保存到: {output_file}")
        
        # 生成总结报告
        print(f"\n📋 总结报告:")
        print("=" * 60)
        
        # 分析主要发现
        for result in all_results:
            if 'search_results' in result:
                print(f"\n查询: {result['query']}")
                
                # 检查similarity_search_with_score
                with_score_result = result['search_results'].get('similarity_search_with_score', {})
                if with_score_result.get('success'):
                    print(f"  ✅ similarity_search_with_score可用")
                else:
                    print(f"  ❌ similarity_search_with_score不可用")
                
                # 检查直接FAISS搜索
                direct_result = result['search_results'].get('direct_faiss_search', {})
                if direct_result.get('success'):
                    print(f"  ✅ 直接FAISS搜索可用")
                else:
                    print(f"  ❌ 直接FAISS搜索不可用")
        
        print(f"\n🎯 主要发现:")
        print("-" * 40)
        
        # 检查是否有可用的解决方案
        has_solution = False
        for result in all_results:
            if result['search_results'].get('similarity_search_with_score', {}).get('success'):
                has_solution = True
                break
        
        if has_solution:
            print("  ✅ 找到解决方案：使用similarity_search_with_score")
        else:
            print("  ❌ 没有找到直接解决方案，需要手动计算相似度")
        
        print(f"\n📖 详细调试结果请查看: {output_file}")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_faiss_score_issue()
