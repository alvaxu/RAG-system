'''
3.6_prophet_model.py
功能：
- 余额宝申购/赎回数据Prophet建模与预测（不做参数调优，直接用Prophet默认参数）。
- 节假日逻辑：凡因法定节假日而放假的所有连续日期都视为节假日，调休补班的周末视为工作日。
- 训练区间2014-03-01到2014-08-31，预测区间2014-09-01到2014-09-30。
- 输出分解图、残差图、9月预测结果、申购和赎回的实际与预测对比图（上下子图）。
- 申购和赎回均使用Prophet默认参数，参数如下：
  changepoint_prior_scale=0.05
  seasonality_prior_scale=10.0
  holidays_prior_scale=10.0
  seasonality_mode='additive'
  yearly_seasonality=True
  weekly_seasonality=True
  daily_seasonality=False
- 不引入外部变量。

成绩：51.6182 与自动调参相比，成绩明显不好。
'''

import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import chinese_calendar
import os
import matplotlib
import logging
import warnings

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('3.6_prophet_output', exist_ok=True)
os.makedirs('3.6_feature_output', exist_ok=True)

# 屏蔽所有debug、info和warning，只保留error及fatal error
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
warnings.filterwarnings('ignore')
for logger_name in ['prophet', 'cmdstanpy', 'matplotlib', 'pandas', 'numpy']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = False
plt.set_loglevel('error')

def main():
    # 1. 读取原始数据
    user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
    user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

    # 2. 聚合每日申购/赎回总额
    daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
    daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

    # 3. 生成Prophet输入格式（ds, y）
    purchase_df = daily[['ds', 'purchase']].rename(columns={'purchase': 'y'})
    redeem_df = daily[['ds', 'redeem']].rename(columns={'redeem': 'y'})
    purchase_df.to_csv('3.6_feature_output/3.6_prophet_purchase.csv', index=False, encoding='utf-8-sig')
    redeem_df.to_csv('3.6_feature_output/3.6_prophet_redeem.csv', index=False, encoding='utf-8-sig')

    # 4. 生成2014-03-01到2014-09-30的节假日和调休补班日（新逻辑）
    holiday_dates = pd.date_range('2014-03-01', '2014-09-30')
    holiday_list = []
    all_holidays = []
    cur_holiday = []
    for d in holiday_dates:
        if chinese_calendar.is_holiday(d):
            cur_holiday.append(d)
        else:
            if len(cur_holiday) > 0:
                all_holidays.append(cur_holiday)
                cur_holiday = []
    if len(cur_holiday) > 0:
        all_holidays.append(cur_holiday)
    for holiday_span in all_holidays:
        for d in holiday_span:
            holiday_list.append({'holiday': 'official_holiday', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    for d in holiday_dates:
        if chinese_calendar.is_workday(d) and d.weekday() >= 5:
            holiday_list.append({'holiday': 'workday_shift', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    holiday_df = pd.DataFrame(holiday_list)
    holiday_df.to_csv('3.6_feature_output/3.6_prophet_holidays.csv', index=False, encoding='utf-8-sig')

    # 5. 特征工程优化
    holiday_set = set(holiday_df[holiday_df['holiday'] == 'official_holiday']['ds'])
    daily['is_holiday'] = daily['ds'].isin(holiday_set).astype(int)
    workday_shift_set = set(holiday_df[holiday_df['holiday'] == 'workday_shift']['ds'])
    daily['is_workday_shift'] = daily['ds'].isin(workday_shift_set).astype(int)
    daily = daily.sort_values('ds').reset_index(drop=True)
    daily['is_next_workday'] = 0
    for i in range(1, len(daily)):
        if daily.loc[i-1, 'is_holiday'] == 1 and daily.loc[i, 'is_holiday'] == 0:
            daily.loc[i, 'is_next_workday'] = 1
    def month_period(day):
        d = day.day
        if d <= 10:
            return 'begin'
        elif d <= 20:
            return 'middle'
        else:
            return 'end'
    daily['weekday'] = daily['ds'].dt.weekday
    daily['month_period'] = daily['ds'].apply(month_period)
    daily.to_csv('3.6_feature_output/3.6_prophet_daily_features.csv', index=False, encoding='utf-8-sig')

    # 6. 训练区间、预测区间
    train_start = pd.to_datetime('2014-03-01')
    train_end = pd.to_datetime('2014-08-31')
    predict_start = pd.to_datetime('2014-09-01')
    predict_end = pd.to_datetime('2014-09-30')

    purchase_df = pd.read_csv('3.6_feature_output/3.6_prophet_purchase.csv', parse_dates=['ds'])
    redeem_df = pd.read_csv('3.6_feature_output/3.6_prophet_redeem.csv', parse_dates=['ds'])
    holidays = pd.read_csv('3.6_feature_output/3.6_prophet_holidays.csv', parse_dates=['ds'])

    purchase_train = purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]
    redeem_train = redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]
    all_dates = pd.date_range(train_start, predict_end)
    predict_dates = pd.date_range(predict_start, predict_end)

    # 7. Prophet建模与预测（默认参数）
    print('申购Prophet默认参数:')
    print('  changepoint_prior_scale=0.05')
    print('  seasonality_prior_scale=10.0')
    print('  holidays_prior_scale=10.0')
    print("  seasonality_mode='additive'")
    print('  yearly_seasonality=True')
    print('  weekly_seasonality=True')
    print('  daily_seasonality=False')
    purchase_model = Prophet(
        holidays=holidays,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    purchase_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    purchase_model.fit(purchase_train)
    future_purchase = pd.DataFrame({'ds': all_dates})
    purchase_forecast = purchase_model.predict(future_purchase)
    # 分解图
    fig = purchase_model.plot_components(purchase_forecast)
    plt.savefig('3.6_prophet_output/3.6_prophet_purchase_components.png')
    plt.close()

    print('赎回Prophet默认参数:')
    print('  changepoint_prior_scale=0.05')
    print('  seasonality_prior_scale=10.0')
    print('  holidays_prior_scale=10.0')
    print("  seasonality_mode='additive'")
    print('  yearly_seasonality=True')
    print('  weekly_seasonality=True')
    print('  daily_seasonality=False')
    redeem_model = Prophet(
        holidays=holidays,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    redeem_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    redeem_model.fit(redeem_train)
    future_redeem = pd.DataFrame({'ds': all_dates})
    redeem_forecast = redeem_model.predict(future_redeem)
    fig = redeem_model.plot_components(redeem_forecast)
    plt.savefig('3.6_prophet_output/3.6_prophet_redeem_components.png')
    plt.close()

    # 8. 可视化：上下两个子图分别展示申购和赎回的实际与预测
    fig, axes = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
    axes[0].plot(purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['ds'],
                 purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['y'],
                 label='申购真实值', color='blue')
    axes[0].plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'],
                 purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'],
                 label='申购in-sample预测', color='blue', linestyle='--')
    axes[0].plot(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'],
                 purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat'],
                 label='申购9月预测', color='blue', linestyle=':')
    axes[0].set_title('申购：真实值、in-sample预测与9月预测')
    axes[0].legend()
    axes[1].plot(redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['ds'],
                 redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['y'],
                 label='赎回真实值', color='green')
    axes[1].plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'],
                 redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'],
                 label='赎回in-sample预测', color='green', linestyle='--')
    axes[1].plot(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['ds'],
                 redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat'],
                 label='赎回9月预测', color='green', linestyle=':')
    axes[1].set_title('赎回：真实值、in-sample预测与9月预测')
    axes[1].legend()
    plt.xlim([train_start, predict_end])
    plt.tight_layout()
    plt.savefig('3.6_prophet_output/3.6_prophet_purchase_redeem_compare.png')
    plt.close()

    # 9. 残差分析
    real_purchase = purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['y'].values
    pred_purchase = purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'].values
    residuals_purchase = real_purchase - pred_purchase
    plt.figure(figsize=(12,4))
    plt.plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'], residuals_purchase)
    plt.title('申购残差分析（真实值-预测值）')
    plt.axhline(0, color='red', linestyle='--')
    plt.savefig('3.6_prophet_output/3.6_prophet_purchase_residuals.png')
    plt.close()
    real_redeem = redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['y'].values
    pred_redeem = redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'].values
    residuals_redeem = real_redeem - pred_redeem
    plt.figure(figsize=(12,4))
    plt.plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'], residuals_redeem)
    plt.title('赎回残差分析（真实值-预测值）')
    plt.axhline(0, color='red', linestyle='--')
    plt.savefig('3.6_prophet_output/3.6_prophet_redeem_residuals.png')
    plt.close()

    # 10. 输出9月预测结果为竞赛格式
    predict_df = pd.DataFrame({
        'report_date': purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'].dt.strftime('%Y%m%d'),
        'purchase': np.round(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat']).astype(int),
        'redeem': np.round(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat']).astype(int)
    })
    predict_df.to_csv('3.6_prophet_output/3.6_prophet_predict.csv', index=False, header=False, encoding='utf-8-sig')

    print('Prophet默认参数建模、分解图与残差分析已完成，结果保存在3.6_prophet_output目录。')

if __name__ == '__main__':
    main() 