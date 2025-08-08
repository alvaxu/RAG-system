"""
程序说明：
## 1. 详细调试QA系统的每个步骤
## 2. 检查检索、重排序、过滤、生成回答的每个环节
## 3. 找出问题所在的具体位置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def debug_qa_system():
    """详细调试QA系统"""
    print("🔧 详细调试QA系统...")
    print("=" * 60)
    
    # 加载配置
    settings = Settings.load_from_file("config.json")
    api_key = settings.dashscope_api_key
    
    if not api_key or api_key == '你的APIKEY':
        print("❌ 错误: 未配置DashScope API密钥")
        return
    
    # 加载QA系统
    vector_db_path = "./central/vector_db"
    qa_system = load_enhanced_qa_system(vector_db_path, api_key)
    
    if not qa_system:
        print("❌ 错误: QA系统加载失败")
        return
    
    print("✅ QA系统加载成功")
    
    # 测试问题
    test_question = "中芯国际的主要业务是什么？"
    print(f"\n🔍 测试问题: {test_question}")
    print("-" * 50)
    
    try:
        # 1. 检查初始检索
        print("📋 步骤1: 初始检索")
        initial_docs = qa_system._initial_retrieval(test_question, 5)
        print(f"✅ 初始检索完成，获得 {len(initial_docs)} 个文档")
        
        if initial_docs:
            for i, doc in enumerate(initial_docs[:2], 1):
                print(f"   文档 {i}: {doc.page_content[:100]}...")
                print(f"   来源: {doc.metadata.get('document_name', '未知')}")
        else:
            print("❌ 初始检索没有找到文档")
            return
        
        # 2. 检查重排序
        print("\n📋 步骤2: 重排序")
        reranked_docs = qa_system._apply_reranking(test_question, initial_docs)
        print(f"✅ 重排序完成，保留 {len(reranked_docs)} 个文档")
        
        # 3. 检查智能过滤
        print("\n📋 步骤3: 智能过滤")
        filtered_docs = qa_system._apply_smart_filtering(test_question, reranked_docs)
        print(f"✅ 智能过滤完成，保留 {len(filtered_docs)} 个文档")
        
        if filtered_docs:
            for i, doc in enumerate(filtered_docs[:2], 1):
                print(f"   过滤后文档 {i}: {doc.page_content[:100]}...")
        else:
            print("❌ 智能过滤后没有保留任何文档")
            return
        
        # 4. 检查LLM调用
        print("\n📋 步骤4: LLM调用")
        print("准备调用LLM生成回答...")
        
        # 直接调用LLM
        try:
            response = qa_system.qa_chain.invoke({
                "input_documents": filtered_docs,
                "question": test_question
            })
            
            print(f"✅ LLM调用成功")
            print(f"响应类型: {type(response)}")
            
            # 检查响应内容
            if isinstance(response, dict):
                if 'output_text' in response:
                    answer = response['output_text']
                elif 'result' in response:
                    answer = response['result']
                elif 'answer' in response:
                    answer = response['answer']
                else:
                    answer = str(response)
            elif hasattr(response, 'content'):
                answer = response.content
            elif hasattr(response, 'text'):
                answer = response.text
            else:
                answer = str(response)
            
            print(f"回答长度: {len(answer)}")
            print(f"回答内容: {answer[:200]}...")
            
            if len(answer.strip()) < 10:
                print("⚠️ 警告: LLM回答过短")
            else:
                print("✅ LLM回答正常")
                
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            return
        
        # 5. 检查完整流程
        print("\n📋 步骤5: 完整流程测试")
        result = qa_system.answer_question(test_question, k=5)
        
        if result and 'answer' in result:
            answer = result['answer']
            sources = result.get('sources', [])
            
            print(f"✅ 完整流程成功")
            print(f"回答: {answer[:300]}...")
            print(f"来源数量: {len(sources)}")
            
            if "没有找到相关信息" not in answer:
                print("🎉 系统正常工作！")
            else:
                print("⚠️ 系统返回了默认回答")
        else:
            print("❌ 完整流程失败")
            
    except Exception as e:
        print(f"❌ 调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 调试完成")

if __name__ == "__main__":
    debug_qa_system() 