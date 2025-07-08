# 4.0_deep_tuning_groupmean_split_purchase_redeem.py
# 功能：申购和赎回分别做周期因子全组合实验（各自1~3个因子的所有组合），输出最优分组及日志
# 作者：AI助手
# 日期：2024-06-18

# ========== 最优分组因子方案 ==========
# 最优实验ID: 38326
# 申购分组因子: weekday|month_period|is_next_workday|is_month_end|holiday_len
# 赎回分组因子: weekday|month_period|is_next_workday|is_month_end|holiday_len
# 训练区间RMSE: 111972410.08

# 最终说明申购和赎回的最优分组因子方案和前面的一样，对于分组因子，已经难以再调优。

import pandas as pd
import numpy as np
import os
from datetime import date, timedelta
from itertools import combinations
from sklearn.metrics import mean_squared_error

"""
:函数: 主流程
:参数: 无
:返回: 无
"""

def main():
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

    # ========== 2. 数据准备 ==========
    agg = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
    agg = agg.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})
    df = pd.merge(feature_df, agg, on='ds', how='left')

    # 训练区间
    date_range = {
        'train_start': pd.to_datetime('2014-03-01'),
        'train_end': pd.to_datetime('2014-08-31'),
    }
    train_df = df[(df['ds'] >= date_range['train_start']) & (df['ds'] <= date_range['train_end'])].copy()

    # ========== 3. 分开全组合实验 ==========
    all_factors = [
        'weekday', 'month_period', 'is_holiday', 'is_next_workday', 'is_workday_shift',
        'is_month_end',  'holiday_len', 'is_long_holiday'
    ]
    max_k = 5  # 只做1~3个因子的组合，防止组合数过多
    log_list = []
    exp_id = 1
    for k1 in range(1, max_k+1):
        for purchase_cols in combinations(all_factors, k1):
            purchase_cols = list(purchase_cols)
            purchase_group_mean = train_df.groupby(purchase_cols)[['purchase']].mean().reset_index()
            def predict_purchase(row):
                for i in range(len(purchase_cols), 0, -1):
                    cond = np.ones(len(purchase_group_mean), dtype=bool)
                    for col in purchase_cols[:i]:
                        cond = cond & (purchase_group_mean[col] == row[col])
                    match = purchase_group_mean[cond]
                    if not match.empty:
                        return match.iloc[0]['purchase']
                return train_df['purchase'].mean()
            pred_purchase = train_df.apply(predict_purchase, axis=1)
            rmse_purchase = np.sqrt(mean_squared_error(train_df['purchase'], pred_purchase))

            for k2 in range(1, max_k+1):
                for redeem_cols in combinations(all_factors, k2):
                    redeem_cols = list(redeem_cols)
                    redeem_group_mean = train_df.groupby(redeem_cols)[['redeem']].mean().reset_index()
                    def predict_redeem(row):
                        for i in range(len(redeem_cols), 0, -1):
                            cond = np.ones(len(redeem_group_mean), dtype=bool)
                            for col in redeem_cols[:i]:
                                cond = cond & (redeem_group_mean[col] == row[col])
                            match = redeem_group_mean[cond]
                            if not match.empty:
                                return match.iloc[0]['redeem']
                        return train_df['redeem'].mean()
                    pred_redeem = train_df.apply(predict_redeem, axis=1)
                    rmse_redeem = np.sqrt(mean_squared_error(train_df['redeem'], pred_redeem))
                    total_rmse = rmse_purchase + rmse_redeem
                    log_list.append({
                        'experiment_id': exp_id,
                        'purchase_cols': '|'.join(purchase_cols),
                        'redeem_cols': '|'.join(redeem_cols),
                        'rmse_purchase': rmse_purchase,
                        'rmse_redeem': rmse_redeem,
                        'total_rmse': total_rmse
                    })
                    if exp_id % 100 == 0:
                        print(f'已完成{exp_id}组实验...')
                    exp_id += 1

    # 输出实验日志
    log_df = pd.DataFrame(log_list)
    log_df.to_csv('4.0_deep_tuning_output/4.0_deep_tuning_split_purchase_redeem_log.csv', index=False, encoding='utf-8-sig')

    # 输出最优方案
    best_row = log_df.loc[log_df['total_rmse'].idxmin()]
    print('\n========== 最优分组因子方案 ==========')
    print(f"最优实验ID: {best_row['experiment_id']}")
    print(f"申购分组因子: {best_row['purchase_cols']}")
    print(f"赎回分组因子: {best_row['redeem_cols']}")
    print(f"训练区间RMSE: {best_row['total_rmse']:.2f}")

    with open('4.0_deep_tuning_output/4.0_deep_tuning_split_purchase_redeem_best_result.txt', 'w', encoding='utf-8') as f:
        f.write('========== 最优分组因子方案 ==========\n')
        f.write(f"最优实验ID: {best_row['experiment_id']}\n")
        f.write(f"申购分组因子: {best_row['purchase_cols']}\n")
        f.write(f"赎回分组因子: {best_row['redeem_cols']}\n")
        f.write(f"训练区间RMSE: {best_row['total_rmse']:.2f}\n")

    print('\n所有实验已完成，实验日志已输出到4.0_deep_tuning_output/4.0_deep_tuning_split_purchase_redeem_log.csv')

if __name__ == '__main__':
    main()