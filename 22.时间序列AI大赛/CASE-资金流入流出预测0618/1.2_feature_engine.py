import pandas as pd
import numpy as np
import chinese_calendar
import os

# 创建输出目录
os.makedirs('1.2_feature_output', exist_ok=True)

# 1. 读取原始数据
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 2. 聚合每日申购/赎回总额
daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# 3. 极端异常点处理（可选：只对极端离群点做简单截断，也可不处理）
# 这里不做截断，保留原始波动

# 4. 生成Prophet输入格式（ds, y）
purchase_df = daily[['ds', 'purchase']].rename(columns={'purchase': 'y'})
redeem_df = daily[['ds', 'redeem']].rename(columns={'redeem': 'y'})
purchase_df.to_csv('1.2_feature_output/1.2_prophet_purchase.csv', index=False, encoding='utf-8-sig')
redeem_df.to_csv('1.2_feature_output/1.2_prophet_redeem.csv', index=False, encoding='utf-8-sig')

# 5. 生成节假日特征（is_holiday）
daily['is_holiday'] = daily['ds'].apply(lambda x: 1 if chinese_calendar.is_holiday(x) else 0)

# 6. 保存节假日特征表
daily[['ds', 'is_holiday']].to_csv('1.2_feature_output/1.2_prophet_daily_features.csv', index=False, encoding='utf-8-sig')

# 7. 生成Prophet假日表（官方节假日，供Prophet holidays参数用）
holiday_list = []
for d in daily['ds']:
    if chinese_calendar.is_holiday(d):
        holiday_list.append({'holiday': 'official_holiday', 'ds': d, 'lower_window': 0, 'upper_window': 0})
holiday_df = pd.DataFrame(holiday_list)
holiday_df.to_csv('1.2_feature_output/1.2_prophet_holidays.csv', index=False, encoding='utf-8-sig')

print('1.2极简特征工程已完成，结果保存在1.2_feature_output目录。') 