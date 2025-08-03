"""
程序说明：
## 1. 测试改进后的QA系统
## 2. 验证是否能平衡使用两个文档
## 3. 检查检索结果的文档分布
"""

import os
import json
from core.enhanced_qa_system import load_enhanced_qa_system
from core.memory_manager import MemoryManager

def test_improved_qa_system():
    """
    测试改进后的QA系统
    """
    print("=== 测试改进后的QA系统 ===")
    
    # 配置API密钥
    api_key = ""
    
    # 首先尝试从config.json加载
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            api_key = config_data.get('api', {}).get('dashscope_api_key', '')
            print(f"✅ 从config.json加载API密钥成功")
        except Exception as e:
            print(f"❌ 从config.json加载API密钥失败: {e}")
    
    # 如果config.json中没有，尝试从环境变量加载
    if not api_key:
        api_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
        if api_key:
            print(f"✅ 从环境变量加载API密钥成功")
    
    if not api_key or api_key == '你的APIKEY':
        print("❌ 未配置有效的DashScope API密钥")
        return
    
    # 加载配置
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    
    # 初始化记忆管理器
    memory_manager = MemoryManager()
    
    # 加载QA系统
    vector_db_path = "central/vector_db"
    qa_system = load_enhanced_qa_system(vector_db_path, api_key, memory_manager, config)
    
    if not qa_system:
        print("❌ QA系统加载失败")
        return
    
    print("✅ QA系统加载成功")
    
    # 测试查询
    test_questions = [
        "中芯国际的主要业务是什么？",
        "中芯国际的产能利用率如何？",
        "中芯国际的毛利率变化趋势怎样？",
        "中芯国际在晶圆代工行业的市场地位如何？",
        "中芯国际的财务表现如何？"
    ]
    
    user_id = "test_user_improved"
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"🔍 测试问题 {i}: {question}")
        
        # 直接使用answer_question方法回答问题
        result = qa_system.answer_question(question, k=8)
        
        if 'error' not in result:
            answer = result.get('answer', '')
            sources = result.get('sources', [])
            
            # 统计文档来源
            doc_sources = {}
            for source in sources:
                doc_name = source.get('metadata', {}).get('document_name', '未知文档')
                doc_sources[doc_name] = doc_sources.get(doc_name, 0) + 1
            
            print(f"📋 文档来源分布: {doc_sources}")
            print(f"📊 总来源数: {len(sources)}")
            
            # 显示答案的前200个字符
            answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
            print(f"💬 答案预览: {answer_preview}")
            
            # 检查是否使用了两个文档
            if len(doc_sources) >= 2:
                print("✅ 成功使用了多个文档")
            elif len(doc_sources) == 1:
                doc_name = list(doc_sources.keys())[0]
                print(f"⚠️ 只使用了单个文档: {doc_name}")
            else:
                print("❌ 没有找到相关文档")
        else:
            print(f"❌ 回答失败: {result.get('error', '未知错误')}")
    
    print(f"\n{'='*60}")
    print("🎯 测试完成！")

if __name__ == "__main__":
    test_improved_qa_system() 