#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试FAISS Filter功能支持情况

目标：
1. 验证FAISS是否真正支持filter参数
2. 测试不同filter格式的效果
3. 确认filter对搜索结果的影响
"""

import os
import sys
import json
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_faiss_filter_support():
    """测试FAISS Filter功能支持"""
    print("="*80)
    print("测试FAISS Filter功能支持情况")
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
            # 初始化embeddings
            text_embeddings = DashScopeEmbeddings(
                dashscope_api_key=api_key,
                model='text-embedding-v1'
            )
            
            # 加载向量数据库
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
        
        # 5. 测试Filter功能
        print("\n测试Filter功能...")
        test_query = "中芯国际的主要业务"
        
        # 测试1：无filter
        print("\n测试1：无filter搜索")
        try:
            no_filter_results = vector_store.similarity_search(test_query, k=10)
            print(f"  无filter结果数量: {len(no_filter_results)}")
            
            # 分析结果类型
            result_types = {}
            for doc in no_filter_results:
                chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                result_types[chunk_type] = result_types.get(chunk_type, 0) + 1
            
            print(f"  结果类型分布: {result_types}")
            
        except Exception as e:
            print(f"  无filter搜索失败: {e}")
        
        # 测试2：使用filter搜索text类型
        print("\n测试2：使用filter搜索text类型")
        try:
            text_filter_results = vector_store.similarity_search(
                test_query, 
                k=10, 
                filter={'chunk_type': 'text'}
            )
            print(f"  text filter结果数量: {len(text_filter_results)}")
            
            # 验证结果是否都是text类型
            all_text = True
            for doc in text_filter_results:
                chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                if chunk_type != 'text':
                    all_text = False
                    print(f"  发现非text类型文档: {chunk_type}")
                    break
            
            if all_text:
                print("  ✅ 所有结果都是text类型")
            else:
                print("  ❌ 发现非text类型结果")
                
        except Exception as e:
            print(f"  text filter搜索失败: {e}")
            print(f"  错误类型: {type(e)}")
        
        # 测试3：使用filter搜索image_text类型
        print("\n测试3：使用filter搜索image_text类型")
        try:
            image_text_filter_results = vector_store.similarity_search(
                test_query, 
                k=10, 
                filter={'chunk_type': 'image_text'}
            )
            print(f"  image_text filter结果数量: {len(image_text_filter_results)}")
            
            # 验证结果类型
            result_types = {}
            for doc in image_text_filter_results:
                chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                result_types[chunk_type] = result_types.get(chunk_type, 0) + 1
            
            print(f"  结果类型分布: {result_types}")
            
        except Exception as e:
            print(f"  image_text filter搜索失败: {e}")
        
        # 测试4：测试filter是否真的生效
        print("\n测试4：验证filter是否真的生效")
        try:
            # 比较有无filter的结果差异
            if 'no_filter_results' in locals() and 'text_filter_results' in locals():
                no_filter_count = len(no_filter_results)
                text_filter_count = len(text_filter_results)
                
                print(f"  无filter结果数量: {no_filter_count}")
                print(f"  text filter结果数量: {text_filter_count}")
                
                if text_filter_count < no_filter_count:
                    print("  ✅ Filter生效：过滤后结果数量减少")
                elif text_filter_count == no_filter_count:
                    print("  ⚠️ Filter可能未生效：结果数量相同")
                else:
                    print("  ❌ Filter异常：过滤后结果数量增加")
                    
                # 检查结果内容差异
                if text_filter_count > 0:
                    print(f"  第一个text filter结果预览: {text_filter_results[0].page_content[:100]}...")
                    
        except Exception as e:
            print(f"  Filter验证失败: {e}")
        
        # 6. 总结分析
        print("\n" + "="*80)
        print("Filter功能支持分析总结")
        print("="*80)
        
        print("🔍 分析结果:")
        print(f"1. 向量数据库总文档数: {len(vector_store.docstore._dict)}")
        print(f"2. 文档类型分布: {chunk_type_stats}")
        
        if 'text_filter_results' in locals():
            print("3. ✅ Filter功能支持: 是")
            print(f"4. text类型文档数量: {chunk_type_stats.get('text', 0)}")
            print(f"5. Filter后text结果数量: {len(text_filter_results)}")
        else:
            print("3. ❌ Filter功能支持: 否")
        
        print("\n💡 建议:")
        if 'text_filter_results' in locals() and len(text_filter_results) > 0:
            print("  - Filter功能正常工作，可以继续使用策略1")
            print("  - 问题可能在于相似度计算或阈值设置")
        else:
            print("  - Filter功能不支持，需要修改策略1")
            print("  - 直接使用策略2（post-filter）")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_faiss_filter_support()
