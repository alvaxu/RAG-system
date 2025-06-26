import pandas as pd
import numpy as np
import chinese_calendar
import os

# 创建输出目录
os.makedirs('1.1_feature_output', exist_ok=True)

# 1. 读取原始数据
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 2. 聚合每日申购/赎回总额
daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# 3. 极端异常点处理：只对明显异常点做处理，保留大部分真实波动
for col in ['purchase', 'redeem']:
    max_val = daily[col].max()
    threshold = max_val * 2  # 超过历史最大值2倍的点视为异常
    daily[col] = np.where(daily[col] > threshold, threshold, daily[col])

# 4. 生成Prophet输入格式（ds, y）
purchase_df = daily[['ds', 'purchase']].rename(columns={'purchase': 'y'})
redeem_df = daily[['ds', 'redeem']].rename(columns={'redeem': 'y'})
purchase_df.to_csv('1.1_feature_output/1.1_prophet_purchase.csv', index=False, encoding='utf-8-sig')
redeem_df.to_csv('1.1_feature_output/1.1_prophet_redeem.csv', index=False, encoding='utf-8-sig')

def get_holiday_and_workday(start_date, end_date):
    dates = pd.date_range(start_date, end_date)
    holiday_list = []
    for d in dates:
        if chinese_calendar.is_holiday(d):
            holiday_list.append({'holiday': 'official_holiday', 'ds': d, 'lower_window': 0, 'upper_window': 0})
        elif chinese_calendar.is_workday(d) and d.weekday() >= 5:
            holiday_list.append({'holiday': 'workday_shift', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    return pd.DataFrame(holiday_list)

# 5. 生成节假日和调休补班日特征
date_min = daily['ds'].min()
date_max = daily['ds'].max()
holiday_df = get_holiday_and_workday(date_min, date_max)
holiday_df.to_csv('1.1_feature_output/1.1_prophet_holidays.csv', index=False, encoding='utf-8-sig')

# 新增：生成是否节假日、是否调休补班日二值特征
holiday_set = set(holiday_df[holiday_df['holiday'] == 'official_holiday']['ds'])
workday_shift_set = set(holiday_df[holiday_df['holiday'] == 'workday_shift']['ds'])
daily['is_holiday'] = daily['ds'].isin(holiday_set).astype(int)
daily['is_workday_shift'] = daily['ds'].isin(workday_shift_set).astype(int)

# 新增：节前/节后N天特征（如3天）
N = 3
daily['is_before_holiday'] = 0
daily['is_after_holiday'] = 0
holiday_days = sorted(list(holiday_set))
for h in holiday_days:
    for i in range(1, N+1):
        before = h - pd.Timedelta(days=i)
        after = h + pd.Timedelta(days=i)
        if before in daily['ds'].values:
            daily.loc[daily['ds'] == before, 'is_before_holiday'] = 1
        if after in daily['ds'].values:
            daily.loc[daily['ds'] == after, 'is_after_holiday'] = 1

# 6. 添加周几、月初/中/末等时间特征
daily['weekday'] = daily['ds'].dt.weekday  # 0=周一
def month_period(day):
    d = day.day
    if d <= 10:
        return 'begin'
    elif d <= 20:
        return 'middle'
    else:
        return 'end'
daily['month_period'] = daily['ds'].apply(month_period)

# 7. 外部特征：收益率、利率
interest = pd.read_csv('mfd_day_share_interest.csv', encoding='utf-8')
interest['mfd_date'] = pd.to_datetime(interest['mfd_date'], format='%Y%m%d')
shibor = pd.read_csv('mfd_bank_shibor.csv', encoding='utf-8')
shibor['mfd_date'] = pd.to_datetime(shibor['mfd_date'], format='%Y%m%d')
# 合并到daily
daily = daily.merge(interest[['mfd_date','mfd_daily_yield','mfd_7daily_yield']], left_on='ds', right_on='mfd_date', how='left')
daily = daily.merge(shibor[['mfd_date','Interest_O_N']], left_on='ds', right_on='mfd_date', how='left')
daily = daily.drop(['mfd_date_x','mfd_date_y'], axis=1)

# 明确补全日期范围，覆盖到2014-09-30
full_dates = pd.date_range(daily['ds'].min(), '2014-09-30')
daily = daily.set_index('ds').reindex(full_dates).reset_index().rename(columns={'index': 'ds'})

# 再次填充所有特征
for col in ['is_holiday', 'is_workday_shift', 'is_before_holiday', 'is_after_holiday',
            'mfd_daily_yield', 'mfd_7daily_yield', 'Interest_O_N']:
    daily[col] = daily[col].fillna(method='ffill')
    daily[col] = daily[col].fillna(method='bfill')
    daily[col] = daily[col].fillna(0)

# 保存前检查是否还有NaN
if daily[['is_holiday', 'is_workday_shift', 'is_before_holiday', 'is_after_holiday',
          'mfd_daily_yield', 'mfd_7daily_yield', 'Interest_O_N']].isnull().any().any():
    print('警告：特征表仍有NaN，请检查！')
else:
    print('特征表无NaN，安全！')

daily.to_csv('1.1_feature_output/1.1_prophet_daily_features.csv', index=False, encoding='utf-8-sig')

print('1.1特征工程已完成，结果保存在1.1_feature_output目录。') 