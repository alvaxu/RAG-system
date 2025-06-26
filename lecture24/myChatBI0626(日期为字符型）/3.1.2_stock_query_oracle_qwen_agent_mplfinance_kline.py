'''
程序说明：
## 1. 本程序为3.1.2版股票历史数据查询助手，基于Qwen_agent的Assistant，支持终端TUI和Web GUI两种模式。
## 2. 在3.1.1基础上，增加了K线图绘制功能：只有用户明确要求K线图时，且SQL返回值包含stock_name、trade_date、open、high、low、close时，才自动绘制K线图。
## 3. 其余可视化（如走势、对比等）仍为折线图，标题和legend风格与3.1.1一致。
## 4. 输出图片目录仍为3.1.1_kline_image_show，兼容WebUI自动渲染。
'''

# ... 其余代码与3.1.1_stock_query_oracle_qwen_agent.py一致，以下为主要修改 ...

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
import numpy as np
import io, time
import re
from datetime import datetime
import matplotlib.font_manager as fm
import matplotlib.dates as mdates

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


# Oracle数据库连接配置
DB_USER = 'dbtest'
DB_PASSWORD = 'test'
DB_HOST = '192.168.43.11:1521'
SERVICE_NAME = 'FREEPDB1'

oracle_connection_string = f"oracle+cx_oracle://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/?service_name={SERVICE_NAME}"

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', '')
dashscope.timeout = 30

system_prompt = """
你是股票历史行情查询助手，数据表stock_data结构如下：
CREATE TABLE stock_data (
    stock_name VARCHAR2(32) NOT NULL, -- 股票名称
    ts_code VARCHAR2(16) NOT NULL,    -- 股票代码
    trade_date VARCHAR2(10) NOT NULL, -- 交易日期，格式为'YYYYMMDD'，如'20200102'
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
用户问题如与时间有关，比如提及年、月、最近、至今等，生成的SQL的返回值中都应包含stock_name、trade_date字段，比如'select stock_name, trade_date...'
每当 exc_sql 工具返回 markdown 表格和图片时，你必须原样输出工具返回的全部内容（包括图片 markdown），不要只总结表格，也不要省略图片。这样用户才能直接看到表格和图片。
如果用户问题只需要一个结果（如最高点、最低点、最新一条等），请只返回一行最有用的结果，不要返回多行表格。
如用户问题涉及多只股票对比、分组、对比、比较等，生成SQL的返回值中必须包含stock_name、trade_date字段，否则无法正确分组和可视化，比如 'select stock_name, trade_date...'
如用户问题涉及画图、走势、趋势、可视化等，生成SQL时的返回值中必须包含stock_name、trade_date字段，否则无法生成可视化图，比如 'select stock_name, trade_date...'
如用户要求K线图，SQL返回字段必须包含：stock_name、trade_date、open、high、low、close，且建议包含vol（成交量）字段。程序会自动将vol重命名为volume以兼容K线图成交量显示。如果没有vol字段，则K线图不显示成交量子图。
"""

@register_tool('exc_sql')
class ExcSQLTool(BaseTool):
    """
    SQL查询工具，执行传入的SQL语句并返回结果，并自动进行可视化（含K线图）。
    """
    description = '对于生成的SQL，进行SQL查询，并自动可视化（含K线图）'
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
        engine = create_engine(oracle_connection_string)
        try:
            df = pd.read_sql(sql_input, engine)
            md = df.head(10).to_markdown(index=False)
            # 判断是否需要画K线图
            user_query = kwargs.get('user_query', '')
            kline_keywords = ['k线', 'K线', 'k线图', 'K线图', 'candlestick', 'candle', '蜡烛图']
            need_kline = any(kw in user_query for kw in kline_keywords)
            # WebUI场景下自动检测messages
            if not need_kline and 'messages' in kwargs:
                for msg in reversed(kwargs['messages']):
                    if msg.get('role') == 'user' and any(kw in msg.get('content', '') for kw in kline_keywords):
                        need_kline = True
                        break
            # ===== 新增自动K线图判断 =====
            kline_fields = {'stock_name', 'trade_date', 'open', 'high', 'low', 'close'}
            if not need_kline and kline_fields.issubset(df.columns):
                # 只支持单股票K线
                if 'stock_name' in df.columns and len(df['stock_name'].unique()) == 1:
                    need_kline = True
            # 判断是否需要画普通折线图
            plot_keywords = ['画图', '走势', '趋势', '可视化', 'plot', 'line chart', '折线', '图', '柱状']
            need_plot = any(kw in user_query for kw in plot_keywords) or len(df) > 1
            # K线图输出目录
            kline_dir = os.path.join(os.path.dirname(__file__), '3.1.2_image_show')
            # 折线/对比图输出目录
            plot_dir = os.path.join(os.path.dirname(__file__), '3.1.2_image_show')
            # 生成图片文件名，包含股票名、日期区间、图类型、时间戳
            stock_name_part = safe_filename(df['stock_name'].iloc[0]) if 'stock_name' in df.columns else 'stock'
            date_range_part = f"{pd.to_datetime(df['trade_date'].iloc[0], format='%Y%m%d').strftime('%Y%m%d')}~{pd.to_datetime(df['trade_date'].iloc[-1], format='%Y%m%d').strftime('%Y%m%d')}" if 'trade_date' in df.columns else ''
            img_type = 'kline' if need_kline else 'line'
            filename = f'{stock_name_part}_{date_range_part}_{img_type}_{int(time.time()*1000)}.png'
            img_md = ''
            
            # print('need_kline:', need_kline)
            # print('df.columns:', df.columns)
            # ====== K线图绘制 ======
            # 字段重命名，兼容mplfinance，vol->volume
            if 'vol' in df.columns and 'volume' not in df.columns:
                df = df.rename(columns={'vol': 'volume'})
            if need_kline:
                os.makedirs(kline_dir, exist_ok=True)
                save_path = os.path.join(kline_dir, filename)
                if kline_fields.issubset(df.columns):
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
                            # trade_date为字符串，需指定format
                            dates = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                            date_range = f"{dates.min().strftime('%Y-%m-%d')}~{dates.max().strftime('%Y-%m-%d')}"
                        except Exception:
                            date_range = f"{df['trade_date'].iloc[0]}~{df['trade_date'].iloc[-1]}"
                    title_prefix = ''
                    if stock_name and ts_code:
                        title_prefix = f"{stock_name}({ts_code})"
                    elif stock_name:
                        title_prefix = stock_name
                    elif ts_code:
                        title_prefix = ts_code
                    title = f"{title_prefix}{date_range} K线图"
                    # 只支持单股票K线
                    if 'stock_name' in df.columns and len(df['stock_name'].unique()) > 1:
                        return f"{md}\n\nK线图仅支持单只股票，请缩小查询范围。"
                    # K线图排序和索引
                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                    df = df.sort_values('trade_date')
                    df.set_index('trade_date', inplace=True)
                    mc = mpf.make_marketcolors(up='r', down='g', edge='i', wick='i', volume='in')
                    s  = mpf.make_mpf_style(marketcolors=mc)
                    # 判断是否有volume字段，决定是否显示成交量子图
                    has_volume = 'volume' in df.columns
                    # 修正K线图中文乱码，手动设置所有文本为SimHei字体
                    font_path = fm.findfont('SimHei')  # 自动查找SimHei字体路径
                    font_prop = fm.FontProperties(fname=font_path)
                    fig, axes = mpf.plot(
                        df,
                        type='candle',
                        style=s,
                        title='',  # 不让mpf自动加title
                        ylabel='价格',
                        ylabel_lower='成交量' if has_volume else '',
                        volume=has_volume,
                        xrotation=15,
                        tight_layout=True,
                        returnfig=True
                    )
                    # 手动设置主图标题
                    axes[0].set_title(title, fontproperties=font_prop)
                    # 设置所有Axes的标题、坐标轴、刻度为SimHei字体
                    for ax in fig.axes:
                        for label in (ax.get_xticklabels() + ax.get_yticklabels()):
                            label.set_fontproperties(font_prop)
                        if ax.get_ylabel():
                            ax.set_ylabel(ax.get_ylabel(), fontproperties=font_prop)
                        if ax.get_xlabel():
                            ax.set_xlabel(ax.get_xlabel(), fontproperties=font_prop)
                    fig.savefig(save_path, dpi=120)
                    plt.close(fig)
                    md_img_path = os.path.join(os.path.basename(kline_dir), filename)
                    img_md = f'![K线图]({md_img_path})'
                    return f"{md}\n\n{img_md}"
                else:
                    return f"{md}\n\nK线图所需字段不全，请确保SQL返回stock_name、trade_date、open、high、low、close。"
            # ====== 普通折线图/对比图 ======
            if need_plot:
                os.makedirs(plot_dir, exist_ok=True)
                save_path = os.path.join(plot_dir, filename)
                columns = df.columns
                # 1. 优先找trade_date/date做x轴
                if 'trade_date' in columns:
                    x_col = 'trade_date'
                elif 'date' in columns:
                    x_col = 'date'
                else:
                    non_num_cols = [col for col in columns if not np.issubdtype(df[col].dtype, np.number)]
                    if non_num_cols:
                        x_col = non_num_cols[0]
                    else:
                        if len(columns) == 1 and np.issubdtype(df[columns[0]].dtype, np.number):
                            return f"{md}\n\n仅有一列数值，无法生成有效折线图，请补充日期或类别字段。"
                        else:
                            x_col = columns[0]
                y_cols = [col for col in df.select_dtypes(include=[np.number]).columns if col != x_col]
                if not y_cols:
                    return f"{md}\n\n无可用数值型字段用于画图。"
                # ======= 标题和legend与3.1.1一致 =======
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
                        # trade_date为字符串，需指定format
                        dates = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                        date_range = f"{dates.min().strftime('%Y-%m-%d')}~{dates.max().strftime('%Y-%m-%d')}"
                    except Exception:
                        date_range = f"{df['trade_date'].iloc[0]}~{df['trade_date'].iloc[-1]}"
                title_prefix = ''
                if stock_name and ts_code:
                    title_prefix = f"{stock_name}({ts_code})"
                elif stock_name:
                    title_prefix = stock_name
                elif ts_code:
                    title_prefix = ts_code
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
                if 'stock_name' in df.columns and len(df['stock_name'].unique()) > 1:
                    for col in y_cols:
                        for name in df['stock_name'].unique():
                            sub_df = df[df['stock_name'] == name]
                            # 确保x轴为datetime类型
                            if not np.issubdtype(sub_df[x_col].dtype, np.datetime64):
                                sub_df[x_col] = pd.to_datetime(sub_df[x_col], format='%Y%m%d')
                            plt.plot(sub_df[x_col], sub_df[col], marker='o', label=f'{name}')
                else:
                    for col in y_cols:
                        # 确保x轴为datetime类型
                        if not np.issubdtype(df[x_col].dtype, np.datetime64):
                            df[x_col] = pd.to_datetime(df[x_col], format='%Y%m%d')
                        plt.plot(df[x_col], df[col], marker='o', label=col)
                # ====== 自动疏密日期刻度 ======
                ax = plt.gca()
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.xticks(rotation=45)
                plt.legend(title='指标')
                plt.title(title)
                plt.xlabel(x_col)
                plt.ylabel('数值')
                plt.tight_layout()
                plt.savefig(save_path)
                plt.close()
                # 统一用plot_dir生成md图片路径（相对路径）
                md_img_path = os.path.join(os.path.basename(plot_dir), filename)
                img_md = f'![折线图]({md_img_path})'
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
                for resp in bot.run(messages, user_query=query):  # 传递user_query
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
                '对比2024年中芯国际和贵州茅台的涨跌幅',
            ]
        }
        print("Web 界面准备就绪，正在启动服务...")
        # WebUI会自动将用户输入作为user_query传递给工具（如未自动传递，可在WebUI源码中补充user_query参数）
        WebUI(
            bot,
            chatbot_config=chatbot_config
        ).run()
    except Exception as e:
        print(f"启动 Web 界面失败: {str(e)}")
        print("请检查网络连接和 API Key 配置")

# 生成图片文件名，包含股票名、日期区间、图类型、时间戳
def safe_filename(s):
    """
    :function: 将字符串转为安全的文件名，只保留中英文、数字，其他替换为下划线
    :param s: 原始字符串
    :return: 安全文件名字符串
    """
    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '_', str(s))

if __name__ == '__main__':
    print("请选择运行模式：1-终端TUI  2-Web GUI")
    mode = input("输入1或2：").strip()
    if mode == '1':
        app_tui()
    elif mode == '2':
        app_gui()
    else:
        print("无效输入，退出。")

