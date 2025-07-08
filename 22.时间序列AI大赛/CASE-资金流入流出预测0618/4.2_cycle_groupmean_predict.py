'''
4.2_cycle_groupmean_predict.py
功能：
- 一键完成周期性特征工程与基于最优周期因子分组均值的申购/赎回预测。
- 分组特征采用('weekday', 'is_workday_shift')，并实现多级降级策略。
- 先生成节假日、调休补班、周期性特征文件（与4.0_cycle_feature_engine.py一致），再进行分组均值预测。
- 训练区间2014-03-01~2014-08-31，预测区间2014-09-01~2014-10-10，输出csv区间2014-09-01~2014-09-30。
- 输出2014-03-01~2014-09-30区间真实值与预测值对比图（上下子图），图片保存到4.2_feature_output/4.2_cycle_groupmean_purchase_redeem_compare.png。
- 结果输出到4.2_cycle_groupmean_predict.csv，便于与Prophet等模型对比。
分组特征: ('weekday', 'is_workday_shift')，多级降级：1. (weekday, is_workday_shift) 2. (weekday) 3. 全局均值。

成绩：111.8994
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
# 创建输出目录
os.makedirs('4.2_feature_output', exist_ok=True)

# 读取原始数据
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 显式定义节假日和调休补班日（与3.7.1一致）
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
# 生成节假日DataFrame
holiday_list = []
for d in sorted(holiday_dates):
    holiday_list.append({'holiday': 'official_holiday', 'ds': pd.Timestamp(d), 'lower_window': 0, 'upper_window': 0})
for d in workday_shift_dates:
    holiday_list.append({'holiday': 'workday_shift', 'ds': pd.Timestamp(d), 'lower_window': 0, 'upper_window': 0})
holiday_df = pd.DataFrame(holiday_list)
holiday_df.to_csv('4.2_feature_output/4.2_cycle_holidays.csv', index=False, encoding='utf-8-sig')

# 构造周期性特征表
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
feature_df.to_csv('4.2_feature_output/4.2_cycle_daily_features.csv', index=False, encoding='utf-8-sig')

print('周期性特征工程已完成，特征文件和节假日文件已输出到4.2_feature_output目录。')

# ========== 2. 基于最优分组特征的分组均值预测 ==========

# 读取刚生成的特征文件
feature_df = pd.read_csv('4.2_feature_output/4.2_cycle_daily_features.csv', parse_dates=['ds'])

# 聚合每日申购/赎回总额
agg = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
agg = agg.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# 合并特征
df = pd.merge(feature_df, agg, on='ds', how='left')

# 训练/预测区间
date_range = {
    'train_start': pd.to_datetime('2014-03-01'),
    'train_end': pd.to_datetime('2014-08-31'),
    'predict_start': pd.to_datetime('2014-09-01'),
    'predict_end': pd.to_datetime('2014-10-10'),
    'predict_csv_end': pd.to_datetime('2014-09-30')
}
train_df = df[(df['ds'] >= date_range['train_start']) & (df['ds'] <= date_range['train_end'])].copy()
predict_df = df[(df['ds'] >= date_range['predict_start']) & (df['ds'] <= date_range['predict_end'])].copy()

# 特征处理：调休补班日与普通工作日合并
predict_df['is_workday'] = (predict_df['is_holiday']==0).astype(int)
train_df['is_workday'] = (train_df['is_holiday']==0).astype(int)

# ========== 多级降级分组均值预测 ==========
group_cols = ['weekday', 'is_workday_shift']
group_mean = train_df.groupby(group_cols)[['purchase','redeem']].mean().reset_index()
group_mean_weekday = train_df.groupby(['weekday'])[['purchase','redeem']].mean().reset_index()

def predict_row(row):
    # 1. (weekday, is_workday_shift)
    match = group_mean[(group_mean['weekday']==row['weekday']) & (group_mean['is_workday_shift']==row['is_workday_shift'])]
    if not match.empty:
        return match.iloc[0]['purchase'], match.iloc[0]['redeem']
    # 2. (weekday)
    match = group_mean_weekday[(group_mean_weekday['weekday']==row['weekday'])]
    if not match.empty:
        return match.iloc[0]['purchase'], match.iloc[0]['redeem']
    # 3. 全局均值
    return train_df['purchase'].mean(), train_df['redeem'].mean()

# 对预测区间做预测
pred_purchase = []
pred_redeem = []
for _, row in predict_df.iterrows():
    p, r = predict_row(row)
    pred_purchase.append(p)
    pred_redeem.append(r)
predict_df['pred_purchase'] = np.round(pred_purchase).astype(int)
predict_df['pred_redeem'] = np.round(pred_redeem).astype(int)

# 输出预测结果csv（仅9月1日-9月30日）
output = predict_df[(predict_df['ds'] >= date_range['predict_start']) & (predict_df['ds'] <= date_range['predict_csv_end'])][['ds','pred_purchase','pred_redeem']].copy()
output['ds'] = output['ds'].dt.strftime('%Y%m%d')
output.to_csv('4.2_feature_output/4.2_cycle_groupmean_predict.csv', index=False, header=False, encoding='utf-8-sig')

print('基于最优分组特征的分组均值预测已完成，结果已输出到4.2_feature_output/4.2_cycle_groupmean_predict.csv。')

# ========== 3. 可视化真实值与预测值对比 ==========
# 画出2014-03-01~2014-09-30区间的真实值、in-sample预测、9月预测
full_df = df.copy()
full_df['pred_purchase'] = np.nan
full_df['pred_redeem'] = np.nan
# 训练区间in-sample预测
for idx, row in train_df.iterrows():
    p, r = predict_row(row)
    full_df.loc[full_df['ds']==row['ds'], 'pred_purchase'] = p
    full_df.loc[full_df['ds']==row['ds'], 'pred_redeem'] = r
# 预测区间预测
for idx, row in predict_df.iterrows():
    full_df.loc[full_df['ds']==row['ds'], 'pred_purchase'] = row['pred_purchase']
    full_df.loc[full_df['ds']==row['ds'], 'pred_redeem'] = row['pred_redeem']

plot_start = pd.to_datetime('2014-03-01')
plot_end = pd.to_datetime('2014-09-30')
plt.figure(figsize=(18,10))
fig, axes = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
# 申购
axes[0].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= date_range['train_end'])]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= date_range['train_end'])]['purchase'],
             label='申购真实值', color='blue')
axes[0].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= date_range['train_end'])]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= date_range['train_end'])]['pred_purchase'],
             label='申购in-sample预测', color='blue', linestyle='--')
axes[0].plot(full_df[(full_df['ds'] >= date_range['predict_start']) & (full_df['ds'] <= plot_end)]['ds'],
             full_df[(full_df['ds'] >= date_range['predict_start']) & (full_df['ds'] <= plot_end)]['pred_purchase'],
             label='申购9月预测', color='blue', linestyle=':')
axes[0].set_title('申购：真实值、in-sample预测与9月预测（最优分组+多级降级法）')
axes[0].legend()
# 赎回
axes[1].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= date_range['train_end'])]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= date_range['train_end'])]['redeem'],
             label='赎回真实值', color='green')
axes[1].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= date_range['train_end'])]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= date_range['train_end'])]['pred_redeem'],
             label='赎回in-sample预测', color='green', linestyle='--')
axes[1].plot(full_df[(full_df['ds'] >= date_range['predict_start']) & (full_df['ds'] <= plot_end)]['ds'],
             full_df[(full_df['ds'] >= date_range['predict_start']) & (full_df['ds'] <= plot_end)]['pred_redeem'],
             label='赎回9月预测', color='green', linestyle=':')
axes[1].set_title('赎回：真实值、in-sample预测与9月预测（最优分组+多级降级法）')
axes[1].legend()
plt.xlim([plot_start, plot_end])
plt.tight_layout()
plt.savefig('4.2_feature_output/4.2_cycle_groupmean_purchase_redeem_compare.png')
plt.close()
print('已输出真实值与预测值对比图：4.2_feature_output/4.2_cycle_groupmean_purchase_redeem_compare.png') 