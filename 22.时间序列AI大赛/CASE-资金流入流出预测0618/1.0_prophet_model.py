import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import os

# 创建输出目录
os.makedirs('1.0_prophet_output', exist_ok=True)

# 1. 读取特征工程输出
daily = pd.read_csv('1.0_feature_output/1.0_prophet_daily_features.csv', parse_dates=['ds'])
purchase_df = pd.read_csv('1.0_feature_output/1.0_prophet_purchase.csv', parse_dates=['ds'])
redeem_df = pd.read_csv('1.0_feature_output/1.0_prophet_redeem.csv', parse_dates=['ds'])
holidays = pd.read_csv('1.0_feature_output/1.0_prophet_holidays.csv', parse_dates=['ds'])

# 2. 训练区间选择（2014-03-01及以后）
train_start = pd.to_datetime('2014-03-01')
val_start = pd.to_datetime('2014-08-01')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')

# 训练集、验证集、预测区间
purchase_train = purchase_df[purchase_df['ds'] < val_start]
purchase_val = purchase_df[(purchase_df['ds'] >= val_start) & (purchase_df['ds'] < predict_start)]
purchase_pred_dates = pd.date_range(predict_start, predict_end)

redeem_train = redeem_df[redeem_df['ds'] < val_start]
redeem_val = redeem_df[(redeem_df['ds'] >= val_start) & (redeem_df['ds'] < predict_start)]
redeem_pred_dates = pd.date_range(predict_start, predict_end)

# 3. Prophet建模函数
def fit_predict_prophet(train_df, holidays, pred_dates, label):
    """
    :function: Prophet建模与预测
    :param train_df: 训练数据（ds, y）
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
        changepoint_prior_scale=0.2
    )
    # 添加月季节性
    m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    m.fit(train_df)
    # 生成未来区间DataFrame
    future = m.make_future_dataframe(periods=len(pred_dates), freq='D', include_history=False)
    # 合并假日特征
    forecast = m.predict(future)
    # 可视化趋势
    fig1 = m.plot(forecast)
    plt.title(f'Prophet {label} 预测趋势')
    plt.savefig(f'1.0_prophet_output/1.0_prophet_{label}_trend.png')
    plt.close()
    # 可视化分解
    fig2 = m.plot_components(forecast)
    plt.savefig(f'1.0_prophet_output/1.0_prophet_{label}_components.png')
    plt.close()
    # 返回预测值
    result = pd.DataFrame({'ds': pred_dates, label: forecast['yhat'].values})
    return result

# 4. 申购/赎回建模与预测
purchase_pred = fit_predict_prophet(purchase_train, holidays, purchase_pred_dates, 'purchase')
redeem_pred = fit_predict_prophet(redeem_train, holidays, redeem_pred_dates, 'redeem')

# 5. 合并预测结果，输出为竞赛格式
predict_df = pd.DataFrame({'report_date': purchase_pred['ds'].dt.strftime('%Y%m%d'),
                           'purchase': np.round(purchase_pred['purchase']).astype(int),
                           'redeem': np.round(redeem_pred['redeem']).astype(int)})
predict_df.to_csv('1.0_prophet_output/1.0_prophet_predict.csv', index=False, header=False, encoding='utf-8-sig')

# 6. 可视化历史与预测对比
plt.figure(figsize=(16,6))
plt.plot(purchase_df['ds'], purchase_df['y'], label='历史申购')
plt.plot(purchase_pred['ds'], purchase_pred['purchase'], label='预测申购')
plt.title('申购金额历史与预测对比')
plt.legend()
plt.savefig('1.0_prophet_output/1.0_prophet_purchase_compare.png')
plt.close()

plt.figure(figsize=(16,6))
plt.plot(redeem_df['ds'], redeem_df['y'], label='历史赎回')
plt.plot(redeem_pred['ds'], redeem_pred['redeem'], label='预测赎回')
plt.title('赎回金额历史与预测对比')
plt.legend()
plt.savefig('1.0_prophet_output/1.0_prophet_redeem_compare.png')
plt.close()

print('Prophet建模与预测已完成，结果保存在1.0_prophet_output目录。') 