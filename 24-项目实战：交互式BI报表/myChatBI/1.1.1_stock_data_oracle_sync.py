'''
程序说明：
## 1. 本程序用于同步贵州茅台、五粮液、国泰君安、中芯国际的历史价格数据（2020-01-01至今）到Oracle数据库。
## 2. 首次运行时自动建表，后续仅补全缺失数据，避免重复导入。表结构与tushare daily接口一致，增加stock_name字段。
## 3. 详细中文注释，便于理解和维护。
'''

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import cx_Oracle
import os

# tushare配置
TS_TOKEN = 'bef9363ee81f40ec250748ae9d8150773c92672fa3f010adf39cec28'
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

# 股票代码及名称映射
stocks = {
    '贵州茅台': '600519.SH',
    '五粮液': '000858.SZ',
    '国泰君安': '601211.SH',
    '中芯国际': '688981.SH',
    '全志科技': '300458.SZ',
    
}

start_date = '20200101'
end_date = datetime.now().strftime('%Y%m%d')

# Oracle数据库连接配置
ORACLE_DSN = cx_Oracle.makedsn('192.168.43.11', 1521, service_name='FREEPDB1')
ORACLE_USER = 'dbtest'
ORACLE_PWD = 'test'

# SQL建表文件路径
SQL_FILE = '1.1.0_oracle_create_stock_history_data_table.sql'

def get_oracle_conn():
    """
    :function: 获取Oracle数据库连接
    :return: cx_Oracle.Connection
    """
    return cx_Oracle.connect(user=ORACLE_USER, password=ORACLE_PWD, dsn=ORACLE_DSN)

def table_exists(conn, table_name):
    """
    :function: 判断表是否存在
    :param conn: Oracle连接
    :param table_name: 表名
    :return: bool
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM user_tables WHERE table_name = :tn
    """, tn=table_name.upper())
    exists = cursor.fetchone()[0] > 0
    cursor.close()
    return exists

def exec_sql_file(conn, sql_file):
    """
    :function: 执行SQL文件
    :param conn: Oracle连接
    :param sql_file: SQL文件路径
    :return: None
    """
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    # 按分号分割执行（注意处理PL/SQL块）
    stmts = [s.strip() for s in sql.split(';') if s.strip()]
    cursor = conn.cursor()
    for stmt in stmts:
        if stmt:
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f'执行SQL时出错: {e}\nSQL: {stmt}')
    cursor.close()
    conn.commit()

def get_latest_trade_date(conn, ts_code):
    """
    :function: 获取某股票已同步的最新交易日
    :param conn: Oracle连接
    :param ts_code: 股票代码
    :return: 最新日期字符串（yyyymmdd），若无数据返回None
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(trade_date) FROM stock_history_data WHERE ts_code = :ts_code
    """, ts_code=ts_code)
    result = cursor.fetchone()[0]
    cursor.close()
    if result:
        return result.strftime('%Y%m%d')
    return None

def get_stock_min_trade_date(ts_code):
    """
    :function: 获取tushare中某股票的最早交易日
    :param ts_code: 股票代码
    :return: 最早日期字符串（yyyymmdd），若无数据返回None
    """
    df = pro.daily(ts_code=ts_code, start_date='19900101', end_date=end_date)
    if df.empty:
        return None
    min_date = df['trade_date'].min()
    return pd.to_datetime(min_date).strftime('%Y%m%d')

def insert_stock_data(conn, stock_name, ts_code, df):
    """
    :function: 批量插入股票数据
    :param conn: Oracle连接
    :param stock_name: 股票名称
    :param ts_code: 股票代码
    :param df: pandas.DataFrame
    :return: None
    """
    if df.empty:
        return
    # 添加stock_name列
    df = df.copy()
    df['stock_name'] = stock_name
    # Oracle日期类型转换
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    # 按表字段顺序准备数据
    cols = ['stock_name', 'ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']
    data = [tuple(row) for row in df[cols].values]
    cursor = conn.cursor()
    sql = '''
        INSERT INTO stock_history_data
        (stock_name, ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount)
        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12)
    '''
    try:
        cursor.executemany(sql, data)
        conn.commit()
        print(f'{stock_name}（{ts_code}）成功插入{len(data)}条数据。')
    except Exception as e:
        print(f'插入{stock_name}（{ts_code}）数据时出错：{e}')
        conn.rollback()
    finally:
        cursor.close()

def main():
    conn = get_oracle_conn()
    try:
        # 1. 检查表是否存在
        if not table_exists(conn, 'stock_history_data'):
            print('表stock_history_data不存在，正在创建...')
            exec_sql_file(conn, SQL_FILE)
            print('表创建完成。')
            # 首次全量导入
            for name, code in stocks.items():
                print(f'首次导入{name}（{code}）数据...')
                min_date = get_stock_min_trade_date(code)
                if min_date is None:
                    print(f'{name}（{code}）tushare无数据，跳过。')
                    continue
                real_start = max(start_date, min_date)
                df = pro.daily(ts_code=code, start_date=real_start, end_date=end_date)
                insert_stock_data(conn, name, code, df)
        else:
            print('表已存在，检查数据是否最新...')
            for name, code in stocks.items():
                latest = get_latest_trade_date(conn, code)
                min_date = get_stock_min_trade_date(code)
                if min_date is None:
                    print(f'{name}（{code}）tushare无数据，跳过。')
                    continue
                real_start = max(start_date, min_date)
                if latest is None:
                    print(f'{name}（{code}）无历史数据，导入全部...')
                    df = pro.daily(ts_code=code, start_date=real_start, end_date=end_date)
                    insert_stock_data(conn, name, code, df)
                elif latest < end_date:
                    # 补全最新数据（latest+1天到end_date）
                    next_day = (datetime.strptime(latest, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
                    # 只补全tushare有数据的区间
                    if next_day > end_date:
                        print(f'{name}（{code}）数据已是最新，无需更新。')
                        continue
                    df = pro.daily(ts_code=code, start_date=next_day, end_date=end_date)
                    insert_stock_data(conn, name, code, df)
                else:
                    print(f'{name}（{code}）数据已是最新，无需更新。')
    finally:
        conn.close()

if __name__ == '__main__':
    main() 
