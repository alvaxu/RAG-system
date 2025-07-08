'''
4.1_cycle_groupmean_autotune.py
功能：
- 自动遍历周期因子分组组合（如weekday、month_period、is_holiday等），在验证集上选择RMSE最优分组。
- 训练集2014-03-01~2014-07-31，验证集2014-08-01~2014-08-31，预测区间2014-09-01~2014-09-30。
- 输出最优分组、验证集RMSE、9月预测结果、对比图。
- 便于周期因子分组均值法的自动调优。

最优分组特征: ('weekday', 'is_workday_shift')
验证集RMSE: 57368172.78 (申购: 53157275.72, 赎回: 61579069.85)
成绩：111.8994
'''

import pandas as pd
import numpy as np
import os
from datetime import date, timedelta
import itertools
import matplotlib.pyplot as plt
import matplotlib
from sklearn.metrics import mean_squared_error

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# ========== 1. 周期性特征工程（与4.0一致） ==========
os.makedirs('4.1_feature_output', exist_ok=True)

user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

holiday_dates = set()
holiday_spans = [
    (date(2014,4,5), date(2014,4,7)),
    (date(2014,5,1), date(2014,5,3)),
    (date(2014,5,31), date(2014,6,2)),
    (date(2014,9,6), date(2014,9,8)),
    (date(2014,10,1), date(2014,10,7)),
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
holiday_df.to_csv('4.1_feature_output/4.1_cycle_holidays.csv', index=False, encoding='utf-8-sig')

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
feature_df.to_csv('4.1_feature_output/4.1_cycle_daily_features.csv', index=False, encoding='utf-8-sig')

# ========== 2. 数据准备 ==========
feature_df = pd.read_csv('4.1_feature_output/4.1_cycle_daily_features.csv', parse_dates=['ds'])
agg = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
agg = agg.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})
df = pd.merge(feature_df, agg, on='ds', how='left')

# ========== 3. 自动调参 ==========
# 可选分组特征
all_factors = ['weekday','month_period','is_holiday','is_next_workday','is_workday_shift']
# 只考虑2~4个特征组合
factor_combos = []
for n in range(2,5):
    factor_combos += list(itertools.combinations(all_factors, n))

# 划分训练/验证/预测区间
train_start = pd.to_datetime('2014-03-01')
train_end = pd.to_datetime('2014-07-31')
val_start = pd.to_datetime('2014-08-01')
val_end = pd.to_datetime('2014-08-31')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')

train_df = df[(df['ds'] >= train_start) & (df['ds'] <= train_end)].copy()
val_df = df[(df['ds'] >= val_start) & (df['ds'] <= val_end)].copy()
predict_df = df[(df['ds'] >= predict_start) & (df['ds'] <= predict_end)].copy()

# 自动调参主循环
def groupmean_predict(train_df, val_df, group_cols):
    group_mean = train_df.groupby(list(group_cols))[['purchase','redeem']].mean().reset_index()
    def predict_row(row):
        match = group_mean
        for col in group_cols:
            match = match[match[col]==row[col]]
        if not match.empty:
            return match.iloc[0]['purchase'], match.iloc[0]['redeem']
        # 降级用全局均值
        return train_df['purchase'].mean(), train_df['redeem'].mean()
    pred_purchase, pred_redeem = [], []
    for _, row in val_df.iterrows():
        p, r = predict_row(row)
        pred_purchase.append(p)
        pred_redeem.append(r)
    return np.array(pred_purchase), np.array(pred_redeem)

best_combo = None
best_rmse = float('inf')
best_detail = None
for combo in factor_combos:
    pred_purchase, pred_redeem = groupmean_predict(train_df, val_df, combo)
    rmse_purchase = np.sqrt(mean_squared_error(val_df['purchase'], pred_purchase))
    rmse_redeem = np.sqrt(mean_squared_error(val_df['redeem'], pred_redeem))
    rmse = (rmse_purchase + rmse_redeem) / 2
    if rmse < best_rmse:
        best_rmse = rmse
        best_combo = combo
        best_detail = (rmse_purchase, rmse_redeem)
    print(f'分组特征: {combo}, 验证集RMSE: {rmse:.2f} (申购: {rmse_purchase:.2f}, 赎回: {rmse_redeem:.2f})')

print(f'最优分组特征: {best_combo}, 验证集RMSE: {best_rmse:.2f} (申购: {best_detail[0]:.2f}, 赎回: {best_detail[1]:.2f})')

# ========== 4. 用最优分组做9月预测 ==========
full_train_df = df[(df['ds'] >= train_start) & (df['ds'] <= val_end)].copy()
group_mean = full_train_df.groupby(list(best_combo))[['purchase','redeem']].mean().reset_index()
def predict_row_final(row):
    match = group_mean
    for col in best_combo:
        match = match[match[col]==row[col]]
    if not match.empty:
        return match.iloc[0]['purchase'], match.iloc[0]['redeem']
    return full_train_df['purchase'].mean(), full_train_df['redeem'].mean()
pred_purchase, pred_redeem = [], []
for _, row in predict_df.iterrows():
    p, r = predict_row_final(row)
    pred_purchase.append(p)
    pred_redeem.append(r)
predict_df['pred_purchase'] = np.round(pred_purchase).astype(int)
predict_df['pred_redeem'] = np.round(pred_redeem).astype(int)

# 输出预测结果csv（无表头）
output = predict_df[['ds','pred_purchase','pred_redeem']].copy()
output['ds'] = output['ds'].dt.strftime('%Y%m%d')
output.to_csv('4.1_feature_output/4.1_cycle_groupmean_predict.csv', index=False, header=False, encoding='utf-8-sig')

# ========== 5. 可视化真实值与预测值对比 ==========
full_df = df.copy()
full_df['pred_purchase'] = np.nan
full_df['pred_redeem'] = np.nan
# 训练+验证区间in-sample预测
for idx, row in full_train_df.iterrows():
    p, r = predict_row_final(row)
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
axes[0].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= val_end)]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= val_end)]['purchase'],
             label='申购真实值', color='blue')
axes[0].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= val_end)]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= val_end)]['pred_purchase'],
             label='申购in-sample预测', color='blue', linestyle='--')
axes[0].plot(full_df[(full_df['ds'] >= predict_start) & (full_df['ds'] <= plot_end)]['ds'],
             full_df[(full_df['ds'] >= predict_start) & (full_df['ds'] <= plot_end)]['pred_purchase'],
             label='申购9月预测', color='blue', linestyle=':')
axes[0].set_title('申购：真实值、in-sample预测与9月预测（自动调参分组均值法）')
axes[0].legend()
# 赎回
axes[1].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= val_end)]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= val_end)]['redeem'],
             label='赎回真实值', color='green')
axes[1].plot(full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= val_end)]['ds'],
             full_df[(full_df['ds'] >= plot_start) & (full_df['ds'] <= val_end)]['pred_redeem'],
             label='赎回in-sample预测', color='green', linestyle='--')
axes[1].plot(full_df[(full_df['ds'] >= predict_start) & (full_df['ds'] <= plot_end)]['ds'],
             full_df[(full_df['ds'] >= predict_start) & (full_df['ds'] <= plot_end)]['pred_redeem'],
             label='赎回9月预测', color='green', linestyle=':')
axes[1].set_title('赎回：真实值、in-sample预测与9月预测（自动调参分组均值法）')
axes[1].legend()
plt.xlim([plot_start, plot_end])
plt.tight_layout()
plt.savefig('4.1_feature_output/4.1_cycle_groupmean_purchase_redeem_compare.png')
plt.close()
print('最优分组特征:', best_combo)
print('验证集RMSE: %.2f (申购: %.2f, 赎回: %.2f)' % (best_rmse, best_detail[0], best_detail[1]))
print('已输出预测csv和对比图到4.1_feature_output目录。') 