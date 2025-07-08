#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 对话流（chatflow）应用调用示例
专门针对对话流类型的应用
"""

from dify_agent_client import DifyAgentClient

def simple_chatflow_example():
    """
    :function: 简单的对话流(chatflow)调用示例
    :param 无
    :return: 无
    """
    # 您的Dify配置
    BASE_URL = "https://api.dify.ai/v1"
    API_KEY = "app-BF3qnUhbd7isXOfmErQVVh9z"
    
    # 创建客户端
    client = DifyAgentClient(BASE_URL, API_KEY)
    
    user_input = "掼蛋的基本规则是什么？"
    print(f"发送消息: {user_input}")
    
    # chatflow 应用调用，app_type 指定为 "chat"
    result = client.chat_completion(
        user_input=user_input,
        user_id="demo_user",
        conversation_id=None,  # 可选，首次对话可不传
        stream=False,
        app_type="chat"
    )
    
    if result.get("error"):
        print(f"调用失败: {result.get('message')}")
    else:
        print(f"对话流回复: {result.get('answer')}")
        print(f"会话ID: {result.get('conversation_id')}")
        print(f"消息ID: {result.get('message_id')}")

if __name__ == "__main__":
    simple_chatflow_example()