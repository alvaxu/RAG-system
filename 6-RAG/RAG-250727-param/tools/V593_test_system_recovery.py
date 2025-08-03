"""
程序说明：
## 1. 测试RAG系统是否恢复正常工作
## 2. 验证不同类型问题的回答能力
## 3. 确认智能过滤引擎不会过度过滤内容
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.enhanced_qa_system import load_enhanced_qa_system
from config.settings import Settings

def test_system_recovery():
    """测试系统恢复情况"""
    print("🧪 测试RAG系统恢复情况...")
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
    
    # 测试问题列表 - 涵盖不同类型
    test_questions = [
        # 基础信息问题
        "中芯国际的主要业务是什么？",
        "中芯国际在晶圆代工行业的地位如何？",
        
        # 具体数据问题
        "中芯国际的产能利用率情况如何？",
        "中芯国际的营业收入预测是多少？",
        
        # 技术相关问题
        "中芯国际的核心技术有哪些？",
        "中芯国际的工艺技术水平如何？",
        
        # 投资相关问题
        "中芯国际的投资建议是什么？",
        "中芯国际的市盈率和市净率是多少？"
    ]
    
    print("\n📋 开始测试不同类型的问题...")
    print("-" * 60)
    
    success_count = 0
    total_count = len(test_questions)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 问题 {i}: {question}")
        print("-" * 50)
        
        try:
            # 获取回答
            result = qa_system.answer_question(question, k=5)
            
            if result and 'answer' in result:
                answer = result['answer']
                sources = result.get('sources', [])
                
                # 检查回答是否有效（不是默认的"没有找到相关信息"）
                if "没有找到相关信息" not in answer and len(answer.strip()) > 20:
                    print(f"✅ 回答: {answer[:300]}...")
                    print(f"📚 来源数量: {len(sources)}")
                    success_count += 1
                    
                    # 显示来源信息
                    for j, source in enumerate(sources[:2], 1):
                        doc_name = source.get('metadata', {}).get('document_name', '未知文档')
                        page_num = source.get('metadata', {}).get('page_number', '未知页码')
                        chunk_type = source.get('metadata', {}).get('chunk_type', 'text')
                        print(f"   来源 {j}: {doc_name} (第{page_num}页, 类型:{chunk_type})")
                else:
                    print(f"❌ 回答无效: {answer}")
                    
            else:
                print("❌ 未获得有效回答")
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 测试完成")
    print(f"✅ 成功回答: {success_count}/{total_count}")
    print(f"📊 成功率: {success_count/total_count*100:.1f}%")
    
    if success_count > 0:
        print("🎉 系统已恢复正常工作！")
    else:
        print("⚠️ 系统仍有问题，需要进一步调试")

if __name__ == "__main__":
    test_system_recovery() 