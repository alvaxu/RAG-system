"""本程序实现了基于Assistant的调用MCP的智能助手：
1. 高德AMAP-MCP - 提供地图服务查询、路线规划等功能
2. fetch MCP - 提供网络资源获取功能
3. Bing 查询及fetch的MCP - 提供搜索引擎查询功能
4. 本地定义的查询桌面txt文件
5. Oracle SQL数据库查询（仅在需要时动态注入表结构提示词）

主要功能：
- 通过自然语言进行地图服务查询
- 支持多种交互方式(GUI、TUI、测试模式)
- 支持旅游规划、地点查询、路线导航等功能
- 支持网络资源获取和搜索引擎查询
- 支持Oracle SQL数据库查询

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
import json

# Oracle数据库连接配置
# 请根据实际情况修改
ORACLE_USER = "dbtest"
ORACLE_PASSWORD = "test"
ORACLE_HOST = "192.168.43.11:1521"
ORACLE_SERVICE = "FREEPDB1"
oracle_connection_string = f"oracle+cx_oracle://{ORACLE_USER}:{ORACLE_PASSWORD}@{ORACLE_HOST}/?service_name={ORACLE_SERVICE}"

# 定义资源文件根目录
ROOT_RESOURCE = os.path.join(os.path.dirname(__file__), 'resource')

# 配置 DashScope
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', '')  # 从环境变量获取 API Key
dashscope.timeout = 30  # 设置超时时间为 30 秒

# ====== Oracle表结构提示词 ======
system_prompt_sql = """我是电商销售助手，以下是关于电商销售订单表orders,货品表order_items和客户表users的相关字段，我可能会编写对应的SQL，对数据进行查询
-- 电商销售订单表
CREATE TABLE "ORDERS" 
   (   "ORDER_ID" NUMBER, 
    "ORDER_NO" VARCHAR2(50) NOT NULL ENABLE, 
    "USER_ID" NUMBER NOT NULL ENABLE, 
    "ADDRESS_ID" NUMBER NOT NULL ENABLE, 
    "TOTAL_AMOUNT" NUMBER(10,2) NOT NULL ENABLE, 
    "PAYMENT_AMOUNT" NUMBER(10,2) NOT NULL ENABLE, 
    "FREIGHT_AMOUNT" NUMBER(10,2) DEFAULT 0, 
    "ORDER_STATUS" NUMBER(1,0) DEFAULT 0, 
    "PAYMENT_TIME" DATE, 
    "DELIVERY_TIME" DATE, 
    "RECEIVE_TIME" DATE, 
    "CREATE_TIME" DATE DEFAULT SYSDATE, 
     PRIMARY KEY ("ORDER_ID")
     )
     
--货品表
CREATE TABLE "ORDER_ITEMS" 
   (   "ITEM_ID" NUMBER, 
    "ORDER_ID" NUMBER NOT NULL ENABLE, 
    "PRODUCT_ID" NUMBER NOT NULL ENABLE, 
    "PRODUCT_NAME" VARCHAR2(100) NOT NULL ENABLE, 
    "PRODUCT_IMAGE" VARCHAR2(200), 
    "PRICE" NUMBER(10,2) NOT NULL ENABLE, 
    "QUANTITY" NUMBER NOT NULL ENABLE, 
    "TOTAL_PRICE" NUMBER(10,2) NOT NULL ENABLE, 
     PRIMARY KEY ("ITEM_ID")
  ）
  
--客户表
CREATE TABLE USERS" 
   (   "USER_ID" NUMBER, 
    "USERNAME" VARCHAR2(50) NOT NULL ENABLE, 
    "PASSWORD" VARCHAR2(100) NOT NULL ENABLE, 
    "EMAIL" VARCHAR2(100) NOT NULL ENABLE, 
    "PHONE" VARCHAR2(20), 
    "REGISTER_DATE" DATE DEFAULT SYSDATE, 
    "STATUS" NUMBER(1,0) DEFAULT 1, 
     PRIMARY KEY ("USER_ID")
)
"""

system_prompt_base = (
    "你扮演一个地图助手，你具有查询地图、规划路线、推荐景点、Oracle SQL数据库查询等能力。"
    "你可以帮助用户规划旅游行程，查找地点，导航，查询数据库等。"
    "你应该充分利用高德地图的各种功能和SQL工具来提供专业的建议。"
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
        
        参数：
        - params: JSON格式的参数字符串，包含sql_input和可选的database
        
        返回：
        - 查询结果（最多10行，以markdown格式返回）
        """
        import json
        args = json.loads(params)
        sql_input = args['sql_input']
        # 创建数据库连接
        engine = create_engine(oracle_connection_string)
        try:
            df = pd.read_sql(sql_input, engine)
            # 返回前10行，防止数据过多
            return df.head(10).to_markdown(index=False)
        except Exception as e:
            return f"SQL执行出错: {str(e)}"

def get_system_message(user_query: str):
    # 只返回通用助手描述
    return system_prompt_base

def init_agent_service(system_message):
    """初始化高德地图助手服务
    
    配置说明：
    - 使用 qwen-max 作为底层语言模型
    - 设置系统角色为地图助手
    - 配置高德地图 MCP 工具
    
    Returns:
        Assistant: 配置好的地图助手实例
    """
    # LLM 模型配置
    llm_cfg = {
        'model': 'qwen-turbo-2025-04-28',
        'timeout': 30,
        'retry_count': 3,
    }
    # MCP 工具配置
    mcp_config_path = os.path.join(os.path.dirname(__file__), 'mcp_config.json')
    with open(mcp_config_path, 'r', encoding='utf-8') as f:
        mcp_servers = json.load(f)
    tools = [{
        "mcpServers": mcp_servers
    }, 'exc_sql']

    try:
        # 创建助手实例
        bot = Assistant(
            llm=llm_cfg,
            name='AI助手',
            description='地图查询/网页获取/Bing搜索/Oracle SQL数据库查询',
            system_message=system_message,
            function_list=tools,
        )
        print("助手初始化成功！")
        return bot
    except Exception as e:
        print(f"助手初始化失败: {str(e)}")
        raise

def app_tui():
    try:
        bot = init_agent_service(get_system_message(""))
        messages = []
        while True:
            try:
                query = input('user question: ')
                file = input('file url (press enter if no file): ').strip()
                if not query:
                    print('user question cannot be empty！')
                    continue
                if not file:
                    messages.append({'role': 'user', 'content': query})
                else:
                    messages.append({'role': 'user', 'content': [{'text': query}, {'file': file}]})
                print("正在处理您的请求...")
                response = []
                for response in bot.run(messages):
                    print('bot response:', response)
                messages.extend(response)
            except Exception as e:
                print(f"处理请求时出错: {str(e)}")
                print("请重试或输入新的问题")
    except Exception as e:
        print(f"启动终端模式失败: {str(e)}")

def app_gui():
    try:
        print("正在启动 Web 界面...")
        # 默认用通用 system_message
        system_message = get_system_message("")
        bot = init_agent_service(system_message)
        chatbot_config = {
            'prompt.suggestions': [
                '将 https://k.sina.com.cn/article_7732457677_1cce3f0cd01901eeeq.html 网页转化为Markdown格式',
                '帮我找一下静安寺附近的停车场',
                '推荐陆家嘴附近的高档餐厅',
                '帮我搜索一下关于AI的最新新闻',
                '帮我查看订单金额排名',
                '帮我从多到小列出前5位购买最多的货物',
                '请帮我查询客户订单金额排名前5的订单信息，包括订单号，订的货物清单以及客户姓名',
                '请帮我查询客户订单金额排名前5的订单信息，包括订单号，订的货物清单以及客户姓名，请按订单为单位显示，一张订单有多个货物的，将货物名称罗列出来'
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