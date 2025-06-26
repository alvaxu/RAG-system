"""
:function: 使用SARIMAX模型结合外部变量（星期几和节假日）预测申购和赎回金额
:param csv_path: 用户余额表CSV文件路径
自动调参
SARIMAX最优参数：非季节性 (5, 1, 1), 季节性 (1, 0, 2, 7)
成绩：110.0372
"""
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np
from datetime import date
import warnings
import pmdarima as pm # 导入 pmdarima 库

warnings.filterwarnings("ignore")

"""
:function: 判断日期是否为法定节假日（2014年中国大陆主要节假日）或周末
:param date_obj: datetime.date 对象
:return: True 如果是节假日或周末，否则 False
"""
def is_special_day(date_obj):
    # 2014年法定节假日（包括调休，根据国家规定）
    holidays_2014 = [
        date(2014, 1, 1), # 元旦
        date(2014, 1, 31), date(2014, 2, 1), date(2014, 2, 2), date(2014, 2, 3), date(2014, 2, 4), date(2014, 2, 5), date(2014, 2, 6), # 春节
        date(2014, 4, 5), date(2014, 4, 6), date(2014, 4, 7), # 清明节
        date(2014, 5, 1), date(2014, 5, 2), date(2014, 5, 3), # 劳动节
        date(2014, 5, 31), date(2014, 6, 1), date(2014, 6, 2), # 六一儿童节 / 端午节 (2014年为同一假期范围)
        date(2014, 9, 6), date(2014, 9, 7), date(2014, 9, 8), # 中秋节
        date(2014, 10, 1), date(2014, 10, 2), date(2014, 10, 3), date(2014, 10, 4), date(2014, 10, 5), date(2014, 10, 6), date(2014, 10, 7) # 国庆节
    ]
    # 检查是否为周末
    if date_obj.weekday() in [5, 6]: # 5是周六，6是周日
        return True
    # 检查是否为法定节假日
    if date_obj in holidays_2014:
        return True
    return False

"""
:function: 使用pmdarima.auto_arima自动选择SARIMAX的最优参数
:param series: 时间序列数据 (pd.Series)
:param exog: 外部变量数据 (pd.DataFrame)
:param series_name: 序列名称，用于输出 (str)
:return: tuple (order, seasonal_order) 包含非季节性和季节性参数
"""
def auto_select_sarimax_params(series, exog, series_name):
    print(f"\n开始为【{series_name}】自动选择SARIMAX参数...")
    # 使用 auto_arima 自动选择参数，考虑外部变量和周季节性
    model_fit = pm.auto_arima(series, 
                              exogenous=exog, 
                              seasonal=True, 
                              m=7, # 周季节性，周期为7天
                              stepwise=True, 
                              trace=False, # 不输出详细的搜索过程
                              suppress_warnings=True, 
                              error_action='ignore')
    
    order = model_fit.order
    seasonal_order = model_fit.seasonal_order
    
    print(f"【{series_name}】SARIMAX最优参数：非季节性 {order}, 季节性 {seasonal_order}")
    return order, seasonal_order

"""
:function: 使用SARIMAX模型结合外部变量（星期几和节假日）预测申购和赎回金额
:param csv_path: 用户余额表CSV文件路径
:return: 无（直接展示图表和保存预测结果）
"""
def sarimax_forecast(csv_path='user_balance_table.csv'):
    # 1. 数据加载与预处理
    try:
        df = pd.read_csv(csv_path, encoding='utf-8', usecols=['report_date', 'total_purchase_amt', 'total_redeem_amt'])
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='gbk', usecols=['report_date', 'total_purchase_amt', 'total_redeem_amt'])
    
    df['report_date'] = pd.to_datetime(df['report_date'], format='%Y%m%d')
    df = df.set_index('report_date').sort_index()

    # 筛选2014-03到2014-08的历史数据
    start_date_hist = pd.to_datetime('2014-03-01')
    end_date_hist = pd.to_datetime('2014-08-31')
    df_hist = df[(df.index >= start_date_hist) & (df.index <= end_date_hist)].copy()
    
    # 按日期汇总
    grouped_hist = df_hist.groupby(df_hist.index).sum()

    # 生成历史数据的外部变量
    exog_hist = pd.DataFrame(index=grouped_hist.index)
    exog_hist['weekday'] = exog_hist.index.weekday # 0=周一, 6=周日
    exog_hist['is_holiday'] = exog_hist.index.map(is_special_day).astype(int)
    
    # 对weekday进行独热编码
    exog_hist = pd.get_dummies(exog_hist, columns=['weekday'], prefix='weekday')
    exog_hist = exog_hist.astype(int) # 确保所有外部变量为整数类型

    # 2. 预测未来日期及对应的外部变量
    last_hist_date = grouped_hist.index.max()
    future_dates = pd.date_range(start=last_hist_date + pd.Timedelta(days=1), periods=30, freq='D')
    
    exog_future = pd.DataFrame(index=future_dates)
    exog_future['weekday'] = exog_future.index.weekday
    exog_future['is_holiday'] = exog_future.index.map(is_special_day).astype(int)

    # 对未来数据的weekday进行独热编码，确保与历史数据列一致
    exog_future = pd.get_dummies(exog_future, columns=['weekday'], prefix='weekday')
    # 确保exog_future的列与exog_hist的列完全一致 (处理独热编码可能缺列的情况)
    for col in exog_hist.columns:
        if col not in exog_future.columns:
            exog_future[col] = 0
    exog_future = exog_future[exog_hist.columns] # 保持列序一致
    exog_future = exog_future.astype(int) # 确保所有外部变量为整数类型

    # 3. SARIMAX模型训练与预测
    predicted_purchase = []
    predicted_redeem = []

    # 申购金额预测
    print("开始训练申购金额SARIMAX模型...")
    # 自动选择申购金额的SARIMAX参数
    purchase_order, purchase_seasonal_order = auto_select_sarimax_params(
        grouped_hist['total_purchase_amt'], exog_hist, '申购金额')

    model_purchase = SARIMAX(grouped_hist['total_purchase_amt'], 
                             exog=exog_hist, 
                             order=purchase_order, 
                             seasonal_order=purchase_seasonal_order, 
                             enforce_stationarity=False, 
                             enforce_invertibility=False)
    results_purchase = model_purchase.fit(disp=False)
    forecast_purchase_result = results_purchase.get_forecast(steps=30, exog=exog_future)
    predicted_purchase = forecast_purchase_result.predicted_mean
    print("申购金额SARIMAX模型训练预测完成。")

    # 赎回金额预测
    print("开始训练赎回金额SARIMAX模型...")
    # 自动选择赎回金额的SARIMAX参数
    redeem_order, redeem_seasonal_order = auto_select_sarimax_params(
        grouped_hist['total_redeem_amt'], exog_hist, '赎回金额')

    model_redeem = SARIMAX(grouped_hist['total_redeem_amt'], 
                           exog=exog_hist, 
                           order=redeem_order, 
                           seasonal_order=redeem_seasonal_order, 
                           enforce_stationarity=False, 
                           enforce_invertibility=False)
    results_redeem = model_redeem.fit(disp=False)
    forecast_redeem_result = results_redeem.get_forecast(steps=30, exog=exog_future)
    predicted_redeem = forecast_redeem_result.predicted_mean
    print("赎回金额SARIMAX模型训练预测完成。")

    # 4. 结果整理与输出
    forecast_df = pd.DataFrame({
        'report_date': future_dates.strftime('%Y%m%d'),
        'purchase': predicted_purchase.values,
        'redeem': predicted_redeem.values
    })
    forecast_df.to_csv('3.auto_sarimax_forecast_201409.csv', index=False, encoding='utf-8', header=False)
    print('SARIMAX预测结果已保存到 3.auto_sarimax_forecast_201409.csv')

    # 5. 可视化
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(figsize=(16, 6))
    plt.plot(grouped_hist.index, grouped_hist['total_purchase_amt'], label='申购金额-历史', color='C0')
    plt.plot(grouped_hist.index, grouped_hist['total_redeem_amt'], label='赎回金额-历史', color='C1')
    
    # 预测数据
    plt.plot(future_dates, predicted_purchase, label='申购金额-预测', color='C0', linestyle='--')
    plt.plot(future_dates, predicted_redeem, label='赎回金额-预测', color='C1', linestyle='--')

    plt.xlabel('日期', fontsize=12)
    plt.ylabel('金额', fontsize=12)
    plt.title('【SARIMAX自动调参预测】2014-03~2014-08及未来30天每日申购与赎回金额趋势', fontsize=14)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('3.auto_sarimax_trend_201409.png')
    plt.show()

if __name__ == "__main__":
    sarimax_forecast() 