'''
程序说明：

## 1. 简化版LLM上下文调试
## 2. 重点检查向量搜索和文档内容
## 3. 分析为什么LLM说没有图4信息
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
import time


def debug_llm_context_simple():
    """简化版LLM上下文调试"""
    print("🔍 简化版LLM上下文调试")
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
        
        # 3. 检查向量搜索结果
        print("\n📊 检查向量搜索详细结果")
        vector_results = image_engine._vector_search(query, max_results=50)
        print(f"  向量搜索结果数量: {len(vector_results)}")
        
        if vector_results:
            for i, result in enumerate(vector_results):
                print(f"\n  结果 {i+1}:")
                print(f"    分数: {result.get('score', 'N/A'):.4f}")
                print(f"    搜索方法: {result.get('search_method', 'N/A')}")
                print(f"    来源: {result.get('source', 'N/A')}")
                print(f"    层级: {result.get('layer', 'N/A')}")
                
                # 检查文档类型
                if hasattr(result['doc'], 'metadata') and result['doc'].metadata:
                    chunk_type = result['doc'].metadata.get('chunk_type', 'unknown')
                    document_name = result['doc'].metadata.get('document_name', 'unknown')
                    page_number = result['doc'].metadata.get('page_number', 'unknown')
                    print(f"    文档类型: {chunk_type}")
                    print(f"    文档名称: {document_name}")
                    print(f"    页码: {page_number}")
                
                # 检查文档内容
                content = result['doc'].page_content
                print(f"    内容长度: {len(content)} 字符")
                
                # 重点检查是否包含图4完整信息
                if '图4：中芯国际归母净利润情况概览' in content:
                    print("    ✅ 包含完整的图4标题!")
                elif '图4' in content and '中芯国际' in content and '净利润' in content:
                    print("    ⚠️  包含图4相关信息，但可能不完整")
                else:
                    print("    ❌ 不包含图4相关信息")
                
                # 显示内容前300字符
                print(f"    内容预览: {content[:300]}...")
                
                # 如果是第一个结果（最相关的），显示完整内容
                if i == 0:
                    print(f"\n    ⭐ 最相关结果的完整内容:")
                    print(f"    {content}")
        
        # 4. 检查是否有enhanced_description
        print(f"\n📊 检查enhanced_description字段")
        for i, result in enumerate(vector_results[:3]):
            if hasattr(result['doc'], 'metadata') and result['doc'].metadata:
                enhanced_desc = result['doc'].metadata.get('enhanced_description', '')
                if enhanced_desc:
                    print(f"\n  结果 {i+1} 的enhanced_description:")
                    print(f"    长度: {len(enhanced_desc)} 字符")
                    print(f"    内容: {enhanced_desc[:500]}...")
                else:
                    print(f"\n  结果 {i+1} 没有enhanced_description字段")
        
        # 5. 模拟构建LLM上下文
        print(f"\n📊 模拟构建LLM上下文")
        if vector_results:
            # 取前5个结果构建上下文
            context_parts = []
            for i, result in enumerate(vector_results[:5]):
                doc_content = result['doc'].page_content
                
                # 检查是否有enhanced_description
                enhanced_desc = ""
                if hasattr(result['doc'], 'metadata') and result['doc'].metadata:
                    enhanced_desc = result['doc'].metadata.get('enhanced_description', '')
                
                # 构建完整的文档内容
                full_content = doc_content
                if enhanced_desc and enhanced_desc not in doc_content:
                    full_content = f"{doc_content}\n\n增强描述: {enhanced_desc}"
                
                context_parts.append(f"相关文档{i+1}:\n{full_content}")
            
            full_context = "\n\n" + "="*50 + "\n\n".join(context_parts)
            
            print(f"  构建的完整上下文长度: {len(full_context)} 字符")
            print(f"  上下文包含图4标题: {'图4：中芯国际归母净利润情况概览' in full_context}")
            print(f"  上下文包含图4关键词: {'图4' in full_context and '中芯国际' in full_context and '净利润' in full_context}")
            
            print(f"\n  完整上下文内容:")
            print(f"  {full_context}")
        
        # 6. 分析问题
        print("\n" + "=" * 80)
        print("🎯 问题分析")
        print("=" * 80)
        
        if vector_results:
            first_result = vector_results[0]
            content = first_result['doc'].page_content
            
            print(f"\n最相关文档分析:")
            print(f"- 文档类型: {first_result['doc'].metadata.get('chunk_type', 'unknown')}")
            print(f"- 分数: {first_result.get('score', 'N/A')}")
            print(f"- 内容长度: {len(content)} 字符")
            print(f"- 包含图4标题: {'图4：中芯国际归母净利润情况概览' in content}")
            
            if '图4：中芯国际归母净利润情况概览' in content:
                print(f"✅ 结论: 向量搜索成功找到了图4相关文档")
                print(f"   问题可能出现在后续的源过滤或LLM处理环节")
            else:
                print(f"❌ 结论: 向量搜索没有找到包含完整图4信息的文档")
                print(f"   需要检查文档索引或向量化过程")
        else:
            print(f"❌ 结论: 向量搜索没有找到任何相关文档")
            print(f"   需要检查后过滤实现或文档索引")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_llm_context_simple()
