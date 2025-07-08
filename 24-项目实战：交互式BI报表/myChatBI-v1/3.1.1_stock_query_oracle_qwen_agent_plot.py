'''
程序说明：
## 1. 本程序为3.1.1版股票历史数据查询助手，基于Qwen_agent的Assistant，支持终端TUI和Web GUI两种模式。
## 2. 数据源为Oracle数据库中的stock_history_data表（由1.1.1_stock_data_oracle_sync.py生成）。
## 3. 支持自然语言查询，自动生成SQL并返回结果，含折线图可视化功能，含详细中文注释。
'''

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
from qwen_agent.tools.base import BaseTool, register_tool
import dashscope
import matplotlib
matplotlib.use('Agg')  # 后台绘图
import matplotlib.pyplot as plt
import mplfinance as mpf
import re
from datetime import datetime
import numpy as np
import io, time

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

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
注意：trade_date 字段为Oracle日期类型，查询时如需按日期筛选，建议首选用TRUNC(trade_date)仅按日期部分比较，及用TO_DATE('2024-06-01', 'YYYY-MM-DD') 格式。
每当 exc_sql 工具返回 markdown 表格和图片时，你必须原样输出工具返回的全部内容（包括图片 markdown），不要只总结表格，也不要省略图片。这样用户才能直接看到表格和图片。
如果用户问题只需要一个结果（如最高点、最低点、最新一条等），请只返回一行最有用的结果，不要返回多行表格。
如用户问题涉及多只股票对比、分组、对比、比较等，生成SQL的返回值中必须包含stock_name、trade_date字段，否则无法正确分组和可视化。
如用户问题涉及画图、走势、趋势、可视化等，生成SQL时的返回值中必须包含stock_name、trade_date字段，否则无法生成可视化图。你可以根据用户的自然语言问题，自动生成SQL并查询，返回表格结果。
如用户要求k线图，则生成SQL时必须包含stock_name、trade_date、open、high、low、close字段，否则无法生成K线图。你可以根据用户的自然语言问题，自动生成SQL并查询，返回表格结果。
"""

# ====== SQL查询工具类 ======
@register_tool('exc_sql')
class ExcSQLTool(BaseTool):
    """
    SQL查询工具，执行传入的SQL语句并返回结果，并自动进行K线图可视化。
    """
    description = '对于生成的SQL，进行SQL查询，并自动K线图可视化'
    parameters = [{
        'name': 'sql_input',
        'type': 'string',
        'description': '生成的SQL语句',
        'required': True
    }]

    def call(self, params: str, **kwargs) -> str:
        import json
        import matplotlib.pyplot as plt
        import numpy as np
        import io, os, time
        args = json.loads(params)
        sql_input = args['sql_input']
        engine = create_engine(oracle_connection_string)
        try:
            df = pd.read_sql(sql_input, engine)
            md = df.head(10).to_markdown(index=False)
            # 判断是否需要画图
            need_plot = False
            user_query = kwargs.get('user_query', '')
            plot_keywords = ['画图', '走势', '趋势', 'K线', '可视化', 'plot', 'line chart', 'k线', '折线', '图', '柱状']
            if user_query:
                for kw in plot_keywords:
                    if kw.lower() in user_query.lower():
                        need_plot = True
                        break
            # 自动创建目录
            save_dir = os.path.join(os.path.dirname(__file__), '3.1.1_kline_image_show')
            os.makedirs(save_dir, exist_ok=True)
            filename = f'stock_{int(time.time()*1000)}.png'
            save_path = os.path.join(save_dir, filename)
            img_md = ''
            if need_plot or len(df) > 1:
                # ======= 智能选择x轴和y轴 =======
                columns = df.columns
                # 1. 优先找trade_date/date做x轴
                if 'trade_date' in columns:
                    x_col = 'trade_date'
                elif 'date' in columns:
                    x_col = 'date'
                else:
                    # 非数值型字段做x轴
                    non_num_cols = [col for col in columns if not np.issubdtype(df[col].dtype, np.number)]
                    if non_num_cols:
                        x_col = non_num_cols[0]
                    else:
                        # 只有一列数值，无法画图
                        if len(columns) == 1 and np.issubdtype(df[columns[0]].dtype, np.number):
                            return f"{md}\n\n仅有一列数值，无法生成有效折线图，请补充日期或类别字段。"
                        else:
                            # 默认用第一列
                            x_col = columns[0]
                # y轴：所有数值型字段，且排除x轴
                y_cols = [col for col in df.select_dtypes(include=[np.number]).columns if col != x_col]
                if not y_cols:
                    return f"{md}\n\n无可用数值型字段用于画图。"
                # ======= 优化标题和legend，支持多股票 =======
                stock_name = ''
                if 'stock_name' in df.columns:
                    unique_names = df['stock_name'].unique()
                    if len(unique_names) == 1:
                        stock_name = unique_names[0]
                    else:
                        stock_name = '、'.join([str(x) for x in unique_names])
                ts_code = ''
                if 'ts_code' in df.columns:
                    unique_codes = df['ts_code'].unique()
                    if len(unique_codes) == 1:
                        ts_code = unique_codes[0]
                    else:
                        ts_code = '、'.join([str(x) for x in unique_codes])
                date_range = ''
                if 'trade_date' in df.columns:
                    try:
                        dates = pd.to_datetime(df['trade_date'])
                        date_range = f"{dates.min().strftime('%Y-%m-%d')}~{dates.max().strftime('%Y-%m-%d')}"
                    except Exception:
                        date_range = f"{df['trade_date'].iloc[0]}~{df['trade_date'].iloc[-1]}"
                # 构造标题
                title_prefix = ''
                if stock_name and ts_code:
                    title_prefix = f"{stock_name}({ts_code})"
                elif stock_name:
                    title_prefix = stock_name
                elif ts_code:
                    title_prefix = ts_code
                # 多股票对比，标题加"对比"
                if 'stock_name' in df.columns and len(df['stock_name'].unique()) > 1:
                    if len(y_cols) == 1:
                        y_label = y_cols[0]
                        title = f"{title_prefix}{date_range} {y_label}对比"
                    else:
                        title = f"{title_prefix}{date_range} 主要行情对比"
                else:
                    if len(y_cols) == 1:
                        y_label = y_cols[0]
                        title = f"{title_prefix}{date_range} {y_label}走势"
                    else:
                        title = f"{title_prefix}{date_range} 主要行情走势"
                plt.figure(figsize=(10, 6))
                # 多股票legend处理
                if 'stock_name' in df.columns and len(df['stock_name'].unique()) > 1:
                    for col in y_cols:
                        for name in df['stock_name'].unique():
                            sub_df = df[df['stock_name'] == name]
                            plt.plot(sub_df[x_col], sub_df[col], marker='o', label=f'{name}')
                else:
                    for col in y_cols:
                        plt.plot(df[x_col], df[col], marker='o', label=col)
                plt.legend(title='指标')
                plt.title(title)
                plt.xlabel(x_col)
                plt.ylabel('数值')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(save_path)
                plt.close()
                img_md = f'![折线图]({os.path.join('3.1.1_kline_image_show', filename)})'
                # ======= K线图可视化（暂时注释） =======
                # kline_fields = {'trade_date', 'open', 'high', 'low', 'close'}
                # if set(kline_fields).issubset(df.columns):
                #     # 这里是K线图绘制逻辑，暂时注释
                #     pass
                return f"{md}\n\n{img_md}"
            return md
        except Exception as e:
            return f"SQL执行或可视化出错: {str(e)}"

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
                    final_resp = response[-1]
                else:
                    final_resp = response
                print('助手:', final_resp.get('content', final_resp))
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
                '绘制2024年贵州茅台收盘价走势',                
                '绘制2024年贵州茅台k线图',
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