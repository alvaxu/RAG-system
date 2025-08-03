"""
程序说明：
## 1. 详细调试QA系统错误
## 2. 查看具体的错误信息和堆栈跟踪
## 3. 检查API密钥配置和系统初始化
"""

import os
import json
import traceback
from core.enhanced_qa_system import load_enhanced_qa_system
from core.memory_manager import MemoryManager

def debug_qa_error():
    """
    详细调试QA系统错误
    """
    print("=== 详细调试QA系统错误 ===")
    
    # 配置API密钥
    api_key = ""
    
    # 首先尝试从config.json加载
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            api_key = config_data.get('api', {}).get('dashscope_api_key', '')
            print(f"✅ 从config.json加载API密钥成功: {api_key[:10]}...")
        except Exception as e:
            print(f"❌ 从config.json加载API密钥失败: {e}")
    
    # 如果config.json中没有，尝试从环境变量加载
    if not api_key:
        api_key = os.getenv('MY_DASHSCOPE_API_KEY', '')
        if api_key:
            print(f"✅ 从环境变量加载API密钥成功: {api_key[:10]}...")
    
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
    
    print(f"✅ 配置加载成功")
    
    # 初始化记忆管理器
    try:
        memory_manager = MemoryManager()
        print(f"✅ 记忆管理器初始化成功")
    except Exception as e:
        print(f"❌ 记忆管理器初始化失败: {e}")
        traceback.print_exc()
        return
    
    # 加载QA系统
    try:
        vector_db_path = "central/vector_db"
        print(f"🔍 尝试加载向量数据库: {vector_db_path}")
        
        if not os.path.exists(vector_db_path):
            print(f"❌ 向量数据库路径不存在: {vector_db_path}")
            return
        
        print(f"✅ 向量数据库路径存在")
        
        qa_system = load_enhanced_qa_system(vector_db_path, api_key, memory_manager, config)
        
        if not qa_system:
            print("❌ QA系统加载失败")
            return
        
        print("✅ QA系统加载成功")
        
        # 测试一个简单的问题
        test_question = "中芯国际的主要业务是什么？"
        print(f"\n🔍 测试问题: {test_question}")
        
        try:
            # 直接调用answer_question方法
            result = qa_system.answer_question(test_question, k=5)
            
            if 'error' in result:
                print(f"❌ 回答失败: {result['error']}")
                print(f"📊 处理时间: {result.get('processing_time', 0):.2f}秒")
            else:
                print(f"✅ 回答成功")
                print(f"📊 处理时间: {result.get('processing_time', 0):.2f}秒")
                print(f"📋 来源数量: {len(result.get('sources', []))}")
                
                # 显示答案预览
                answer = result.get('answer', '')
                answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"💬 答案预览: {answer_preview}")
                
        except Exception as e:
            print(f"❌ 调用answer_question方法失败: {e}")
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ 加载QA系统失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_qa_error() 