import pandas as pd
from statsmodels.tsa.stattools import adfuller
import pmdarima as pm
import time
import warnings

"""
:function: 自动为申购和赎回金额序列选择ARIMA最优(p,d,q)参数，并输出调参耗时和尝试次数
:param 无
:return: 控制台输出最优参数、耗时和尝试次数
"""
def auto_arima_param_select(csv_path='user_balance_table.csv'):
    # 屏蔽警告信息
    warnings.filterwarnings('ignore')
    # 读取数据
    try:
        df = pd.read_csv(csv_path, encoding='utf-8', usecols=['report_date', 'total_purchase_amt', 'total_redeem_amt'])
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='gbk', usecols=['report_date', 'total_purchase_amt', 'total_redeem_amt'])
    df['report_date'] = pd.to_datetime(df['report_date'], format='%Y%m%d')

    # 选取2014-03~2014-08区间数据
    start_date = pd.to_datetime('2014-03-01')
    end_date = pd.to_datetime('2014-08-31')
    df_range = df[(df['report_date'] >= start_date) & (df['report_date'] <= end_date)]
    grouped_range = df_range.groupby('report_date').sum().reset_index()

    for col, name in [('total_purchase_amt', '申购金额'), ('total_redeem_amt', '赎回金额')]:
        series = grouped_range[col]
        # 1. 先adfuller检验决定d
        d = 0
        adf_result = adfuller(series)
        if adf_result[1] > 0.05:
            # 非平稳，尝试一阶差分
            d = 1
            adf_result_diff = adfuller(series.diff().dropna())
            if adf_result_diff[1] > 0.05:
                d = 2
        # 2. auto_arima自动选p,q
        start_time = time.time()
        auto_model = pm.auto_arima(series, d=d, seasonal=False, stepwise=True, trace=False, suppress_warnings=True)
        end_time = time.time()
        n_trials = getattr(getattr(auto_model, "arima_res_", None), "nfit", '未知')
        print(f'【{name}】最优(p,d,q): {auto_model.order} | 耗时: {end_time - start_time:.2f}秒 | 参数尝试次数: {n_trials}')

if __name__ == "__main__":
    auto_arima_param_select() 