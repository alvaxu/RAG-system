"""
程序说明：
## 1. 调试QA系统的向量存储状态
## 2. 检查检索功能是否正常
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
    """调试QA系统"""
    print("🔧 调试QA系统...")
    print("=" * 50)
    
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
    
    # 检查向量存储
    if qa_system.vector_store:
        print(f"✅ 向量存储已加载")
        print(f"📊 文档数量: {len(qa_system.vector_store.docstore._dict)}")
        
        # 直接测试检索
        print("\n🧪 直接测试检索...")
        test_questions = ["中芯国际", "晶圆制造", "产能利用率"]
        
        for question in test_questions:
            print(f"\n🔍 测试问题: {question}")
            try:
                # 直接使用向量存储检索
                docs = qa_system.vector_store.similarity_search(question, k=3)
                print(f"✅ 直接检索成功，找到 {len(docs)} 个文档")
                
                for i, doc in enumerate(docs, 1):
                    print(f"   文档 {i}: {doc.page_content[:100]}...")
                    
            except Exception as e:
                print(f"❌ 直接检索失败: {e}")
        
        # 测试QA系统的初始检索
        print("\n🧪 测试QA系统初始检索...")
        for question in test_questions:
            print(f"\n🔍 测试问题: {question}")
            try:
                docs = qa_system._initial_retrieval(question, 3)
                print(f"✅ QA系统初始检索成功，找到 {len(docs)} 个文档")
                
                for i, doc in enumerate(docs, 1):
                    print(f"   文档 {i}: {doc.page_content[:100]}...")
                    
            except Exception as e:
                print(f"❌ QA系统初始检索失败: {e}")
    
    else:
        print("❌ 向量存储未加载")
    
    print("\n" + "=" * 50)
    print("🎯 调试完成")

if __name__ == "__main__":
    debug_qa_system() 