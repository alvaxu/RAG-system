'''
4.4_cycle_groupmean_predict.py
功能：
- 周期性特征工程+分组均值法+异常点检测与剔除，提升预测精度。
- 训练时自动检测并剔除异常点，预测时遇异常点自动降级。
- 只用weekday分组。
- 输出异常点列表、预测结果、对比图。
'''

import pandas as pd
import numpy as np
import os
from datetime import date, timedelta
import matplotlib.pyplot as plt
import matplotlib

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# ========== 1. 周期性特征工程 ==========
os.makedirs('4.4_feature_output', exist_ok=True)

user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

holiday_dates = set()
holiday_spans = [
    (date(2014,4,5), date(2014,4,7)),   # 清明节
    (date(2014,5,1), date(2014,5,3)),   # 劳动节
    (date(2014,5,31), date(2014,6,2)),  # 端午节
    (date(2014,9,6), date(2014,9,8)),   # 中秋节
    (date(2014,10,1), date(2014,10,7)), # 国庆节
]
for start, end in holiday_spans:
    for i in range((end-start).days+1):
        holiday_dates.add(start + timedelta(days=i))
workday_shift_dates = [date(2014,5,4), date(2014,9,28), date(2014,10,11), date(2014,10,12)]
all_dates_list = [date(2014,3,1) + timedelta(days=i) for i in range((date(2014,10,10)-date(2014,3,1)).days+1)]
for d in all_dates_list:
    if d.weekday() >= 5 and d not in workday_shift_dates:
        holiday_dates.add(d)
holiday_list = []
for d in sorted(holiday_dates):
    holiday_list.append({'holiday': 'official_holiday', 'ds': pd.Timestamp(d), 'lower_window': 0, 'upper_window': 0})
for d in workday_shift_dates:
    holiday_list.append({'holiday': 'workday_shift', 'ds': pd.Timestamp(d), 'lower_window': 0, 'upper_window': 0})
holiday_df = pd.DataFrame(holiday_list)
holiday_df.to_csv('4.4_feature_output/4.4_cycle_holidays.csv', index=False, encoding='utf-8-sig')

feature_df = pd.DataFrame({'ds': pd.date_range('2014-03-01', '2014-10-10')})
feature_df['weekday'] = feature_df['ds'].dt.weekday
feature_df['month_period'] = feature_df['ds'].apply(lambda x: 'begin' if x.day<=10 else ('middle' if x.day<=20 else 'end'))
holiday_set = set(holiday_df[holiday_df['holiday']=='official_holiday']['ds'])
feature_df['is_holiday'] = feature_df['ds'].isin(holiday_set).astype(int)
workday_shift_set = set(holiday_df[holiday_df['holiday']=='workday_shift']['ds'])
feature_df['is_workday_shift'] = feature_df['ds'].isin(workday_shift_set).astype(int)
df = feature_df
feature_df['is_next_workday'] = 0
for i in range(1, len(df)):
    if df.loc[i-1, 'is_holiday'] == 1 and df.loc[i, 'is_holiday'] == 0:
        feature_df.loc[i, 'is_next_workday'] = 1
feature_df.to_csv('4.4_feature_output/4.4_cycle_daily_features.csv', index=False, encoding='utf-8-sig')

print('周期性特征工程已完成，特征文件和节假日文件已输出到4.4_feature_output目录。')

# ========== 2. 异常点检测 ==========
# 训练/预测区间
train_start = pd.to_datetime('2014-03-01')
train_end = pd.to_datetime('2014-08-31')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-10-10')
predict_csv_end = pd.to_datetime('2014-09-30')

feature_df = pd.read_csv('4.4_feature_output/4.4_cycle_daily_features.csv', parse_dates=['ds'])
agg = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
agg = agg.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})
df = pd.merge(feature_df, agg, on='ds', how='left')

train_df = df[(df['ds'] >= train_start) & (df['ds'] <= train_end)].copy()
predict_df = df[(df['ds'] >= predict_start) & (df['ds'] <= predict_end)].copy()

# 分组特征
weekday_col = ['weekday']
# 1. 用分组均值法做in-sample预测
in_sample_group_mean = train_df.groupby(weekday_col)[['purchase','redeem']].mean().reset_index()

def in_sample_predict_row(row):
    match = in_sample_group_mean[in_sample_group_mean['weekday']==row['weekday']]
    if not match.empty:
        return match.iloc[0]['purchase'], match.iloc[0]['redeem']
    return train_df['purchase'].mean(), train_df['redeem'].mean()

# 2. 计算残差
train_df['pred_purchase'], train_df['pred_redeem'] = zip(*train_df.apply(in_sample_predict_row, axis=1))
train_df['resid_purchase'] = train_df['purchase'] - train_df['pred_purchase']
train_df['resid_redeem'] = train_df['redeem'] - train_df['pred_redeem']

# 3. 分组统计均值和std，标记异常点
train_df['is_outlier_purchase'] = 0
train_df['is_outlier_redeem'] = 0
grouped = train_df.groupby(weekday_col)
for name, group in grouped:
    mean_p = group['resid_purchase'].mean()
    std_p = group['resid_purchase'].std()
    mean_r = group['resid_redeem'].mean()
    std_r = group['resid_redeem'].std()
    idx_p = group.index[(group['resid_purchase'] > mean_p + 3*std_p) | (group['resid_purchase'] < mean_p - 3*std_p)]
    idx_r = group.index[(group['resid_redeem'] > mean_r + 3*std_r) | (group['resid_redeem'] < mean_r - 3*std_r)]
    train_df.loc[idx_p, 'is_outlier_purchase'] = 1
    train_df.loc[idx_r, 'is_outlier_redeem'] = 1

# 4. 输出异常点csv
outlier_df = train_df[(train_df['is_outlier_purchase']==1) | (train_df['is_outlier_redeem']==1)][['ds','purchase','redeem','pred_purchase','pred_redeem','resid_purchase','resid_redeem','is_outlier_purchase','is_outlier_redeem']]
outlier_df.to_csv('4.4_feature_output/4.4_cycle_groupmean_outliers.csv', index=False, encoding='utf-8-sig')
print(f'异常点检测完成，检测到{len(outlier_df)}个异常点，已输出到4.4_feature_output/4.4_cycle_groupmean_outliers.csv')

# ========== 3. 剔除异常点后分组均值训练 ==========
train_df_clean = train_df[(train_df['is_outlier_purchase']==0) & (train_df['is_outlier_redeem']==0)].copy()

# 重新分组均值
group_mean = train_df_clean.groupby(weekday_col)[['purchase','redeem']].mean().reset_index()

def predict_row(row):
    match = group_mean[group_mean['weekday']==row['weekday']]
    if not match.empty:
        return match.iloc[0]['purchase'], match.iloc[0]['redeem']
    return train_df_clean['purchase'].mean(), train_df_clean['redeem'].mean()

# ========== 4. 预测 ==========
pred_purchase = []
pred_redeem = []
for _, row in predict_df.iterrows():
    p, r = predict_row(row)
    pred_purchase.append(p)
    pred_redeem.append(r)
predict_df['pred_purchase'] = np.round(pred_purchase).astype(int)
predict_df['pred_redeem'] = np.round(pred_redeem).astype(int)

output = predict_df[(predict_df['ds'] >= predict_start) & (predict_df['ds'] <= predict_csv_end)][['ds','pred_purchase','pred_redeem']].copy()
output['ds'] = output['ds'].dt.strftime('%Y%m%d')
output.to_csv('4.4_feature_output/4.4_cycle_groupmean_predict.csv', index=False, header=False, encoding='utf-8-sig')

print('异常点剔除后分组均值预测已完成，结果已输出到4.4_feature_output/4.4_cycle_groupmean_predict.csv。')

# ========== 5. 可视化真实值与预测值对比 ==========
full_df = df.copy()
full_df['pred_purchase'] = np.nan
full_df['pred_redeem'] = np.nan
for idx, row in train_df.iterrows():
    p, r = predict_row(row)
    full_df.loc[full_df['ds']==row['ds'], 'pred_purchase'] = p
    full_df.loc[full_df['ds']==row['ds'], 'pred_redeem'] = r
for idx, row in predict_df.iterrows():
    full_df.loc[full_df['ds']==row['ds'], 'pred_purchase'] = row['pred_purchase']
    full_df.loc[full_df['ds']==row['ds'], 'pred_redeem'] = row['pred_redeem']

plot_start = pd.to_datetime('2014-03-01')
plot_end = pd.to_datetime('2014-09-30')
plt.figure(figsize=(18,10))
fig, axes = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
# 申购
axes[0].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= train_end)]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= train_end)]['purchase'],
             label='申购真实值', color='blue')
axes[0].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= train_end)]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= train_end)]['pred_purchase'],
             label='申购in-sample预测', color='blue', linestyle='--')
axes[0].plot(full_df[(full_df['ds'] >= predict_start) & (full_df['ds'] <= plot_end)]['ds'],
             full_df[(full_df['ds'] >= predict_start) & (full_df['ds'] <= plot_end)]['pred_purchase'],
             label='申购9月预测', color='blue', linestyle=':')
axes[0].set_title('申购：真实值、in-sample预测与9月预测（异常点剔除分组均值法，weekday分组）')
axes[0].legend()
# 赎回
axes[1].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= train_end)]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= train_end)]['redeem'],
             label='赎回真实值', color='green')
axes[1].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= train_end)]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= train_end)]['pred_redeem'],
             label='赎回in-sample预测', color='green', linestyle='--')
axes[1].plot(full_df[(full_df['ds'] >= predict_start) & (full_df['ds'] <= plot_end)]['ds'],
             full_df[(full_df['ds'] >= predict_start) & (full_df['ds'] <= plot_end)]['pred_redeem'],
             label='赎回9月预测', color='green', linestyle=':')
axes[1].set_title('赎回：真实值、in-sample预测与9月预测（异常点剔除分组均值法，weekday分组）')
axes[1].legend()
plt.xlim([plot_start, plot_end])
plt.tight_layout()
plt.savefig('4.4_feature_output/4.4_cycle_groupmean_purchase_redeem_compare.png')
plt.close()
print('已输出真实值与预测值对比图：4.4_feature_output/4.4_cycle_groupmean_purchase_redeem_compare.png') 