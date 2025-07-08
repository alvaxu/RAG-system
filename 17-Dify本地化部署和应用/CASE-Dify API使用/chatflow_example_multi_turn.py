#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 对话流（chatflow）多轮对话示例
用户可多轮输入，输入q或exit退出
"""

from dify_agent_client import DifyAgentClient


def multi_turn_chatflow_example():
    """
    :function: 多轮对话流(chatflow)调用示例，支持用户多轮输入
    :param 无
    :return: 无
    """
    # Dify配置
    BASE_URL = "https://api.dify.ai/v1"
    API_KEY = "app-BF3qnUhbd7isXOfmErQVVh9z"

    # 创建客户端
    client = DifyAgentClient(BASE_URL, API_KEY)

    conversation_id = None  # 首轮对话不传conversation_id
    user_id = "demo_user"

    print("欢迎使用Dify对话流多轮对话示例，输入q或exit退出。")
    while True:
        user_input = input("你: ")
        if user_input.strip().lower() in ["q", "exit"]:
            print("对话已结束。")
            break
        # chatflow 应用调用，app_type 指定为 "chat"
        result = client.chat_completion(
            user_input=user_input,
            user_id=user_id,
            conversation_id=conversation_id,
            stream=False,
            app_type="chat"
        )
        if result.get("error"):
            print(f"调用失败: {result.get('message')}")
            break
        else:
            print(f"Dify: {result.get('answer')}")
            # 更新conversation_id，保证上下文连续
            conversation_id = result.get("conversation_id", conversation_id)

if __name__ == "__main__":
    multi_turn_chatflow_example() 