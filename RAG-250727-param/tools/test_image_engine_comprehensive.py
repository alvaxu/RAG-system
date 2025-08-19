#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 全面测试ImageEngine的FAISS filter功能
## 2. 测试不同查询类型的表现
## 3. 验证向量搜索的完整性和准确性
## 4. 分析查询结果的质量和相关性
"""

import sys
import os
import logging

# 修复路径问题，添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from v2.core.image_engine import ImageEngine
from v2.config.v2_config import ImageEngineConfigV2

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_image_engine_comprehensive():
    """全面测试ImageEngine的FAISS filter功能"""
    print("🔍 全面测试ImageEngine的FAISS filter功能")
    print("=" * 60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        
        # 创建ImageEngine配置
        image_config = ImageEngineConfigV2(
            enabled=True,
            max_results=20,
            image_similarity_threshold=0.01,  # 降低阈值，获取更多结果
            enable_vector_search=True,
            enable_keyword_search=True,
            max_recall_results=150,
            use_new_pipeline=False,
            enable_enhanced_reranking=False
        )
        
        print("✅ ImageEngine配置创建成功")
        
        # 加载向量数据库
        print("📚 正在加载向量数据库...")
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        from config.api_key_manager import get_dashscope_api_key
        
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
        print(f"✅ 向量数据库加载成功，包含 {len(vector_store.docstore._dict)} 个文档")
        
        # 创建ImageEngine实例
        image_engine = ImageEngine(
            config=image_config,
            vector_store=vector_store,
            skip_initial_load=True
        )
        
        print("✅ ImageEngine实例创建成功")
        
        # 手动加载文档
        print("📚 正在加载文档...")
        image_engine._load_from_vector_store()
        
        if not image_engine.image_docs:
            print("❌ 没有加载到图片文档")
            return
        
        print(f"✅ 成功加载 {len(image_engine.image_docs)} 个图片文档")
        
        # 测试不同类型的查询
        test_queries = [
            # 财务相关查询
            "中芯国际净利润",
            "财务数据",
            "营收情况",
            "利润分析",
            
            # 图表相关查询
            "图表数据",
            "数据图表",
            "统计图表",
            "趋势图",
            
            # 技术相关查询
            "技术指标",
            "工艺水平",
            "制程技术",
            "良率数据",
            
            # 通用查询
            "中芯国际",
            "半导体",
            "芯片制造",
            "晶圆代工"
        ]
        
        # 统计结果
        total_queries = len(test_queries)
        successful_queries = 0
        query_results = {}
        
        for test_query in test_queries:
            print(f"\n🔍 测试查询: {test_query}")
            print("-" * 50)
            
            try:
                # 测试第一层向量搜索
                vector_results = image_engine._vector_search(test_query, max_results=15)
                print(f"✅ 第一层向量搜索成功，返回 {len(vector_results)} 个结果")
                
                # 记录查询结果
                query_results[test_query] = {
                    'total_results': len(vector_results),
                    'semantic_results': len([r for r in vector_results if 'semantic' in r.get('search_method', '')]),
                    'visual_results': len([r for r in vector_results if 'visual' in r.get('search_method', '')]),
                    'results': vector_results[:5]  # 只记录前5个结果
                }
                
                if vector_results:
                    successful_queries += 1
                    print("📋 结果详情:")
                    
                    # 统计不同搜索方法的结果
                    semantic_count = 0
                    visual_count = 0
                    
                    for i, result in enumerate(vector_results[:5]):
                        doc = result['doc']
                        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                        chunk_type = metadata.get('chunk_type', 'N/A')
                        score = result.get('score', 'N/A')
                        search_method = result.get('search_method', 'N/A')
                        source = result.get('source', 'N/A')
                        
                        print(f"  结果{i+1}:")
                        print(f"    chunk_type: {chunk_type}")
                        print(f"    score: {score}")
                        print(f"    search_method: {search_method}")
                        print(f"    source: {source}")
                        
                        if chunk_type == 'image':
                            img_caption = metadata.get('img_caption', 'N/A')
                            print(f"    img_caption: {img_caption}")
                            visual_count += 1
                        elif chunk_type == 'image_text':
                            enhanced_desc = metadata.get('enhanced_description', '')[:100] + '...' if len(metadata.get('enhanced_description', '')) > 100 else metadata.get('enhanced_description', '')
                            print(f"    enhanced_description: {enhanced_desc}")
                            semantic_count += 1
                    
                    print(f"  📊 结果统计: 语义相似度 {semantic_count} 个, 视觉相似度 {visual_count} 个")
                else:
                    print("⚠️ 第一层向量搜索没有返回结果")
                    
            except Exception as e:
                print(f"❌ 第一层向量搜索失败: {e}")
                query_results[test_query] = {
                    'error': str(e),
                    'total_results': 0
                }
        
        # 输出测试总结
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        print(f"总查询数: {total_queries}")
        print(f"成功查询数: {successful_queries}")
        print(f"成功率: {successful_queries/total_queries*100:.1f}%")
        
        # 分析查询类型表现
        print("\n🔍 查询类型表现分析:")
        print("-" * 40)
        
        query_categories = {
            '财务相关': ['中芯国际净利润', '财务数据', '营收情况', '利润分析'],
            '图表相关': ['图表数据', '数据图表', '统计图表', '趋势图'],
            '技术相关': ['技术指标', '工艺水平', '制程技术', '良率数据'],
            '通用查询': ['中芯国际', '半导体', '芯片制造', '晶圆代工']
        }
        
        for category, queries in query_categories.items():
            category_results = [query_results.get(q, {}) for q in queries if q in query_results]
            if category_results:
                avg_results = sum(r.get('total_results', 0) for r in category_results) / len(category_results)
                avg_semantic = sum(r.get('semantic_results', 0) for r in category_results) / len(category_results)
                avg_visual = sum(r.get('visual_results', 0) for r in category_results) / len(category_results)
                
                print(f"{category}:")
                print(f"  平均结果数: {avg_results:.1f}")
                print(f"  平均语义结果: {avg_semantic:.1f}")
                print(f"  平均视觉结果: {avg_visual:.1f}")
        
        print("\n✅ 全面测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_engine_comprehensive()
