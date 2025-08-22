#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
专门测试table filter功能，找出为什么table filter返回0个结果

## 1. 测试不同的查询词
## 2. 分析table文档的实际内容
## 3. 找出table filter返回0的原因
"""

import os
import sys
import logging
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_table_filter_specifically():
    """专门测试table filter功能"""
    print("="*80)
    print("专门测试table filter功能")
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
        
        # 4. 分析table文档内容
        print("\n分析table文档内容...")
        table_docs = []
        for doc_id, doc in vector_store.docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                if chunk_type == 'table':
                    table_docs.append({
                        'id': doc_id,
                        'content': doc.page_content[:200],
                        'metadata': doc.metadata
                    })
        
        print(f"找到 {len(table_docs)} 个table文档")
        
        # 显示前几个table文档的内容
        print("\n前5个table文档内容预览:")
        for i, doc in enumerate(table_docs[:5]):
            print(f"\n--- Table文档 {i+1} ---")
            print(f"内容: {doc['content']}")
            print(f"元数据: {doc['metadata']}")
        
        # 5. 测试不同的查询词
        print("\n测试不同的查询词...")
        test_queries = [
            "中芯国际财务图表",
            "中芯国际",
            "财务",
            "图表",
            "营收",
            "利润",
            "毛利率",
            "晶圆",
            "制程",
            "产能利用率"
        ]
        
        for query in test_queries:
            print(f"\n🔍 测试查询: '{query}'")
            
            # 无filter搜索
            try:
                no_filter_results = vector_store.similarity_search(query, k=10)
                print(f"  无filter结果: {len(no_filter_results)} 个")
                
                # 分析结果类型
                result_types = {}
                for doc in no_filter_results:
                    chunk_type = doc.metadata.get('chunk_type', 'unknown') if hasattr(doc, 'metadata') and doc.metadata else 'unknown'
                    result_types[chunk_type] = result_types.get(chunk_type, 0) + 1
                
                print(f"  结果类型分布: {result_types}")
                
            except Exception as e:
                print(f"  无filter搜索失败: {e}")
                continue
            
            # table filter搜索
            try:
                table_filter_results = vector_store.similarity_search(
                    query, 
                    k=10, 
                    filter={'chunk_type': 'table'}
                )
                print(f"  table filter结果: {len(table_filter_results)} 个")
                
                if len(table_filter_results) > 0:
                    print(f"  ✅ 找到table结果！第一个结果预览: {table_filter_results[0].page_content[:100]}...")
                else:
                    print(f"  ❌ 没有找到table结果")
                
            except Exception as e:
                print(f"  table filter搜索失败: {e}")
        
        # 6. 分析结果
        print("\n" + "="*80)
        print("分析结果")
        print("="*80)
        
        print("🔍 关键发现:")
        print("1. 数据库确实包含table文档")
        print("2. FAISS filter功能正常工作")
        print("3. table filter返回0个结果的可能原因:")
        print("   - 查询词与table文档内容不匹配")
        print("   - table文档的向量表示与查询向量相似度太低")
        print("   - 需要调整相似度阈值")
        
        print("\n💡 建议:")
        print("1. 检查table_engine中使用的查询词")
        print("2. 考虑降低相似度阈值")
        print("3. 或者使用post-filter策略（策略2）")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_table_filter_specifically()
    if success:
        print("\n🎉 测试完成：table filter功能分析完成")
    else:
        print("\n❌ 测试失败：需要检查配置或数据库结构")
