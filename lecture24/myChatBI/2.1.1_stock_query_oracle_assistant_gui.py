'''
程序说明：
## 1. 本程序为2.1.1版股票历史数据查询助手，基于2.1.0版，增加了streamlit图形界面。
## 2. 支持股票列表、最新交易日、区间行情查询，结果可表格和折线图展示。
## 3. 数据源为Oracle数据库中的stock_history_data表。
## 4. 运行在bash中，执行命令：streamlit run 2.1.1_stock_query_oracle_assistant_gui.py
'''

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import streamlit as st

# Oracle数据库连接配置
DB_USER = 'dbtest'
DB_PASSWORD = 'test'
DB_HOST = '192.168.43.11:1521'
SERVICE_NAME = 'FREEPDB1'

oracle_connection_string = f"oracle+cx_oracle://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/?service_name={SERVICE_NAME}"

# 通用SQL查询函数
def query_oracle(sql: str, params=None):
    """
    :function: 执行SQL并返回DataFrame
    :param sql: SQL语句
    :param params: 可选参数
    :return: pandas.DataFrame
    """
    engine = create_engine(oracle_connection_string)
    try:
        with engine.connect() as conn:
            if params:
                df = pd.read_sql(text(sql), conn, params=params)
            else:
                df = pd.read_sql(sql, conn)
        return df
    except SQLAlchemyError as e:
        st.error(f"SQL执行出错: {e}")
        return None

# Streamlit主界面
def main():
    st.set_page_config(page_title="股票历史数据查询助手", layout="wide")
    st.title("2.1.1版 股票历史数据查询助手（Oracle数据源）")
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["股票列表", "最新交易日", "区间行情查询"])

    with tab1:
        st.subheader("已同步股票列表")
        sql = "SELECT DISTINCT stock_name, ts_code FROM stock_history_data ORDER BY stock_name"
        df = query_oracle(sql)
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无数据")

    with tab2:
        st.subheader("每只股票的最新交易日")
        sql = "SELECT stock_name, ts_code, MAX(trade_date) AS latest_date FROM stock_history_data GROUP BY stock_name, ts_code ORDER BY stock_name"
        df = query_oracle(sql)
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无数据")

    with tab3:
        st.subheader("区间行情查询")
        # 获取股票列表
        sql = "SELECT DISTINCT stock_name FROM stock_history_data ORDER BY stock_name"
        df_names = query_oracle(sql)
        stock_list = df_names['stock_name'].tolist() if df_names is not None else []
        stock_name = st.selectbox("选择股票名称", stock_list)
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.text_input("开始日期(YYYYMMDD)", value="20200101")
        with col2:
            end_date = st.text_input("结束日期(YYYYMMDD)", value=pd.Timestamp.today().strftime('%Y%m%d'))
        if st.button("查询"):
            def fmt(d):
                d = str(d).replace('-', '').replace('/', '')
                return d[:8]
            start = fmt(start_date)
            end = fmt(end_date)
            sql = """
                SELECT * FROM stock_history_data
                WHERE stock_name = :stock_name
                  AND trade_date >= TO_DATE(:start, 'YYYYMMDD')
                  AND trade_date <= TO_DATE(:end, 'YYYYMMDD')
                ORDER BY trade_date
            """
            df = query_oracle(sql, params={"stock_name": stock_name, "start": start, "end": end})
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
                # 折线图展示收盘价
                st.line_chart(df.set_index('trade_date')['close'], use_container_width=True)
            else:
                st.warning(f"无数据：{stock_name} {start_date}~{end_date}")

if __name__ == '__main__':
    main() 