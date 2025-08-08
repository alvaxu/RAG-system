"""
程序说明：
## 1. 测试系统对不同类型问题的回答能力
## 2. 验证文本、表格、图表问题的处理
## 3. 确认系统正常工作
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def test_system_questions():
    """测试系统问题回答能力"""
    print("🧪 测试系统问题回答能力...")
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
    
    # 测试问题列表 - 涵盖文本、表格、图表三种类型
    test_questions = [
        # 文本类问题
        "中芯国际的主要业务和核心技术是什么？",
        "中芯国际在晶圆代工行业的市场地位如何？",
        
        # 表格类问题  
        "中芯国际2024-2027年的营业收入预测数据是多少？",
        "中芯国际的市盈率和市净率数据是多少？",
        
        # 图表类问题
        "中芯国际全球部署示意图显示了什么？",
        "中芯国际的股票价格走势图如何？"
    ]
    
    print("\n📋 开始测试不同类型的问题...")
    print("-" * 60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 问题 {i}: {question}")
        print("-" * 50)
        
        try:
            # 获取回答
            result = qa_system.answer_question(question, k=5)
            
            if result and 'answer' in result:
                answer = result['answer']
                sources = result.get('sources', [])
                
                print(f"✅ 回答: {answer[:300]}...")
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
    
    print("\n" + "=" * 60)
    print("🎯 测试完成")

if __name__ == "__main__":
    test_system_questions() 