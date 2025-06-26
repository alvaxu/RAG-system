# 4.1_deep_tuning_residual_model.py
# 功能：基于最优分组均值法的残差建模（岭回归），输出预测csv、可视化图和实验日志
# 训练区间RMSE: 113855117.08 (申购: 51960681.09, 赎回: 61894435.99) 比4.0的最优组合训练区间RMSE=112069151.87差
# 不予采纳

import pandas as pd
import numpy as np
import os
from datetime import date, timedelta
import matplotlib.pyplot as plt
import matplotlib
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# ========== 1. 周期性特征工程 ==========
os.makedirs('4.1_deep_tuning_output', exist_ok=True)
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 显式定义节假日和调休补班日（与4.0一致）
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
holiday_df.to_csv('4.1_deep_tuning_output/4.1_deep_tuning_holidays.csv', index=False, encoding='utf-8-sig')

# 构造周期性特征表
feature_df = pd.DataFrame({'ds': pd.date_range('2014-03-01', '2014-10-10')})
feature_df['weekday'] = feature_df['ds'].dt.weekday
feature_df['month_period'] = feature_df['ds'].apply(lambda x: 'begin' if x.day<=10 else ('middle' if x.day<=20 else 'end'))
holiday_set = set(holiday_df[holiday_df['holiday']=='official_holiday']['ds'])
feature_df['is_holiday'] = feature_df['ds'].isin(holiday_set).astype(int)
workday_shift_set = set(holiday_df[holiday_df['holiday']=='workday_shift']['ds'])
feature_df['is_workday_shift'] = feature_df['ds'].isin(workday_shift_set).astype(int)
feature_df['is_next_workday'] = 0
for i in range(1, len(feature_df)):
    if feature_df.loc[i-1, 'is_holiday'] == 1 and feature_df.loc[i, 'is_holiday'] == 0:
        feature_df.loc[i, 'is_next_workday'] = 1
feature_df['is_month_end'] = feature_df['ds'].dt.is_month_end.astype(int)
feature_df['is_quarter_end'] = feature_df['ds'].dt.month.isin([3,6,9]).astype(int) & feature_df['ds'].dt.is_month_end.astype(int)
feature_df['is_festival_eve'] = 0
for i in range(1, len(feature_df)):
    if feature_df.loc[i, 'is_holiday']==1 and feature_df.loc[i-1, 'is_holiday']==0:
        feature_df.loc[i-1, 'is_festival_eve'] = 1
feature_df['holiday_len'] = 0
cur_len = 0
for i in range(len(feature_df)):
    if feature_df.loc[i, 'is_holiday'] == 1:
        cur_len += 1
        feature_df.loc[i, 'holiday_len'] = cur_len
    else:
        cur_len = 0
feature_df['is_long_holiday'] = (feature_df['holiday_len'] >= 3).astype(int)
feature_df.to_csv('4.1_deep_tuning_output/4.1_deep_tuning_daily_features.csv', index=False, encoding='utf-8-sig')

# ========== 2. 数据准备 ==========
agg = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
agg = agg.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})
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

# ========== 3. 最优分组均值法一阶预测 ==========
# 这里用实验3的分组因子（假设为weekday, month_period, is_holiday, is_next_workday, is_workday_shift）
group_cols = ['weekday', 'month_period', 'is_holiday', 'is_next_workday', 'is_workday_shift']
group_mean = train_df.groupby(group_cols)[['purchase','redeem']].mean().reset_index()

def predict_row(row):
    # 依次降级去掉最后一个分组因子
    for i in range(len(group_cols), 0, -1):
        cond = np.ones(len(group_mean), dtype=bool)
        for col in group_cols[:i]:
            cond = cond & (group_mean[col] == row[col])
        match = group_mean[cond]
        if not match.empty:
            return match.iloc[0]['purchase'], match.iloc[0]['redeem']
    # 最后用全局均值
    return train_df['purchase'].mean(), train_df['redeem'].mean()

# 一阶预测
train_df['pred_purchase'], train_df['pred_redeem'] = zip(*train_df.apply(predict_row, axis=1))
predict_df['pred_purchase'], predict_df['pred_redeem'] = zip(*predict_df.apply(predict_row, axis=1))

# ========== 4. 残差建模（岭回归） ==========
# 以周期特征为输入，残差为目标
feature_cols = ['weekday', 'month_period', 'is_holiday', 'is_next_workday', 'is_workday_shift',
                'is_month_end', 'is_quarter_end', 'is_festival_eve', 'holiday_len', 'is_long_holiday']
# month_period为类别特征，需独热编码
train_X = pd.get_dummies(train_df[feature_cols], columns=['month_period'])
predict_X = pd.get_dummies(predict_df[feature_cols], columns=['month_period'])
# 保证列一致
predict_X = predict_X.reindex(columns=train_X.columns, fill_value=0)

# 申购残差建模
purchase_residual = train_df['purchase'] - train_df['pred_purchase']
purchase_model = Ridge(alpha=1.0)
purchase_model.fit(train_X, purchase_residual)
purchase_residual_pred = purchase_model.predict(train_X)
purchase_residual_pred_predict = purchase_model.predict(predict_X)

# 赎回残差建模
redeem_residual = train_df['redeem'] - train_df['pred_redeem']
redeem_model = Ridge(alpha=1.0)
redeem_model.fit(train_X, redeem_residual)
redeem_residual_pred = redeem_model.predict(train_X)
redeem_residual_pred_predict = redeem_model.predict(predict_X)

# 二阶预测
train_df['final_purchase'] = train_df['pred_purchase'] + purchase_residual_pred
train_df['final_redeem'] = train_df['pred_redeem'] + redeem_residual_pred
predict_df['final_purchase'] = predict_df['pred_purchase'] + purchase_residual_pred_predict
predict_df['final_redeem'] = predict_df['pred_redeem'] + redeem_residual_pred_predict

# ========== 5. 评估与输出 ==========
# 训练区间RMSE
rmse_purchase = np.sqrt(mean_squared_error(train_df['purchase'], train_df['final_purchase']))
rmse_redeem = np.sqrt(mean_squared_error(train_df['redeem'], train_df['final_redeem']))
total_rmse = rmse_purchase + rmse_redeem

# 输出预测csv（仅9月1日-9月30日）
output = predict_df[(predict_df['ds'] >= date_range['predict_start']) & (predict_df['ds'] <= date_range['predict_csv_end'])][['ds','final_purchase','final_redeem']].copy()
output['ds'] = output['ds'].dt.strftime('%Y%m%d')
output['final_purchase'] = np.round(output['final_purchase']).astype(int)
output['final_redeem'] = np.round(output['final_redeem']).astype(int)
output.to_csv('4.1_deep_tuning_output/4.1_deep_tuning_predict.csv', index=False, header=False, encoding='utf-8-sig')

# 可视化
plot_start = pd.to_datetime('2014-03-01')
plot_end = pd.to_datetime('2014-09-30')
plt.figure(figsize=(18,10))
fig, axes = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
# 申购
axes[0].plot(train_df['ds'], train_df['purchase'], label='申购真实值', color='blue')
axes[0].plot(train_df['ds'], train_df['pred_purchase'], label='申购一阶预测', color='blue', linestyle='--')
axes[0].plot(train_df['ds'], train_df['final_purchase'], label='申购二阶预测', color='blue', linestyle=':')
axes[0].set_title('申购：真实值、一阶预测与二阶预测（残差建模）')
axes[0].legend()
# 赎回
axes[1].plot(train_df['ds'], train_df['redeem'], label='赎回真实值', color='green')
axes[1].plot(train_df['ds'], train_df['pred_redeem'], label='赎回一阶预测', color='green', linestyle='--')
axes[1].plot(train_df['ds'], train_df['final_redeem'], label='赎回二阶预测', color='green', linestyle=':')
axes[1].set_title('赎回：真实值、一阶预测与二阶预测（残差建模）')
axes[1].legend()
plt.xlim([plot_start, plot_end])
plt.tight_layout()
plt.savefig('4.1_deep_tuning_output/4.1_deep_tuning_compare.png')
plt.close()

# 输出实验日志
with open('4.1_deep_tuning_output/4.1_deep_tuning_experiment_log.txt', 'w', encoding='utf-8') as f:
    f.write(f"分组因子: {group_cols}\n")
    f.write(f"训练区间RMSE: {total_rmse:.2f}\n")
    f.write(f"申购RMSE: {rmse_purchase:.2f}\n")
    f.write(f"赎回RMSE: {rmse_redeem:.2f}\n")
    f.write(f"预测csv: 4.1_deep_tuning_output/4.1_deep_tuning_predict.csv\n")
    f.write(f"可视化图: 4.1_deep_tuning_output/4.1_deep_tuning_compare.png\n")
print(f'分组因子: {group_cols}')
print(f'训练区间RMSE: {total_rmse:.2f} (申购: {rmse_purchase:.2f}, 赎回: {rmse_redeem:.2f})')
print('预测csv: 4.1_deep_tuning_output/4.1_deep_tuning_predict.csv')
print('可视化图: 4.1_deep_tuning_output/4.1_deep_tuning_compare.png') 