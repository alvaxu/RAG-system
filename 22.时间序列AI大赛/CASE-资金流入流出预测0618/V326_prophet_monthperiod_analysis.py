'''
程序说明：
## 1. 本程序在3.2.5_prophet_model(122).py基础上，增加了对month_period（月内分段特征）的统计分析和可视化。
## 2. month_period特征分析结果输出到3.2.6_prophet_output目录，原有Prophet建模、预测、可视化等功能全部保留。
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
os.makedirs('3.2.6_prophet_output', exist_ok=True)
os.makedirs('3.2.6_feature_output', exist_ok=True)

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

# 3. 生成Prophet输入格式（ds, y）
purchase_df = daily[['ds', 'purchase']].rename(columns={'purchase': 'y'})
redeem_df = daily[['ds', 'redeem']].rename(columns={'redeem': 'y'})
purchase_df.to_csv('3.2.6_feature_output/3.2.6_prophet_purchase.csv', index=False, encoding='utf-8-sig')
redeem_df.to_csv('3.2.6_feature_output/3.2.6_prophet_redeem.csv', index=False, encoding='utf-8-sig')

# 4. 生成2014-03-01到2014-09-30的节假日和调休补班日
holiday_dates = pd.date_range('2014-03-01', '2014-09-30')
holiday_list = []
for d in holiday_dates:
    if chinese_calendar.is_holiday(d):
        holiday_list.append({'holiday': 'official_holiday', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    elif chinese_calendar.is_workday(d) and d.weekday() >= 5:
        holiday_list.append({'holiday': 'workday_shift', 'ds': d, 'lower_window': 0, 'upper_window': 0})
holiday_df = pd.DataFrame(holiday_list)
holiday_df.to_csv('3.2.6_feature_output/3.2.6_prophet_holidays.csv', index=False, encoding='utf-8-sig')

# 5. 特征工程优化
holiday_set = set(holiday_df[holiday_df['holiday'] == 'official_holiday']['ds'])
daily['is_holiday'] = daily['ds'].isin(holiday_set).astype(int)
workday_shift_set = set(holiday_df[holiday_df['holiday'] == 'workday_shift']['ds'])
daily['is_workday_shift'] = daily['ds'].isin(workday_shift_set).astype(int)
daily = daily.sort_values('ds').reset_index(drop=True)
daily['is_next_workday'] = 0
for i in range(1, len(daily)):
    if daily.loc[i-1, 'is_holiday'] == 1 and daily.loc[i, 'is_holiday'] == 0:
        daily.loc[i, 'is_next_workday'] = 1

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
daily.to_csv('3.2.6_feature_output/3.2.6_prophet_daily_features.csv', index=False, encoding='utf-8-sig')

# ========== month_period特征分析与可视化 ==========
month_period_counts = daily['month_period'].value_counts().reindex(['begin','middle','end'])
month_period_purchase = daily.groupby('month_period')['purchase'].mean().reindex(['begin','middle','end'])
month_period_redeem = daily.groupby('month_period')['redeem'].mean().reindex(['begin','middle','end'])
# 统计数量柱状图
plt.figure(figsize=(6,4))
month_period_counts.plot(kind='bar', color=['#4C72B0','#55A868','#C44E52'])
plt.title('各月内分段天数统计')
plt.ylabel('天数')
plt.xlabel('月内分段')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('3.2.6_prophet_output/month_period_counts.png')
plt.close()
# 申购均值
plt.figure(figsize=(6,4))
month_period_purchase.plot(kind='bar', color=['#4C72B0','#55A868','#C44E52'])
plt.title('各月内分段申购均值')
plt.ylabel('申购均值')
plt.xlabel('月内分段')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('3.2.6_prophet_output/month_period_purchase_mean.png')
plt.close()
# 赎回均值
plt.figure(figsize=(6,4))
month_period_redeem.plot(kind='bar', color=['#4C72B0','#55A868','#C44E52'])
plt.title('各月内分段赎回均值')
plt.ylabel('赎回均值')
plt.xlabel('月内分段')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('3.2.6_prophet_output/month_period_redeem_mean.png')
plt.close()
# 保存统计数据
month_period_counts.to_csv('3.2.6_prophet_output/month_period_counts.csv', encoding='utf-8-sig')
month_period_purchase.to_csv('3.2.6_prophet_output/month_period_purchase_mean.csv', encoding='utf-8-sig')
month_period_redeem.to_csv('3.2.6_prophet_output/month_period_redeem_mean.csv', encoding='utf-8-sig')
print('month_period特征分析已完成，结果保存在3.2.6_prophet_output目录。')

# ========== 以下为原有Prophet建模、预测、可视化等功能 ==========
# 6. 训练区间、预测区间
train_start = pd.to_datetime('2014-03-01')
train_end = pd.to_datetime('2014-08-31')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')

purchase_df = pd.read_csv('3.2.6_feature_output/3.2.6_prophet_purchase.csv', parse_dates=['ds'])
redeem_df = pd.read_csv('3.2.6_feature_output/3.2.6_prophet_redeem.csv', parse_dates=['ds'])
holidays = pd.read_csv('3.2.6_feature_output/3.2.6_prophet_holidays.csv', parse_dates=['ds'])

purchase_train = purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]
redeem_train = redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]
all_dates = pd.date_range(train_start, predict_end)
predict_dates = pd.date_range(predict_start, predict_end)

# 7. 申购Prophet建模与预测（直接用建议参数）
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
purchase_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
purchase_model.fit(purchase_train)
purchase_forecast = purchase_model.predict(pd.DataFrame({'ds': all_dates}))

# 8. 赎回Prophet建模与预测（直接用建议参数）
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
redeem_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
redeem_model.fit(redeem_train)
redeem_forecast = redeem_model.predict(pd.DataFrame({'ds': all_dates}))

# 9. 可视化：3-8月真实值、in-sample预测，9月预测
plt.figure(figsize=(18,8))
# 申购
plt.plot(purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['ds'],
         purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['y'],
         label='申购真实值', color='blue')
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'],
         purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'],
         label='申购in-sample预测', color='blue', linestyle='--')
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'],
         purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat'],
         label='申购9月预测', color='blue', linestyle=':')
# 赎回
plt.plot(redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['ds'],
         redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['y'],
         label='赎回真实值', color='green')
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'],
         redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'],
         label='赎回in-sample预测', color='green', linestyle='--')
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['ds'],
         redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat'],
         label='赎回9月预测', color='green', linestyle=':')
plt.title('2014-03-01至2014-09-30申购/赎回真实值、in-sample预测与9月预测对比（建议参数）')
plt.legend()
plt.xlim([train_start, predict_end])
plt.savefig('3.2.6_prophet_output/3.2.6_prophet_purchase_redeem_compare.png')
plt.close()

# 10. 分解图
fig = purchase_model.plot_components(purchase_forecast)
plt.savefig('3.2.6_prophet_output/3.2.6_prophet_purchase_components.png')
plt.close()
fig = redeem_model.plot_components(redeem_forecast)
plt.savefig('3.2.6_prophet_output/3.2.6_prophet_redeem_components.png')
plt.close()

# 11. 残差分析
# 申购残差
real_purchase = purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['y'].values
pred_purchase = purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'].values
residuals_purchase = real_purchase - pred_purchase
plt.figure(figsize=(12,4))
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'], residuals_purchase)
plt.title('申购残差分析（真实值-预测值）')
plt.axhline(0, color='red', linestyle='--')
plt.savefig('3.2.6_prophet_output/3.2.6_prophet_purchase_residuals.png')
plt.close()
# 赎回残差
real_redeem = redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['y'].values
pred_redeem = redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'].values
residuals_redeem = real_redeem - pred_redeem
plt.figure(figsize=(12,4))
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'], residuals_redeem)
plt.title('赎回残差分析（真实值-预测值）')
plt.axhline(0, color='red', linestyle='--')
plt.savefig('3.2.6_prophet_output/3.2.6_prophet_redeem_residuals.png')
plt.close()

# 12. 输出9月预测结果为竞赛格式
predict_df = pd.DataFrame({
    'report_date': purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'].dt.strftime('%Y%m%d'),
    'purchase': np.round(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat']).astype(int),
    'redeem': np.round(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat']).astype(int)
})
predict_df.to_csv('3.2.6_prophet_output/3.2.6_prophet_predict.csv', index=False, header=False, encoding='utf-8-sig')

print('Prophet建议参数建模、分解图与残差分析已完成，结果保存在3.2.6_prophet_output目录。') 