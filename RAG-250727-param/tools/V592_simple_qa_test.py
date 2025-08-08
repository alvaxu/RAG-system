"""
程序说明：
## 1. 简化的QA测试
## 2. 直接使用LLM生成回答
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def simple_qa_test():
    """简化的QA测试"""
    print("🧪 简化QA测试...")
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
    
    # 测试问题
    test_question = "中芯国际的主要业务是什么？"
    print(f"\n🔍 测试问题: {test_question}")
    
    try:
        # 直接获取文档
        docs = qa_system._initial_retrieval(test_question, 3)
        print(f"✅ 检索到 {len(docs)} 个文档")
        
        if docs:
            # 显示文档内容
            for i, doc in enumerate(docs, 1):
                print(f"\n📄 文档 {i}:")
                print(f"   内容: {doc.page_content[:200]}...")
                print(f"   来源: {doc.metadata.get('document_name', '未知')}")
            
            # 直接生成回答
            print(f"\n🤖 生成回答...")
            answer_result = qa_system._generate_answer(test_question, docs)
            
            print(f"✅ 回答: {answer_result['answer']}")
            
        else:
            print("❌ 没有检索到相关文档")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成")

if __name__ == "__main__":
    simple_qa_test() 