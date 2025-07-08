# # 4.0_deep_tuning_groupmean_experiments.py
# # 功能：自动化分组因子增强实验，遍历所有分组特征组合，输出每次实验的分数、预测csv和可视化图
# 该脚本会自动遍历所有分组特征组合（每次加一个新特征），依次完成：
# 特征工程
# 分组均值法预测（多级降级）
# 计算训练区间RMSE分数
# 输出每次实验的预测csv和可视化图（每次实验一张图，两个子图）
# 记录所有实验的特征组合与分数到实验日志csv
# ========== 最优分组因子方案 ==========
# 最优实验ID: 3
# 分组因子: weekday|month_period|is_holiday|is_next_workday|is_month_end
# 训练区间RMSE: 112069151.87
# 预测csv: 4.0_deep_tuning_output/4.0_deep_tuning_predict_3.csv
# 可视化图: 4.0_deep_tuning_output/4.0_deep_tuning_compare_3.png
# 最终分数为124.5645分

import pandas as pd
import numpy as np
import os
from datetime import date, timedelta
import matplotlib.pyplot as plt
import matplotlib
from itertools import combinations

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# ========== 1. 周期性特征工程 ==========
os.makedirs('4.0_deep_tuning_output', exist_ok=True)
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
holiday_df.to_csv('4.0_deep_tuning_output/4.0_deep_tuning_holidays.csv', index=False, encoding='utf-8-sig')

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

# 新增周期特征
feature_df['is_month_end'] = feature_df['ds'].dt.is_month_end.astype(int)
feature_df['is_quarter_end'] = feature_df['ds'].dt.month.isin([3,6,9]).astype(int) & feature_df['ds'].dt.is_month_end.astype(int)
# 节前一天
feature_df['is_festival_eve'] = 0
for i in range(1, len(feature_df)):
    if feature_df.loc[i, 'is_holiday']==1 and feature_df.loc[i-1, 'is_holiday']==0:
        feature_df.loc[i-1, 'is_festival_eve'] = 1
# 假期长度
feature_df['holiday_len'] = 0
cur_len = 0
for i in range(len(feature_df)):
    if feature_df.loc[i, 'is_holiday'] == 1:
        cur_len += 1
        feature_df.loc[i, 'holiday_len'] = cur_len
    else:
        cur_len = 0
# 是否长假
feature_df['is_long_holiday'] = (feature_df['holiday_len'] >= 3).astype(int)

feature_df.to_csv('4.0_deep_tuning_output/4.0_deep_tuning_daily_features.csv', index=False, encoding='utf-8-sig')

# ========== 2. 自动化实验主流程 ==========
# 所有可选分组特征
base_cols = ['weekday', 'month_period', 'is_holiday', 'is_next_workday']
extra_cols = ['is_workday_shift', 'is_month_end', 'is_quarter_end', 'is_festival_eve', 'holiday_len', 'is_long_holiday']

# 只做单一增强实验（每次加一个新特征），如需多特征组合可自行扩展
all_experiments = [base_cols] + [base_cols + [col] for col in extra_cols]

# 读取数据
agg = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
agg = agg.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})
df = pd.merge(feature_df, agg, on='ds', how='left')

date_range = {
    'train_start': pd.to_datetime('2014-03-01'),
    'train_end': pd.to_datetime('2014-08-31'),
    'predict_start': pd.to_datetime('2014-09-01'),
    'predict_end': pd.to_datetime('2014-10-10'),
    'predict_csv_end': pd.to_datetime('2014-09-30')
}
train_df = df[(df['ds'] >= date_range['train_start']) & (df['ds'] <= date_range['train_end'])].copy()
predict_df = df[(df['ds'] >= date_range['predict_start']) & (df['ds'] <= date_range['predict_end'])].copy()

# 记录实验结果
log_list = []

for idx, group_cols in enumerate(all_experiments):
    print(f'\n==== 实验{idx+1}: 分组因子 {group_cols} ====')
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

    # 预测
    pred_purchase = []
    pred_redeem = []
    for _, row in predict_df.iterrows():
        p, r = predict_row(row)
        pred_purchase.append(p)
        pred_redeem.append(r)
    predict_df['pred_purchase'] = np.round(pred_purchase).astype(int)
    predict_df['pred_redeem'] = np.round(pred_redeem).astype(int)

    # 训练区间in-sample预测
    full_df = df.copy()
    full_df['pred_purchase'] = np.nan
    full_df['pred_redeem'] = np.nan
    for _, row in train_df.iterrows():
        p, r = predict_row(row)
        full_df.loc[full_df['ds']==row['ds'], 'pred_purchase'] = p
        full_df.loc[full_df['ds']==row['ds'], 'pred_redeem'] = r
    for _, row in predict_df.iterrows():
        full_df.loc[full_df['ds']==row['ds'], 'pred_purchase'] = row['pred_purchase']
        full_df.loc[full_df['ds']==row['ds'], 'pred_redeem'] = row['pred_redeem']

    # 计算训练区间RMSE
    from sklearn.metrics import mean_squared_error
    train_real_purchase = train_df['purchase'].values
    train_pred_purchase = full_df[(full_df['ds'] >= date_range['train_start']) & (full_df['ds'] <= date_range['train_end'])]['pred_purchase'].values
    train_real_redeem = train_df['redeem'].values
    train_pred_redeem = full_df[(full_df['ds'] >= date_range['train_start']) & (full_df['ds'] <= date_range['train_end'])]['pred_redeem'].values
    rmse_purchase = np.sqrt(mean_squared_error(train_real_purchase, train_pred_purchase))
    rmse_redeem = np.sqrt(mean_squared_error(train_real_redeem, train_pred_redeem))
    total_rmse = rmse_purchase + rmse_redeem

    # 输出预测csv
    output = predict_df[(predict_df['ds'] >= date_range['predict_start']) & (predict_df['ds'] <= date_range['predict_csv_end'])][['ds','pred_purchase','pred_redeem']].copy()
    output['ds'] = output['ds'].dt.strftime('%Y%m%d')
    csv_name = f'4.0_deep_tuning_output/4.0_deep_tuning_predict_{idx+1}.csv'
    output.to_csv(csv_name, index=False, header=False, encoding='utf-8-sig')

    # 可视化
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
    axes[0].set_title(f'申购：真实值、in-sample预测与9月预测（分组因子: {group_cols}）')
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
    axes[1].set_title(f'赎回：真实值、in-sample预测与9月预测（分组因子: {group_cols}）')
    axes[1].legend()
    plt.xlim([plot_start, plot_end])
    plt.tight_layout()
    fig_name = f'4.0_deep_tuning_output/4.0_deep_tuning_compare_{idx+1}.png'
    plt.savefig(fig_name)
    plt.close()
    print(f'输出：{csv_name}，{fig_name}，训练区间RMSE={total_rmse:.2f}')

    # 记录日志
    log_list.append({
        'experiment_id': idx+1,
        'group_cols': '|'.join(group_cols),
        'rmse_purchase': rmse_purchase,
        'rmse_redeem': rmse_redeem,
        'total_rmse': total_rmse,
        'csv': csv_name,
        'fig': fig_name
    })

# 输出实验日志
log_df = pd.DataFrame(log_list)
log_df.to_csv('4.0_deep_tuning_output/4.0_deep_tuning_experiment_log.csv', index=False, encoding='utf-8-sig')

# ========== 输出最优方案结论 ==========
best_row = log_df.loc[log_df['total_rmse'].idxmin()]
print('\n========== 最优分组因子方案 ==========')
print(f"最优实验ID: {best_row['experiment_id']}")
print(f"分组因子: {best_row['group_cols']}")
print(f"训练区间RMSE: {best_row['total_rmse']:.2f}")
print(f"预测csv: {best_row['csv']}")
print(f"可视化图: {best_row['fig']}")

# 也写入日志文件
with open('4.0_deep_tuning_output/4.0_deep_tuning_best_result.txt', 'w', encoding='utf-8') as f:
    f.write('========== 最优分组因子方案 ==========\n')
    f.write(f"最优实验ID: {best_row['experiment_id']}\n")
    f.write(f"分组因子: {best_row['group_cols']}\n")
    f.write(f"训练区间RMSE: {best_row['total_rmse']:.2f}\n")
    f.write(f"预测csv: {best_row['csv']}\n")
    f.write(f"可视化图: {best_row['fig']}\n")

print('\n所有实验已完成，实验日志已输出到4.0_deep_tuning_output/4.0_deep_tuning_experiment_log.csv')