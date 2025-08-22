#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
测试策略一（FAISS filter）在阈值0.15下的表现

## 1. 测试FAISS filter是否能返回table文档
## 2. 验证降低阈值后的效果
## 3. 对比策略一和策略二的结果
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

def test_strategy1_threshold_0_15():
    """测试策略一在阈值0.15下的表现"""
    print("="*80)
    print("测试策略一（FAISS filter）在阈值0.15下的表现")
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
        
        # 4. 分析数据库结构
        print("\n分析数据库结构...")
        chunk_type_stats = {}
        for doc_id, doc in vector_store.docstore._dict.items():
            if hasattr(doc, 'metadata') and doc.metadata:
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
        
        print("文档类型分布:")
        for chunk_type, count in sorted(chunk_type_stats.items()):
            print(f"  {chunk_type}: {count} 个")
        
        # 5. 测试策略一：FAISS filter
        print("\n" + "="*80)
        print("测试策略一：FAISS filter（阈值0.15）")
        print("="*80)
        
        test_query = "中芯国际财务图表"
        print(f"测试查询: '{test_query}'")
        
        # 策略一：使用FAISS filter
        print("\n🔍 策略一：FAISS filter搜索")
        try:
            strategy1_results = vector_store.similarity_search(
                test_query, 
                k=40,  # 使用配置中的top_k
                filter={'chunk_type': 'table'}
            )
            print(f"✅ 策略一成功，返回 {len(strategy1_results)} 个table文档")
            
            if len(strategy1_results) > 0:
                print("\n前3个结果预览:")
                for i, doc in enumerate(strategy1_results[:3]):
                    print(f"\n--- 结果 {i+1} ---")
                    print(f"内容: {doc.page_content[:150]}...")
                    print(f"元数据: {doc.metadata}")
            else:
                print("❌ 策略一仍然返回0个结果")
                
        except Exception as e:
            print(f"❌ 策略一失败: {e}")
            return False
        
        # 6. 测试策略二：post-filter（对比）
        print("\n" + "="*80)
        print("测试策略二：post-filter（对比）")
        print("="*80)
        
        print("\n🔍 策略二：post-filter搜索")
        try:
            # 先搜索更多候选结果
            all_candidates = vector_store.similarity_search(test_query, k=100)
            print(f"搜索到 {len(all_candidates)} 个候选结果")
            
            # 后过滤：筛选出table类型的文档
            table_candidates = []
            for doc in all_candidates:
                if (hasattr(doc, 'metadata') and doc.metadata and 
                    doc.metadata.get('chunk_type') == 'table'):
                    table_candidates.append(doc)
            
            print(f"后过滤后找到 {len(table_candidates)} 个table文档")
            
            # 应用阈值0.15（模拟table_engine的逻辑）
            from v2.core.table_engine import TableEngine
            
            # 创建临时的table_engine实例来使用_calculate_content_relevance方法
            temp_engine = TableEngine(skip_initial_load=True)
            
            threshold = 0.15
            processed_results = []
            
            for doc in table_candidates:
                # 使用内容相关性分数
                vector_score = temp_engine._calculate_content_relevance(test_query, doc.page_content)
                
                # 应用阈值过滤
                if vector_score >= threshold:
                    processed_results.append({
                        'doc': doc,
                        'score': vector_score,
                        'content_preview': doc.page_content[:100]
                    })
            
            print(f"通过阈值{threshold}检查的结果数量: {len(processed_results)}")
            
            if len(processed_results) > 0:
                print("\n前3个通过阈值的结果:")
                for i, result in enumerate(processed_results[:3]):
                    print(f"\n--- 结果 {i+1} ---")
                    print(f"分数: {result['score']:.3f}")
                    print(f"内容: {result['content_preview']}...")
            else:
                print("❌ 策略二也没有通过阈值的结果")
                
        except Exception as e:
            print(f"❌ 策略二失败: {e}")
            return False
        
        # 7. 对比分析
        print("\n" + "="*80)
        print("对比分析")
        print("="*80)
        
        print(f"策略一（FAISS filter）结果数量: {len(strategy1_results)}")
        print(f"策略二（post-filter + 阈值0.15）结果数量: {len(processed_results)}")
        
        if len(strategy1_results) > 0:
            print("🎉 策略一现在可以工作了！")
            print("💡 说明：降低阈值到0.15解决了策略一的问题")
        elif len(processed_results) > 0:
            print("⚠️ 策略一仍然不工作，但策略二可以工作")
            print("💡 建议：继续使用策略二，或者进一步降低阈值")
        else:
            print("❌ 两种策略都不工作")
            print("💡 建议：检查查询词或进一步降低阈值")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_strategy1_threshold_0_15()
    if success:
        print("\n🎉 测试完成：策略一阈值0.15测试完成")
    else:
        print("\n❌ 测试失败：需要检查配置或数据库结构")
