"""
程序说明：
## 1. 测试新增文档的查询功能
## 2. 检查是否能检索到新增文档的内容
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def test_new_doc_query():
    """测试新增文档的查询功能"""
    print("🔍 测试新增文档查询功能...")
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
    
    # 测试问题列表
    test_questions = [
        "中芯国际的产能利用率如何？",
        "中芯国际的工艺技术有哪些？", 
        "中芯国际的财务表现怎么样？",
        "中芯国际的技术发展情况如何？",
        "中芯国际的市场地位如何？"
    ]
    
    print("\n📋 开始测试查询...")
    print("-" * 60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 问题 {i}: {question}")
        print("-" * 40)
        
        try:
            # 获取回答
            result = qa_system.answer_question(question, k=5)
            
            if result and 'answer' in result:
                answer = result['answer']
                sources = result.get('sources', [])
                
                print(f"✅ 回答: {answer[:200]}...")
                print(f"📚 来源数量: {len(sources)}")
                
                # 显示来源信息
                for j, source in enumerate(sources[:3], 1):
                    doc_name = source.get('metadata', {}).get('document_name', '未知文档')
                    page_num = source.get('metadata', {}).get('page_number', '未知页码')
                    chunk_type = source.get('metadata', {}).get('chunk_type', 'text')
                    print(f"   来源 {j}: {doc_name} (第{page_num}页, 类型:{chunk_type})")
                
            else:
                print("❌ 未获得有效回答")
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 测试完成")

if __name__ == "__main__":
    test_new_doc_query() 