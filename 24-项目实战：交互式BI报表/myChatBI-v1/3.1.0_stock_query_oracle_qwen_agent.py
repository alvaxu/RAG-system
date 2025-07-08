'''
程序说明：
## 1. 本程序为3.1.0版股票历史数据查询助手，基于Qwen_agent的Assistant，支持终端TUI和Web GUI两种模式。
## 2. 数据源为Oracle数据库中的stock_history_data表（由1.1.1_stock_data_oracle_sync.py生成）。
## 3. 支持自然语言查询，自动生成SQL并返回结果，含详细中文注释。
'''

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
from qwen_agent.tools.base import BaseTool, register_tool
import dashscope

# Oracle数据库连接配置
DB_USER = 'dbtest'
DB_PASSWORD = 'test'
DB_HOST = '192.168.43.11:1521'
SERVICE_NAME = 'FREEPDB1'

oracle_connection_string = f"oracle+cx_oracle://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/?service_name={SERVICE_NAME}"

# 配置 DashScope（如有API Key）
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', '')
dashscope.timeout = 30

# ====== 股票表结构描述（system prompt） ======
system_prompt = """
你是股票历史行情查询助手，数据表stock_history_data结构如下：
CREATE TABLE stock_history_data (
    stock_name VARCHAR2(32) NOT NULL, -- 股票名称
    ts_code VARCHAR2(16) NOT NULL,    -- 股票代码
    trade_date DATE NOT NULL,         -- 交易日期，Oracle日期类型，格式为'YYYY-MM-DD HH24:MI:SS.FF3'，如'2020-01-02 00:00:00.000'
    open NUMBER(10, 3),              -- 开盘价
    high NUMBER(10, 3),              -- 最高价
    low NUMBER(10, 3),               -- 最低价
    close NUMBER(10, 3),             -- 收盘价
    pre_close NUMBER(10, 3),         -- 昨收价
    change NUMBER(10, 3),            -- 涨跌额
    pct_chg NUMBER(6, 3),            -- 涨跌幅(%)
    vol NUMBER(20),                  -- 成交量(手)
    amount NUMBER(20, 3)             -- 成交额(千元)
)
特别重要：因为后台数据库为跑在centos操作系统上的oracle 23C，你可以根据用户的自然语言问题，自动生成兼容oralce的SQL并查询，返回表格结果。
特别强调，生成的SQL必须兼容Oracle。
注意：trade_date 字段为Oracle日期类型，查询时如需按日期筛选，建议首选用TRUNC(trade_date)仅按日期部分比较，或用TO_DATE('2020-01-02 00:00:00.000', 'YYYY-MM-DD HH24:MI:SS.FF3')格式。
请只返回表格结果，不要对每一行数据做详细解释，除非用户特别要求。
如果用户问题只需要一个结果（如最高点、最低点、最新一条等），请只返回一行最有用的结果，不要返回多行表格。
你可以根据用户的自然语言问题，自动生成SQL并查询，返回表格结果。
"""

# ====== SQL查询工具类 ======
@register_tool('exc_sql')
class ExcSQLTool(BaseTool):
    """
    SQL查询工具，执行传入的SQL语句并返回结果。
    :param sql_input: SQL查询语句
    :return: 查询结果（最多10行，以markdown表格返回）
    """
    description = '对于生成的SQL，进行SQL查询'
    parameters = [{
        'name': 'sql_input',
        'type': 'string',
        'description': '生成的SQL语句',
        'required': True
    }]

    def call(self, params: str, **kwargs) -> str:
        import json
        args = json.loads(params)
        sql_input = args['sql_input']
        # 创建数据库连接
        engine = create_engine(oracle_connection_string)
        try:
            df = pd.read_sql(sql_input, engine)
            if len(df) > 10:
                md = pd.concat([df.head(5), df.tail(5)]).to_markdown(index=False)
            else:
                md = df.to_markdown(index=False)
            # 只返回表格
            return md

        except Exception as e:
            return f"SQL执行出错: {str(e)}"

# ====== 初始化助手 ======
def init_agent_service():
    """
    初始化股票查询助手服务
    :return: 配置好的助手实例
    """
    llm_cfg = {
        'model': 'qwen-turbo-2025-04-28',
        'timeout': 30,
        'retry_count': 3,
    }
    try:
        bot = Assistant(
            llm=llm_cfg,
            name='股票历史查询助手',
            description='股票行情查询与分析',
            system_message=system_prompt,
            function_list=['exc_sql'],
        )
        print("助手初始化成功！")
        return bot
    except Exception as e:
        print(f"助手初始化失败: {str(e)}")
        raise

# ====== 终端TUI模式 ======
def app_tui():
    """
    终端交互模式，支持连续对话和SQL查询
    """
    try:
        bot = init_agent_service()
        messages = []
        while True:
            try:
                query = input('请输入你的股票查询问题（或exit退出）：')
                if query.strip().lower() in ['exit', 'quit']:
                    print('感谢使用，再见！')
                    break
                if not query:
                    print('问题不能为空！')
                    continue
                messages.append({'role': 'user', 'content': query})
                print("正在处理您的请求...")
                response = None
                for resp in bot.run(messages):
                    response = resp  # 只保留最后一次
                # 只输出最终回复
                if isinstance(response, list):
                    # 取最后一个有效回复
                    final_resp = response[-1]
                else:
                    final_resp = response
                print('助手:', final_resp.get('content', final_resp))
                # 只保存最终回复到对话历史
                messages.append({'role': 'assistant', 'content': final_resp.get('content', final_resp)})
            except Exception as e:
                print(f"处理请求时出错: {str(e)}")
                print("请重试或输入新的问题")
    except Exception as e:
        print(f"启动终端模式失败: {str(e)}")

# ====== Web GUI模式 ======
def app_gui():
    """
    图形界面模式，基于WebUI
    """
    try:
        print("正在启动 Web 界面...")
        bot = init_agent_service()
        chatbot_config = {
            'prompt.suggestions': [
                '查询2024年全年贵州茅台的收盘价走势',
                '五粮液近30天的最高价和最低价',
                '国泰君安2022年全年涨跌幅',
                '统计2024年4月国泰君安的日均成交量',
                '对比2024年中芯国际和贵州茅台的涨跌幅',
               
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
    print("请选择运行模式：1-终端TUI  2-Web GUI")
    mode = input("输入1或2：").strip()
    if mode == '1':
        app_tui()
    elif mode == '2':
        app_gui()
    else:
        print("无效输入，退出。") 