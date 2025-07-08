import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
import numpy as np

"""
:function: 统计所有人的申购和赎回金额，并按report_date进行趋势折线图展示
:param 无
:return: 无（直接展示图表）
"""
def plot_purchase_redeem_trend():
    # 读取全部数据，只读取需要的列
    try:
        df = pd.read_csv('user_balance_table.csv', encoding='utf-8', usecols=['report_date', 'total_purchase_amt', 'total_redeem_amt'])
    except UnicodeDecodeError:
        # 如果utf-8编码出错，尝试使用gbk编码
        df = pd.read_csv('user_balance_table.csv', encoding='gbk', usecols=['report_date', 'total_purchase_amt', 'total_redeem_amt'])

    # 将report_date转为日期格式，便于横坐标显示
    df['report_date'] = pd.to_datetime(df['report_date'], format='%Y%m%d')

    # 设置中文字体，防止图表中中文乱码
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # ====== 1. 全量数据趋势图 ======
    grouped_all = df.groupby('report_date').sum().reset_index()

    # 对申购金额和赎回金额进行adfuller平稳性检验（全量数据）
    print('【全量数据】申购金额 adfuller 检验:')
    result_purchase = adfuller(grouped_all['total_purchase_amt'])
    print(f'ADF Statistic: {result_purchase[0]}')
    print(f'p-value: {result_purchase[1]}')
    print('Critical Values:')
    for key, value in result_purchase[4].items():
        print(f'   {key}: {value}')
    print('-----------------------------')
    print('【全量数据】赎回金额 adfuller 检验:')
    result_redeem = adfuller(grouped_all['total_redeem_amt'])
    print(f'ADF Statistic: {result_redeem[0]}')
    print(f'p-value: {result_redeem[1]}')
    print('Critical Values:')
    for key, value in result_redeem[4].items():
        print(f'   {key}: {value}')
    print('=============================')

    plt.figure(figsize=(12, 6))
    plt.plot(grouped_all['report_date'], grouped_all['total_purchase_amt'], label='申购金额')
    plt.plot(grouped_all['report_date'], grouped_all['total_redeem_amt'], label='赎回金额')
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('金额', fontsize=12)
    plt.title('【全量】每日申购与赎回金额趋势', fontsize=14)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('all_data_trend.png')  # 保存全量数据趋势图
    plt.show()

    # ====== 2. 2014-03到2014-08区间趋势图及未来30天预测 ======
    start_date = pd.to_datetime('2014-03-01')
    end_date = pd.to_datetime('2014-08-31')
    df_range = df[(df['report_date'] >= start_date) & (df['report_date'] <= end_date)]
    grouped_range = df_range.groupby('report_date').sum().reset_index()
    
        # 对申购金额和赎回金额进行adfuller平稳性检验（区间数据）
    print('【2014-03~2014-08区间】申购金额 adfuller 检验:')
    result_purchase_range = adfuller(grouped_range['total_purchase_amt'])
    print(f'ADF Statistic: {result_purchase_range[0]}')
    print(f'p-value: {result_purchase_range[1]}')
    print('Critical Values:')
    for key, value in result_purchase_range[4].items():
        print(f'   {key}: {value}')
    print('-----------------------------')
    print('【2014-03~2014-08区间】赎回金额 adfuller 检验:')
    result_redeem_range = adfuller(grouped_range['total_redeem_amt'])
    print(f'ADF Statistic: {result_redeem_range[0]}')
    print(f'p-value: {result_redeem_range[1]}')
    print('Critical Values:')
    for key, value in result_redeem_range[4].items():
        print(f'   {key}: {value}')
    print('=============================')

    # ====== ARIMA预测2014-09申购和赎回金额（提前到画图前） ======
    purchase_series = grouped_range['total_purchase_amt']
    redeem_series = grouped_range['total_redeem_amt']
    last_date = grouped_range['report_date'].max()
    

    # 申购金额（平稳序列，d=0）
    model_purchase = ARIMA(purchase_series, order=(5,0,1))
    result_purchase = model_purchase.fit()
    forecast_purchase = result_purchase.forecast(steps=30)

    # 赎回金额（非平稳序列，d=1）
    model_redeem = ARIMA(redeem_series, order=(5,1,2))
    result_redeem = model_redeem.fit()
    forecast_redeem = result_redeem.forecast(steps=30)

    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=30, freq='D')
    forecast_df = pd.DataFrame({
        'report_date': future_dates.strftime('%Y%m%d'),
        'purchase': forecast_purchase,
        'redeem': forecast_redeem
    })
    forecast_df.to_csv('arima_forecast_201409.csv', index=False, encoding='utf-8', header=False)
    print('ARIMA预测结果已保存到 arima_forecast_201409.csv')



    # 画2014-03~2014-08及未来30天预测
    plt.figure(figsize=(16, 6))
    # 历史数据
    plt.plot(grouped_range['report_date'], grouped_range['total_purchase_amt'], label='申购金额-历史', color='C0')
    plt.plot(grouped_range['report_date'], grouped_range['total_redeem_amt'], label='赎回金额-历史', color='C1')
    # 预测数据
    forecast_df['report_date'] = pd.to_datetime(forecast_df['report_date'], format='%Y%m%d')
    plt.plot(forecast_df['report_date'], forecast_df['purchase'], label='申购金额-预测', color='C0', linestyle='--')
    plt.plot(forecast_df['report_date'], forecast_df['redeem'], label='赎回金额-预测', color='C1', linestyle='--')
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('金额', fontsize=12)
    plt.title('【2014-03~2014-08及未来30天】每日申购与赎回金额趋势', fontsize=14)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('range_201403_201408_trend.png')  # 保存区间趋势图
    plt.show()

if __name__ == "__main__":
    plot_purchase_redeem_trend() 