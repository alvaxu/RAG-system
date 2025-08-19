'''
程序说明：

## 1. 测试修改后的metadata传递功能
## 2. 验证新增字段是否正确传递
## 3. 检查LLM上下文是否完整
## 4. 验证来源信息是否完整
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


def test_enhanced_metadata():
    """测试修改后的metadata传递功能"""
    print("🧪 测试修改后的metadata传递功能")
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
                
                # 检查新增的metadata字段
                print(f"    📋 新增metadata字段:")
                print(f"      document_name: {result.get('document_name', 'N/A')}")
                print(f"      page_number: {result.get('page_number', 'N/A')}")
                print(f"      chunk_type: {result.get('chunk_type', 'N/A')}")
                print(f"      enhanced_description: {result.get('enhanced_description', 'N/A')[:100]}...")
                print(f"      llm_context: {result.get('llm_context', 'N/A')[:100]}...")
                
                # 检查文档类型
                if hasattr(result['doc'], 'metadata') and result['doc'].metadata:
                    chunk_type = result['doc'].metadata.get('chunk_type', 'unknown')
                    document_name = result['doc'].metadata.get('document_name', 'unknown')
                    page_number = result['doc'].metadata.get('page_number', 'unknown')
                    print(f"    📄 文档信息:")
                    print(f"      文档类型: {chunk_type}")
                    print(f"      文档名称: {document_name}")
                    print(f"      页码: {page_number}")
                
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
                
                # 显示内容前200字符
                print(f"    内容预览: {content[:200]}...")
        
        # 4. 验证LLM上下文完整性
        print(f"\n📊 验证LLM上下文完整性")
        if vector_results:
            first_result = vector_results[0]
            llm_context = first_result.get('llm_context', '')
            
            if llm_context:
                print(f"  LLM上下文长度: {len(llm_context)} 字符")
                print(f"  包含图4标题: {'图4：中芯国际归母净利润情况概览' in llm_context}")
                print(f"  包含图4关键词: {'图4' in llm_context and '中芯国际' in llm_context and '净利润' in llm_context}")
                
                # 检查enhanced_description是否包含在上下文中
                enhanced_desc = first_result.get('enhanced_description', '')
                if enhanced_desc and enhanced_desc in llm_context:
                    print("  ✅ enhanced_description已正确包含在LLM上下文中")
                else:
                    print("  ❌ enhanced_description未包含在LLM上下文中")
                
                print(f"\n  LLM上下文内容预览:")
                print(f"  {llm_context[:500]}...")
            else:
                print("  ❌ 没有找到llm_context字段")
        
        # 5. 验证来源信息完整性
        print(f"\n📊 验证来源信息完整性")
        if vector_results:
            first_result = vector_results[0]
            
            required_fields = ['document_name', 'page_number', 'chunk_type']
            missing_fields = []
            
            for field in required_fields:
                value = first_result.get(field, '')
                if value:
                    print(f"  ✅ {field}: {value}")
                else:
                    print(f"  ❌ {field}: 缺失")
                    missing_fields.append(field)
            
            if not missing_fields:
                print("  ✅ 所有必需的来源信息字段都已正确传递")
            else:
                print(f"  ❌ 缺失的字段: {missing_fields}")
        
        # 6. 总结
        print("\n" + "=" * 80)
        print("🎯 测试总结")
        print("=" * 80)
        
        if vector_results:
            first_result = vector_results[0]
            
            print(f"\n修改效果验证:")
            print(f"✅ 新增metadata字段传递: {'document_name' in first_result and 'page_number' in first_result}")
            print(f"✅ LLM上下文完整性: {'llm_context' in first_result and first_result['llm_context']}")
            print(f"✅ 来源信息完整性: {first_result.get('document_name') and first_result.get('page_number')}")
            
            print(f"\n预期效果:")
            print(f"1. 前端能正确显示来源信息（不再显示'未知文档'）")
            print(f"2. LLM能获得完整的图4上下文信息")
            print(f"3. 能生成准确的答案而不是'没有关于图4的信息'")
        else:
            print(f"❌ 没有找到向量搜索结果，需要检查后过滤实现")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    test_enhanced_metadata()
