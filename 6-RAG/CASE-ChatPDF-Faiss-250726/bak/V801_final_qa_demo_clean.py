'''
程序说明：
## 1. 该模块演示了如何使用向量存储和问答系统
## 2. 使用预定义的问题进行问答，无需用户交互
## 3. 可以展示问答系统的完整功能
'''

import os
from dotenv import load_dotenv

from bak.V302_vector_store_qa_fixed import load_vector_store_and_answer_questions, QuestionAnsweringSystem, VectorStoreManager


def demo_batch_qa():
    """
    演示批量问答功能
    """
    print("=== 批量问答演示 ===")
    
    # 加载环境变量
    load_dotenv()
    
    # 从环境变量中获取API密钥
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '你的APIKEY')
    
    # 检查API密钥是否有效
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY == '你的APIKEY':
        print("错误: 请在.env文件中配置有效的DashScope API密钥")
        return
    
    # 创建向量存储管理器
    vector_manager = VectorStoreManager(DASHSCOPE_API_KEY)
    
    # 加载向量存储
    try:
        vector_store = vector_manager.load_vector_store("./vector_db")
        print("向量数据库加载成功")
    except Exception as e:
        print(f"向量数据库加载失败: {e}")
        return
    
    # 创建问答系统
    try:
        qa_system = QuestionAnsweringSystem(vector_store, DASHSCOPE_API_KEY)
        print("问答系统初始化成功")
    except Exception as e:
        print(f"问答系统初始化失败: {e}")
        return
    
    # 预定义问题列表
    questions = [
        "个金客户经理的职责是什么？",
        "客户经理的考核标准有哪些？",
        "如何聘任客户经理？"
    ]
    
    print("\n开始问答演示:\n")
    
    # 回答每个问题
    for i, question in enumerate(questions, 1):
        print(f"问题 {i}: {question}")
        
        try:
            # 回答问题
            result = qa_system.answer_question(question)
            
            # 显示答案
            print(f"答案: {result['answer']}")
            
            # 显示来源
            print("相关信息来源:")
            for j, source in enumerate(result['sources'], 1):
                print(f"  {j}. 文档: {source['document_name']}, 页码: {source['page_number']}")
                print(f"     内容: {source['content']}")
            
            print("-" * 50)
        except Exception as e:
            print(f"回答问题时出错: {e}")
            print("-" * 50)
    
    print("\n问答演示结束！")


if __name__ == "__main__":
    demo_batch_qa()