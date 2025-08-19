#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序说明：
## 1. 测试修复后的ImageEngine
## 2. 验证post-filtering策略是否正常工作
## 3. 检查第一层向量搜索是否能返回结果
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

def test_fixed_image_engine():
    """测试修复后的ImageEngine"""
    print("🔍 测试修复后的ImageEngine")
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
        test_query = "中芯国际净利润"
        print(f"\n🔍 测试查询: {test_query}")
        
        # 测试第一层向量搜索
        print("\n📊 测试第一层向量搜索")
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
                    
                    print(f"  结果{i+1}:")
                    print(f"    chunk_type: {chunk_type}")
                    print(f"    score: {score}")
                    print(f"    search_method: {search_method}")
                    
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
        
        # 测试五层召回策略
        print("\n📊 测试五层召回策略")
        try:
            recall_results = image_engine._search_images_with_five_layer_recall(test_query)
            print(f"✅ 五层召回策略成功，返回 {len(recall_results)} 个结果")
            
            if recall_results:
                print("📋 召回结果统计:")
                layer_counts = {}
                for result in recall_results:
                    layer = result.get('layer', 'unknown')
                    layer_counts[layer] = layer_counts.get(layer, 0) + 1
                
                for layer, count in sorted(layer_counts.items()):
                    print(f"  第{layer}层: {count} 个结果")
            else:
                print("⚠️ 五层召回策略没有返回结果")
                
        except Exception as e:
            print(f"❌ 五层召回策略失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n✅ ImageEngine测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_image_engine()
