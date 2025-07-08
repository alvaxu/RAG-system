'''
直接预测，用历史数据直接预测未来30天（9月），不依赖8月的真实或预测值。
成绩：38.1575
'''
import pandas as pd
import numpy as np
import os
import matplotlib
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('2.0_sarima_output', exist_ok=True)

# 1. 读取特征工程输出
purchase_df = pd.read_csv('2.0_feature_output/2.0_sarima_purchase.csv', parse_dates=['ds'])
redeem_df = pd.read_csv('2.0_feature_output/2.0_sarima_redeem.csv', parse_dates=['ds'])

# 2. 训练区间与预测区间
date_split = pd.to_datetime('2014-08-01')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')
predict_dates = pd.date_range(predict_start, predict_end)

# 3. SARIMA建模与预测函数
def fit_predict_sarima(train_series, predict_steps, order=(5,1,1), seasonal_order=(1,0,2,7)):
# def fit_predict_sarima(train_series, predict_steps, order=(1,1,1), seasonal_order=(1,1,1,7)):
    """
    :function: SARIMA建模与预测
    :param train_series: 训练序列（pd.Series，index为日期）
    :param predict_steps: 预测步数
    :param order: SARIMA参数
    :param seasonal_order: SARIMA季节性参数
    :return: 预测值数组
    """
    model = SARIMAX(train_series, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
    results = model.fit(disp=False)
    forecast = results.forecast(steps=predict_steps)
    return forecast

# 4. 申购建模与预测
purchase_train = purchase_df[purchase_df['ds'] < date_split].set_index('ds')['y']
purchase_train.index = pd.DatetimeIndex(purchase_train.index, freq='D')
purchase_pred = fit_predict_sarima(purchase_train, len(predict_dates))

# 5. 赎回建模与预测
redeem_train = redeem_df[redeem_df['ds'] < date_split].set_index('ds')['y']
redeem_train.index = pd.DatetimeIndex(redeem_train.index, freq='D')
redeem_pred = fit_predict_sarima(redeem_train, len(predict_dates))

# 6. 合并预测结果，输出为竞赛格式
predict_df = pd.DataFrame({'report_date': predict_dates.strftime('%Y%m%d'),
                           'purchase': np.round(purchase_pred).astype(int),
                           'redeem': np.round(redeem_pred).astype(int)})
predict_df.to_csv('2.0_sarima_output/2.0_sarima_predict.csv', index=False, header=False, encoding='utf-8-sig')

# 7. 可视化历史与预测对比
plt.figure(figsize=(16,6))
plt.plot(purchase_df['ds'], purchase_df['y'], label='历史申购')
plt.plot(predict_dates, purchase_pred, label='预测申购')
plt.title('申购金额历史与预测对比（SARIMA）')
plt.legend()
plt.savefig('2.0_sarima_output/2.0_sarima_purchase_compare.png')
plt.close()

plt.figure(figsize=(16,6))
plt.plot(redeem_df['ds'], redeem_df['y'], label='历史赎回')
plt.plot(predict_dates, redeem_pred, label='预测赎回')
plt.title('赎回金额历史与预测对比（SARIMA）')
plt.legend()
plt.savefig('2.0_sarima_output/2.0_sarima_redeem_compare.png')
plt.close()

print('2.0 SARIMA建模与预测已完成，结果保存在2.0_sarima_output目录。') 