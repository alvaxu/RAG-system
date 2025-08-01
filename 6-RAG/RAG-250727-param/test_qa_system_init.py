"""
程序说明：
## 1. 测试QA系统初始化过程
## 2. 验证各个组件是否正常加载
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_qa_system import load_enhanced_qa_system
from core.memory_manager import MemoryManager
from config.settings import Settings

def test_qa_system_init():
    """测试QA系统初始化"""
    try:
        # 加载配置
        settings = Settings.load_from_file('config.json')
        print(f"配置加载成功")
        
        # 初始化记忆管理器
        memory_manager = MemoryManager(settings.memory_db_dir)
        print(f"记忆管理器初始化成功")
        
        # 初始化QA系统
        print(f"开始初始化QA系统...")
        qa_system = load_enhanced_qa_system(
            vector_db_path=settings.vector_db_dir,
            api_key=settings.dashscope_api_key,
            memory_manager=memory_manager,
            config=settings.to_dict()
        )
        
        if qa_system:
            print(f"QA系统初始化成功")
            print(f"向量存储: {'已加载' if qa_system.vector_store else '未加载'}")
            print(f"LLM: {'已初始化' if qa_system.llm else '未初始化'}")
            print(f"重排序引擎: {'已初始化' if qa_system.reranking_engine else '未初始化'}")
            print(f"智能过滤引擎: {'已初始化' if qa_system.smart_filter_engine else '未初始化'}")
            print(f"源过滤引擎: {'已初始化' if qa_system.source_filter_engine else '未初始化'}")
            
            # 直接测试向量检索
            print(f"\n直接测试向量检索...")
            try:
                docs = qa_system.vector_store.similarity_search("中芯国际", k=3)
                print(f"直接检索成功，获得 {len(docs)} 个文档")
                for i, doc in enumerate(docs[:2]):
                    print(f"文档 {i+1}: {doc.page_content[:50]}...")
            except Exception as e:
                print(f"直接检索失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 测试QA系统的检索方法
            print(f"\n测试QA系统检索方法...")
            try:
                docs = qa_system._initial_retrieval("中芯国际", 3)
                print(f"QA系统检索成功，获得 {len(docs)} 个文档")
            except Exception as e:
                print(f"QA系统检索失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 测试简单问答
            print(f"\n测试简单问答...")
            result = qa_system.answer_question("中芯国际", k=3)
            print(f"问答结果: {result.get('answer', '无答案')}")
            print(f"来源数量: {len(result.get('sources', []))}")
            
        else:
            print(f"QA系统初始化失败")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qa_system_init() 