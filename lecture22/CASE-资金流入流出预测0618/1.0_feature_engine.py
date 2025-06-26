import pandas as pd
import numpy as np
import chinese_calendar
import os

# 创建输出目录
os.makedirs('1.0_feature_output', exist_ok=True)

# 1. 读取原始数据
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 2. 聚合每日申购/赎回总额
daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# 3. 生成Prophet输入格式（ds, y）
purchase_df = daily[['ds', 'purchase']].rename(columns={'purchase': 'y'})
redeem_df = daily[['ds', 'redeem']].rename(columns={'redeem': 'y'})
purchase_df.to_csv('1.0_feature_output/1.0_prophet_purchase.csv', index=False, encoding='utf-8-sig')
redeem_df.to_csv('1.0_feature_output/1.0_prophet_redeem.csv', index=False, encoding='utf-8-sig')

def get_holiday_and_workday(start_date, end_date):
    """
    :function: 获取指定日期区间内的法定节假日和调休补班日
    :param start_date: 开始日期（字符串，YYYY-MM-DD）
    :param end_date: 结束日期（字符串，YYYY-MM-DD）
    :return: DataFrame，包含holiday, ds, lower_window, upper_window
    """
    dates = pd.date_range(start_date, end_date)
    holiday_list = []
    for d in dates:
        if chinese_calendar.is_holiday(d):
            holiday_list.append({'holiday': 'official_holiday', 'ds': d, 'lower_window': 0, 'upper_window': 0})
        elif chinese_calendar.is_workday(d) and d.weekday() >= 5:
            # 周末但被调为工作日
            holiday_list.append({'holiday': 'workday_shift', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    return pd.DataFrame(holiday_list)

# 4. 生成节假日和调休补班日特征
date_min = daily['ds'].min()
date_max = daily['ds'].max()
holiday_df = get_holiday_and_workday(date_min, date_max)
holiday_df.to_csv('1.0_feature_output/1.0_prophet_holidays.csv', index=False, encoding='utf-8-sig')

# 新增：生成是否节假日、是否调休补班日二值特征
holiday_set = set(holiday_df[holiday_df['holiday'] == 'official_holiday']['ds'])
workday_shift_set = set(holiday_df[holiday_df['holiday'] == 'workday_shift']['ds'])
daily['is_holiday'] = daily['ds'].isin(holiday_set).astype(int)
daily['is_workday_shift'] = daily['ds'].isin(workday_shift_set).astype(int)

# 5. 添加周几、月初/中/末等时间特征
daily['weekday'] = daily['ds'].dt.weekday  # 0=周一
# 月初/中/末：月初1-10，月中11-20，月末21号及以后
def month_period(day):
    d = day.day
    if d <= 10:
        return 'begin'
    elif d <= 20:
        return 'middle'
    else:
        return 'end'
daily['month_period'] = daily['ds'].apply(month_period)
daily.to_csv('1.0_feature_output/1.0_prophet_daily_features.csv', index=False, encoding='utf-8-sig')

print('特征工程已完成，结果保存在1.0_feature_output目录。') 