'''
4.0_cycle_feature_engine.py
功能：
- 读取余额宝申购/赎回原始数据，提取周期性特征。
- 周期性特征包括：weekday（月/周/节假日/调休）、month_period、is_holiday、is_workday_shift、is_next_workday等。
- 节假日和调休补班日全部手工指定（与3.7.1一致）。
- 输出特征文件和节假日文件，供后续周期因子建模使用。
'''

import pandas as pd
import numpy as np
import os
from datetime import date, timedelta

# 创建输出目录
os.makedirs('4.0_feature_output', exist_ok=True)

# 1. 读取原始数据
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 2. 聚合每日申购/赎回总额
# 这里只做特征工程，后续建模可再聚合
all_dates = pd.date_range('2014-03-01', '2014-10-10')

# 3. 显式定义节假日和调休补班日（与3.7.1一致）
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
holiday_df.to_csv('4.0_feature_output/4.0_cycle_holidays.csv', index=False, encoding='utf-8-sig')

# 4. 构造周期性特征表
feature_df = pd.DataFrame({'ds': pd.date_range('2014-03-01', '2014-10-10')})
feature_df['weekday'] = feature_df['ds'].dt.weekday
# 月初/中/末
feature_df['month_period'] = feature_df['ds'].apply(lambda x: 'begin' if x.day<=10 else ('middle' if x.day<=20 else 'end'))
# 是否节假日
holiday_set = set(holiday_df[holiday_df['holiday']=='official_holiday']['ds'])
feature_df['is_holiday'] = feature_df['ds'].isin(holiday_set).astype(int)
# 是否调休补班
workday_shift_set = set(holiday_df[holiday_df['holiday']=='workday_shift']['ds'])
feature_df['is_workday_shift'] = feature_df['ds'].isin(workday_shift_set).astype(int)
# 是否节后首个工作日
df = feature_df
feature_df['is_next_workday'] = 0
for i in range(1, len(df)):
    if df.loc[i-1, 'is_holiday'] == 1 and df.loc[i, 'is_holiday'] == 0:
        feature_df.loc[i, 'is_next_workday'] = 1
# 输出特征文件
feature_df.to_csv('4.0_feature_output/4.0_cycle_daily_features.csv', index=False, encoding='utf-8-sig')

print('周期性特征工程已完成，特征文件和节假日文件已输出到4.0_feature_output目录。') 