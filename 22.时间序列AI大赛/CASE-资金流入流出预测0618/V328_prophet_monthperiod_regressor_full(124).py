'''
程序说明：
## 1. 本程序严格参考3.2.5_prophet_model(122).py流程，从原始数据出发，month_period（月内分段）作为回归特征参与Prophet建模。
## 2. 生成完整的预测区间（2014-03-01到2014-09-30），为每一天补齐month_period one-hot特征，保证9月有预测。
## 3. 所有输出文件和目录升级为3.2.8前缀，流程、注释、可视化等与3.2.5完全一致。
分数:124.0158 
'''

import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import chinese_calendar
import os
import matplotlib
import logging
import warnings
import seaborn as sns

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('3.2.8_prophet_output', exist_ok=True)
os.makedirs('3.2.8_feature_output', exist_ok=True)

# 屏蔽所有库的debug和info输出
for logger_name in ['prophet', 'cmdstanpy', 'matplotlib', 'pandas', 'numpy']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = False
plt.set_loglevel('error')

# 1. 读取原始数据
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 2. 聚合每日申购/赎回总额
daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# 3. 生成2014-03-01到2014-09-30的节假日和调休补班日
holiday_dates = pd.date_range('2014-03-01', '2014-09-30')
holiday_list = []
for d in holiday_dates:
    if chinese_calendar.is_holiday(d):
        holiday_list.append({'holiday': 'official_holiday', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    elif chinese_calendar.is_workday(d) and d.weekday() >= 5:
        holiday_list.append({'holiday': 'workday_shift', 'ds': d, 'lower_window': 0, 'upper_window': 0})
holiday_df = pd.DataFrame(holiday_list)
holiday_df.to_csv('3.2.8_feature_output/3.2.8_prophet_holidays.csv', index=False, encoding='utf-8-sig')

# 4. 特征工程优化
def month_period_func(day):
    d = day.day
    if d <= 10:
        return 'begin'
    elif d <= 20:
        return 'middle'
    else:
        return 'end'

daily['month_period'] = daily['ds'].apply(month_period_func)

# 保存原始特征文件
daily.to_csv('3.2.8_feature_output/3.2.8_prophet_daily_features.csv', index=False, encoding='utf-8-sig')

# 5. 训练区间、预测区间
train_start = pd.to_datetime('2014-03-01')
train_end = pd.to_datetime('2014-08-31')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')
all_dates = pd.date_range(train_start, predict_end)

# 6. 构造完整all_dates的month_period one-hot特征
def get_month_period_onehot(date):
    d = date.day
    return {
        'month_period_begin': int(d <= 10),
        'month_period_middle': int(10 < d <= 20),
        'month_period_end': int(d > 20)
    }
predict_df = pd.DataFrame({'ds': all_dates})
mp_onehot = predict_df['ds'].apply(get_month_period_onehot)
mp_df = pd.DataFrame(list(mp_onehot))
predict_df = pd.concat([predict_df, mp_df], axis=1)

# 7. 生成Prophet训练集（带回归特征）
purchase_train = daily[(daily['ds'] >= train_start) & (daily['ds'] <= train_end)][['ds','purchase','month_period']].copy()
redeem_train = daily[(daily['ds'] >= train_start) & (daily['ds'] <= train_end)][['ds','redeem','month_period']].copy()
# one-hot编码
purchase_train = pd.concat([purchase_train, pd.get_dummies(purchase_train['month_period'], prefix='month_period')], axis=1)
redeem_train = pd.concat([redeem_train, pd.get_dummies(redeem_train['month_period'], prefix='month_period')], axis=1)

# 8. 读取节假日
holidays = pd.read_csv('3.2.8_feature_output/3.2.8_prophet_holidays.csv', parse_dates=['ds'])

# 9. Prophet建模与预测（申购）
purchase_model = Prophet(
    holidays=holidays,
    yearly_seasonality=False,
    weekly_seasonality=True,
    daily_seasonality=False,
    changepoint_prior_scale=0.10,
    seasonality_prior_scale=10.0,
    holidays_prior_scale=5.0,
    seasonality_mode='additive', 
    changepoint_range= 0.8,
    n_changepoints= 25
)
for col in ['month_period_begin', 'month_period_middle', 'month_period_end']:
    purchase_model.add_regressor(col)
purchase_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
purchase_model.fit(purchase_train.rename(columns={'purchase':'y'}).drop(columns=['month_period']))
purchase_forecast = purchase_model.predict(predict_df[['ds','month_period_begin','month_period_middle','month_period_end']])

# 10. Prophet建模与预测（赎回）
redeem_model = Prophet(
    holidays=holidays,
    yearly_seasonality=False,
    weekly_seasonality=True,
    daily_seasonality=False,
    changepoint_prior_scale=0.05,
    seasonality_prior_scale=15.0,
    holidays_prior_scale=5.0,
    seasonality_mode='additive',
    changepoint_range= 0.8,
    n_changepoints= 20
)
for col in ['month_period_begin', 'month_period_middle', 'month_period_end']:
    redeem_model.add_regressor(col)
redeem_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
redeem_model.fit(redeem_train.rename(columns={'redeem':'y'}).drop(columns=['month_period']))
redeem_forecast = redeem_model.predict(predict_df[['ds','month_period_begin','month_period_middle','month_period_end']])

# 11. 可视化：3-8月真实值、in-sample预测，9月预测
plt.figure(figsize=(18,8))
# 申购
plt.plot(purchase_train['ds'], purchase_train['purchase'], label='申购真实值', color='blue')
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'],
         purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'],
         label='申购in-sample预测', color='blue', linestyle='--')
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'],
         purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat'],
         label='申购9月预测', color='blue', linestyle=':')
# 赎回
plt.plot(redeem_train['ds'], redeem_train['redeem'], label='赎回真实值', color='green')
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'],
         redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'],
         label='赎回in-sample预测', color='green', linestyle='--')
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['ds'],
         redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat'],
         label='赎回9月预测', color='green', linestyle=':')
plt.title('2014-03-01至2014-09-30申购/赎回真实值、in-sample预测与9月预测对比（含month_period回归特征）')
plt.legend()
plt.xlim([train_start, predict_end])
plt.savefig('3.2.8_prophet_output/3.2.8_prophet_purchase_redeem_compare.png')
plt.close()

# 12. 分解图
fig = purchase_model.plot_components(purchase_forecast)
plt.savefig('3.2.8_prophet_output/3.2.8_prophet_purchase_components.png')
plt.close()
fig = redeem_model.plot_components(redeem_forecast)
plt.savefig('3.2.8_prophet_output/3.2.8_prophet_redeem_components.png')
plt.close()

# 13. 残差分析
# 申购残差
real_purchase = purchase_train['purchase'].values
pred_purchase = purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'].values
residuals_purchase = real_purchase - pred_purchase
plt.figure(figsize=(12,4))
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'], residuals_purchase)
plt.title('申购残差分析（真实值-预测值）')
plt.axhline(0, color='red', linestyle='--')
plt.savefig('3.2.8_prophet_output/3.2.8_prophet_purchase_residuals.png')
plt.close()
# 赎回残差
real_redeem = redeem_train['redeem'].values
pred_redeem = redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'].values
residuals_redeem = real_redeem - pred_redeem
plt.figure(figsize=(12,4))
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'], residuals_redeem)
plt.title('赎回残差分析（真实值-预测值）')
plt.axhline(0, color='red', linestyle='--')
plt.savefig('3.2.8_prophet_output/3.2.8_prophet_redeem_residuals.png')
plt.close()

# 14. 输出9月预测结果为竞赛格式
predict_result = pd.DataFrame({
    'report_date': purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'].dt.strftime('%Y%m%d'),
    'purchase': np.round(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat']).astype(int),
    'redeem': np.round(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat']).astype(int)
})
predict_result.to_csv('3.2.8_prophet_output/3.2.8_prophet_predict.csv', index=False, header=False, encoding='utf-8-sig')

print('Prophet建模（含month_period回归特征）、分解图与残差分析已完成，结果保存在3.2.8_prophet_output目录。') 