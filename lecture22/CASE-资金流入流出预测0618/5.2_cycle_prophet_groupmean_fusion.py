'''
5.2_cycle_prophet_groupmean_fusion.py
功能：
- Prophet模型与周期因子分组均值法残差修正型融合预测。与3.2.1和4.0完全一致
- 优化分组均值法降级策略，最大程度利用分组信息，避免9月大量用全局均值。
- 自动调优残差修正权重β（在8月验证集上），输出最优β、融合预测结果、对比图、RMSE等。
最优残差修正权重beta=0.35, 8月验证集RMSE=97354951.16
已输出融合预测结果csv：5.2_feature_output/5.2_cycle_prophet_groupmean_fusion_predict.csv
已输出对比图：5.2_feature_output/5.2_cycle_prophet_groupmean_fusion_compare.png
训练区间RMSE: 申购=47613775.25, 赎回=61136591.58
成绩：114.108（与5.1一样）
'''

import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import os
import matplotlib
import warnings
import logging
import chinese_calendar

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
os.makedirs('5.2_feature_output', exist_ok=True)
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# ========== 2. 特征工程 ==========
def make_features(df):
    df = df.copy().reset_index(drop=True)
    df['weekday'] = df['ds'].dt.weekday
    df['month_period'] = df['ds'].apply(lambda x: 'begin' if x.day<=10 else ('middle' if x.day<=20 else 'end'))
    # 用chinese_calendar生成节假日、调休补班
    df['is_holiday'] = df['ds'].apply(lambda d: 1 if chinese_calendar.is_holiday(d) else 0)
    df['is_workday_shift'] = df['ds'].apply(lambda d: 1 if (chinese_calendar.is_workday(d) and d.weekday() >= 5) else 0)
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

# ========== 3. Prophet建模与预测 ==========
def get_holidays(start, end):
    holiday_dates = pd.date_range(start, end)
    holiday_list = []
    for d in holiday_dates:
        if chinese_calendar.is_holiday(d):
            holiday_list.append({'holiday': 'official_holiday', 'ds': d, 'lower_window': 0, 'upper_window': 0})
        elif chinese_calendar.is_workday(d) and d.weekday() >= 5:
            holiday_list.append({'holiday': 'workday_shift', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    return pd.DataFrame(holiday_list)

def prophet_predict(label, y_col):
    df = daily[['ds', y_col]].rename(columns={y_col: 'y'})
    train = df[(df['ds'] >= '2014-03-01') & (df['ds'] <= '2014-08-31')]
    all_dates = pd.date_range('2014-03-01', '2014-09-30')
    holidays = get_holidays('2014-03-01', '2014-09-30')
    if label == 'purchase':
        m = Prophet(
            holidays=holidays,
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative',
            changepoint_prior_scale=0.01,
            seasonality_prior_scale=10.0,
            holidays_prior_scale=20.0
        )
    else:
        m = Prophet(
            holidays=holidays,
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='additive',
            changepoint_prior_scale=0.01,
            seasonality_prior_scale=20.0,
            holidays_prior_scale=1.0
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

# ========== 4. 分组均值法建模与预测（多级降级） ==========
group_cols = ['weekday','month_period','is_holiday','is_next_workday']
group_mean = train_df.groupby(group_cols)[['purchase','redeem']].mean().reset_index()
global_mean_purchase = train_df['purchase'].mean()
global_mean_redeem = train_df['redeem'].mean()

def groupmean_predict_row(row, label):
    # 1. 全特征分组
    match = group_mean[(group_mean['weekday']==row['weekday']) &
                      (group_mean['month_period']==row['month_period']) &
                      (group_mean['is_holiday']==row['is_holiday']) &
                      (group_mean['is_next_workday']==row['is_next_workday'])]
    if not match.empty:
        return match.iloc[0][label]
    # 2. 去掉month_period
    match = group_mean[(group_mean['weekday']==row['weekday']) &
                      (group_mean['is_holiday']==row['is_holiday']) &
                      (group_mean['is_next_workday']==row['is_next_workday'])]
    if not match.empty:
        return match.iloc[0][label]
    # 3. 去掉is_next_workday
    match = group_mean[(group_mean['weekday']==row['weekday']) &
                      (group_mean['is_holiday']==row['is_holiday'])]
    if not match.empty:
        return match.iloc[0][label]
    # 4. 全局均值
    return global_mean_purchase if label=='purchase' else global_mean_redeem

# 训练集和预测区间分别做分组均值预测
train_df['groupmean_purchase'] = train_df.apply(lambda row: groupmean_predict_row(row, 'purchase'), axis=1)
train_df['groupmean_redeem'] = train_df.apply(lambda row: groupmean_predict_row(row, 'redeem'), axis=1)
predict_df['groupmean_purchase'] = predict_df.apply(lambda row: groupmean_predict_row(row, 'purchase'), axis=1)
predict_df['groupmean_redeem'] = predict_df.apply(lambda row: groupmean_predict_row(row, 'redeem'), axis=1)

# ========== 5. 残差修正型融合（自动调优β） ==========
beta_grid = np.arange(0, 1.01, 0.05)
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

# 自动调优β（在8月验证集上）
from sklearn.metrics import mean_squared_error
val_dates = pd.date_range('2014-08-01', '2014-08-31')
real_val_purchase = daily.set_index('ds').reindex(val_dates)['purchase'].fillna(global_mean_purchase).values
real_val_redeem = daily.set_index('ds').reindex(val_dates)['redeem'].fillna(global_mean_redeem).values
val_idx = ((all_dates >= pd.to_datetime('2014-08-01')) & (all_dates <= pd.to_datetime('2014-08-31')))
best_beta = 0.5
best_rmse = float('inf')
for b in beta_grid:
    val_pred_purchase = purchase_prophet_pred[val_idx] + b * (purchase_groupmean_pred[val_idx] - purchase_prophet_pred[val_idx])
    val_pred_redeem = redeem_prophet_pred[val_idx] + b * (redeem_groupmean_pred[val_idx] - redeem_prophet_pred[val_idx])
    rmse = np.sqrt(mean_squared_error(real_val_purchase, val_pred_purchase)) + np.sqrt(mean_squared_error(real_val_redeem, val_pred_redeem))
    if rmse < best_rmse:
        best_rmse = rmse
        best_beta = b
print(f'最优残差修正权重beta={best_beta:.2f}, 8月验证集RMSE={best_rmse:.2f}')

# 用最优beta做全区间融合
purchase_fusion = purchase_prophet_pred + best_beta * (purchase_groupmean_pred - purchase_prophet_pred)
redeem_fusion = redeem_prophet_pred + best_beta * (redeem_groupmean_pred - redeem_prophet_pred)

# ========== 6. 输出csv、对比图、RMSE ==========
predict_dates = pd.date_range('2014-09-01', '2014-09-30')
predict_df_out = pd.DataFrame({
    'ds': predict_dates.strftime('%Y%m%d'),
    'purchase': np.round(purchase_fusion[-30:]).astype(int),
    'redeem': np.round(redeem_fusion[-30:]).astype(int)
})
predict_df_out.to_csv('5.2_feature_output/5.2_cycle_prophet_groupmean_fusion_predict.csv', index=False, header=False, encoding='utf-8-sig')
print('已输出融合预测结果csv：5.2_feature_output/5.2_cycle_prophet_groupmean_fusion_predict.csv')

plt.figure(figsize=(18,10))
fig, axes = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
axes[0].plot(daily[(daily['ds'] >= '2014-03-01') & (daily['ds'] <= '2014-09-30')]['ds'],
             daily[(daily['ds'] >= '2014-03-01') & (daily['ds'] <= '2014-09-30')]['purchase'],
             label='申购真实值', color='blue')
axes[0].plot(all_dates, purchase_prophet_pred, label='Prophet预测', color='orange', linestyle='--')
axes[0].plot(all_dates, purchase_groupmean_pred, label='分组均值预测', color='green', linestyle=':')
axes[0].plot(all_dates, purchase_fusion, label='残差修正融合预测', color='red', linestyle='-')
axes[0].set_title('申购：真实值、Prophet、分组均值与残差修正融合预测对比')
axes[0].legend()
axes[1].plot(daily[(daily['ds'] >= '2014-03-01') & (daily['ds'] <= '2014-09-30')]['ds'],
             daily[(daily['ds'] >= '2014-03-01') & (daily['ds'] <= '2014-09-30')]['redeem'],
             label='赎回真实值', color='blue')
axes[1].plot(all_dates, redeem_prophet_pred, label='Prophet预测', color='orange', linestyle='--')
axes[1].plot(all_dates, redeem_groupmean_pred, label='分组均值预测', color='green', linestyle=':')
axes[1].plot(all_dates, redeem_fusion, label='残差修正融合预测', color='red', linestyle='-')
axes[1].set_title('赎回：真实值、Prophet、分组均值与残差修正融合预测对比')
axes[1].legend()
plt.xlim([all_dates[0], all_dates[-1]])
plt.tight_layout()
plt.savefig('5.2_feature_output/5.2_cycle_prophet_groupmean_fusion_compare.png')
plt.close()
print('已输出对比图：5.2_feature_output/5.2_cycle_prophet_groupmean_fusion_compare.png')

train_dates = pd.date_range('2014-03-01', '2014-08-31')
real_purchase = daily.set_index('ds').reindex(train_dates)['purchase'].fillna(global_mean_purchase).values
real_redeem = daily.set_index('ds').reindex(train_dates)['redeem'].fillna(global_mean_redeem).values
rmse_purchase = np.sqrt(mean_squared_error(real_purchase, purchase_fusion[:len(train_dates)]))
rmse_redeem = np.sqrt(mean_squared_error(real_redeem, redeem_fusion[:len(train_dates)]))
print(f'训练区间RMSE: 申购={rmse_purchase:.2f}, 赎回={rmse_redeem:.2f}') 