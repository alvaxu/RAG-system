"""
程序说明：
## 1. 精简测试RAG系统
## 2. 专注于核心功能验证
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def simple_test():
    """精简测试"""
    print("🧪 精简测试RAG系统")
    print("=" * 40)
    
    # 加载配置
    settings = Settings.load_from_file("config.json")
    api_key = settings.dashscope_api_key
    
    print(f"API密钥状态: {'已配置' if api_key and api_key != '你的APIKEY' else '未配置'}")
    
    # 加载QA系统
    vector_db_path = "./central/vector_db"
    qa_system = load_enhanced_qa_system(vector_db_path, api_key)
    
    if not qa_system:
        print("❌ QA系统加载失败")
        return
    
    print("✅ QA系统加载成功")
    
    # 测试问题
    test_question = "中芯国际的主要业务是什么？"
    print(f"\n🔍 测试问题: {test_question}")
    
    try:
        result = qa_system.answer_question(test_question, k=3)
        
        if result and 'answer' in result:
            answer = result['answer']
            sources = result.get('sources', [])
            
            print(f"✅ 回答长度: {len(answer)}")
            print(f"📚 来源数量: {len(sources)}")
            
            if "没有找到相关信息" not in answer:
                print("🎉 系统正常工作！")
                print(f"回答: {answer[:200]}...")
            else:
                print("❌ 系统返回默认回答")
        else:
            print("❌ 未获得有效回答")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    simple_test() 