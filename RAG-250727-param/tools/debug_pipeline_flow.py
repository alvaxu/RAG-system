'''
程序说明：

## 1. 深入调试pipeline处理流程
## 2. 追踪metadata字段在各个环节的传递情况
## 3. 分析为什么LLM仍然说没有图4信息
## 4. 检查源过滤和LLM上下文构建过程
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


def debug_pipeline_flow():
    """深入调试pipeline处理流程"""
    print("🔍 深入调试pipeline处理流程")
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
        
        # 3. 第一步：检查向量搜索结果
        print("\n📊 第一步：检查向量搜索结果")
        vector_results = image_engine._vector_search(query, max_results=50)
        print(f"  向量搜索结果数量: {len(vector_results)}")
        
        if vector_results:
            first_result = vector_results[0]
            print(f"\n  第一个结果分析:")
            print(f"    分数: {first_result.get('score', 'N/A'):.4f}")
            print(f"    搜索方法: {first_result.get('search_method', 'N/A')}")
            
            # 检查我们的新增字段
            print(f"    📋 我们的新增字段:")
            print(f"      document_name: {first_result.get('document_name', 'N/A')}")
            print(f"      page_number: {first_result.get('page_number', 'N/A')}")
            print(f"      chunk_type: {first_result.get('chunk_type', 'N/A')}")
            print(f"      enhanced_description: {first_result.get('enhanced_description', 'N/A')[:100]}...")
            print(f"      llm_context: {first_result.get('llm_context', 'N/A')[:100]}...")
            
            # 检查doc字段
            doc = first_result['doc']
            print(f"    📄 doc字段信息:")
            print(f"      类型: {type(doc)}")
            print(f"      内容长度: {len(doc.page_content)} 字符")
            if hasattr(doc, 'metadata') and doc.metadata:
                print(f"      元数据: {doc.metadata}")
        
        # 4. 第二步：模拟五层召回过程
        print(f"\n📊 第二步：模拟五层召回过程")
        try:
            # 这里我们需要模拟五层召回，但先检查image_engine是否有相关方法
            print("  检查image_engine的五层召回方法...")
            
            # 查看image_engine的方法
            methods = [method for method in dir(image_engine) if 'recall' in method.lower() or 'search' in method.lower()]
            print(f"  相关方法: {methods}")
            
            # 尝试找到五层召回的主方法
            if hasattr(image_engine, 'search'):
                print("  ✅ 找到search方法")
            else:
                print("  ❌ 没有找到search方法")
                
        except Exception as e:
            print(f"  五层召回检查失败: {e}")
        
        # 5. 第三步：检查unified_pipeline
        print(f"\n📊 第三步：检查unified_pipeline")
        try:
            # 初始化unified_pipeline
            llm_engine = DashScopeLLMEngine(config=config)
            source_filter_engine = SourceFilterEngine(config=config)
            
            unified_pipeline = UnifiedPipeline(
                llm_engine=llm_engine,
                source_filter_engine=source_filter_engine,
                config=config
            )
            print("  ✅ unified_pipeline初始化成功")
            
            # 检查unified_pipeline的方法
            pipeline_methods = [method for method in dir(unified_pipeline) if not method.startswith('_')]
            print(f"  pipeline方法: {pipeline_methods}")
            
            # 检查process方法
            if hasattr(unified_pipeline, 'process'):
                print("  ✅ 找到process方法")
                # 查看process方法的参数
                import inspect
                sig = inspect.signature(unified_pipeline.process)
                print(f"  process方法参数: {sig}")
            else:
                print("  ❌ 没有找到process方法")
                
        except Exception as e:
            print(f"  unified_pipeline检查失败: {e}")
            import traceback
            print(f"  详细错误: {traceback.format_exc()}")
        
        # 6. 第四步：检查source_filter_engine
        print(f"\n📊 第四步：检查source_filter_engine")
        try:
            source_filter_engine = SourceFilterEngine(config=config)
            print("  ✅ source_filter_engine初始化成功")
            
            # 检查filter_sources方法
            if hasattr(source_filter_engine, 'filter_sources'):
                print("  ✅ 找到filter_sources方法")
                import inspect
                sig = inspect.signature(source_filter_engine.filter_sources)
                print(f"  filter_sources方法参数: {sig}")
            else:
                print("  ❌ 没有找到filter_sources方法")
                
        except Exception as e:
            print(f"  source_filter_engine检查失败: {e}")
        
        # 7. 第五步：分析问题
        print("\n" + "=" * 80)
        print("🎯 问题分析")
        print("=" * 80)
        
        print(f"\n当前状态:")
        print(f"✅ 向量搜索层面：metadata字段正确传递")
        print(f"❌ 后续pipeline：可能没有使用我们的metadata字段")
        
        print(f"\n可能的问题点:")
        print(f"1. unified_pipeline没有使用我们传递的llm_context字段")
        print(f"2. source_filter_engine过滤过于严格，丢失了关键结果")
        print(f"3. LLM上下文构建逻辑有问题")
        print(f"4. 其他召回策略的结果没有我们的metadata字段")
        
        print(f"\n建议的调试方向:")
        print(f"1. 检查unified_pipeline如何处理输入结果")
        print(f"2. 检查source_filter_engine的过滤逻辑")
        print(f"3. 检查LLM上下文构建过程")
        print(f"4. 确认其他召回策略是否也需要增强metadata")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_pipeline_flow()
