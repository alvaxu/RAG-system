#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
准确验证FAISS Filter是否真正生效

目标：
1. 验证Filter是否真的能过滤出指定类型的文档
2. 检查向量搜索本身是否有问题
3. 确认文档类型分布和查询匹配情况
"""

import os
import sys
import json
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_filter_accuracy():
    """准确验证Filter功能"""
    print("="*80)
    print("准确验证FAISS Filter是否真正生效")
    print("="*80)
    
    try:
        # 1. 导入必要模块
        print("导入必要模块...")
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        from config.api_key_manager import get_dashscope_api_key
        from config.settings import Settings
        
        print("✅ 模块导入成功")
        
        # 2. 获取配置和API密钥
        print("获取配置和API密钥...")
        try:
            old_cwd = os.getcwd()
            os.chdir(project_root)
            config = Settings.load_from_file('config.json')
            os.chdir(old_cwd)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            return False
        
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        if not api_key:
            print("未找到有效的DashScope API密钥")
            return False
        
        print("✅ 配置和API密钥获取成功")
        
        # 3. 加载向量数据库
        print("加载向量数据库...")
        try:
            text_embeddings = DashScopeEmbeddings(
                dashscope_api_key=api_key,
                model='text-embedding-v1'
            )
            
            vector_db_path = config.vector_db_dir
            vector_store = FAISS.load_local(
                vector_db_path, 
                text_embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"✅ 向量数据库加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
            
        except Exception as e:
            print(f"❌ 向量数据库加载失败: {e}")
            return False
        
        # 4. 分析文档类型分布
        print("\n分析文档类型分布...")
        chunk_type_stats = {}
        chunk_type_samples = {}
        
        for doc_id, doc in vector_store.docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
                
                # 保存每种类型的样本
                if chunk_type not in chunk_type_samples:
                    chunk_type_samples[chunk_type] = []
                if len(chunk_type_samples[chunk_type]) < 3:  # 每种类型保存3个样本
                    chunk_type_samples[chunk_type].append({
                        'id': doc_id,
                        'content': doc.page_content[:100] + '...' if len(doc.page_content) > 100 else doc.page_content,
                        'metadata': doc.metadata
                    })
        
        print("文档类型分布:")
        for chunk_type, count in sorted(chunk_type_stats.items()):
            print(f"  {chunk_type}: {count} 个")
        
        # 5. 显示样本内容
        print("\n各类型文档样本:")
        for chunk_type, samples in chunk_type_samples.items():
            print(f"\n{chunk_type}类型样本:")
            for i, sample in enumerate(samples):
                print(f"  样本{i+1}: {sample['content']}")
        
        # 6. 测试Filter功能
        print("\n测试Filter功能...")
        
        # 使用更合适的查询
        test_queries = [
            "中芯国际",
            "财务报表",
            "图表分析",
            "数据统计"
        ]
        
        for query in test_queries:
            print(f"\n--- 测试查询: {query} ---")
            
            # 无filter搜索
            try:
                no_filter_results = vector_store.similarity_search(query, k=10)
                print(f"  无filter结果数量: {len(no_filter_results)}")
                
                # 分析结果类型分布
                result_types = {}
                for doc in no_filter_results:
                    chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                    result_types[chunk_type] = result_types.get(chunk_type, 0) + 1
                
                print(f"  无filter结果类型分布: {result_types}")
                
                # 显示前几个结果的内容
                for i, doc in enumerate(no_filter_results[:3]):
                    chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                    print(f"    结果{i+1} ({chunk_type}): {doc.page_content[:80]}...")
                
            except Exception as e:
                print(f"  无filter搜索失败: {e}")
                continue
            
            # 测试各种filter
            filter_tests = [
                {'chunk_type': 'text'},
                {'chunk_type': 'table'},
                {'chunk_type': 'image'},
                {'chunk_type': 'image_text'}
            ]
            
            for filter_test in filter_tests:
                try:
                    filter_results = vector_store.similarity_search(query, k=10, filter=filter_test)
                    print(f"  Filter {filter_test}: {len(filter_results)} 个结果")
                    
                    if filter_results:
                        # 验证结果类型
                        all_correct_type = True
                        for doc in filter_results:
                            chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                            expected_type = filter_test['chunk_type']
                            if chunk_type != expected_type:
                                all_correct_type = False
                                print(f"    ❌ 发现类型错误: 期望{expected_type}, 实际{chunk_type}")
                                break
                        
                        if all_correct_type:
                            print(f"    ✅ 所有结果都是{filter_test['chunk_type']}类型")
                        
                        # 显示第一个结果
                        first_doc = filter_results[0]
                        chunk_type = first_doc.metadata.get('chunk_type', 'unknown') if hasattr(first_doc, 'metadata') and first_doc.metadata else 'unknown'
                        print(f"    第一个结果 ({chunk_type}): {first_doc.page_content[:80]}...")
                    
                except Exception as e:
                    print(f"  Filter {filter_test} 失败: {e}")
        
        # 7. 总结分析
        print("\n" + "="*80)
        print("Filter功能准确验证总结")
        print("="*80)
        
        print("🔍 验证结果:")
        print(f"1. 向量数据库总文档数: {len(vector_store.docstore._dict)}")
        print(f"2. 文档类型分布: {chunk_type_stats}")
        
        # 分析Filter是否真的生效
        print("\n💡 Filter功能分析:")
        print("  - 如果Filter返回0个结果，说明Filter可能没有生效")
        print("  - 或者查询和文档类型不匹配")
        print("  - 需要进一步检查向量搜索本身的问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_filter_accuracy()
