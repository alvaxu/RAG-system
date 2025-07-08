from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import Tongyi
from langchain.agents import AgentType
import socket
import subprocess
import platform
import re
from typing import Dict, Any, List, Optional, Type
import os

# 网络连通性检查工具
class PingTool(BaseTool):
    name: str = "ping_check"
    description: str = "检查从本机到指定主机名或IP的网络连通性"

    def _run(self, target: str) -> str:
        try:
            # 根据操作系统选择ping命令参数
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '4', target]
            
            # 执行ping命令
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 提取延迟信息
                delay_match = re.search(r'平均 = (\d+)ms', result.stdout)
                delay = delay_match.group(1) if delay_match else "未知"
                return f"连接成功，平均延迟: {delay}ms"
            else:
                return "连接失败，目标主机不可达"
        except Exception as e:
            return f"执行ping命令时出错: {str(e)}"

# DNS解析查询工具
class DNSTool(BaseTool):
    name: str = "dns_resolve"
    description: str = "将主机名解析为IP地址"

    def _run(self, hostname: str) -> str:
        try:
            ip_address = socket.gethostbyname(hostname)
            return f"主机名 {hostname} 解析为IP地址: {ip_address}"
        except socket.gaierror:
            return f"无法解析主机名 {hostname}，DNS解析失败"
        except Exception as e:
            return f"DNS解析过程中出错: {str(e)}"

# 本地网络接口检查工具
class InterfaceCheckTool(BaseTool):
    name: str = "interface_check"
    description: str = "检查本地网络接口的状态"

    def _run(self, interface_name: Optional[str] = None) -> str:
        try:
            if platform.system().lower() == 'windows':
                command = ['ipconfig', '/all']
            else:
                command = ['ifconfig']
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                if interface_name:
                    # 查找特定接口的信息
                    pattern = rf"{interface_name}.*?(?=\n\n|$)"
                    match = re.search(pattern, result.stdout, re.DOTALL)
                    if match:
                        return f"接口 {interface_name} 信息:\n{match.group(0)}"
                    else:
                        return f"未找到接口 {interface_name} 的信息"
                else:
                    return "所有网络接口信息:\n" + result.stdout
            else:
                return "获取网络接口信息失败"
        except Exception as e:
            return f"检查网络接口时出错: {str(e)}"

# 网络日志分析工具
class LogAnalysisTool(BaseTool):
    name: str = "log_analysis"
    description: str = "在系统或应用日志中搜索网络相关问题"

    def _run(self, keyword: str, time_range: Optional[str] = None) -> str:
        try:
            # 模拟日志分析
            log_entries = [
                "2024-03-20 10:15:23 [ERROR] Connection timeout to server",
                "2024-03-20 10:15:24 [INFO] Retrying connection...",
                "2024-03-20 10:15:25 [ERROR] DNS resolution failed",
                "2024-03-20 10:15:26 [WARNING] High latency detected"
            ]
            
            # 搜索包含关键词的日志
            matching_entries = [entry for entry in log_entries if keyword.lower() in entry.lower()]
            
            if matching_entries:
                return "找到匹配的日志条目:\n" + "\n".join(matching_entries)
            else:
                return f"未找到包含关键词 '{keyword}' 的日志条目"
        except Exception as e:
            return f"分析日志时出错: {str(e)}"

def create_tool_chain():
    # 创建工具实例
    tools = [
        PingTool(),
        DNSTool(),
        InterfaceCheckTool(),
        LogAnalysisTool()
    ]
    
    # 初始化大语言模型
    DASHSCOPE_API_KEY = 'sk-882e296067b744289acf27e6e20f3ec0'
    llm = Tongyi(
        model_name="qwen-turbo",
        dashscope_api_key=DASHSCOPE_API_KEY 
    )
    
    # 创建提示模板
    template = """你是一个专业的网络诊断助手，可以使用以下工具:
    {tools}
    可用工具名称: {tool_names}

    使用以下格式:
    问题: 你需要回答的问题
    思考: 你应该始终思考要做什么
    行动: 要使用的工具名称，必须是 [{tool_names}] 中的一个
    行动输入: 工具的输入
    观察: 工具的结果
    ... (这个思考/行动/行动输入/观察可以重复 N 次)
    思考: 我现在已经有了最终答案
    回答: 对原始问题的最终回答

    开始!
    问题: {input}
    思考: {agent_scratchpad}"""
    
    prompt = PromptTemplate.from_template(template)
    
    # 创建memory，记住input和output
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="input",
        output_key="output"
    )
    
    # 创建Zero-Shot ReAct agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
    )
    
    # 创建代理执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=False,
        return_intermediate_steps=True  # 返回中间步骤，便于调试
    )
    
    return agent_executor

def process_task(task_description: str) -> str:
    try:
        agent_executor = create_tool_chain()
        result = agent_executor.invoke({
            "input": task_description,
            "chat_history": []  # 初始化空的对话历史
        })
        return result["output"]
    except Exception as e:
        return f"处理任务时出错: {str(e)}"

if __name__ == "__main__":
    # 示例任务
    task1 = "我无法访问 www.example.com，浏览器显示连接超时。"
    print("任务1:", task1)
    result = process_task(task1)
    print("任务执行结果：")
    print(result) 