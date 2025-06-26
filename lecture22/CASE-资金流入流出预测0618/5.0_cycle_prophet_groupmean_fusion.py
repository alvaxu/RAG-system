'''
5.0_cycle_prophet_groupmean_fusion.py
功能：
- Prophet模型与周期因子分组均值法加权融合预测。
- 支持权重调优，输出融合预测结果、对比图、RMSE等。
- 修正特征工程，确保训练集和预测区间分组特征完全一致，避免边界效应。
- 成绩：101.2800
'''

import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import os
import matplotlib
import warnings
import logging

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 彻底关闭所有debug/info输出
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
warnings.filterwarnings('ignore')
for logger_name in ['prophet', 'cmdstanpy', 'matplotlib', 'pandas', 'numpy']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = False
try:
    plt.set_loglevel('error')
except Exception:
    pass

# ========== 1. 数据准备 ==========
os.makedirs('5.0_feature_output', exist_ok=True)
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# ========== 2. 特征工程（严格区分训练集和预测区间） ==========
def make_features(df):
    df = df.copy().reset_index(drop=True)
    df['weekday'] = df['ds'].dt.weekday
    df['month_period'] = df['ds'].apply(lambda x: 'begin' if x.day<=10 else ('middle' if x.day<=20 else 'end'))
    # 节假日与调休补班
    holiday_spans = [
        (pd.Timestamp('2014-04-05'), pd.Timestamp('2014-04-07')),
        (pd.Timestamp('2014-05-01'), pd.Timestamp('2014-05-03')),
        (pd.Timestamp('2014-05-31'), pd.Timestamp('2014-06-02')),
        (pd.Timestamp('2014-09-06'), pd.Timestamp('2014-09-08')),
        (pd.Timestamp('2014-10-01'), pd.Timestamp('2014-10-07')),
    ]
    holiday_dates = set()
    for start, end in holiday_spans:
        for i in range((end-start).days+1):
            holiday_dates.add(start + pd.Timedelta(days=i))
    workday_shift_dates = [pd.Timestamp('2014-05-04'), pd.Timestamp('2014-09-28'), pd.Timestamp('2014-10-11'), pd.Timestamp('2014-10-12')]
    all_dates_list = list(df['ds'])
    for d in all_dates_list:
        if d.weekday() >= 5 and d not in workday_shift_dates:
            holiday_dates.add(d)
    df['is_holiday'] = df['ds'].isin(holiday_dates).astype(int)
    df['is_workday_shift'] = df['ds'].isin(workday_shift_dates).astype(int)
    df['is_next_workday'] = 0
    for i in range(1, len(df)):
        if df.loc[i-1, 'is_holiday'] == 1 and df.loc[i, 'is_holiday'] == 0:
            df.loc[i, 'is_next_workday'] = 1
    return df

# 训练集和预测区间分别做特征工程
train_df = daily[(daily['ds'] >= '2014-03-01') & (daily['ds'] <= '2014-08-31')].copy()
predict_df = daily[(daily['ds'] >= '2014-09-01') & (daily['ds'] <= '2014-09-30')].copy()
train_df = make_features(train_df)
predict_df = make_features(predict_df)

# ========== 3. Prophet建模与预测（不变） ==========
def prophet_predict(label, y_col):
    df = daily[['ds', y_col]].rename(columns={y_col: 'y'})
    train = df[(df['ds'] >= '2014-03-01') & (df['ds'] <= '2014-08-31')]
    all_dates = pd.date_range('2014-03-01', '2014-09-30')
    # 节假日DataFrame
    holiday_list = []
    for start, end in [
        (pd.Timestamp('2014-04-05'), pd.Timestamp('2014-04-07')),
        (pd.Timestamp('2014-05-01'), pd.Timestamp('2014-05-03')),
        (pd.Timestamp('2014-05-31'), pd.Timestamp('2014-06-02')),
        (pd.Timestamp('2014-09-06'), pd.Timestamp('2014-09-08')),
        (pd.Timestamp('2014-10-01'), pd.Timestamp('2014-10-07')),
    ]:
        for i in range((end-start).days+1):
            holiday_list.append({'holiday': 'official_holiday', 'ds': start + pd.Timedelta(days=i), 'lower_window': 0, 'upper_window': 0})
    for d in [pd.Timestamp('2014-05-04'), pd.Timestamp('2014-09-28'), pd.Timestamp('2014-10-11'), pd.Timestamp('2014-10-12')]:
        holiday_list.append({'holiday': 'workday_shift', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    holidays = pd.DataFrame(holiday_list)
    m = Prophet(
        holidays=holidays,
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.01,
        seasonality_prior_scale=10.0,
        holidays_prior_scale=20.0 if label=='purchase' else 1.0
    )
    m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    try:
        m.fit(train)
        future = pd.DataFrame({'ds': pd.date_range('2014-03-01', '2014-09-30')})
        forecast = m.predict(future)
        return forecast[['ds','yhat']].set_index('ds')
    except Exception as e:
        print(f'[Prophet-{label}] 训练或预测异常: {e}')
        return pd.DataFrame({'ds': pd.date_range('2014-03-01', '2014-09-30'), 'yhat': 0}).set_index('ds')

prophet_purchase = prophet_predict('purchase', 'purchase')
prophet_redeem = prophet_predict('redeem', 'redeem')

# ========== 4. 分组均值法建模与预测 ==========
group_cols = ['weekday','month_period','is_holiday','is_next_workday']
group_mean = train_df.groupby(group_cols)[['purchase','redeem']].mean().reset_index()
global_mean_purchase = train_df['purchase'].mean()
global_mean_redeem = train_df['redeem'].mean()

def groupmean_predict_row(row, label):
    if row['is_next_workday']==1:
        match = group_mean[(group_mean['is_next_workday']==1) &
                           (group_mean['weekday']==row['weekday']) &
                           (group_mean['month_period']==row['month_period']) &
                           (group_mean['is_holiday']==row['is_holiday'])]
        if not match.empty:
            return match.iloc[0][label]
    match = group_mean[(group_mean['is_next_workday']==0) &
                      (group_mean['weekday']==row['weekday']) &
                      (group_mean['month_period']==row['month_period']) &
                      (group_mean['is_holiday']==row['is_holiday'])]
    if not match.empty:
        return match.iloc[0][label]
    match = group_mean[(group_mean['is_next_workday']==0) &
                      (group_mean['weekday']==row['weekday']) &
                      (group_mean['is_holiday']==row['is_holiday'])]
    if not match.empty:
        return match.iloc[0][label]
    return global_mean_purchase if label=='purchase' else global_mean_redeem

# 训练集和预测区间分别做分组均值预测
train_df['groupmean_purchase'] = train_df.apply(lambda row: groupmean_predict_row(row, 'purchase'), axis=1)
train_df['groupmean_redeem'] = train_df.apply(lambda row: groupmean_predict_row(row, 'redeem'), axis=1)
predict_df['groupmean_purchase'] = predict_df.apply(lambda row: groupmean_predict_row(row, 'purchase'), axis=1)
predict_df['groupmean_redeem'] = predict_df.apply(lambda row: groupmean_predict_row(row, 'redeem'), axis=1)

# ========== 5. 融合预测（加权平均） ==========
alpha = 0.5
all_dates = pd.date_range('2014-03-01', '2014-09-30')
purchase_prophet_pred = prophet_purchase.reindex(all_dates)['yhat'].fillna(global_mean_purchase).values
redeem_prophet_pred = prophet_redeem.reindex(all_dates)['yhat'].fillna(global_mean_redeem).values
# 训练区间分组均值
purchase_groupmean_pred_train = train_df.set_index('ds').reindex(all_dates)['groupmean_purchase'].fillna(global_mean_purchase).values
redeem_groupmean_pred_train = train_df.set_index('ds').reindex(all_dates)['groupmean_redeem'].fillna(global_mean_redeem).values
# 预测区间分组均值
purchase_groupmean_pred_predict = predict_df.set_index('ds').reindex(all_dates)['groupmean_purchase'].fillna(global_mean_purchase).values
redeem_groupmean_pred_predict = predict_df.set_index('ds').reindex(all_dates)['groupmean_redeem'].fillna(global_mean_redeem).values
# 合并：前len(train_df)用train，后len(predict_df)用predict
purchase_groupmean_pred = np.where(
    (all_dates >= pd.to_datetime('2014-09-01')) & (all_dates <= pd.to_datetime('2014-09-30')),
    purchase_groupmean_pred_predict,
    purchase_groupmean_pred_train
)
redeem_groupmean_pred = np.where(
    (all_dates >= pd.to_datetime('2014-09-01')) & (all_dates <= pd.to_datetime('2014-09-30')),
    redeem_groupmean_pred_predict,
    redeem_groupmean_pred_train
)
# 融合
purchase_fusion = alpha * purchase_prophet_pred + (1-alpha) * purchase_groupmean_pred
redeem_fusion = alpha * redeem_prophet_pred + (1-alpha) * redeem_groupmean_pred

# ========== 6. 输出csv、对比图、RMSE ==========
predict_dates = pd.date_range('2014-09-01', '2014-09-30')
predict_df_out = pd.DataFrame({
    'ds': predict_dates.strftime('%Y%m%d'),
    'purchase': np.round(purchase_fusion[-30:]).astype(int),
    'redeem': np.round(redeem_fusion[-30:]).astype(int)
})
predict_df_out.to_csv('5.0_feature_output/5.0_cycle_prophet_groupmean_fusion_predict.csv', index=False, header=False, encoding='utf-8-sig')
print('已输出融合预测结果csv：5.0_feature_output/5.0_cycle_prophet_groupmean_fusion_predict.csv')

plt.figure(figsize=(18,10))
fig, axes = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
axes[0].plot(daily[(daily['ds'] >= '2014-03-01') & (daily['ds'] <= '2014-09-30')]['ds'],
             daily[(daily['ds'] >= '2014-03-01') & (daily['ds'] <= '2014-09-30')]['purchase'],
             label='申购真实值', color='blue')
axes[0].plot(all_dates, purchase_prophet_pred, label='Prophet预测', color='orange', linestyle='--')
axes[0].plot(all_dates, purchase_groupmean_pred, label='分组均值预测', color='green', linestyle=':')
axes[0].plot(all_dates, purchase_fusion, label='融合预测', color='red', linestyle='-')
axes[0].set_title('申购：真实值、Prophet、分组均值与融合预测对比')
axes[0].legend()
axes[1].plot(daily[(daily['ds'] >= '2014-03-01') & (daily['ds'] <= '2014-09-30')]['ds'],
             daily[(daily['ds'] >= '2014-03-01') & (daily['ds'] <= '2014-09-30')]['redeem'],
             label='赎回真实值', color='blue')
axes[1].plot(all_dates, redeem_prophet_pred, label='Prophet预测', color='orange', linestyle='--')
axes[1].plot(all_dates, redeem_groupmean_pred, label='分组均值预测', color='green', linestyle=':')
axes[1].plot(all_dates, redeem_fusion, label='融合预测', color='red', linestyle='-')
axes[1].set_title('赎回：真实值、Prophet、分组均值与融合预测对比')
axes[1].legend()
plt.xlim([all_dates[0], all_dates[-1]])
plt.tight_layout()
plt.savefig('5.0_feature_output/5.0_cycle_prophet_groupmean_fusion_compare.png')
plt.close()
print('已输出对比图：5.0_feature_output/5.0_cycle_prophet_groupmean_fusion_compare.png')

from sklearn.metrics import mean_squared_error
train_dates = pd.date_range('2014-03-01', '2014-08-31')
real_purchase = daily.set_index('ds').reindex(train_dates)['purchase'].fillna(global_mean_purchase).values
real_redeem = daily.set_index('ds').reindex(train_dates)['redeem'].fillna(global_mean_redeem).values
rmse_purchase = np.sqrt(mean_squared_error(real_purchase, purchase_fusion[:len(train_dates)]))
rmse_redeem = np.sqrt(mean_squared_error(real_redeem, redeem_fusion[:len(train_dates)]))
print(f'训练区间RMSE: 申购={rmse_purchase:.2f}, 赎回={rmse_redeem:.2f}') 