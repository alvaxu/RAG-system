'''
3.7_prophet_model.py
功能：
- 余额宝申购/赎回数据Prophet自动调参建模与预测。
- 节假日逻辑：2014年3月1日-10月10日，所有法定节假日、连续放假日期、正常周末均视为节假日，调休补班的周末视为工作日。
- 节假日和调休补班日期全部手工显式指定，无需chinese_calendar。
- 训练区间2014-03-01到2014-08-31，预测区间2014-09-01到2014-10-10，输出csv结果仅到9月30日。
- 输出最优参数、验证集RMSE、9月预测结果、分解图、残差图、上下子图对比图。
- 不引入外部变量。
申购最优参数: {'changepoint_prior_scale': 0.01, 'seasonality_prior_scale': 5.0, 'holidays_prior_scale': 5.0, 'seasonality_mode': 'multiplicative'}, 最优验证集RMSE: 92057040.43
赎回最优参数: {'changepoint_prior_scale': 0.01, 'seasonality_prior_scale': 5.0, 'holidays_prior_scale': 20.0, 'seasonality_mode': 'additive'}, 最优验证集RMSE: 67659354.34
成绩:82.0209
'''

import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import matplotlib.pyplot as plt
import os
import matplotlib
import itertools
import logging
import warnings
from datetime import date, timedelta, datetime

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('3.7_prophet_output', exist_ok=True)
os.makedirs('3.7_feature_output', exist_ok=True)

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
    purchase_df.to_csv('3.7_feature_output/3.7_prophet_purchase.csv', index=False, encoding='utf-8-sig')
    redeem_df.to_csv('3.7_feature_output/3.7_prophet_redeem.csv', index=False, encoding='utf-8-sig')

    # 4. 显式定义2014年3月1日-10月10日节假日和调休补班日
    # 节假日包括：所有法定节假日、连续放假日期、正常周末（调休补班除外）
    # 调休补班周末：2014年5月4日、9月28日、10月11日、10月12日
    # 其它周末均为节假日
    holiday_dates = set()
    # 法定节假日及连续放假
    holiday_spans = [
        # 清明节 4.5-4.7
        (date(2014,4,5), date(2014,4,7)),
        # 劳动节 5.1-5.3
        (date(2014,5,1), date(2014,5,3)),
        # 端午节 5.31-6.2
        (date(2014,5,31), date(2014,6,2)),
        # 中秋节 9.6-9.8
        (date(2014,9,6), date(2014,9,8)),
        # 国庆节 10.1-10.7
        (date(2014,10,1), date(2014,10,7)),
    ]
    for start, end in holiday_spans:
        for i in range((end-start).days+1):
            holiday_dates.add(start + timedelta(days=i))
    # 3月1日-10月10日所有周末（调休补班除外）
    all_dates = [date(2014,3,1) + timedelta(days=i) for i in range((date(2014,10,10)-date(2014,3,1)).days+1)]
    workday_shift_dates = [date(2014,5,4), date(2014,9,28), date(2014,10,11), date(2014,10,12)]
    for d in all_dates:
        if d.weekday() >= 5 and d not in workday_shift_dates:
            holiday_dates.add(d)
    # 生成节假日DataFrame
    holiday_list = []
    for d in sorted(holiday_dates):
        holiday_list.append({'holiday': 'official_holiday', 'ds': pd.Timestamp(d), 'lower_window': 0, 'upper_window': 0})
    for d in workday_shift_dates:
        holiday_list.append({'holiday': 'workday_shift', 'ds': pd.Timestamp(d), 'lower_window': 0, 'upper_window': 0})
    holiday_df = pd.DataFrame(holiday_list)
    holiday_df.to_csv('3.7_feature_output/3.7_prophet_holidays.csv', index=False, encoding='utf-8-sig')

    # 5. 特征工程优化（与3.5一致）
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
    daily.to_csv('3.7_feature_output/3.7_prophet_daily_features.csv', index=False, encoding='utf-8-sig')

    # 6. Prophet自动调参与建模函数（与3.5一致）
    def auto_prophet(train_df, holidays, all_dates, label, out_prefix):
        param_grid = {
            'changepoint_prior_scale': [0.01, 0.05, 0.1, 0.5],
            'seasonality_prior_scale': [1.0, 5.0, 10.0, 20.0],
            'holidays_prior_scale': [1.0, 5.0, 10.0, 20.0],
            'seasonality_mode': ['additive', 'multiplicative']
        }
        all_params = [dict(zip(param_grid.keys(), v)) for v in itertools.product(*param_grid.values())]
        best_params = None
        best_rmse = float('inf')
        best_model = None
        print(f'[{label}] 开始自动调参...')
        for params in all_params:
            m = Prophet(
                holidays=holidays,
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                **params
            )
            m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            m.fit(train_df)
            try:
                df_cv = cross_validation(m, initial='120 days', period='30 days', horizon='30 days', parallel='processes')
                df_p = performance_metrics(df_cv, rolling_window=1)
                rmse = df_p['rmse'].values[0]
                print(f'[{label}] 参数: {params}, 验证集RMSE: {rmse:.2f}')
                if rmse < best_rmse:
                    best_rmse = rmse
                    best_params = params
                    best_model = m
            except Exception as e:
                print(f'[{label}] 参数: {params} 发生异常: {e}')
                raise
        print(f'[{label}] 最优参数: {best_params}, 最优验证集RMSE: {best_rmse:.2f}')
        # 用最优参数做全区间预测
        future = pd.DataFrame({'ds': all_dates})
        forecast = best_model.predict(future)
        # 分解图
        fig = best_model.plot_components(forecast)
        plt.savefig(f'3.7_prophet_output/3.7_prophet_{out_prefix}_components.png')
        plt.close()
        return best_model, forecast, best_params, best_rmse

    # 7. 训练区间、预测区间
    train_start = pd.to_datetime('2014-03-01')
    train_end = pd.to_datetime('2014-08-31')
    predict_start = pd.to_datetime('2014-09-01')
    predict_end = pd.to_datetime('2014-10-10')

    purchase_df = pd.read_csv('3.7_feature_output/3.7_prophet_purchase.csv', parse_dates=['ds'])
    redeem_df = pd.read_csv('3.7_feature_output/3.7_prophet_redeem.csv', parse_dates=['ds'])
    holidays = pd.read_csv('3.7_feature_output/3.7_prophet_holidays.csv', parse_dates=['ds'])

    purchase_train = purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]
    redeem_train = redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]
    all_dates = pd.date_range(train_start, predict_end)
    predict_dates = pd.date_range(predict_start, predict_end)

    # 8. 申购自动调参、预测、分解图
    purchase_model, purchase_forecast, purchase_best_params, purchase_best_rmse = auto_prophet(
        purchase_train, holidays, all_dates, '申购', 'purchase')
    # 9. 赎回自动调参、预测、分解图
    redeem_model, redeem_forecast, redeem_best_params, redeem_best_rmse = auto_prophet(
        redeem_train, holidays, all_dates, '赎回', 'redeem')

    # 10. 可视化：上下两个子图分别展示申购和赎回的实际与预测
    fig, axes = plt.subplots(2, 1, figsize=(18, 12), sharex=True)
    axes[0].plot(purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['ds'],
                 purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['y'],
                 label='申购真实值', color='blue')
    axes[0].plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'],
                 purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'],
                 label='申购in-sample预测', color='blue', linestyle='--')
    axes[0].plot(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['ds'],
                 purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= predict_end)]['yhat'],
                 label='申购9月及10月预测', color='blue', linestyle=':')
    axes[0].set_title('申购：真实值、in-sample预测与9-10月预测')
    axes[0].legend()
    axes[1].plot(redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['ds'],
                 redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['y'],
                 label='赎回真实值', color='green')
    axes[1].plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'],
                 redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'],
                 label='赎回in-sample预测', color='green', linestyle='--')
    axes[1].plot(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['ds'],
                 redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= predict_end)]['yhat'],
                 label='赎回9月及10月预测', color='green', linestyle=':')
    axes[1].set_title('赎回：真实值、in-sample预测与9-10月预测')
    axes[1].legend()
    plt.xlim([train_start, predict_end])
    plt.tight_layout()
    plt.savefig('3.7_prophet_output/3.7_prophet_purchase_redeem_compare.png')
    plt.close()

    # 11. 残差分析
    real_purchase = purchase_df[(purchase_df['ds'] >= train_start) & (purchase_df['ds'] <= train_end)]['y'].values
    pred_purchase = purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['yhat'].values
    residuals_purchase = real_purchase - pred_purchase
    plt.figure(figsize=(12,4))
    plt.plot(purchase_forecast[(purchase_forecast['ds'] >= train_start) & (purchase_forecast['ds'] <= train_end)]['ds'], residuals_purchase)
    plt.title('申购残差分析（真实值-预测值）')
    plt.axhline(0, color='red', linestyle='--')
    plt.savefig('3.7_prophet_output/3.7_prophet_purchase_residuals.png')
    plt.close()
    real_redeem = redeem_df[(redeem_df['ds'] >= train_start) & (redeem_df['ds'] <= train_end)]['y'].values
    pred_redeem = redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['yhat'].values
    residuals_redeem = real_redeem - pred_redeem
    plt.figure(figsize=(12,4))
    plt.plot(redeem_forecast[(redeem_forecast['ds'] >= train_start) & (redeem_forecast['ds'] <= train_end)]['ds'], residuals_redeem)
    plt.title('赎回残差分析（真实值-预测值）')
    plt.axhline(0, color='red', linestyle='--')
    plt.savefig('3.7_prophet_output/3.7_prophet_redeem_residuals.png')
    plt.close()

    # 12. 输出9月预测结果为竞赛格式（只保留9月1日-9月30日）
    predict_df = pd.DataFrame({
        'report_date': purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= pd.to_datetime('2014-09-30'))]['ds'].dt.strftime('%Y%m%d'),
        'purchase': np.round(purchase_forecast[(purchase_forecast['ds'] >= predict_start) & (purchase_forecast['ds'] <= pd.to_datetime('2014-09-30'))]['yhat']).astype(int),
        'redeem': np.round(redeem_forecast[(redeem_forecast['ds'] >= predict_start) & (redeem_forecast['ds'] <= pd.to_datetime('2014-09-30'))]['yhat']).astype(int)
    })
    predict_df.to_csv('3.7_prophet_output/3.7_prophet_predict.csv', index=False, header=False, encoding='utf-8-sig')

    # 13. 保存最优参数和RMSE到txt文件
    with open('3.7_prophet_output/3.7_prophet_best_params.txt', 'w', encoding='utf-8') as f:
        f.write(f"申购最优参数: {purchase_best_params}, 最优验证集RMSE: {purchase_best_rmse:.2f}\n")
        f.write(f"赎回最优参数: {redeem_best_params}, 最优验证集RMSE: {redeem_best_rmse:.2f}\n")

    print('Prophet自动调参建模、分解图与残差分析已完成，结果保存在3.7_prophet_output目录。')

if __name__ == '__main__':
    main() 