"""
程序说明：
## 1. 简单测试QA系统
## 2. 使用已知能检索到内容的问题
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
    """简单测试QA系统"""
    print("🧪 简单测试QA系统...")
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
    
    # 使用已知能检索到内容的问题
    test_questions = [
        "中芯国际产能利用率",
        "晶圆制造",
        "上海证券",
        "投资建议"
    ]
    
    print("\n📋 开始测试...")
    print("-" * 40)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 问题 {i}: {question}")
        print("-" * 30)
        
        try:
            # 获取回答
            result = qa_system.answer_question(question, k=3)
            
            if result and 'answer' in result:
                answer = result['answer']
                sources = result.get('sources', [])
                
                print(f"✅ 回答: {answer[:200]}...")
                print(f"📚 来源数量: {len(sources)}")
                
                # 显示来源信息
                for j, source in enumerate(sources[:2], 1):
                    doc_name = source.get('metadata', {}).get('document_name', '未知文档')
                    page_num = source.get('metadata', {}).get('page_number', '未知页码')
                    chunk_type = source.get('metadata', {}).get('chunk_type', 'text')
                    print(f"   来源 {j}: {doc_name} (第{page_num}页, 类型:{chunk_type})")
                
            else:
                print("❌ 未获得有效回答")
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成")

if __name__ == "__main__":
    simple_test() 