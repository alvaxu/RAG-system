"""
:function: 使用SARIMAX模型结合更丰富的外部变量预测申购和赎回金额，并进行残差分析
:param balance_csv_path: 用户余额表CSV文件路径
调用feature_engine.py中的load_and_engineer_features()函数生成特征
成绩：100.8430
"""


import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np
from datetime import date, timedelta
import warnings
import pmdarima as pm # 导入 pmdarima 库
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from feature_engine import load_and_engineer_features # 导入特征工程函数

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
:function: 使用SARIMAX模型结合更丰富的外部变量预测申购和赎回金额，并进行残差分析
:param balance_csv_path: 用户余额表CSV文件路径
:return: 无（直接展示图表和保存预测结果）
"""
def sarimax_forecast_with_features_and_residuals(balance_csv_path='user_balance_table.csv'):
    # 1. 加载并生成所有特征
    # 这里我们直接使用 feature_engine.py 中生成的特征数据框
    features_df = load_and_engineer_features()
    
    # 确保日期索引是完整的，并且排序
    features_df = features_df.sort_index()

    # 筛选2014-03到2014-08的历史数据
    start_date_hist = pd.to_datetime('2014-03-01')
    end_date_hist = pd.to_datetime('2014-08-31')
    
    df_hist = features_df[(features_df.index >= start_date_hist) & (features_df.index <= end_date_hist)].copy()
    
    # 定义自变量 (endog) 和外部变量 (exog)
    endog_purchase_hist = df_hist['total_purchase_amt']
    endog_redeem_hist = df_hist['total_redeem_amt']
    
    # 排除自身的滞后特征和目标变量，选择其他所有特征作为外部变量
    exog_columns = [col for col in df_hist.columns if col not in ['total_purchase_amt', 'total_redeem_amt'] and
                    not col.startswith('purchase_lag_') and not col.startswith('redeem_lag_')]
    exog_hist = df_hist[exog_columns]

    # 2. 预测未来日期及对应的外部变量
    last_hist_date = df_hist.index.max()
    future_dates = pd.date_range(start=last_hist_date + pd.Timedelta(days=1), periods=30, freq='D')
    
    # 创建未来外部变量数据框
    exog_future = pd.DataFrame(index=future_dates)
    
    # 填充未来日期特征
    exog_future['weekday'] = exog_future.index.weekday
    exog_future['dayofmonth'] = exog_future.index.day
    exog_future['month'] = exog_future.index.month
    exog_future['year'] = exog_future.index.year
    exog_future['dayofyear'] = exog_future.index.dayofyear
    exog_future['weekofyear'] = exog_future.index.isocalendar().week.astype(int)
    exog_future['is_holiday'] = exog_future.index.map(is_special_day).astype(int)

    # 对weekday进行独热编码，确保与历史数据列一致
    exog_future = pd.get_dummies(exog_future, columns=['weekday'], prefix='weekday')
    
    # 确保 exog_future 包含 exog_hist 的所有独热编码列，缺失的补0
    for col in [c for c in exog_hist.columns if c.startswith('weekday_')]:
        if col not in exog_future.columns:
            exog_future[col] = 0

    # 填充未来外部变量的滞后特征和非日期/非节假日特征
    # 对于这些外部变量，我们简单地使用历史数据的最后一个值进行填充。
    # 更复杂的预测场景需要对外部变量本身进行预测。
    for col in exog_columns:
        if col not in exog_future.columns: # 如果该列是日期/假日特征，则前面已生成
            if col.startswith('weekday_') or col == 'is_holiday' or col in ['dayofmonth', 'month', 'year', 'dayofyear', 'weekofyear']:
                continue
            # 对于其他外部变量（收益率、Shibor及其滞后），使用最后一个历史值填充
            exog_future[col] = df_hist[col].iloc[-1]
    
    # 保持列序一致
    exog_future = exog_future[exog_hist.columns]
    exog_future = exog_future.astype(float) # 确保所有外部变量为浮点类型

    # 3. SARIMAX模型训练与预测
    predicted_purchase = []
    predicted_redeem = []

    # 申购金额 SARIMAX 模型自动调参
    print("开始训练申购金额SARIMAX模型...")
    purchase_model_fit = pm.auto_arima(
        endog_purchase_hist,
        exogenous=exog_hist,
        start_p=0, start_q=0,
        max_p=5, max_q=5, # 扩大搜索范围
        d=0, # 强制非季节性差分阶数为0
        start_P=0, start_Q=0,
        max_P=2, max_Q=2, # 扩大季节性搜索范围
        max_D=1, # 允许季节性差分
        seasonal=True, m=7, # 周为季节周期
        error_action='ignore',
        suppress_warnings=True,
        stepwise=True, # 逐步搜索
        trace=True # 显示搜索过程
    )
    print(f"【申购金额】SARIMAX最优参数：非季节性 {purchase_model_fit.order}, 季节性 {purchase_model_fit.seasonal_order}")
    print("申购金额SARIMAX模型训练预测完成。")

    # 赎回金额 SARIMAX 模型自动调参
    print("开始训练赎回金额SARIMAX模型...")
    redeem_model_fit = pm.auto_arima(
        endog_redeem_hist,
        exogenous=exog_hist,
        start_p=0, start_q=0,
        max_p=5, max_q=5, # 扩大搜索范围
        d=1, # 强制非季节性差分阶数为1，解决赎回金额非平稳问题
        start_P=0, start_Q=0,
        max_P=2, max_Q=2, # 扩大季节性搜索范围
        max_D=1, # 允许季节性差分
        seasonal=True, m=7, # 周为季节周期
        error_action='ignore',
        suppress_warnings=True,
        stepwise=True, # 逐步搜索
        trace=True # 显示搜索过程
    )
    print(f"【赎回金额】SARIMAX最优参数：非季节性 {redeem_model_fit.order}, 季节性 {redeem_model_fit.seasonal_order}")
    print("赎回金额SARIMAX模型训练预测完成。")

    model_purchase = SARIMAX(endog_purchase_hist, 
                             exog=exog_hist, 
                             order=purchase_model_fit.order, 
                             seasonal_order=purchase_model_fit.seasonal_order, 
                             enforce_stationarity=False, 
                             enforce_invertibility=False)
    results_purchase = model_purchase.fit(disp=False)
    forecast_purchase_result = results_purchase.get_forecast(steps=30, exog=exog_future)
    predicted_purchase = forecast_purchase_result.predicted_mean

    model_redeem = SARIMAX(endog_redeem_hist, 
                           exog=exog_hist, 
                           order=redeem_model_fit.order, 
                           seasonal_order=redeem_model_fit.seasonal_order, 
                           enforce_stationarity=False, 
                           enforce_invertibility=False)
    results_redeem = model_redeem.fit(disp=False)
    forecast_redeem_result = results_redeem.get_forecast(steps=30, exog=exog_future)
    predicted_redeem = forecast_redeem_result.predicted_mean

    # 4. 残差分析
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 申购金额残差分析
    purchase_residuals = results_purchase.resid
    plt.figure(figsize=(18, 10))
    
    plt.subplot(2, 2, 1)
    plt.plot(purchase_residuals)
    plt.title('申购金额残差')
    plt.xlabel('日期')
    plt.ylabel('残差')

    plt.subplot(2, 2, 2)
    plot_acf(purchase_residuals, lags=40, ax=plt.gca(), title='申购金额残差ACF')
    
    plt.subplot(2, 2, 3)
    plot_pacf(purchase_residuals, lags=40, ax=plt.gca(), title='申购金额残差PACF')

    lb_test_purchase = acorr_ljungbox(purchase_residuals, lags=20, return_df=True)
    print("\n申购金额残差 Ljung-Box 检验结果:")
    print(lb_test_purchase)
    
    plt.tight_layout()
    plt.savefig('5.purchase_residuals_analysis.png') # 添加前缀
    # plt.show() # 不在代码中直接显示，由用户决定

    # 赎回金额残差分析
    redeem_residuals = results_redeem.resid
    plt.figure(figsize=(18, 10))

    plt.subplot(2, 2, 1)
    plt.plot(redeem_residuals)
    plt.title('赎回金额残差')
    plt.xlabel('日期')
    plt.ylabel('残差')

    plt.subplot(2, 2, 2)
    plot_acf(redeem_residuals, lags=40, ax=plt.gca(), title='赎回金额残差ACF')
    
    plt.subplot(2, 2, 3)
    plot_pacf(redeem_residuals, lags=40, ax=plt.gca(), title='赎回金额残差PACF')

    lb_test_redeem = acorr_ljungbox(redeem_residuals, lags=20, return_df=True)
    print("\n赎回金额残差 Ljung-Box 检验结果:")
    print(lb_test_redeem)

    plt.tight_layout()
    plt.savefig('5.redeem_residuals_analysis.png') # 添加前缀
    # plt.show() # 不在代码中直接显示，由用户决定

    # 5. 结果整理与输出
    forecast_df = pd.DataFrame({
        'report_date': future_dates.strftime('%Y%m%d'),
        'purchase': [int(round(p)) for p in predicted_purchase.tolist()], # 转换为列表，逐个 round 后转 int
        'redeem': [int(round(r)) for r in predicted_redeem.tolist()]    # 转换为列表，逐个 round 后转 int
    })
    forecast_df.to_csv('5.sarimax_forecast_advanced_tuning_201409.csv', index=False, encoding='utf-8', header=False)
    print('SARIMAX预测结果已保存到 5.sarimax_forecast_advanced_tuning_201409.csv')

    # 6. 可视化预测结果
    plt.figure(figsize=(16, 6))
    plt.plot(endog_purchase_hist.index, endog_purchase_hist, label='申购金额-历史', color='C0')
    plt.plot(endog_redeem_hist.index, endog_redeem_hist, label='赎回金额-历史', color='C1')
    
    # 预测数据
    plt.plot(future_dates, predicted_purchase, label='申购金额-预测', color='C0', linestyle='--')
    plt.plot(future_dates, predicted_redeem, label='赎回金额-预测', color='C1', linestyle='--')

    plt.xlabel('日期', fontsize=12)
    plt.ylabel('金额', fontsize=12)
    plt.title('【SARIMAX多特征高级调参预测】2014-03~2014-08及未来30天每日申购与赎回金额趋势', fontsize=14)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('5.sarimax_advanced_tuning_trend_201409.png')
    plt.show()

if __name__ == "__main__":
    sarimax_forecast_with_features_and_residuals() # 函数名保持不变，内部逻辑已更新 