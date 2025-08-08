'''
程序说明：
## 1. 调试API系统中的QA系统
## 2. 检查API系统中的向量数据库加载
## 3. 测试API系统中的检索功能
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.enhanced_qa_system import load_enhanced_qa_system
from core.memory_manager import MemoryManager

def debug_api_qa_system():
    """调试API系统中的QA系统"""
    print("="*60)
    print("🔍 调试API系统中的QA系统")
    print("="*60)
    
    try:
        # 加载配置
        config = Settings.load_from_file('config.json')
        print(f"✅ 配置加载成功")
        print(f"   向量数据库路径: {config.vector_db_dir}")
        print(f"   API密钥: {'已配置' if config.dashscope_api_key and config.dashscope_api_key != '你的DashScope API密钥' else '未配置'}")
        
        # 初始化记忆管理器（模拟API系统）
        print(f"\n🔍 初始化记忆管理器...")
        memory_manager = MemoryManager(config.memory_db_dir)
        print(f"✅ 记忆管理器初始化成功")
        
        # 加载QA系统（模拟API系统的方式）
        print(f"\n🔍 加载QA系统...")
        qa_system = load_enhanced_qa_system(
            config.vector_db_dir, 
            config.dashscope_api_key, 
            memory_manager, 
            config.to_dict()
        )
        
        if qa_system:
            print(f"✅ QA系统加载成功")
            print(f"   向量存储: {'已加载' if qa_system.vector_store else '未加载'}")
            
            if qa_system.vector_store:
                print(f"   向量存储文档数: {len(qa_system.vector_store.docstore._dict)}")
                print(f"   向量存储索引大小: {qa_system.vector_store.index.ntotal}")
                
                # 测试检索
                print(f"\n🔍 测试检索功能...")
                results = qa_system.vector_store.similarity_search("中芯国际", k=3)
                print(f"✅ 直接检索成功，找到 {len(results)} 个结果")
                
                # 测试QA系统检索
                print(f"\n🔍 测试QA系统检索...")
                result = qa_system.answer_question("中芯国际", k=3)
                print(f"✅ QA系统检索成功")
                print(f"   检索到的文档数: {len(result.get('sources', []))}")
                print(f"   答案长度: {len(result.get('answer', ''))}")
                
            else:
                print(f"❌ 向量存储未加载")
                
        else:
            print(f"❌ QA系统加载失败")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_qa_system() 