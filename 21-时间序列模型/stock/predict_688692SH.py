# -*- coding: utf-8 -*-
# 对688692.SH股票价格进行预测，使用时间序列ARIMA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import warnings
from itertools import product
from datetime import datetime, timedelta
import calendar

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

warnings.filterwarnings('ignore')

# 数据加载
print("加载688692.SH股票数据...")
df = pd.read_csv('./688692_SH_daily_data.csv')
df['trade_date'] = pd.to_datetime(df['trade_date'])
df.set_index('trade_date', inplace=True)

# 数据探索
print("数据基本信息:")
print(df[['close']].head())

# 绘制原始收盘价走势图
plt.figure(figsize=[15, 7])
plt.suptitle('688692.SH股票收盘价', fontsize=20)
plt.plot(df.index, df.close, '-', label='日收盘价')
plt.legend()
plt.xlabel('日期')
plt.ylabel('收盘价(元)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 按照不同周期统计
df_week = df.resample('W-MON').mean()  # 周数据
df_month = df.resample('M').mean()     # 月数据

# 绘制不同周期的股价走势图
fig = plt.figure(figsize=[15, 10])
plt.suptitle('688692.SH股票收盘价 - 不同周期', fontsize=20)
plt.subplot(311)
plt.plot(df.close, '-', label='日收盘价')
plt.legend()
plt.subplot(312)
plt.plot(df_week.close, '-', label='周收盘价')
plt.legend()
plt.subplot(313)
plt.plot(df_month.close, '-', label='月收盘价')
plt.legend()
plt.tight_layout()
plt.show()

# 使用日线数据进行ARIMA模型拟合
# 设置参数范围
print("开始寻找最优ARIMA模型参数...")
ps = range(0, 5)  # AR阶数
ds = range(0, 2)  # 差分阶数
qs = range(0, 5)  # MA阶数
parameters = product(ps, ds, qs)
parameters_list = list(parameters)

# 寻找最优ARIMA模型参数
results = []
best_aic = float("inf")
for param in parameters_list:
    # 跳过一些不合理的参数组合
    if param[0] == 0 and param[2] == 0:
        continue
    
    try:
        model = sm.tsa.statespace.SARIMAX(df.close,
                                order=(param[0], param[1], param[2]),
                                enforce_stationarity=False,
                                enforce_invertibility=False).fit(disp=False)
    except:
        continue
    
    aic = model.aic
    if aic < best_aic:
        best_model = model
        best_aic = aic
        best_param = param
    results.append([param, model.aic])

# 输出最优模型信息
print('最优ARIMA模型参数:', best_param)
print('最优AIC值:', best_aic)
print('最优模型摘要:')
print(best_model.summary())

# 预测未来7天的股价
print("预测未来7天的股价...")
last_date = df.index[-1]

# 创建未来7天的日期列表
date_list = []
for i in range(1, 8):  # 预测未来7天
    next_date = last_date + timedelta(days=i)
    # 跳过周六和周日
    while next_date.weekday() >= 5:  # 5是周六，6是周日
        next_date = next_date + timedelta(days=1)
    date_list.append(next_date)

# 添加未来7天的时间索引
future = pd.DataFrame(index=date_list, columns=df.columns)
df_pred = pd.concat([df[['close']], future])

# 使用最优模型进行预测
pred = best_model.get_prediction(start=len(df), end=len(df)+len(date_list)-1)
pred_mean = pred.predicted_mean
pred_ci = pred.conf_int()

# 将预测结果添加到df_pred
for i, date in enumerate(date_list):
    df_pred.loc[date, 'close'] = pred_mean.iloc[i]
    df_pred.loc[date, 'lower'] = pred_ci.iloc[i, 0]
    df_pred.loc[date, 'upper'] = pred_ci.iloc[i, 1]

# 输出预测结果
print("\n未来7个交易日收盘价预测结果:")
future_pred = df_pred.iloc[-7:]
print(future_pred[['close', 'lower', 'upper']])

# 可视化预测结果
plt.figure(figsize=(12, 6))

# 绘制历史数据
plt.plot(df.index[-30:], df.close[-30:], 'b-', label='历史收盘价')

# 绘制预测数据
plt.plot(future_pred.index, future_pred['close'], 'r--', label='预测收盘价')
plt.fill_between(future_pred.index, 
                 future_pred['lower'], 
                 future_pred['upper'], 
                 color='pink', alpha=0.3, label='95%置信区间')

# 设置图形属性
plt.title('688692.SH股票价格预测 (未来7个交易日)')
plt.xlabel('日期')
plt.ylabel('收盘价(元)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

# 保存预测结果图
plt.savefig('688692_SH_prediction.png')
plt.show()

# 保存预测结果到CSV
future_pred.to_csv('688692_SH_prediction_results.csv')
print("预测结果已保存到 688692_SH_prediction_results.csv")

# 评估模型在历史数据上的表现
# 计算过去30天的预测值与实际值的对比
print("\n评估模型在历史数据上的表现:")
historical_pred = best_model.get_prediction(start=-30)
historical_pred_mean = historical_pred.predicted_mean
historical_pred_ci = historical_pred.conf_int()

# 计算均方根误差(RMSE)
from sklearn.metrics import mean_squared_error
rmse = np.sqrt(mean_squared_error(df.close[-30:], historical_pred_mean))
print(f"过去30天的RMSE (均方根误差): {rmse:.2f}")

# 可视化历史数据的预测效果
plt.figure(figsize=(12, 6))
plt.plot(df.index[-30:], df.close[-30:], 'b-', label='实际收盘价')
plt.plot(df.index[-30:], historical_pred_mean, 'g--', label='模型拟合')
plt.fill_between(df.index[-30:], 
                 historical_pred_ci.iloc[:, 0], 
                 historical_pred_ci.iloc[:, 1], 
                 color='green', alpha=0.1)
plt.title('模型在历史数据上的表现 (过去30个交易日)')
plt.xlabel('日期')
plt.ylabel('收盘价(元)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('688692_SH_model_fit.png')
plt.show()

print("预测完成!") 