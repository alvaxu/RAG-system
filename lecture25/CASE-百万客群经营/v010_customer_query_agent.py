'''
程序说明：
## 1. 本程序为v010版对公授信客户助手，基于Qwen_agent的Assistant，支持终端TUI和Web GUI两种模式。
## 2. 支持客户基础信息和行为资产数据的查询分析。
## 3. 支持多种可视化图表展示，包括柱状图、折线图、趋势图、饼图等。
## 4. 基于Oracle数据库，表结构包含customer_base和customer_behavior_assets两张表。
## 5. 所有生成的图片统一保存在v010_image_output子目录下。
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
import numpy as np
import io, time
import re
from datetime import datetime, timedelta
import matplotlib.font_manager as fm
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns

# ========== 常量定义 ==========
IMAGE_OUTPUT_DIR = 'v010_image_output'  # 图片输出目录名

# ========== 新增：动态插入当前系统时间到system_prompt ===========
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
system_time_prompt = f"当前系统时间为：{now_str}。请在推理和回答时参考此时间。"

matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
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

system_prompt = system_time_prompt + """
你是对公授信客户助手，可以查询和分析客户基础信息表(customer_base)和客户行为与资产表(customer_behavior_assets)的数据。

数据表结构如下：

1. 客户基础信息表(customer_base)：
CREATE TABLE customer_base (
    customer_id VARCHAR2(32) PRIMARY KEY,           -- 客户唯一标识
    name VARCHAR2(32) NOT NULL,                     -- 客户姓名
    age NUMBER(3),                                  -- 客户年龄
    gender VARCHAR2(4),                             -- 性别(男/女)
    occupation VARCHAR2(32),                        -- 职业
    occupation_type VARCHAR2(32),                   -- 职业类型
    monthly_income NUMBER(12,2),                    -- 月收入
    open_account_date DATE,                         -- 开户日期
    lifecycle_stage VARCHAR2(16),                   -- 生命周期阶段(新客户/成长客户/成熟客户/忠诚客户)
    marriage_status VARCHAR2(8),                    -- 婚姻状况(已婚/未婚)
    city_level VARCHAR2(16),                        -- 城市等级(一线城市/二线城市/三线城市/其他)
    branch_name VARCHAR2(64)                        -- 开户网点
);

2. 客户行为与资产表(customer_behavior_assets)：
CREATE TABLE customer_behavior_assets (
    id VARCHAR2(32) PRIMARY KEY,                    -- 记录唯一标识
    customer_id VARCHAR2(32) NOT NULL,              -- 客户唯一标识
    total_assets NUMBER(20,2),                      -- 总资产
    deposit_balance NUMBER(20,2),                   -- 存款余额
    financial_balance NUMBER(20,2),                 -- 理财余额
    fund_balance NUMBER(20,2),                      -- 基金余额
    insurance_balance NUMBER(20,2),                 -- 保险余额
    asset_level VARCHAR2(16),                       -- 资产等级(普通客户/中端客户/高端客户/私人银行)
    deposit_flag NUMBER(1),                         -- 存款标志(0:无存款产品,1:有存款产品)
    financial_flag NUMBER(1),                       -- 理财标志(0:无理财产品,1:有理财产品)
    fund_flag NUMBER(1),                            -- 基金标志(0:无基金产品,1:有基金产品)
    insurance_flag NUMBER(1),                       -- 保险标志(0:无保险产品,1:有保险产品)
    product_count NUMBER(4),                        -- 产品持有数
    financial_repurchase_count NUMBER(6),           -- 理财复购次数
    credit_card_monthly_expense NUMBER(12,2),       -- 信用卡月消费
    investment_monthly_count NUMBER(6),             -- 月投资次数
    app_login_count NUMBER(6),                      -- APP登录次数
    app_financial_view_time NUMBER(10,2),           -- APP理财页面浏览时长
    app_product_compare_count NUMBER(6),            -- APP产品对比次数
    last_app_login_time TIMESTAMP,                  -- 最近APP登录时间
    last_contact_time TIMESTAMP,                    -- 最近联系时间
    contact_result VARCHAR2(16),                    -- 联系结果(成功/未接通/NaN，NaN表示未联系)
    marketing_cool_period DATE,                     -- 营销冷却期
    stat_month VARCHAR2(7)                          -- 统计月份
);

特别重要要求：
1. 因为后台数据库为跑在centos操作系统上的oracle 23C，你可以根据用户的自然语言问题，自动生成兼容oracle的SQL并查询，返回表格结果。
2. 特别强调，生成的SQL必须兼容Oracle。
3. 请务必严格用数据库表结构中的字段名，不要编造不存在的字段名
4. 注意数据库中有两个表，在生成SQL查询时要区别不同的字段在不同表里，不要误用。
5. 注意Oracle数据库的SQL语句中，不能出现分号(;)，否则会报错。
6. 为了提高查询效率，请尽量使用索引字段。
7. 注意：DATE和TIMESTAMP类型字段查询时，建议用TRUNC()函数仅按日期部分比较，及用TO_DATE()函数转换日期字符串。
8. 如果用户问题中包含“最近”、“最近一个月”、“最近三个月”、“本月”、“本季度”、“本年”等时间范围，请用SYSDATE函数获取当前日期，并计算出对应的时间范围。

可视化要求：
1. 如果用户问题涉及统计分析、分布、占比等，应该生成合适的可视化图表：
   - 分布分析：柱状图、直方图
   - 趋势分析：折线图
   - 占比分析：饼图、环形图
   - 多维对比：并列柱状图、堆叠柱状图
   - 相关性分析：散点图
2. 生成SQL时要包含必要的字段以支持可视化。
3. 每当exc_sql工具返回markdown表格和图片时，必须原样输出工具返回的全部内容。

分析建议：
1. 对查询结果进行分析和总结，给出数据洞察。
2. 如果涉及客户价值评估，要综合考虑：
   - 资产规模(total_assets)
   - 产品持有情况(product_count及各类产品标志)
   - 交易活跃度(investment_monthly_count)
   - APP活跃度(app_login_count, app_financial_view_time)
3. 如果涉及营销建议，要考虑：
   - 生命周期阶段(lifecycle_stage)
   - 最近联系情况(last_contact_time, contact_result)
   - 营销冷却期(marketing_cool_period)
"""

@register_tool('exc_sql')
class ExcSQLTool(BaseTool):
    """
    SQL查询工具，执行传入的SQL语句并返回结果，支持自动可视化。
    """
    description = '执行SQL查询并自动生成合适的可视化图表'
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
            if df.empty:
                return "查询结果为空。"
            
            md = df.head(10).to_markdown(index=False)
            # 统计描述
            describe_md = df.describe().to_markdown()
            
            # 确保user_query是字符串类型
            user_query = str(kwargs.get('user_query', ''))
            plot_keywords = ['分布', '占比', '比例', '趋势', '对比', '分析', '可视化', 
                           '画图', '柱状图', '饼图', '折线图', '图']
            
            # 默认需要可视化的情况
            need_plot = True
            
            # WebUI场景下自动检测messages
            if 'messages' in kwargs:
                messages = kwargs['messages']
                if isinstance(messages, list):
                    for msg in reversed(messages):
                        if isinstance(msg, dict) and msg.get('role') == 'user':
                            content = str(msg.get('content', ''))
                            if any(kw in content.lower() for kw in plot_keywords):
                                need_plot = True
                                break
            
            if need_plot:
                # 创建图片保存目录
                image_output_path = os.path.join(os.path.dirname(__file__), IMAGE_OUTPUT_DIR)
                os.makedirs(image_output_path, exist_ok=True)
                
                # 生成图片文件名，包含查询类型和时间戳
                query_type = ''
                if '分布' in user_query or '统计' in user_query:
                    query_type = 'distribution'
                elif '占比' in user_query or '比例' in user_query:
                    query_type = 'proportion'
                elif '趋势' in user_query:
                    query_type = 'trend'
                elif '对比' in user_query:
                    query_type = 'comparison'
                else:
                    query_type = 'analysis'
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'{query_type}_{timestamp}.png'
                save_path = os.path.join(image_output_path, filename)
                
                # 根据数据特征和查询类型选择合适的图表类型
                plt.figure(figsize=(12, 6))
                
                # 1. 分布/计数分析
                if len(df.columns) == 2 and df[df.columns[1]].dtype in ['int64', 'float64']:
                    # 柱状图
                    plt.bar(df[df.columns[0]], df[df.columns[1]])
                    plt.xticks(rotation=45)
                    plt.title(f'{df.columns[1]}分布')
                    plt.xlabel(df.columns[0])
                    plt.ylabel(df.columns[1])
                
                # 2. 占比分析
                elif len(df.columns) == 2 and 'ratio' in df.columns[1].lower():
                    # 饼图
                    plt.pie(df[df.columns[1]], labels=df[df.columns[0]], autopct='%1.1f%%')
                    plt.title(f'{df.columns[0]}占比')
                
                # 3. 趋势分析
                elif 'date' in str(df.columns[0]).lower() or 'month' in str(df.columns[0]).lower():
                    # 折线图
                    for col in df.select_dtypes(include=[np.number]).columns:
                        if col != df.columns[0]:
                            plt.plot(df[df.columns[0]], df[col], marker='o', label=col)
                    plt.legend()
                    plt.xticks(rotation=45)
                    plt.title('趋势分析')
                
                # 4. 多维对比
                elif len(df.columns) > 2:
                    # 并列柱状图
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 1:
                        x = np.arange(len(df))
                        width = 0.8 / len(numeric_cols)
                        for i, col in enumerate(numeric_cols):
                            plt.bar(x + i * width, df[col], width, label=col)
                        plt.xticks(x + width * (len(numeric_cols)-1)/2, df[df.columns[0]], rotation=45)
                        plt.legend()
                        plt.title('多维对比分析')
                
                plt.tight_layout()
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                # 生成Markdown图片链接
                md_img_path = os.path.join(IMAGE_OUTPUT_DIR, filename)
                img_md = f'![分析图]({md_img_path})'
                
                # 生成分析总结
                summary = generate_analysis_summary(df)
                
                return f"{md}\n\n{img_md}\n\n### 统计描述\n{describe_md}\n\n### 分析总结\n{summary}"
            
            return md
            
        except Exception as e:
            return f"SQL执行或可视化出错: {str(e)}"

def generate_analysis_summary(df):
    """
    根据查询结果生成分析总结
    :param df: 查询结果DataFrame
    :return: 分析总结文本
    """
    summary = []
    
    # 1. 基础统计
    row_count = len(df)
    summary.append(f"共有{row_count}条记录。")
    
    # 2. 数值型字段分析
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].notna().any():
            avg = df[col].mean()
            max_val = df[col].max()
            min_val = df[col].min()
            summary.append(f"{col}的平均值为{avg:.2f}，最大值为{max_val:.2f}，最小值为{min_val:.2f}。")
    
    # 3. 分类字段分析
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].notna().any():
            value_counts = df[col].value_counts()
            top_value = value_counts.index[0]
            top_count = value_counts.iloc[0]
            summary.append(f"{col}中最常见的值是{top_value}，出现{top_count}次。")
    
    # 4. 时间相关分析
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    for col in date_cols:
        if df[col].notna().any():
            try:
                dates = pd.to_datetime(df[col])
                min_date = dates.min()
                max_date = dates.max()
                summary.append(f"{col}的时间跨度从{min_date.strftime('%Y-%m-%d')}到{max_date.strftime('%Y-%m-%d')}。")
            except:
                pass
    
    return "\n".join(summary)

def init_agent_service():
    """
    初始化对公授信客户助手服务
    :return: 配置好的助手实例
    """
    llm_cfg = {
        'model': 'qwen-turbo-2025-04-28',
        'timeout': 30,
        'retry_count': 3,
    }
    tools = ['exc_sql']
    try:
        bot = Assistant(
            llm=llm_cfg,
            name='对公授信客户助手',
            description='客户信息查询与分析',
            system_message=system_prompt,
            function_list=tools,
        )
        print("助手初始化成功！")
        return bot
    except Exception as e:
        print(f"助手初始化失败: {str(e)}")
        raise

def app_tui():
    """
    终端交互模式，支持连续对话和SQL查询
    """
    try:
        bot = init_agent_service()
        messages = []
        while True:
            try:
                query = input('请输入你的查询问题（或exit退出）：')
                if query.strip().lower() in ['exit', 'quit']:
                    print('感谢使用，再见！')
                    break
                if not query:
                    print('问题不能为空！')
                    continue
                messages.append({'role': 'user', 'content': query})
                print("正在处理您的请求...")
                response = None
                for resp in bot.run(messages, user_query=query):
                    response = resp
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

def app_gui():
    """
    图形界面模式，基于WebUI
    """
    try:
        print("正在启动 Web 界面...")
        bot = init_agent_service()
        chatbot_config = {
            'prompt.suggestions': [
                '我行目前有多少客户？总资产管理规模是多少？',
                '客户的平均资产是多少？高净值客户的占比如何？',
                '客户年龄分布情况如何？哪个年龄段客户最多？'
                '客户在不同城市等级（一线、二线、三线）的分布如何？',
                '不同职业客户的产品偏好有什么差异？',
                '客户的网银登录次数和网点访问次数分布情况如何？',
                '年龄与手机银行使用频率有何关联？',
                '多少客户在过去三个月内没有任何交易行为?',
                '统计不同网点的客户资产分布情况如何？',
                '分析客户流失风险较高的群体特征',
                '统计各类产品的客户持有率',
                '分析高净值客户的年龄和职业分布',
                '客户持有的四类产品（存款、理财、基金、保险）分布情况如何？',
                '不同客户等级（普通、潜力、临界、高净值）的资产占比及客户数量是多少？',
         
                
            ]
        }
                # '影响客户价值的最重要因素有哪些？',
                # '哪些产品组合的关联度最高？',
                # '根据历史数据，未来3个月的客户资产总规模预计会如何变化？'      
                # '查询本月需要重点营销的高价值客户',
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
    # mode = input("输入1或2：").strip()
    mode = '2'
    if mode == '1':
        app_tui()
    elif mode == '2':
        app_gui()
    else:
        print("无效输入，退出。") 