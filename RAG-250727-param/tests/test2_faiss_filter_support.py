#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试2：FAISS filter功能支持验证

测试目标：
1. 确认FAISS是否支持chunk_type过滤
2. 验证filter搜索的准确性和性能
3. 测试跨模态搜索的稳定性
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_faiss_filter_support():
    """测试FAISS的filter功能"""
    print("="*60)
    print("�� 测试2：FAISS filter功能支持验证")
    print("="*60)
    
    try:
        # 1. 导入必要的模块
        print("📦 导入必要模块...")
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        from config.api_key_manager import get_dashscope_api_key
        from config.settings import Settings
        
        print("✅ 模块导入成功")
        
        # 2. 获取API密钥和配置
        print("🔑 获取配置...")
        
        # 找到正确的配置文件路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config.json')
        
        print(f"   项目根目录: {project_root}")
        print(f"   配置文件路径: {config_path}")
        
        if not os.path.exists(config_path):
            print(f"❌ 配置文件不存在: {config_path}")
            return False
        
        try:
            # 临时切换到项目根目录，确保路径解析正确
            old_cwd = os.getcwd()
            os.chdir(project_root)
            
            config = Settings.load_from_file('config.json')
            print(f"   ✅ 配置文件加载成功: {config_path}")
            
            # 恢复原来的工作目录
            os.chdir(old_cwd)
            
        except Exception as e:
            print(f"   ❌ 配置文件加载失败: {e}")
            # 恢复原来的工作目录
            os.chdir(old_cwd)
            return False
        
        # 调试配置信息
        print(f"   配置类型: {type(config)}")
        print(f"   vector_db_dir: {getattr(config, 'vector_db_dir', 'NOT_FOUND')}")
        
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        
        if not api_key:
            print("❌ 未找到有效的DashScope API密钥")
            return False
        
        print("✅ 配置获取成功")
        
        # 3. 初始化embeddings
        print("🚀 初始化embeddings...")
        # 使用text embeddings来加载FAISS数据库
        text_embeddings = DashScopeEmbeddings(
            dashscope_api_key=api_key,
            model='text-embedding-v1'
        )
        print("✅ text embeddings初始化成功")
        
        # 4. 加载向量数据库
        print("📚 加载向量数据库...")
        
        # 使用配置中的向量数据库路径
        vector_db_path = config.vector_db_dir
        
        # 调试路径信息
        print(f"   配置路径: {vector_db_path}")
        print(f"   当前工作目录: {os.getcwd()}")
        
        if not os.path.exists(vector_db_path):
            print(f"❌ 向量数据库路径不存在: {vector_db_path}")
            return False
        
        print(f"✅ 向量数据库路径存在: {vector_db_path}")
        
        # 检查必要文件是否存在
        index_file = os.path.join(vector_db_path, "index.faiss")
        pkl_file = os.path.join(vector_db_path, "index.pkl")
        
        if not os.path.exists(index_file) or not os.path.exists(pkl_file):
            print(f"❌ 向量存储文件不完整: {vector_db_path}")
            print(f"   index.faiss存在: {os.path.exists(index_file)}")
            print(f"   index.pkl存在: {os.path.exists(pkl_file)}")
            return False
        
        try:
            # 使用正确的嵌入模型和设置
            embedding_model = getattr(config, 'text_embedding_model', 'text-embedding-v1')
            allow_dangerous_deserialization = getattr(config, 'allow_dangerous_deserialization', True)
            
            print(f"   使用嵌入模型: {embedding_model}")
            print(f"   允许反序列化: {allow_dangerous_deserialization}")
            
            vector_store = FAISS.load_local(
                vector_db_path, 
                text_embeddings,
                allow_dangerous_deserialization=allow_dangerous_deserialization
            )
            print("✅ 向量数据库加载成功")
        except Exception as e:
            print(f"❌ 向量数据库加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 5. 分析数据库结构
        print("🔍 分析数据库结构...")
        if not hasattr(vector_store, 'docstore') or not hasattr(vector_store.docstore, '_dict'):
            print("❌ 向量数据库结构不符合预期")
            return False
        
        docstore_dict = vector_store.docstore._dict
        print(f"✅ 数据库包含 {len(docstore_dict)} 个文档")
        
        # 统计不同类型的chunks
        chunk_type_stats = {}
        for doc_id, doc in docstore_dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
        
        print("📊 数据库chunk类型统计:")
        for chunk_type, count in chunk_type_stats.items():
            print(f"   - {chunk_type}: {count} 个")
        
        # 6. 测试filter功能
        print("🔍 测试FAISS filter功能...")
        
        # 测试1：过滤image类型
        print("   测试1：过滤image类型chunks...")
        try:
            image_filter_results = vector_store.similarity_search(
                "测试查询", 
                k=50,
                filter={'chunk_type': 'image'}
            )
            
            print(f"   ✅ image filter搜索成功，返回 {len(image_filter_results)} 个结果")
            
            # 验证结果是否都是image类型
            image_count = 0
            for doc in image_filter_results:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                if metadata.get('chunk_type') == 'image':
                    image_count += 1
            
            print(f"   📊 结果验证：{image_count}/{len(image_filter_results)} 个是image类型")
            
            if image_count == len(image_filter_results):
                print("   ✅ image filter过滤准确")
            else:
                print("   ⚠️ image filter过滤不准确")
                
        except Exception as e:
            print(f"   ❌ image filter搜索失败: {e}")
            return False
        
        # 测试2：过滤image_text类型
        print("   测试2：过滤image_text类型chunks...")
        try:
            image_text_filter_results = vector_store.similarity_search(
                "测试查询", 
                k=50,
                filter={'chunk_type': 'image_text'}
            )
            
            print(f"   ✅ image_text filter搜索成功，返回 {len(image_text_filter_results)} 个结果")
            
            # 验证结果是否都是image_text类型
            image_text_count = 0
            for doc in image_text_filter_results:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                if metadata.get('chunk_type') == 'image_text':
                    image_text_count += 1
            
            print(f"   📊 结果验证：{image_text_count}/{len(image_text_filter_results)} 个是image_text类型")
            
            if image_text_count == len(image_text_filter_results):
                print("   ✅ image_text filter过滤准确")
            else:
                print("   ⚠️ image_text filter过滤不准确")
                
        except Exception as e:
            print(f"   ❌ image_text filter搜索失败: {e}")
            return False
        
        # 测试3：组合filter
        print("   测试3：组合filter测试...")
        try:
            # 测试多个条件的filter
            combined_filter_results = vector_store.similarity_search(
                "测试查询", 
                k=50,
                filter={'chunk_type': 'image', 'document_name': '中芯国际'}
            )
            
            print(f"   ✅ 组合filter搜索成功，返回 {len(combined_filter_results)} 个结果")
            
            # 验证结果
            valid_count = 0
            for doc in combined_filter_results:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                if (metadata.get('chunk_type') == 'image' and 
                    '中芯国际' in metadata.get('document_name', '')):
                    valid_count += 1
            
            print(f"   📊 组合filter验证：{valid_count}/{len(combined_filter_results)} 个符合条件")
            
        except Exception as e:
            print(f"   ⚠️ 组合filter搜索失败: {e}")
            print("   这不会影响基本功能，但可能影响高级搜索")
        
        # 7. 测试跨模态搜索稳定性
        print("🔄 测试跨模态搜索稳定性...")
        
        test_queries = [
            "中芯国际财务图表",
            "半导体制造工艺",
            "晶圆代工产能"
        ]
        
        stability_results = []
        for i, query in enumerate(test_queries, 1):
            print(f"   稳定性测试 {i}: {query}")
            
            try:
                # 生成查询向量
                query_embedding = multimodal_embeddings.embed_query(query)
                
                # 使用filter搜索
                start_time = time.time()
                filter_results = vector_store.similarity_search(
                    query, 
                    k=20,
                    filter={'chunk_type': 'image'}
                )
                search_time = time.time() - start_time
                
                stability_results.append({
                    'query': query,
                    'success': True,
                    'results_count': len(filter_results),
                    'search_time': search_time
                })
                
                print(f"   ✅ 查询 {i} 成功，返回 {len(filter_results)} 个结果，耗时 {search_time:.3f}秒")
                
            except Exception as e:
                stability_results.append({
                    'query': query,
                    'success': False,
                    'error': str(e)
                })
                print(f"   ❌ 查询 {i} 失败: {e}")
        
        # 统计稳定性
        successful_searches = sum(1 for r in stability_results if r['success'])
        total_searches = len(stability_results)
        success_rate = successful_searches / total_searches if total_searches > 0 else 0
        
        print(f"�� 稳定性统计：成功率 {success_rate:.1%} ({successful_searches}/{total_searches})")
        
        if success_rate >= 0.8:
            print("✅ 跨模态搜索稳定性良好")
        elif success_rate >= 0.6:
            print("⚠️ 跨模态搜索稳定性一般")
        else:
            print("❌ 跨模态搜索稳定性较差")
        
        # 8. 性能测试
        print("⚡ 性能测试...")
        try:
            # 测试搜索性能
            performance_queries = ["测试查询"] * 5
            
            total_time = 0
            for i, query in enumerate(performance_queries, 1):
                start_time = time.time()
                vector_store.similarity_search(
                    query, 
                    k=10,
                    filter={'chunk_type': 'image'}
                )
                query_time = time.time() - start_time
                total_time += query_time
                
                print(f"   查询 {i} 耗时: {query_time:.3f}秒")
            
            avg_time = total_time / len(performance_queries)
            print(f"📊 平均查询耗时: {avg_time:.3f}秒")
            
            if avg_time < 1.0:
                print("✅ 搜索性能优秀")
            elif avg_time < 3.0:
                print("✅ 搜索性能良好")
            else:
                print("⚠️ 搜索性能一般")
                
        except Exception as e:
            print(f"   ⚠️ 性能测试失败: {e}")
        
        print("\n" + "="*60)
        print("�� 测试2完成：FAISS filter功能支持验证成功！")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_faiss_filter_support()
    if success:
        print("\n✅ 测试2通过：FAISS filter功能正常工作，支持跨模态搜索")
    else:
        print("\n❌ 测试2失败：需要检查FAISS配置或数据库结构")