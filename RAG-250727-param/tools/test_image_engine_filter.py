#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试修改后的ImageEngine的FAISS filter功能
## 2. 验证image_text和image的filter搜索是否正常工作
## 3. 确认向量搜索策略的改进效果
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

def test_image_engine_filter():
    """测试修改后的ImageEngine的FAISS filter功能"""
    print("🔍 测试修改后的ImageEngine的FAISS filter功能")
    print("=" * 60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        
        # 创建ImageEngine配置
        image_config = ImageEngineConfigV2(
            enabled=True,
            max_results=20,
            image_similarity_threshold=0.05,
            enable_vector_search=True,
            enable_keyword_search=True,
            max_recall_results=150,
            use_new_pipeline=False,  # 暂时关闭新pipeline，专注测试召回
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
            skip_initial_load=True  # 跳过初始加载，手动加载
        )
        
        print("✅ ImageEngine实例创建成功")
        
        # 手动加载文档
        print("📚 正在加载文档...")
        image_engine._load_from_vector_store()
        
        if not image_engine.image_docs:
            print("❌ 没有加载到图片文档")
            return
        
        print(f"✅ 成功加载 {len(image_engine.image_docs)} 个图片文档")
        
        # 测试查询
        test_queries = [
            "中芯国际净利润",
            "股价相对走势",
            "图表数据",
            "财务分析"
        ]
        
        for test_query in test_queries:
            print(f"\n🔍 测试查询: {test_query}")
            print("-" * 40)
            
            # 测试第一层向量搜索
            try:
                vector_results = image_engine._vector_search(test_query, max_results=10)
                print(f"✅ 第一层向量搜索成功，返回 {len(vector_results)} 个结果")
                
                if vector_results:
                    print("📋 结果详情:")
                    for i, result in enumerate(vector_results[:3]):
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
                        elif chunk_type == 'image_text':
                            enhanced_desc = metadata.get('enhanced_description', '')[:100] + '...' if len(metadata.get('enhanced_description', '')) > 100 else metadata.get('enhanced_description', '')
                            print(f"    enhanced_description: {enhanced_desc}")
                else:
                    print("⚠️ 第一层向量搜索没有返回结果")
                    
            except Exception as e:
                print(f"❌ 第一层向量搜索失败: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n✅ ImageEngine FAISS filter功能测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_engine_filter()
