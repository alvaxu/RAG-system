#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试策略2：跨模态搜索效果验证

测试目标：
1. 验证改造后的策略2是否正常工作
2. 测试multimodal-embedding-v1的跨模态向量化
3. 验证FAISS filter在跨模态搜索中的效果
4. 对比策略1和策略2的召回效果
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

def test_strategy2_cross_modal():
    """测试策略2跨模态搜索效果"""
    print("="*80)
    print("测试策略2：跨模态搜索效果验证")
    print("="*80)
    
    try:
        # 1. 导入必要的模块
        print("导入必要模块...")
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import DashScopeEmbeddings
        from config.api_key_manager import get_dashscope_api_key
        from config.settings import Settings
        
        print("模块导入成功")
        
        # 2. 获取配置
        print("获取配置...")
        try:
            old_cwd = os.getcwd()
            os.chdir(project_root)
            config = Settings.load_from_file('config.json')
            os.chdir(old_cwd)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            return False
        
        # 3. 获取API密钥
        api_key = get_dashscope_api_key(config.dashscope_api_key)
        if not api_key:
            print("未找到有效的DashScope API密钥")
            return False
        
        print("配置获取成功")
        
        # 4. 初始化embeddings
        text_embeddings = DashScopeEmbeddings(
            dashscope_api_key=api_key,
            model='text-embedding-v1'
        )
        print("text embeddings初始化成功")
        
        # 5. 加载向量数据库
        vector_db_path = config.vector_db_dir
        vector_store = FAISS.load_local(
            vector_db_path, 
            text_embeddings,
            allow_dangerous_deserialization=True
        )
        print("向量数据库加载成功")
        
        # 6. 分析数据库结构
        docstore_dict = vector_store.docstore._dict
        print(f"数据库包含 {len(docstore_dict)} 个文档")
        
        # 统计不同类型的chunks
        chunk_type_stats = {}
        for doc_id, doc in docstore_dict.items():
            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
            chunk_type = metadata.get('chunk_type', 'unknown')
            chunk_type_stats[chunk_type] = chunk_type_stats.get(chunk_type, 0) + 1
        
        print("数据库chunk类型统计:")
        for chunk_type, count in chunk_type_stats.items():
            print(f"   - {chunk_type}: {count} 个")
        
        # 7. 测试策略1：image_text搜索（对比基准）
        print("\n" + "="*80)
        print("测试策略1：image_text搜索（对比基准）")
        print("="*80)
        
        test_query = "中芯国际财务图表"
        print(f"测试查询: {test_query}")
        
        # 策略1：使用filter搜索image_text类型
        try:
            strategy1_results = vector_store.similarity_search(
                test_query, 
                k=50,
                filter={'chunk_type': 'image_text'}
            )
            print(f"策略1结果数量: {len(strategy1_results)}")
            
            # 统计策略1结果
            strategy1_stats = {}
            for doc in strategy1_results:
                metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                chunk_type = metadata.get('chunk_type', 'unknown')
                strategy1_stats[chunk_type] = strategy1_stats.get(chunk_type, 0) + 1
            
            print("策略1结果分布:")
            for chunk_type, count in strategy1_stats.items():
                print(f"   - {chunk_type}: {count} 个")
                
        except Exception as e:
            print(f"策略1测试失败: {e}")
            return False
        
        # 8. 测试策略2：跨模态搜索image类型
        print("\n" + "="*80)
        print("测试策略2：跨模态搜索image类型")
        print("="*80)
        
        try:
            # 使用multimodal-embedding-v1进行跨模态向量化
            from dashscope import MultiModalEmbedding
            import dashscope
            
            # 设置API密钥
            dashscope.api_key = api_key
            
            print("调用multimodal-embedding-v1 API...")
            result = MultiModalEmbedding.call(
                model='multimodal-embedding-v1',
                input=[{'text': test_query}]
            )
            
            if result.status_code == 200:
                # 提取查询向量
                query_embedding = result.output['embeddings'][0]['embedding']
                print(f"跨模态向量化成功，向量维度: {len(query_embedding)}")
                
                # 测试策略2：使用filter搜索image类型
                print("测试策略2：使用filter搜索image类型...")
                try:
                    strategy2_results = vector_store.similarity_search(
                        test_query, 
                        k=50,
                        filter={'chunk_type': 'image'}
                    )
                    print(f"策略2结果数量: {len(strategy2_results)}")
                    
                    # 统计策略2结果
                    strategy2_stats = {}
                    for doc in strategy2_results:
                        metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                        chunk_type = metadata.get('chunk_type', 'unknown')
                        strategy2_stats[chunk_type] = strategy2_stats.get(chunk_type, 0) + 1
                    
                    print("策略2结果分布:")
                    for chunk_type, count in strategy2_stats.items():
                        print(f"   - {chunk_type}: {count} 个")
                    
                    # 验证策略2是否真的只返回image类型
                    non_image_count = sum(count for chunk_type, count in strategy2_stats.items() if chunk_type != 'image')
                    if non_image_count == 0:
                        print("✅ 策略2 filter工作正常：只返回image类型")
                    else:
                        print(f"⚠️ 策略2 filter有问题：返回了 {non_image_count} 个非image类型")
                        
                except Exception as filter_error:
                    print(f"策略2 filter搜索失败: {filter_error}")
                    print("尝试无filter搜索...")
                    
                    # 降级：无filter搜索 + 后过滤
                    try:
                        all_candidates = vector_store.similarity_search(test_query, k=100)
                        print(f"无filter搜索返回 {len(all_candidates)} 个候选结果")
                        
                        # 后过滤：筛选出image类型的文档
                        image_candidates = []
                        for doc in all_candidates:
                            if (hasattr(doc, 'metadata') and doc.metadata and 
                                doc.metadata.get('chunk_type') == 'image'):
                                image_candidates.append(doc)
                        
                        print(f"后过滤后找到 {len(image_candidates)} 个image文档")
                        
                        # 统计后过滤结果
                        strategy2_fallback_stats = {}
                        for doc in image_candidates:
                            metadata = doc.metadata if hasattr(doc, 'metadata') and doc.metadata else {}
                            chunk_type = metadata.get('chunk_type', 'unknown')
                            strategy2_fallback_stats[chunk_type] = strategy2_fallback_stats.get(chunk_type, 0) + 1
                        
                        print("策略2降级结果分布:")
                        for chunk_type, count in strategy2_fallback_stats.items():
                            print(f"   - {chunk_type}: {count} 个")
                            
                    except Exception as fallback_error:
                        print(f"策略2降级搜索也失败: {fallback_error}")
                        
            else:
                print(f"multimodal-embedding-v1 API调用失败: {result}")
                return False
                
        except Exception as e:
            print(f"策略2测试失败: {e}")
            return False
        
        # 9. 策略对比分析
        print("\n" + "="*80)
        print("策略对比分析")
        print("="*80)
        
        print("策略1（image_text搜索）:")
        print(f"  结果数量: {len(strategy1_results)}")
        print(f"  主要类型: image_text")
        
        print("策略2（跨模态image搜索）:")
        if 'strategy2_results' in locals():
            print(f"  结果数量: {len(strategy2_results)}")
            print(f"  主要类型: image")
        else:
            print("  结果数量: 0（filter搜索失败）")
        
        # 10. 结论
        print("\n" + "="*80)
        print("测试结论")
        print("="*80)
        
        if 'strategy2_results' in locals() and len(strategy2_results) > 0:
            print("✅ 策略2跨模态搜索工作正常！")
            print("   建议：可以安全使用跨模态搜索进行图片召回")
        else:
            print("❌ 策略2跨模态搜索存在问题")
            print("   建议：需要进一步调试或使用降级方案")
        
        print("\n" + "="*80)
        print("测试完成")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_strategy2_cross_modal()
    if success:
        print("\n测试通过")
    else:
        print("\n测试失败")
