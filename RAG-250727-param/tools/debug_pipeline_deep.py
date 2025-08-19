'''
程序说明：

## 1. 深度调试unified_pipeline和source_filter_engine
## 2. 追踪metadata字段在pipeline中的传递和丢失情况
## 3. 分析LLM上下文构建过程
## 4. 检查源过滤逻辑
'''

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from config.api_key_manager import get_dashscope_api_key
from v2.core.image_engine import ImageEngine
from v2.core.document_loader import DocumentLoader
from v2.config.v2_config import ImageEngineConfigV2
from v2.core.unified_pipeline import UnifiedPipeline
from v2.core.source_filter_engine import SourceFilterEngine
from v2.core.dashscope_llm_engine import DashScopeLLMEngine
import time


def debug_pipeline_deep():
    """深度调试pipeline处理流程"""
    print("🔍 深度调试pipeline处理流程")
    print("=" * 80)
    
    try:
        # 1. 初始化组件
        print("📡 初始化组件...")
        config = ImageEngineConfigV2()
        
        api_key = get_dashscope_api_key()
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        vector_db_path = "../central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        
        document_loader = DocumentLoader(vector_store=vector_store)
        image_engine = ImageEngine(
            config=config,
            vector_store=vector_store,
            document_loader=document_loader
        )
        print("✅ 组件初始化成功")
        
        # 2. 测试查询
        query = "图4：中芯国际归母净利润情况概览"
        print(f"\n🔍 测试查询: {query}")
        print("-" * 60)
        
        # 3. 第一步：获取完整的五层召回结果
        print("\n📊 第一步：获取完整的五层召回结果")
        try:
            # 检查image_engine的五层召回方法
            if hasattr(image_engine, '_search_images_with_five_layer_recall'):
                print("  ✅ 找到五层召回方法")
                
                # 调用五层召回
                all_results = image_engine._search_images_with_five_layer_recall(query)
                print(f"  五层召回结果数量: {len(all_results)}")
                
                # 分析结果
                if all_results:
                    print(f"\n  结果分析:")
                    for i, result in enumerate(all_results[:3]):  # 只看前3个
                        print(f"    结果{i+1}:")
                        print(f"      分数: {result.get('score', 'N/A'):.4f}")
                        print(f"      搜索方法: {result.get('search_method', 'N/A')}")
                        print(f"      来源: {result.get('source', 'N/A')}")
                        
                        # 检查我们的新增字段
                        if 'document_name' in result:
                            print(f"      📋 document_name: {result.get('document_name', 'N/A')}")
                            print(f"      📋 page_number: {result.get('page_number', 'N/A')}")
                            print(f"      📋 chunk_type: {result.get('chunk_type', 'N/A')}")
                            print(f"      📋 llm_context长度: {len(result.get('llm_context', ''))}")
                        else:
                            print(f"      ❌ 缺少我们的新增字段")
                        
                        # 检查doc字段
                        if 'doc' in result:
                            doc = result['doc']
                            print(f"      📄 doc类型: {type(doc)}")
                            print(f"      📄 内容长度: {len(doc.page_content)} 字符")
                        else:
                            print(f"      ❌ 缺少doc字段")
                        print()
                        
            else:
                print("  ❌ 没有找到五层召回方法")
                
        except Exception as e:
            print(f"  五层召回失败: {e}")
            import traceback
            print(f"  详细错误: {traceback.format_exc()}")
        
        # 4. 第二步：检查unified_pipeline
        print(f"\n📊 第二步：检查unified_pipeline")
        try:
            # 初始化unified_pipeline
            from v2.config.v2_config import LLMConfigV2
            llm_config = LLMConfigV2()
            llm_engine = DashScopeLLMEngine(api_key=api_key, config=llm_config)
            source_filter_engine = SourceFilterEngine(config=config)
            
            unified_pipeline = UnifiedPipeline(
                llm_engine=llm_engine,
                source_filter_engine=source_filter_engine,
                config=config
            )
            print("  ✅ unified_pipeline初始化成功")
            
            # 检查process方法
            if hasattr(unified_pipeline, 'process'):
                print("  ✅ 找到process方法")
                import inspect
                sig = inspect.signature(unified_pipeline.process)
                print(f"  process方法参数: {sig}")
                
                # 查看process方法的实现
                source = inspect.getsource(unified_pipeline.process)
                print(f"  process方法实现预览:")
                lines = source.split('\n')
                for i, line in enumerate(lines[:20]):  # 显示前20行
                    print(f"    {i+1:2d}: {line}")
                if len(lines) > 20:
                    print(f"    ... (共{len(lines)}行)")
                    
            else:
                print("  ❌ 没有找到process方法")
                
        except Exception as e:
            print(f"  unified_pipeline检查失败: {e}")
            import traceback
            print(f"  详细错误: {traceback.format_exc()}")
        
        # 5. 第三步：检查source_filter_engine
        print(f"\n📊 第三步：检查source_filter_engine")
        try:
            source_filter_engine = SourceFilterEngine(config=config)
            print("  ✅ source_filter_engine初始化成功")
            
            # 检查filter_sources方法
            if hasattr(source_filter_engine, 'filter_sources'):
                print("  ✅ 找到filter_sources方法")
                import inspect
                sig = inspect.signature(source_filter_engine.filter_sources)
                print(f"  filter_sources方法参数: {sig}")
                
                # 查看filter_sources方法的实现
                source = inspect.getsource(source_filter_engine.filter_sources)
                print(f"  filter_sources方法实现预览:")
                lines = source.split('\n')
                for i, line in enumerate(lines[:20]):  # 显示前20行
                    print(f"    {i+1:2d}: {line}")
                if len(lines) > 20:
                    print(f"    ... (共{len(lines)}行)")
                    
            else:
                print("  ❌ 没有找到filter_sources方法")
                
        except Exception as e:
            print(f"  source_filter_engine检查失败: {e}")
            import traceback
            print(f"  详细错误: {traceback.format_exc()}")
        
        # 6. 第四步：模拟pipeline处理过程
        print(f"\n📊 第四步：模拟pipeline处理过程")
        try:
            # 获取向量搜索结果作为输入
            vector_results = image_engine._vector_search(query, max_results=20)
            print(f"  输入结果数量: {len(vector_results)}")
            
            if vector_results:
                # 模拟源过滤
                print(f"\n  模拟源过滤过程:")
                print(f"    输入: {len(vector_results)} 个结果")
                
                # 检查每个结果的分数
                scores = [r.get('score', 0) for r in vector_results]
                print(f"    分数范围: {min(scores):.4f} - {max(scores):.4f}")
                print(f"    平均分数: {sum(scores)/len(scores):.4f}")
                
                # 检查我们的字段
                fields_check = {
                    'document_name': 0,
                    'page_number': 0,
                    'chunk_type': 0,
                    'llm_context': 0
                }
                
                for result in vector_results:
                    for field in fields_check:
                        if result.get(field):
                            fields_check[field] += 1
                
                print(f"    字段统计:")
                for field, count in fields_check.items():
                    print(f"      {field}: {count}/{len(vector_results)}")
                
                # 模拟LLM上下文构建
                print(f"\n  模拟LLM上下文构建:")
                if vector_results:
                    first_result = vector_results[0]
                    if 'llm_context' in first_result:
                        llm_context = first_result['llm_context']
                        print(f"    使用我们的llm_context:")
                        print(f"      长度: {len(llm_context)} 字符")
                        print(f"      内容预览: {llm_context[:200]}...")
                    else:
                        print(f"    ❌ 没有llm_context字段")
                        
                        # 尝试从doc构建
                        if 'doc' in first_result:
                            doc = first_result['doc']
                            print(f"    从doc构建上下文:")
                            print(f"      内容: {doc.page_content}")
                            if hasattr(doc, 'metadata') and doc.metadata:
                                print(f"      元数据: {doc.metadata}")
                
        except Exception as e:
            print(f"  模拟pipeline处理失败: {e}")
            import traceback
            print(f"  详细错误: {traceback.format_exc()}")
        
        # 7. 第五步：问题分析
        print("\n" + "=" * 80)
        print("🎯 深度问题分析")
        print("=" * 80)
        
        print(f"\n关键发现:")
        print(f"1. 向量搜索层面：✅ 我们的metadata字段正确传递")
        print(f"2. 五层召回层面：❓ 需要确认是否所有策略都有metadata")
        print(f"3. unified_pipeline：❓ 需要确认如何处理输入结果")
        print(f"4. source_filter_engine：❓ 需要确认过滤逻辑")
        
        print(f"\n可能的问题点:")
        print(f"1. 五层召回中，只有_vector_search有我们的metadata，其他策略没有")
        print(f"2. unified_pipeline可能重新构建LLM上下文，忽略我们的llm_context")
        print(f"3. source_filter_engine可能过滤掉了包含图4信息的结果")
        print(f"4. 最终LLM上下文可能来自其他召回策略的结果，而不是我们的")
        
        print(f"\n建议的调试方向:")
        print(f"1. 检查五层召回的完整结果，确认metadata字段分布")
        print(f"2. 检查unified_pipeline的LLM上下文构建逻辑")
        print(f"3. 检查source_filter_engine的过滤规则")
        print(f"4. 确认最终传递给LLM的上下文来源")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_pipeline_deep()
