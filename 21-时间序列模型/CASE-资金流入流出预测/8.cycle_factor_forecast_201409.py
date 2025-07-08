"""
:function: 基于周期因子（weekday和day）分解的申购和赎回预测
:param csv_path: 用户余额表CSV文件路径
输出：8.cycle_factor_forecast_201409.csv（无表头），8.cycle_factor_trend_201409.png
:return: 无（直接展示图表和保存预测结果）
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date
import warnings

warnings.filterwarnings("ignore")

"""
:function: 预测2014-09-01到2014-09-30的申购和赎回金额，基于weekday和day的周期分解
:param csv_path: 用户余额表CSV文件路径
:return: 无（直接展示图表和保存预测结果）
"""
def cycle_factor_forecast(csv_path='user_balance_table.csv'):
    # 1. 数据加载与预处理
    try:
        df = pd.read_csv(csv_path, encoding='utf-8', usecols=['report_date', 'total_purchase_amt', 'total_redeem_amt'])
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='gbk', usecols=['report_date', 'total_purchase_amt', 'total_redeem_amt'])
    
    df['report_date'] = pd.to_datetime(df['report_date'], format='%Y%m%d')
    df = df.set_index('report_date').sort_index()

    # 筛选2014-03到2014-08的历史数据
    start_date_hist = pd.to_datetime('2014-03-01')
    end_date_hist = pd.to_datetime('2014-08-31')
    df_hist = df[(df.index >= start_date_hist) & (df.index <= end_date_hist)].copy()
    
    # 按日期汇总
    grouped_hist = df_hist.groupby(df_hist.index).sum()
    grouped_hist['weekday'] = grouped_hist.index.weekday # 0=周一, 6=周日
    grouped_hist['day'] = grouped_hist.index.day # 1-31

    # 2. 计算周期因子（weekday和day的均值）
    # 申购
    weekday_purchase = grouped_hist.groupby('weekday')['total_purchase_amt'].mean()
    day_purchase = grouped_hist.groupby('day')['total_purchase_amt'].mean()
    # 赎回
    weekday_redeem = grouped_hist.groupby('weekday')['total_redeem_amt'].mean()
    day_redeem = grouped_hist.groupby('day')['total_redeem_amt'].mean()

    # 3. 预测未来日期
    future_dates = pd.date_range(start='2014-09-01', end='2014-09-30', freq='D')
    future_weekday = future_dates.weekday
    future_day = future_dates.day

    # 4. 组合周期因子进行预测（加权平均，权重可调，默认各50%）
    w1, w2 = 0.5, 0.5
    purchase_pred = []
    redeem_pred = []
    for wd, d in zip(future_weekday, future_day):
        # 若某天在历史中未出现，使用均值填补
        p = w1 * weekday_purchase.get(wd, weekday_purchase.mean()) + w2 * day_purchase.get(d, day_purchase.mean())
        r = w1 * weekday_redeem.get(wd, weekday_redeem.mean()) + w2 * day_redeem.get(d, day_redeem.mean())
        purchase_pred.append(int(round(p)))
        redeem_pred.append(int(round(r)))

    # 5. 输出CSV
    forecast_df = pd.DataFrame({
        'report_date': future_dates.strftime('%Y%m%d'),
        'purchase': purchase_pred,
        'redeem': redeem_pred
    })
    forecast_df.to_csv('8.cycle_factor_forecast_201409.csv', index=False, header=False, encoding='utf-8')
    print('周期因子预测结果已保存到 8.cycle_factor_forecast_201409.csv')

    # 6. 可视化
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(16, 6))
    plt.plot(grouped_hist.index, grouped_hist['total_purchase_amt'], label='申购金额-历史', color='C0')
    plt.plot(grouped_hist.index, grouped_hist['total_redeem_amt'], label='赎回金额-历史', color='C1')
    plt.plot(future_dates, purchase_pred, label='申购金额-预测', color='C0', linestyle='--')
    plt.plot(future_dates, redeem_pred, label='赎回金额-预测', color='C1', linestyle='--')
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('金额', fontsize=12)
    plt.title('【周期因子分解预测】2014-03~2014-08及未来30天每日申购与赎回金额趋势', fontsize=14)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('8.cycle_factor_trend_201409.png')
    plt.show()
    print('趋势图已保存到 8.cycle_factor_trend_201409.png')

if __name__ == "__main__":
    cycle_factor_forecast() 