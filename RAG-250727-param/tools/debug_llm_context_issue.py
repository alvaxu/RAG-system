'''
程序说明：

## 1. 调试LLM答案错误问题
## 2. 检查源过滤是否过于严格
## 3. 分析传递给LLM的上下文内容
## 4. 验证图4相关信息是否正确传递
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
from v2.core.source_filter_engine import SourceFilterEngine
from v2.core.dashscope_llm_engine import DashScopeLLMEngine
from v2.core.unified_pipeline import UnifiedPipeline
import time


def debug_llm_context_issue():
    """调试LLM答案错误问题"""
    print("🔍 调试LLM答案错误问题")
    print("=" * 80)
    
    try:
        # 1. 初始化所有组件
        print("📡 初始化组件...")
        
        # 配置
        config = ImageEngineConfigV2()
        print(f"✅ 配置加载成功，image_similarity_threshold: {config.image_similarity_threshold}")
        
        # 向量数据库
        api_key = get_dashscope_api_key()
        embeddings = DashScopeEmbeddings(dashscope_api_key=api_key, model='text-embedding-v1')
        vector_db_path = "../central/vector_db"
        vector_store = FAISS.load_local(vector_db_path, embeddings, allow_dangerous_deserialization=True)
        print("✅ 向量数据库加载成功")
        
        # 文档加载器
        document_loader = DocumentLoader(vector_store=vector_store)
        print("✅ 文档加载器初始化成功")
        
        # 图片引擎
        image_engine = ImageEngine(
            config=config,
            vector_store=vector_store,
            document_loader=document_loader
        )
        print("✅ 图片引擎初始化成功")
        
        # 2. 测试查询
        query = "图4：中芯国际归母净利润情况概览"
        print(f"\n🔍 测试查询: {query}")
        print("-" * 60)
        
        # 3. 第一步：检查向量搜索结果
        print("\n📊 第一步：检查向量搜索结果")
        vector_results = image_engine._vector_search(query, max_results=50)
        print(f"  向量搜索结果数量: {len(vector_results)}")
        
        if vector_results:
            print("\n  前3个向量搜索结果:")
            for i, result in enumerate(vector_results[:3]):
                print(f"    {i+1}. 分数: {result.get('score', 'N/A'):.4f}")
                print(f"       搜索方法: {result.get('search_method', 'N/A')}")
                print(f"       内容片段: {result['doc'].page_content[:200]}...")
                if hasattr(result['doc'], 'metadata') and result['doc'].metadata:
                    chunk_type = result['doc'].metadata.get('chunk_type', 'unknown')
                    print(f"       文档类型: {chunk_type}")
                print()
        
        # 4. 第二步：检查五层召回结果
        print("\n📊 第二步：检查五层召回结果")
        try:
            # 调用完整的五层召回
            from v2.core.base_engine import QueryType
            recall_results = image_engine.search(query, query_type=QueryType.IMAGE, max_results=20)
            
            print(f"  五层召回结果数量: {len(recall_results.results)}")
            
            if recall_results.results:
                print("\n  前5个召回结果:")
                for i, result in enumerate(recall_results.results[:5]):
                    print(f"    {i+1}. 分数: {result.get('score', 'N/A'):.4f}")
                    print(f"       来源: {result.get('source', 'N/A')}")
                    print(f"       层级: {result.get('layer', 'N/A')}")
                    print(f"       内容片段: {result['doc'].page_content[:200]}...")
                    
                    # 检查是否包含图4信息
                    content = result['doc'].page_content.lower()
                    if '图4' in content and '中芯国际' in content and '净利润' in content:
                        print(f"       ✅ 包含图4相关信息!")
                    print()
        except Exception as e:
            print(f"  五层召回测试失败: {e}")
        
        # 5. 第三步：模拟源过滤过程
        print("\n📊 第三步：模拟源过滤过程")
        try:
            # 使用前20个结果模拟源过滤
            test_results = vector_results[:20] if len(vector_results) >= 20 else vector_results
            print(f"  输入源过滤的结果数量: {len(test_results)}")
            
            # 检查输入结果中是否包含图4信息
            figure4_count = 0
            for result in test_results:
                content = result['doc'].page_content.lower()
                if '图4' in content and '中芯国际' in content and '净利润' in content:
                    figure4_count += 1
                    print(f"  ✅ 发现图4相关文档: {result['doc'].page_content[:100]}...")
            
            print(f"  输入中包含图4信息的文档数量: {figure4_count}")
            
            # 初始化源过滤引擎
            source_filter_engine = SourceFilterEngine(config=config)
            
            # 执行源过滤
            filtered_results = source_filter_engine.filter_sources(
                query=query,
                results=test_results,
                query_type=QueryType.IMAGE,
                max_results=10
            )
            
            print(f"  源过滤后结果数量: {len(filtered_results)}")
            
            # 检查过滤后是否还有图4信息
            figure4_after_filter = 0
            for result in filtered_results:
                content = result['doc'].page_content.lower()
                if '图4' in content and '中芯国际' in content and '净利润' in content:
                    figure4_after_filter += 1
                    print(f"  ✅ 过滤后保留的图4文档: {result['doc'].page_content[:100]}...")
            
            print(f"  过滤后包含图4信息的文档数量: {figure4_after_filter}")
            
            if figure4_count > 0 and figure4_after_filter == 0:
                print("  ❌ 问题发现：源过滤把图4相关文档过滤掉了！")
            elif figure4_after_filter > 0:
                print("  ✅ 源过滤正常：图4相关文档被保留")
            
        except Exception as e:
            print(f"  源过滤测试失败: {e}")
            import traceback
            print(f"  详细错误: {traceback.format_exc()}")
        
        # 6. 第四步：检查LLM输入上下文
        print("\n📊 第四步：模拟LLM输入上下文")
        try:
            if 'filtered_results' in locals() and filtered_results:
                # 构建上下文，模拟传递给LLM的内容
                context_parts = []
                for i, result in enumerate(filtered_results[:5]):
                    doc_content = result['doc'].page_content
                    context_parts.append(f"文档{i+1}: {doc_content}")
                
                full_context = "\n\n".join(context_parts)
                print(f"  构建的上下文长度: {len(full_context)} 字符")
                print(f"  前500字符: {full_context[:500]}...")
                
                # 检查上下文中是否包含图4信息
                if '图4' in full_context and '中芯国际' in full_context and '净利润' in full_context:
                    print("  ✅ 上下文包含图4相关信息")
                    
                    # 进一步检查具体的图4内容
                    if '图4：中芯国际归母净利润情况概览' in full_context:
                        print("  ✅ 上下文包含完整的图4标题")
                    else:
                        print("  ⚠️  上下文包含图4信息但可能不完整")
                else:
                    print("  ❌ 上下文不包含图4相关信息")
                
        except Exception as e:
            print(f"  LLM上下文检查失败: {e}")
        
        # 7. 总结和建议
        print("\n" + "=" * 80)
        print("🎯 问题诊断总结")
        print("=" * 80)
        
        print("\n可能的问题点:")
        print("1. 源过滤过于严格，把相关文档过滤掉了")
        print("2. 文档内容格式问题，LLM无法正确理解")
        print("3. 上下文长度限制，关键信息被截断")
        print("4. LLM提示词问题，没有正确引导LLM使用上下文")
        
        print("\n建议的解决方案:")
        print("1. 调整源过滤的阈值参数")
        print("2. 优化文档内容的格式化方式")
        print("3. 增加上下文长度限制")
        print("4. 改进LLM的提示词")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_llm_context_issue()
