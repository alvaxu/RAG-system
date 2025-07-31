'''
程序说明：
## 1. 该模块演示了如何使用向量存储和问答系统
## 2. 提供了两种使用模式：批量处理和交互式问答
## 3. 可以加载已创建的向量数据库并进行问答
'''

import os
from dotenv import load_dotenv

from bak.V302_vector_store_qa_fixed import load_vector_store_and_answer_questions


def demo_interactive_qa():
    """
    演示交互式问答功能
    """
    print("=== 交互式问答演示 ===")
    print("系统将加载已创建的向量数据库并启动问答交互。")
    
    # 加载环境变量
    load_dotenv()
    
    # 从环境变量中获取API密钥
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '你的APIKEY')
    
    # 启动问答交互
    load_vector_store_and_answer_questions("./vector_db", DASHSCOPE_API_KEY)


def demo_batch_qa():
    """
    演示批量问答功能
    """
    print("=== 批量问答演示 ===")
    print("此功能演示如何批量处理问题并生成答案。")
    
    # 这里可以添加批量处理问题的代码
    # 例如从文件中读取问题列表，逐个处理并保存结果
    
    print("批量问答功能示例：")
    print("1. 从文件读取问题列表")
    print("2. 逐个处理问题")
    print("3. 将结果保存到文件中")


if __name__ == "__main__":
    print("向量存储和问答系统演示")
    print("请选择演示模式：")
    print("1. 交互式问答")
    print("2. 批量问答")
    
    choice = input("请输入选项 (1 或 2): ").strip()
    
    if choice == "1":
        demo_interactive_qa()
    elif choice == "2":
        demo_batch_qa()
    else:
        print("无效选项，请选择 1 或 2。")