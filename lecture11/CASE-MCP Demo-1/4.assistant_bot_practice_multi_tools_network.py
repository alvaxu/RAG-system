"""本程序实现了基于Assistant的多工具智能助手：
1. 高德AMAP-MCP - 地图服务查询、路线规划
2. fetch MCP - 网络资源获取
3. Bing MCP - 搜索引擎查询
4. 本地txt计数MCP
5. Oracle SQL数据库查询
6. 天气查询（高德API）
7. IP地理位置查询（高德API）
8. 网络诊断工具（Ping、DNS、接口检查、日志分析）

主要功能：
- 通过自然语言进行地图、天气、IP、SQL、网络诊断等多种服务查询
- 支持多种交互方式(GUI、TUI、测试模式)
- 支持旅游规划、地点查询、路线导航、天气、IP定位、数据库、网络诊断等
"""

import os
import asyncio
from typing import Optional
import dashscope
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from qwen_agent.tools.base import BaseTool, register_tool
import requests
import platform
import subprocess
import socket
import re

# Oracle数据库连接配置
ORACLE_USER = "dbtest"
ORACLE_PASSWORD = "test"
ORACLE_HOST = "192.168.43.11:1521"
ORACLE_SERVICE = "FREEPDB1"
oracle_connection_string = f"oracle+cx_oracle://{ORACLE_USER}:{ORACLE_PASSWORD}@{ORACLE_HOST}/?service_name={ORACLE_SERVICE}"

# 配置 DashScope
ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), 'resource')
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', '')
dashscope.timeout = 30

# ====== Oracle表结构提示词 ======
system_prompt_sql = """你可以根据如下表结构生成SQL：\n\n-- 电商销售订单表 ORDERS\nORDER_ID, ORDER_NO, USER_ID, ADDRESS_ID, TOTAL_AMOUNT, PAYMENT_AMOUNT, FREIGHT_AMOUNT, ORDER_STATUS, PAYMENT_TIME, DELIVERY_TIME, RECEIVE_TIME, CREATE_TIME\n-- 货品表 ORDER_ITEMS\nITEM_ID, ORDER_ID, PRODUCT_ID, PRODUCT_NAME, PRODUCT_IMAGE, PRICE, QUANTITY, TOTAL_PRICE\n-- 客户表 USERS\nUSER_ID, USERNAME, PASSWORD, EMAIL, PHONE, REGISTER_DATE, STATUS\n"""

system_prompt_base = (
    "你是一个多功能智能助手，具备如下能力：\n"
    "- 地图查询、路线规划、景点推荐\n"
    "- Oracle SQL数据库查询（如需SQL会自动提供表结构）\n"
    "- 天气查询、IP地理位置查询\n"
    "- 网络资源获取、Bing搜索等\n"
    "- 网络诊断（Ping、DNS、接口检查、日志分析）\n"
    "你会根据用户需求自动选择合适的工具。\n"
    "如果你调用某个工具失败或未能解决用户问题，可以自动尝试其他相关工具，无需询问用户是否需要继续，但最多尝试5次，避免重复和死循环。如果所有工具都无法解决，请如实告知用户。"
)

# ====== exc_sql 工具类实现（Oracle版） ======
@register_tool('exc_sql')
class ExcSQLTool(BaseTool):
    """
    :function: SQL查询工具，执行传入的SQL语句并返回结果。
    :param sql_input: SQL查询语句
    :return: 查询结果（最多10行，以markdown格式返回）
    """
    description = (
        '对于生成的SQL，进行SQL查询（Oracle数据库）。\n\n'
        '【表结构参考】\n'
        '电商销售订单表 ORDERS:\n'
        'ORDER_ID, ORDER_NO, USER_ID, ADDRESS_ID, TOTAL_AMOUNT, PAYMENT_AMOUNT, FREIGHT_AMOUNT, ORDER_STATUS, PAYMENT_TIME, DELIVERY_TIME, RECEIVE_TIME, CREATE_TIME\n'
        '货品表 ORDER_ITEMS:\n'
        'ITEM_ID, ORDER_ID, PRODUCT_ID, PRODUCT_NAME, PRODUCT_IMAGE, PRICE, QUANTITY, TOTAL_PRICE\n'
        '客户表 USERS:\n'
        'USER_ID, USERNAME, PASSWORD, EMAIL, PHONE, REGISTER_DATE, STATUS\n'
        '请根据上述表结构生成SQL。'
    )
    parameters = [{
        'name': 'sql_input',
        'type': 'string',
        'description': '生成的SQL语句',
        'required': True
    }]

    def call(self, params: str, **kwargs) -> str:
        """
        执行SQL查询并返回结果
        :param params: JSON格式的参数字符串，包含sql_input
        :return: 查询结果（最多10行，以markdown格式返回）
        """
        import json
        args = json.loads(params)
        sql_input = args['sql_input']
        engine = create_engine(oracle_connection_string)
        try:
            df = pd.read_sql(sql_input, engine)
            return df.head(10).to_markdown(index=False)
        except Exception as e:
            return f"SQL执行出错: {str(e)}"

# ====== 天气查询工具 ======
@register_tool('get_current_weather')
class GetCurrentWeatherTool(BaseTool):
    """
    :function: 查询指定城市的实时天气信息
    :param location: 城市名称
    :param adcode: 城市编码（可选）
    :return: 天气信息JSON
    """
    description = '查询指定城市的实时天气信息（高德API）'
    parameters = [
        {
            'name': 'location',
            'type': 'string',
            'description': '城市名称，如 北京',
            'required': True
        },
        {
            'name': 'adcode',
            'type': 'string',
            'description': '城市编码，如 110000（可选）',
            'required': False
        }
    ]

    def call(self, params: str, **kwargs) -> str:
        """
        :function: 查询指定城市的实时天气信息
        :param params: JSON格式参数，包含location和可选adcode
        :return: 天气信息JSON
        """
        import json
        args = json.loads(params)
        location = args.get('location')
        adcode = args.get('adcode')
        gaode_api_key = "96e6841038817fab25821697f44d15c8"
        base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        req_params = {
            "key": gaode_api_key,
            "city": adcode if adcode else location,
            "extensions": "base",
        }
        response = requests.get(base_url, params=req_params)
        if response.status_code == 200:
            return response.text
        else:
            return f"天气查询失败: {response.status_code}"

# ====== IP地理位置查询工具 ======
@register_tool('get_ip_location')
class GetIPLocationTool(BaseTool):
    """
    :function: 查询IP地址的地理位置
    :param ip: IP地址
    :return: 地理位置信息JSON
    """
    description = '查询IP地址的地理位置（高德API）'
    parameters = [
        {
            'name': 'ip',
            'type': 'string',
            'description': '要查询的IP地址，如 114.247.50.2',
            'required': True
        }
    ]

    def call(self, params: str, **kwargs) -> str:
        """
        :function: 查询IP地址的地理位置
        :param params: JSON格式参数，包含ip
        :return: 地理位置信息JSON
        """
        import json
        args = json.loads(params)
        ip = args.get('ip')
        gaode_api_key = "96e6841038817fab25821697f44d15c8"
        base_url = "https://restapi.amap.com/v3/ip"
        req_params = {
            "key": gaode_api_key,
            "ip": ip,
        }
        response = requests.get(base_url, params=req_params)
        if response.status_code == 200:
            return response.text
        else:
            return f"IP地理位置查询失败: {response.status_code}"

# ====== 网络诊断工具 ======
@register_tool('ping_check')
class PingTool(BaseTool):
    """
    :function: 检查从本机到指定主机名或IP的网络连通性
    :param target: 目标主机名或IP
    :return: 连通性结果及延迟
    """
    description = '检查从本机到指定主机名或IP的网络连通性（ping）'
    parameters = [
        {
            'name': 'target',
            'type': 'string',
            'description': '目标主机名或IP',
            'required': True
        }
    ]

    def call(self, params: str, **kwargs) -> str:
        import json
        args = json.loads(params)
        target = args.get('target')
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '4', target]
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                delay_match = re.search(r'平均 = (\d+)ms', result.stdout)
                delay = delay_match.group(1) if delay_match else "未知"
                return f"连接成功，平均延迟: {delay}ms"
            else:
                return "连接失败，目标主机不可达"
        except Exception as e:
            return f"执行ping命令时出错: {str(e)}"

@register_tool('dns_resolve')
class DNSTool(BaseTool):
    """
    :function: 将主机名解析为IP地址
    :param hostname: 主机名
    :return: IP地址
    """
    description = '将主机名解析为IP地址（DNS）'
    parameters = [
        {
            'name': 'hostname',
            'type': 'string',
            'description': '主机名',
            'required': True
        }
    ]

    def call(self, params: str, **kwargs) -> str:
        import json
        args = json.loads(params)
        hostname = args.get('hostname')
        try:
            ip_address = socket.gethostbyname(hostname)
            return f"主机名 {hostname} 解析为IP地址: {ip_address}"
        except socket.gaierror:
            return f"无法解析主机名 {hostname}，DNS解析失败"
        except Exception as e:
            return f"DNS解析过程中出错: {str(e)}"

@register_tool('interface_check')
class InterfaceCheckTool(BaseTool):
    """
    :function: 检查本地网络接口的状态
    :param interface_name: 接口名（可选）
    :return: 接口状态信息
    """
    description = '检查本地网络接口的状态'
    parameters = [
        {
            'name': 'interface_name',
            'type': 'string',
            'description': '接口名（可选）',
            'required': False
        }
    ]

    def call(self, params: str, **kwargs) -> str:
        import json
        args = json.loads(params)
        interface_name = args.get('interface_name')
        if platform.system().lower() == 'windows':
            command = ['ipconfig', '/all']
        else:
            command = ['ifconfig']
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                if interface_name:
                    # 修正正则表达式，避免无效转义警告，使用$匹配字符串结尾
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

@register_tool('log_analysis')
class LogAnalysisTool(BaseTool):
    """
    :function: 在系统或应用日志中搜索网络相关问题
    :param keyword: 关键词
    :param time_range: 时间范围（可选）
    :return: 匹配的日志条目
    """
    description = '在系统或应用日志中搜索网络相关问题'
    parameters = [
        {
            'name': 'keyword',
            'type': 'string',
            'description': '关键词',
            'required': True
        },
        {
            'name': 'time_range',
            'type': 'string',
            'description': '时间范围（可选）',
            'required': False
        }
    ]

    def call(self, params: str, **kwargs) -> str:
        import json
        args = json.loads(params)
        keyword = args.get('keyword')
        # time_range = args.get('time_range')  # 可扩展
        log_entries = [
            "2024-03-20 10:15:23 [ERROR] Connection timeout to server",
            "2024-03-20 10:15:24 [INFO] Retrying connection...",
            "2024-03-20 10:15:25 [ERROR] DNS resolution failed",
            "2024-03-20 10:15:26 [WARNING] High latency detected"
        ]
        matching_entries = [entry for entry in log_entries if keyword.lower() in entry.lower()]
        if matching_entries:
            return "找到匹配的日志条目:\n" + "\n".join(matching_entries)
        else:
            return f"未找到包含关键词 '{keyword}' 的日志条目"

def get_system_message(user_query: str):
    return system_prompt_base

def init_agent_service(system_message):
    """
    初始化多工具智能助手服务
    :param system_message: 系统提示词
    :return: Assistant实例
    """
    llm_cfg = {
        'model': 'qwen-turbo-2025-04-28',
        'timeout': 30,
        'retry_count': 3,
    }
    tools = ['exc_sql', 'get_current_weather', 'get_ip_location', 'ping_check', 'dns_resolve', 'interface_check', 'log_analysis',
             {
            "mcpServers": {
                "amap-maps": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@amap/amap-maps-mcp-server"
                    ],
                    "env": {
                        "AMAP_MAPS_API_KEY": "96e6841038817fab25821697f44d15c8"
                    }
                },
                "fetch": {
                    "type": "sse",
                    "url": "https://mcp.api-inference.modelscope.cn/sse/729c49665d834c"
                },
                "bing-cn-mcp-server": {
                    "type": "sse",
                    "url": "https://mcp.api-inference.modelscope.cn/sse/2aba790abd024b"
                },
                "txt-counter-practice": {
                    "command": "python",
                    "args": ["txt_counter_practice.py"],
                    "port": 6274
                }
        }
    }]

    try:
        bot = Assistant(
            llm=llm_cfg,
            name='多工具AI助手（含网络诊断+自动多工具尝试）',
            description='地图/网页/搜索/SQL/天气/IP/网络诊断等多功能智能助手，支持自动多工具尝试：遇到调用某个工具失败或未能解决用户问题时会自动尝试其他相关工具，无需询问用户是否继续，最多尝试5次，防止死循环。',
            system_message=system_message,
            function_list=tools,
        )
        print("助手初始化成功！")
        return bot
    except Exception as e:
        print(f"助手初始化失败: {str(e)}")
        raise

def app_gui():
    try:
        print("正在启动 Web 界面...")
        system_message = get_system_message("")
        bot = init_agent_service(system_message)
        chatbot_config = {
            'prompt.suggestions': [
                '将 https://k.sina.com.cn/article_7732457677_1cce3f0cd01901eeeq.html 网页转化为Markdown格式',
                '推荐陆家嘴附近的高档餐厅',
                '帮我搜索一下关于AI的最新新闻',
                '请用bing的MCP查询出三条苏州的徒步路线，然后用高德MCP 做一个苏州一日徒步的攻略',
                '帮我从多到小列出前5位购买最多的货物',
                '请帮我查询客户订单金额排名前5的订单信息，包括订单号，订的货物清单以及客户姓名',
                '北京现在天气怎么样？',
                '请查询114.247.50.2的IP地址所在城市及其天气情况？',
                '我无法访问 www.google.com，浏览器显示连接超时,请帮我查明原因',
                '请帮我分析日志中包含timeout的网络问题'
            ]
        }
        print("Web 界面准备就绪，正在启动服务...")
        WebUI(
            bot,
            chatbot_config=chatbot_config
        ).run()
    except Exception as e:
        print(f"启动 Web 界面失败: {str(e)}")
        print("请检查网络连接和 API Key 配置")

if __name__ == '__main__':
    app_gui()          # 图形界面模式（默认） 