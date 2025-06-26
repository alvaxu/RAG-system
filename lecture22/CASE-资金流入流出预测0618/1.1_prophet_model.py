import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import os
import matplotlib

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']  # 任选其一，优先级从左到右
matplotlib.rcParams['axes.unicode_minus'] = False  # 正常显示负号

# 创建输出目录
os.makedirs('1.1_prophet_output', exist_ok=True)

# 1. 读取特征工程输出
daily = pd.read_csv('1.1_feature_output/1.1_prophet_daily_features.csv', parse_dates=['ds'])
purchase_df = pd.read_csv('1.1_feature_output/1.1_prophet_purchase.csv', parse_dates=['ds'])
redeem_df = pd.read_csv('1.1_feature_output/1.1_prophet_redeem.csv', parse_dates=['ds'])
holidays = pd.read_csv('1.1_feature_output/1.1_prophet_holidays.csv', parse_dates=['ds'])

# 2. 训练区间选择（2014-03-01及以后）
train_start = pd.to_datetime('2014-03-01')
val_start = pd.to_datetime('2014-08-01')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')

# 3. 需要用到的regressor特征
df_features = daily[['ds', 'is_holiday', 'is_workday_shift', 'is_before_holiday', 'is_after_holiday',
                     'mfd_daily_yield', 'mfd_7daily_yield', 'Interest_O_N']]

# 4. Prophet建模函数，支持regressor
def fit_predict_prophet(train_df, full_df, holidays, pred_dates, label):
    """
    :function: Prophet建模与预测，支持regressor
    :param train_df: 训练数据（ds, y）
    :param full_df: 包含所有regressor的DataFrame
    :param holidays: 假日特征DataFrame
    :param pred_dates: 预测区间日期序列
    :param label: 标签（purchase/redeem）
    :return: 预测结果DataFrame
    """
    m = Prophet(
        holidays=holidays,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='additive',
        changepoint_prior_scale=0.5
    )
    # 添加月季节性
    m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    # 添加regressor
    for reg in ['is_holiday', 'is_workday_shift', 'is_before_holiday', 'is_after_holiday',
                'mfd_daily_yield', 'mfd_7daily_yield', 'Interest_O_N']:
        m.add_regressor(reg)
    # 合并regressor到训练集
    train = train_df.merge(full_df, on='ds', how='left')
    m.fit(train)
    # 生成未来区间DataFrame
    future = pd.DataFrame({'ds': pred_dates})
    # 合并regressor到future
    future = future.merge(full_df, on='ds', how='left')
    # 彻底兜底，防止任何NaN
    future = future.fillna(0)
    # 检查是否还有NaN
    if future.isnull().any().any():
        print(f'警告：future数据仍有NaN！')
    forecast = m.predict(future)
    # 可视化趋势
    fig1 = m.plot(forecast)
    plt.title(f'Prophet {label} 预测趋势')
    plt.savefig(f'1.1_prophet_output/1.1_prophet_{label}_trend.png')
    plt.close()
    # 可视化分解
    fig2 = m.plot_components(forecast)
    plt.savefig(f'1.1_prophet_output/1.1_prophet_{label}_components.png')
    plt.close()
    # 返回预测值
    result = pd.DataFrame({'ds': pred_dates, label: forecast['yhat'].values})
    return result

# 5. 训练集、验证集、预测区间划分
purchase_train = purchase_df[purchase_df['ds'] < val_start]
purchase_pred_dates = pd.date_range(predict_start, predict_end)
redeem_train = redeem_df[redeem_df['ds'] < val_start]
redeem_pred_dates = pd.date_range(predict_start, predict_end)

# 6. 申购/赎回建模与预测
purchase_pred = fit_predict_prophet(purchase_train, df_features, holidays, purchase_pred_dates, 'purchase')
redeem_pred = fit_predict_prophet(redeem_train, df_features, holidays, redeem_pred_dates, 'redeem')

# 7. 合并预测结果，输出为竞赛格式
predict_df = pd.DataFrame({'report_date': purchase_pred['ds'].dt.strftime('%Y%m%d'),
                           'purchase': np.round(purchase_pred['purchase']).astype(int),
                           'redeem': np.round(redeem_pred['redeem']).astype(int)})
predict_df.to_csv('1.1_prophet_output/1.1_prophet_predict.csv', index=False, header=False, encoding='utf-8-sig')

# 8. 可视化历史与预测对比
plt.figure(figsize=(16,6))
plt.plot(purchase_df['ds'], purchase_df['y'], label='历史申购')
plt.plot(purchase_pred['ds'], purchase_pred['purchase'], label='预测申购')
plt.title('申购金额历史与预测对比')
plt.legend()
plt.savefig('1.1_prophet_output/1.1_prophet_purchase_compare.png')
plt.close()

plt.figure(figsize=(16,6))
plt.plot(redeem_df['ds'], redeem_df['y'], label='历史赎回')
plt.plot(redeem_pred['ds'], redeem_pred['redeem'], label='预测赎回')
plt.title('赎回金额历史与预测对比')
plt.legend()
plt.savefig('1.1_prophet_output/1.1_prophet_redeem_compare.png')
plt.close()

print('1.1 Prophet建模与预测已完成，结果保存在1.1_prophet_output目录。') 