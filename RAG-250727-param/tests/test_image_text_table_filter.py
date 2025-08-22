#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试image_text和table filter功能

目标：
1. 使用更合适的查询确保image_text和table filter能返回结果
2. 验证Filter是否真的生效
3. 分析查询和文档类型的匹配关系
"""

import os
import sys
import json
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_image_text_table_filter():
    """专门测试image_text和table filter功能"""
    print("="*80)
    print("专门测试image_text和table filter功能")
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
        
        for doc_id, doc in vector_store.docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
        
        print("文档类型分布:")
        for chunk_type, count in sorted(chunk_type_stats.items()):
            print(f"  {chunk_type}: {count} 个")
        
        # 5. 专门测试image_text和table的查询
        print("\n专门测试image_text和table filter...")
        
        # 针对table的查询
        table_queries = [
            "营业收入",
            "净利润",
            "财务数据",
            "市场数据",
            "收益表现",
            "港股指标"
        ]
        
        # 针对image_text的查询
        image_text_queries = [
            "股价走势",
            "产能利用率",
            "月产能",
            "全球部署",
            "季度业绩",
            "图表分析"
        ]
        
        # 测试table filter
        print("\n" + "="*60)
        print("测试Table Filter")
        print("="*60)
        
        for query in table_queries:
            print(f"\n--- 查询: {query} ---")
            
            # 无filter搜索
            try:
                no_filter_results = vector_store.similarity_search(query, k=20)
                print(f"  无filter结果数量: {len(no_filter_results)}")
                
                # 分析结果类型分布
                result_types = {}
                for doc in no_filter_results:
                    chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                    result_types[chunk_type] = result_types.get(chunk_type, 0) + 1
                
                print(f"  无filter结果类型分布: {result_types}")
                
            except Exception as e:
                print(f"  无filter搜索失败: {e}")
                continue
            
            # 测试table filter
            try:
                table_filter_results = vector_store.similarity_search(query, k=20, filter={'chunk_type': 'table'})
                print(f"  table filter结果数量: {len(table_filter_results)}")
                
                if table_filter_results:
                    # 验证结果类型
                    all_table = True
                    for doc in table_filter_results:
                        chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                        if chunk_type != 'table':
                            all_table = False
                            print(f"    ❌ 发现非table类型: {chunk_type}")
                            break
                    
                    if all_table:
                        print(f"    ✅ 所有结果都是table类型")
                    
                    # 显示第一个结果
                    first_doc = table_filter_results[0]
                    print(f"    第一个结果: {first_doc.page_content[:100]}...")
                    
                    # 验证filter是否生效
                    if len(table_filter_results) < len(no_filter_results):
                        print(f"    ✅ Filter生效：结果数量减少 ({len(no_filter_results)} -> {len(table_filter_results)})")
                    else:
                        print(f"    ⚠️ Filter可能未生效：结果数量相同或增加")
                
            except Exception as e:
                print(f"  table filter失败: {e}")
        
        # 测试image_text filter
        print("\n" + "="*60)
        print("测试Image_Text Filter")
        print("="*60)
        
        for query in image_text_queries:
            print(f"\n--- 查询: {query} ---")
            
            # 无filter搜索
            try:
                no_filter_results = vector_store.similarity_search(query, k=20)
                print(f"  无filter结果数量: {len(no_filter_results)}")
                
                # 分析结果类型分布
                result_types = {}
                for doc in no_filter_results:
                    chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                    result_types[chunk_type] = result_types.get(chunk_type, 0) + 1
                
                print(f"  无filter结果类型分布: {result_types}")
                
            except Exception as e:
                print(f"  无filter搜索失败: {e}")
                continue
            
            # 测试image_text filter
            try:
                image_text_filter_results = vector_store.similarity_search(query, k=20, filter={'chunk_type': 'image_text'})
                print(f"  image_text filter结果数量: {len(image_text_filter_results)}")
                
                if image_text_filter_results:
                    # 验证结果类型
                    all_image_text = True
                    for doc in image_text_filter_results:
                        chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                        if chunk_type != 'image_text':
                            all_image_text = False
                            print(f"    ❌ 发现非image_text类型: {chunk_type}")
                            break
                    
                    if all_image_text:
                        print(f"    ✅ 所有结果都是image_text类型")
                    
                    # 显示第一个结果
                    first_doc = image_text_filter_results[0]
                    print(f"    第一个结果: {first_doc.page_content[:100]}...")
                    
                    # 验证filter是否生效
                    if len(image_text_filter_results) < len(no_filter_results):
                        print(f"    ✅ Filter生效：结果数量减少 ({len(no_filter_results)} -> {len(image_text_filter_results)})")
                    else:
                        print(f"    ⚠️ Filter可能未生效：结果数量相同或增加")
                
            except Exception as e:
                print(f"  image_text filter失败: {e}")
        
        # 6. 总结分析
        print("\n" + "="*80)
        print("Image_Text和Table Filter测试总结")
        print("="*80)
        
        print("🔍 测试结果:")
        print(f"1. 向量数据库总文档数: {len(vector_store.docstore._dict)}")
        print(f"2. 文档类型分布: {chunk_type_stats}")
        
        print("\n💡 Filter功能分析:")
        print("  - 如果Filter能返回结果，说明Filter功能正常")
        print("  - 如果Filter返回0个结果，可能是查询不匹配")
        print("  - 需要选择合适的查询来测试Filter功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_image_text_table_filter()
