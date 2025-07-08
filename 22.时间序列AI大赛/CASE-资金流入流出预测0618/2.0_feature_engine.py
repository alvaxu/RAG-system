import pandas as pd
import os

# 创建输出目录
os.makedirs('2.0_feature_output', exist_ok=True)

# 1. 读取原始数据
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 2. 聚合每日申购/赎回总额
daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# 补全所有日期，缺失的天用0填充
full_dates = pd.date_range(daily['ds'].min(), daily['ds'].max(), freq='D')
daily = daily.set_index('ds').reindex(full_dates).fillna(0).reset_index().rename(columns={'index': 'ds'})

# 3. 生成SARIMA输入格式（ds, y）
purchase_df = daily[['ds', 'purchase']].rename(columns={'purchase': 'y'})
redeem_df = daily[['ds', 'redeem']].rename(columns={'redeem': 'y'})
purchase_df.to_csv('2.0_feature_output/2.0_sarima_purchase.csv', index=False, encoding='utf-8-sig')
redeem_df.to_csv('2.0_feature_output/2.0_sarima_redeem.csv', index=False, encoding='utf-8-sig')

print('2.0特征工程已完成，结果保存在2.0_feature_output目录。') 