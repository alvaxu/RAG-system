'''
程序说明：
## 1. 本程序为股票历史数据查询助手，数据源为Oracle数据库中的stock_history_data表（由1.1.1_stock_data_oracle_sync.py生成）。
## 2. 支持SQL查询、简单分析，采用SQLAlchemy和pandas，参考oracle-bot-1 practice.py风格，含详细中文注释。
'''

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Oracle数据库连接配置
DB_USER = 'dbtest'
DB_PASSWORD = 'test'
DB_HOST = '192.168.43.11:1521'
SERVICE_NAME = 'FREEPDB1'

oracle_connection_string = f"oracle+cx_oracle://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/?service_name={SERVICE_NAME}"

# 通用SQL查询函数
def query_oracle(sql: str):
    """
    :function: 执行SQL并返回DataFrame
    :param sql: SQL语句
    :return: pandas.DataFrame
    """
    engine = create_engine(oracle_connection_string)
    try:
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        return df
    except SQLAlchemyError as e:
        print(f"SQL执行出错: {e}")
        return None

# 典型查询示例

def show_stock_list():
    """
    :function: 显示所有已同步的股票名称及代码
    :return: None
    """
    sql = "SELECT DISTINCT stock_name, ts_code FROM stock_history_data ORDER BY stock_name"
    df = query_oracle(sql)
    if df is not None:
        print(df.to_markdown(index=False))
    else:
        print("查询失败")

def show_latest_trade_date():
    """
    :function: 显示每只股票的最新交易日
    :return: None
    """
    sql = "SELECT stock_name, ts_code, MAX(trade_date) AS latest_date FROM stock_history_data GROUP BY stock_name, ts_code ORDER BY stock_name"
    df = query_oracle(sql)
    if df is not None:
        print(df.to_markdown(index=False))
    else:
        print("查询失败")

def query_stock_history(stock_name, start_date, end_date):
    """
    :function: 查询指定股票在指定区间的历史行情
    :param stock_name: 股票名称
    :param start_date: 开始日期（yyyy-mm-dd或yyyy/mm/dd或yyyyMMdd）
    :param end_date: 结束日期
    :return: None
    """
    # 日期格式兼容
    def fmt(d):
        d = str(d).replace('-', '').replace('/', '')
        return d[:8]
    start = fmt(start_date)
    end = fmt(end_date)
    sql = f"""
        SELECT * FROM stock_history_data
        WHERE stock_name = :stock_name
          AND trade_date >= TO_DATE(:start, 'YYYYMMDD')
          AND trade_date <= TO_DATE(:end, 'YYYYMMDD')
        ORDER BY trade_date
    """
    engine = create_engine(oracle_connection_string)
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params={"stock_name": stock_name, "start": start, "end": end})
        if df.empty:
            print(f"无数据：{stock_name} {start_date}~{end_date}")
        else:
            print(df.to_markdown(index=False))
    except SQLAlchemyError as e:
        print(f"SQL执行出错: {e}")

# 交互主程序
def main():
    print("欢迎使用2.1.0版股票历史数据查询助手！")
    print("数据源：Oracle数据库 stock_history_data 表\n")
    while True:
        print("\n可用操作：")
        print("1. 查看已同步股票列表")
        print("2. 查看每只股票的最新交易日")
        print("3. 查询某只股票历史行情")
        print("0. 退出")
        choice = input("请输入操作编号：").strip()
        if choice == '1':
            show_stock_list()
        elif choice == '2':
            show_latest_trade_date()
        elif choice == '3':
            stock_name = input("请输入股票名称：").strip()
            start_date = input("请输入开始日期(YYYYMMDD)：").strip()
            end_date = input("请输入结束日期(YYYYMMDD)：").strip()
            query_stock_history(stock_name, start_date, end_date)
        elif choice == '0':
            print("感谢使用，再见！")
            break
        else:
            print("无效输入，请重试。")

if __name__ == '__main__':
    main() 