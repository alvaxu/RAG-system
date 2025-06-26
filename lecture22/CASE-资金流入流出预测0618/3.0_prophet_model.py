import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import chinese_calendar
import os
import matplotlib

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('3.0_prophet_output', exist_ok=True)
os.makedirs('3.0_feature_output', exist_ok=True)

# 1. 读取原始数据
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 2. 聚合每日申购/赎回总额
# ... existing code ...
daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
daily = daily.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# 3. 生成Prophet输入格式（ds, y）
purchase_df = daily[['ds', 'purchase']].rename(columns={'purchase': 'y'})
redeem_df = daily[['ds', 'redeem']].rename(columns={'redeem': 'y'})
purchase_df.to_csv('3.0_feature_output/3.0_prophet_purchase.csv', index=False, encoding='utf-8-sig')
redeem_df.to_csv('3.0_feature_output/3.0_prophet_redeem.csv', index=False, encoding='utf-8-sig')

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
# 只用2014-03-01到2014-09-30的节假日
holiday_df = get_holiday_and_workday('2014-03-01', '2014-09-30')
holiday_df.to_csv('3.0_feature_output/3.0_prophet_holidays.csv', index=False, encoding='utf-8-sig')

# 新增：生成是否节假日、是否调休补班日二值特征
holiday_set = set(holiday_df[holiday_df['holiday'] == 'official_holiday']['ds'])
workday_shift_set = set(holiday_df[holiday_df['holiday'] == 'workday_shift']['ds'])
daily['is_holiday'] = daily['ds'].isin(holiday_set).astype(int)
daily['is_workday_shift'] = daily['ds'].isin(workday_shift_set).astype(int)

def month_period(day):
    d = day.day
    if d <= 10:
        return 'begin'
    elif d <= 20:
        return 'middle'
    else:
        return 'end'
daily['weekday'] = daily['ds'].dt.weekday
# 月初/中/末：月初1-10，月中11-20，月末21号及以后
daily['month_period'] = daily['ds'].apply(month_period)
daily.to_csv('3.0_feature_output/3.0_prophet_daily_features.csv', index=False, encoding='utf-8-sig')

# 打印2014年端午节节假日
print('2014年端午节节假日:')
dragon_boat_2014 = [d for d in holiday_set if pd.Timestamp('2014-05-30') <= d <= pd.Timestamp('2014-06-02')]
print(dragon_boat_2014)

# 5. Prophet建模与预测
train_start = pd.to_datetime('2014-03-01')
train_end = pd.to_datetime('2014-08-31')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')

purchase_df = pd.read_csv('3.0_feature_output/3.0_prophet_purchase.csv', parse_dates=['ds'])
redeem_df = pd.read_csv('3.0_feature_output/3.0_prophet_redeem.csv', parse_dates=['ds'])
holidays = pd.read_csv('3.0_feature_output/3.0_prophet_holidays.csv', parse_dates=['ds'])

# 训练集
purchase_train = purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]
redeem_train = redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]

# 预测区间
all_dates = pd.date_range(train_start, predict_end)
predict_dates = pd.date_range(predict_start, predict_end)

# Prophet建模与in-sample+out-of-sample预测
def prophet_predict(train_df, holidays, all_dates, label):
    m = Prophet(
        holidays=holidays,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='additive',
        changepoint_prior_scale=0.2
    )
    m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    m.fit(train_df)
    future = pd.DataFrame({'ds': all_dates})
    forecast = m.predict(future)
    return forecast

purchase_forecast = prophet_predict(purchase_train, holidays, all_dates, 'purchase')
redeem_forecast = prophet_predict(redeem_train, holidays, all_dates, 'redeem')

# 可视化：2014-03-01到2014-09-30，真实值（3-8月）+预测值（3-9月）+in-sample预测
plt.figure(figsize=(18,8))
# 真实值（3-8月）
plt.plot(purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['ds'],
         purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['y'],
         label='申购真实值', color='blue')
plt.plot(redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['ds'],
         redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['y'],
         label='赎回真实值', color='green')
# in-sample预测（3-8月）
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'],
         purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'],
         label='申购in-sample预测', color='blue', linestyle='--')
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'],
         redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'],
         label='赎回in-sample预测', color='green', linestyle='--')
# 9月预测（无真实值）
plt.plot(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'],
         purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat'],
         label='申购9月预测', color='blue', linestyle=':')
plt.plot(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['ds'],
         redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat'],
         label='赎回9月预测', color='green', linestyle=':')
plt.title('2014-03-01至2014-09-30申购/赎回真实值与Prophet预测对比')
plt.legend()
plt.xlim([train_start, predict_end])
plt.savefig('3.0_prophet_output/3.0_prophet_purchase_redeem_compare.png')
plt.close()

# 输出9月预测结果为竞赛格式
predict_df = pd.DataFrame({
    'report_date': purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'].dt.strftime('%Y%m%d'),
    'purchase': np.round(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat']).astype(int),
    'redeem': np.round(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat']).astype(int)
})
predict_df.to_csv('3.0_prophet_output/3.0_prophet_predict.csv', index=False, header=False, encoding='utf-8-sig')

print('Prophet特征工程、建模与预测已完成，结果保存在3.0_prophet_output目录。') 