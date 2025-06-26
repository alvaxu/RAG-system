'''
3.1_prophet_model.py
功能：
- 余额宝申购/赎回数据Prophet建模与预测，支持节假日、调休、节后顺延等业务规则。
- 特征工程优化：
  1. 只用法定节假日生成is_holiday，不把普通周末算作节假日。
  2. 新增is_next_workday特征，标记节假日后第一个工作日（捕捉顺延效应）。
  3. 保留is_workday_shift（调休补班），但该特征与银行实际工作日可能有出入，仅供参考。
  4. 保留weekday、month_period等常规时间特征。
- 只采用直接外推预测（one-shot forecasting），不再使用递推预测。

申购参数设置为：
{
    'changepoint_prior_scale': 0.2,
    'seasonality_prior_scale': Prophet默认值（10.0）,
    'holidays_prior_scale': Prophet默认值（10.0）,
    'seasonality_mode': 'additive',
    'yearly_seasonality': True,
    'weekly_seasonality': True,
    'daily_seasonality': False
}

赎回参数设置为
{
    'changepoint_prior_scale': 0.2,
    'seasonality_prior_scale': Prophet默认值（10.0）,
    'holidays_prior_scale': Prophet默认值（10.0）,
    'seasonality_mode': 'additive',
    'yearly_seasonality': True,
    'weekly_seasonality': True,
    'daily_seasonality': False
}
'''

import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import chinese_calendar
import os
import matplotlib

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('3.1_prophet_output', exist_ok=True)
os.makedirs('3.1_feature_output', exist_ok=True)

# 1. 读取原始数据
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 2. 聚合每日申购/赎回总额
daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# 3. 生成Prophet输入格式（ds, y）
purchase_df = daily[['ds', 'purchase']].rename(columns={'purchase': 'y'})
redeem_df = daily[['ds', 'redeem']].rename(columns={'redeem': 'y'})
purchase_df.to_csv('3.1_feature_output/3.1_prophet_purchase.csv', index=False, encoding='utf-8-sig')
redeem_df.to_csv('3.1_feature_output/3.1_prophet_redeem.csv', index=False, encoding='utf-8-sig')

# 4. 生成2014-03-01到2014-09-30的节假日和调休补班日
holiday_dates = pd.date_range('2014-03-01', '2014-09-30')
holiday_list = []
for d in holiday_dates:
    if chinese_calendar.is_holiday(d):
        holiday_list.append({'holiday': 'official_holiday', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    elif chinese_calendar.is_workday(d) and d.weekday() >= 5:
        holiday_list.append({'holiday': 'workday_shift', 'ds': d, 'lower_window': 0, 'upper_window': 0})
holiday_df = pd.DataFrame(holiday_list)
holiday_df.to_csv('3.1_feature_output/3.1_prophet_holidays.csv', index=False, encoding='utf-8-sig')

# 5. 特征工程优化
# 只用法定节假日生成is_holiday
holiday_set = set(holiday_df[holiday_df['holiday'] == 'official_holiday']['ds'])
daily['is_holiday'] = daily['ds'].isin(holiday_set).astype(int)
# 标记调休补班日（注意：该特征与银行实际工作日可能有出入，仅供参考）
workday_shift_set = set(holiday_df[holiday_df['holiday'] == 'workday_shift']['ds'])
daily['is_workday_shift'] = daily['ds'].isin(workday_shift_set).astype(int)
# 新增：节假日后第一个工作日
# 先按日期排序
daily = daily.sort_values('ds').reset_index(drop=True)
daily['is_next_workday'] = 0
for i in range(1, len(daily)):
    if daily.loc[i-1, 'is_holiday'] == 1 and daily.loc[i, 'is_holiday'] == 0:
        daily.loc[i, 'is_next_workday'] = 1
# 其他时间特征

def month_period(day):
    d = day.day
    if d <= 10:
        return 'begin'
    elif d <= 20:
        return 'middle'
    else:
        return 'end'
daily['weekday'] = daily['ds'].dt.weekday
daily['month_period'] = daily['ds'].apply(month_period)
daily.to_csv('3.1_feature_output/3.1_prophet_daily_features.csv', index=False, encoding='utf-8-sig')

# 6. Prophet直接外推预测
train_start = pd.to_datetime('2014-03-01')
train_end = pd.to_datetime('2014-08-31')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')

purchase_df = pd.read_csv('3.1_feature_output/3.1_prophet_purchase.csv', parse_dates=['ds'])
redeem_df = pd.read_csv('3.1_feature_output/3.1_prophet_redeem.csv', parse_dates=['ds'])
holidays = pd.read_csv('3.1_feature_output/3.1_prophet_holidays.csv', parse_dates=['ds'])

purchase_train = purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]
redeem_train = redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]
all_dates = pd.date_range(train_start, predict_end)
predict_dates = pd.date_range(predict_start, predict_end)

def prophet_predict(train_df, holidays, all_dates, label):
    m = Prophet(
        holidays=holidays,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='additive',
        changepoint_prior_scale=0.2
    )
    m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    m.fit(train_df)
    future = pd.DataFrame({'ds': all_dates})
    forecast = m.predict(future)
    return forecast

purchase_forecast = prophet_predict(purchase_train, holidays, all_dates, 'purchase')
redeem_forecast = prophet_predict(redeem_train, holidays, all_dates, 'redeem')

# 7. 可视化：3-8月真实值、in-sample预测，9月直接外推预测
plt.figure(figsize=(18,8))
# 真实值（3-8月）
plt.plot(purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['ds'],
         purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['y'],
         label='申购真实值', color='blue')
plt.plot(redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['ds'],
         redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['y'],
         label='赎回真实值', color='green')
# in-sample预测（3-8月）
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'],
         purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'],
         label='申购in-sample预测', color='blue', linestyle='--')
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'],
         redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'],
         label='赎回in-sample预测', color='green', linestyle='--')
# 9月直接外推预测
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'],
         purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat'],
         label='申购9月预测', color='blue', linestyle=':')
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['ds'],
         redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat'],
         label='赎回9月预测', color='green', linestyle=':')
plt.title('2014-03-01至2014-09-30申购/赎回真实值、in-sample预测与9月预测对比')
plt.legend()
plt.xlim([train_start, predict_end])
plt.savefig('3.1_prophet_output/3.1_prophet_purchase_redeem_compare.png')
plt.close()

# 8. 输出9月预测结果为竞赛格式
predict_df = pd.DataFrame({
    'report_date': purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'].dt.strftime('%Y%m%d'),
    'purchase': np.round(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat']).astype(int),
    'redeem': np.round(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat']).astype(int)
})
predict_df.to_csv('3.1_prophet_output/3.1_prophet_predict.csv', index=False, header=False, encoding='utf-8-sig')

print('Prophet直接外推预测、特征工程优化与可视化已完成，结果保存在3.1_prophet_output目录。') 