# -*- coding: utf-8 -*-
# 对688692.SH股票价格进行预测，使用Prophet模型
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

# 数据加载
print("加载688692.SH股票数据...")
df = pd.read_csv('./688692_SH_daily_data.csv')
df['trade_date'] = pd.to_datetime(df['trade_date'])

# 数据预处理 - Prophet需要特定的列名格式
prophet_df = df[['trade_date', 'close']].rename(columns={'trade_date': 'ds', 'close': 'y'})

# 数据探索
print("数据基本信息:")
print(prophet_df.head())

# 绘制原始收盘价走势图
plt.figure(figsize=[15, 7])
plt.suptitle('688692.SH股票收盘价', fontsize=20)
plt.plot(prophet_df['ds'], prophet_df['y'], '-', label='日收盘价')
plt.legend()
plt.xlabel('日期')
plt.ylabel('收盘价(元)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 训练Prophet模型
print("训练Prophet模型...")
model = Prophet(
    changepoint_prior_scale=0.05,  # 控制趋势变化点的灵活性
    seasonality_prior_scale=10,    # 控制季节性的强度
    daily_seasonality=False,       # 不考虑每日季节性
    weekly_seasonality=True,       # 考虑每周季节性
    yearly_seasonality=True,       # 考虑每年季节性
    seasonality_mode='multiplicative'  # 季节性模式，可以是加法或乘法
)

# 添加股市的特殊季节性 - 交易周期
model.add_seasonality(
    name='monthly',
    period=30.5,
    fourier_order=5
)

# 拟合模型
model.fit(prophet_df)

# 预测未来7个交易日
last_date = prophet_df['ds'].max()

# 创建未来7个交易日的日期
future_dates = []
next_date = last_date
for i in range(1, 10):  # 多生成几天以应对周末
    next_date = next_date + timedelta(days=1)
    if next_date.weekday() < 5:  # 只保留工作日
        future_dates.append(next_date)
    if len(future_dates) == 7:  # 当有7个工作日时停止
        break

# 创建未来日期的DataFrame
future = pd.DataFrame({'ds': future_dates})

# 合并历史数据和未来日期
future_all = model.make_future_dataframe(periods=0)
future_all = pd.concat([future_all, future])

# 进行预测
print("预测未来7个交易日的股价...")
forecast = model.predict(future_all)

# 显示预测结果
print("\n未来7个交易日收盘价预测结果 (Prophet模型):")
forecast_future = forecast[forecast['ds'].isin(future_dates)][['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
forecast_future = forecast_future.rename(columns={'ds': '日期', 'yhat': '预测价格', 'yhat_lower': '下限', 'yhat_upper': '上限'})
print(forecast_future)

# 可视化预测结果
plt.figure(figsize=(12, 6))

# 绘制历史数据
plt.plot(prophet_df['ds'][-30:], prophet_df['y'][-30:], 'b-', label='历史收盘价')

# 绘制预测数据
plt.plot(forecast_future['日期'], forecast_future['预测价格'], 'r--', label='预测收盘价')
plt.fill_between(forecast_future['日期'], 
                 forecast_future['下限'], 
                 forecast_future['上限'], 
                 color='pink', alpha=0.3, label='95%置信区间')

# 设置图形属性
plt.title('688692.SH股票价格预测 (Prophet模型 - 未来7个交易日)')
plt.xlabel('日期')
plt.ylabel('收盘价(元)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

# 保存预测结果图
plt.savefig('688692_SH_prediction_prophet.png')
plt.show()

# 保存预测结果到CSV
forecast_future.to_csv('688692_SH_prediction_prophet_results.csv', index=False)
print("预测结果已保存到 688692_SH_prediction_prophet_results.csv")

# 绘制完整的预测结果
plt.figure(figsize=(12, 6))

# 绘制历史数据和预测结果
plt.plot(prophet_df['ds'], prophet_df['y'], 'b-', label='历史收盘价')
plt.plot(forecast['ds'], forecast['yhat'], 'r--', label='拟合/预测价格')
plt.fill_between(forecast['ds'], 
                 forecast['yhat_lower'], 
                 forecast['yhat_upper'], 
                 color='pink', alpha=0.3, label='95%置信区间')

# 设置图形属性
plt.title('688692.SH股票价格: 历史与Prophet预测')
plt.xlabel('日期')
plt.ylabel('收盘价(元)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('688692_SH_full_prediction_prophet.png')
plt.show()

# 使用Prophet的内置函数绘制更详细的预测组件
fig1 = model.plot(forecast)
plt.title('Prophet预测结果')
plt.savefig('688692_SH_prophet_forecast.png')
plt.show()

# 绘制预测的各个组件 (趋势、季节性等)
fig2 = model.plot_components(forecast)
plt.savefig('688692_SH_prophet_components.png')
plt.show()

# 评估模型在历史数据上的表现
from sklearn.metrics import mean_squared_error, mean_absolute_error

# 获取历史数据的预测值
historical_dates = prophet_df['ds']
historical_forecast = forecast[forecast['ds'].isin(historical_dates)]

# 计算误差
y_true = prophet_df['y'].values
y_pred = historical_forecast['yhat'].values

rmse = np.sqrt(mean_squared_error(y_true, y_pred))
mae = mean_absolute_error(y_true, y_pred)

print("\n模型评估:")
print(f"RMSE (均方根误差): {rmse:.2f}")
print(f"MAE (平均绝对误差): {mae:.2f}")

# 绘制最近30天的预测与实际值对比
plt.figure(figsize=(12, 6))
plt.plot(prophet_df['ds'][-30:], prophet_df['y'][-30:], 'b-', label='实际收盘价')
plt.plot(historical_dates[-30:], historical_forecast['yhat'][-30:], 'g--', label='模型拟合')
plt.fill_between(historical_dates[-30:], 
                 historical_forecast['yhat_lower'][-30:], 
                 historical_forecast['yhat_upper'][-30:], 
                 color='green', alpha=0.1)
plt.title('Prophet模型在历史数据上的表现 (过去30个交易日)')
plt.xlabel('日期')
plt.ylabel('收盘价(元)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('688692_SH_model_fit_prophet.png')
plt.show()

print("预测完成!") 