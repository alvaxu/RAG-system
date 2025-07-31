'''
程序说明：
## 1. 本程序实现“分组均值法+Prophet残差提升”方案，先用分组均值法做基线预测，再用Prophet对残差建模提升预测精度。
## 2. 参考4.0_deep_tuning_groupmean_best_combine_2(125).py和V328_prophet_monthperiod_regressor_full(124).py，流程自洽，输出丰富。
分数:108.1828b (反而下降了)
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

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('3.2.9_prophet_output', exist_ok=True)
os.makedirs('3.2.9_feature_output', exist_ok=True)

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
holiday_df.to_csv('3.2.9_feature_output/3.2.9_prophet_holidays.csv', index=False, encoding='utf-8-sig')

# 4. 构造全量特征表（含month_period等）
def month_period_func(day):
    d = day.day
    if d <= 10:
        return 'begin'
    elif d <= 20:
        return 'middle'
    else:
        return 'end'

date_range = pd.date_range('2014-03-01', '2014-09-30')
feature_df = pd.DataFrame({'ds': date_range})
feature_df['weekday'] = feature_df['ds'].dt.weekday
feature_df['month_period'] = feature_df['ds'].apply(month_period_func)
# 可扩展更多特征

# 合并真实数据
df = pd.merge(feature_df, daily, on='ds', how='left')

# 5. 分组均值法预测（训练集和预测区间）
group_cols = ['weekday', 'month_period']
group_mean = df[(df['ds'] >= '2014-03-01') & (df['ds'] <= '2014-08-31')].groupby(group_cols)[['purchase','redeem']].mean().reset_index()

def predict_groupmean(row, target):
    cond = (group_mean['weekday'] == row['weekday']) & (group_mean['month_period'] == row['month_period'])
    match = group_mean[cond]
    if not match.empty:
        return match.iloc[0][target]
    # 若无匹配，降级用全局均值
    return group_mean[target].mean()

df['gm_purchase_pred'] = df.apply(lambda row: predict_groupmean(row, 'purchase'), axis=1)
df['gm_redeem_pred'] = df.apply(lambda row: predict_groupmean(row, 'redeem'), axis=1)

# 6. 计算训练集残差
df['purchase_residual'] = df['purchase'] - df['gm_purchase_pred']
df['redeem_residual'] = df['redeem'] - df['gm_redeem_pred']

# 7. Prophet对残差建模（申购）
purchase_residual_train = df[(df['ds'] >= '2014-03-01') & (df['ds'] <= '2014-08-31')][['ds','purchase_residual','month_period']].copy()
purchase_residual_train = pd.concat([purchase_residual_train, pd.get_dummies(purchase_residual_train['month_period'], prefix='month_period')], axis=1)

holidays = pd.read_csv('3.2.9_feature_output/3.2.9_prophet_holidays.csv', parse_dates=['ds'])

# 构造全量预测特征
def get_month_period_onehot(date):
    d = date.day
    return {
        'month_period_begin': int(d <= 10),
        'month_period_middle': int(10 < d <= 20),
        'month_period_end': int(d > 20)
    }
predict_df = pd.DataFrame({'ds': date_range})
mp_onehot = predict_df['ds'].apply(get_month_period_onehot)
mp_df = pd.DataFrame(list(mp_onehot))
predict_df = pd.concat([predict_df, mp_df], axis=1)

# Prophet建模
purchase_residual_model = Prophet(
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
    purchase_residual_model.add_regressor(col)
purchase_residual_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
purchase_residual_model.fit(purchase_residual_train.rename(columns={'purchase_residual':'y'}).drop(columns=['month_period']))
purchase_residual_forecast = purchase_residual_model.predict(predict_df[['ds','month_period_begin','month_period_middle','month_period_end']])

# 8. Prophet对残差建模（赎回）
redeem_residual_train = df[(df['ds'] >= '2014-03-01') & (df['ds'] <= '2014-08-31')][['ds','redeem_residual','month_period']].copy()
redeem_residual_train = pd.concat([redeem_residual_train, pd.get_dummies(redeem_residual_train['month_period'], prefix='month_period')], axis=1)

redeem_residual_model = Prophet(
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
    redeem_residual_model.add_regressor(col)
redeem_residual_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
redeem_residual_model.fit(redeem_residual_train.rename(columns={'redeem_residual':'y'}).drop(columns=['month_period']))
redeem_residual_forecast = redeem_residual_model.predict(predict_df[['ds','month_period_begin','month_period_middle','month_period_end']])

# 9. 融合预测：分组均值预测+Prophet残差预测
# 用set_index对齐，避免错位
purchase_residual_forecast = purchase_residual_forecast.set_index('ds')
redeem_residual_forecast = redeem_residual_forecast.set_index('ds')
df = df.set_index('ds')
df['fusion_purchase_pred'] = df['gm_purchase_pred'] + purchase_residual_forecast['yhat']
df['fusion_redeem_pred'] = df['gm_redeem_pred'] + redeem_residual_forecast['yhat']
df = df.reset_index()

# 10. 输出9月预测结果
predict_result = df[(df['ds'] >= '2014-09-01') & (df['ds'] <= '2014-09-30')][['ds','fusion_purchase_pred','fusion_redeem_pred']].copy()
predict_result['ds'] = predict_result['ds'].dt.strftime('%Y%m%d')
predict_result[['ds','fusion_purchase_pred','fusion_redeem_pred']].to_csv('3.2.9_prophet_output/3.2.9_prophet_predict.csv', index=False, header=False, encoding='utf-8-sig')

# 11. 可视化
train_mask = (df['ds'] >= '2014-03-01') & (df['ds'] <= '2014-08-31')
full_mask = (df['ds'] >= '2014-03-01') & (df['ds'] <= '2014-09-30')
plt.figure(figsize=(18,8))
plt.plot(df.loc[full_mask, 'ds'], df.loc[full_mask, 'purchase'], label='申购真实值', color='blue')
plt.plot(df.loc[full_mask, 'ds'], df.loc[full_mask, 'gm_purchase_pred'], label='分组均值预测', color='yellow', linestyle='--')
plt.plot(df.loc[full_mask, 'ds'], df.loc[full_mask, 'fusion_purchase_pred'], label='融合预测', color='red', linestyle=':')
plt.title('申购：真实值、分组均值预测、融合预测对比（全区间）')
plt.legend()
plt.savefig('3.2.9_prophet_output/3.2.9_prophet_purchase_compare_full.png')
plt.close()

plt.figure(figsize=(18,8))
plt.plot(df.loc[full_mask, 'ds'], df.loc[full_mask, 'redeem'], label='赎回真实值', color='green')
plt.plot(df.loc[full_mask, 'ds'], df.loc[full_mask, 'gm_redeem_pred'], label='分组均值预测', color='yellow', linestyle='--')
plt.plot(df.loc[full_mask, 'ds'], df.loc[full_mask, 'fusion_redeem_pred'], label='融合预测', color='red', linestyle=':')
plt.title('赎回：真实值、分组均值预测、融合预测对比（全区间）')
plt.legend()
plt.savefig('3.2.9_prophet_output/3.2.9_prophet_redeem_compare_full.png')
plt.close()

print('分组均值+Prophet残差提升建模、预测与可视化已完成，结果保存在3.2.9_prophet_output目录。') 