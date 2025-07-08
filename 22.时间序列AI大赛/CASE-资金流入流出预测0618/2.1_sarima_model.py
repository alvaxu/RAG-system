'''
递推预测，先用历史数据预测8月和9月的共61天，然后只取最后30天（9月）作为正式预测结果
成绩：54.1208
'''
import pandas as pd
import numpy as np
import os
import matplotlib
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('2.1_sarima_output', exist_ok=True)

# 1. 读取特征工程输出
purchase_df = pd.read_csv('2.0_feature_output/2.0_sarima_purchase.csv', parse_dates=['ds'])
redeem_df = pd.read_csv('2.0_feature_output/2.0_sarima_redeem.csv', parse_dates=['ds'])

# 2. 区间设置
train_end = pd.to_datetime('2014-08-01')
val_start = pd.to_datetime('2014-08-01')
val_end = pd.to_datetime('2014-08-31')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')
val_dates = pd.date_range(val_start, val_end)
predict_dates = pd.date_range(predict_start, predict_end)

# 3. SARIMA建模与预测函数
def fit_predict_sarima(train_series, predict_steps, order=(5,1,1), seasonal_order=(1,0,2,7)):
    """
    :function: SARIMA建模与预测
    :param train_series: 训练序列（pd.Series，index为日期）
    :param predict_steps: 预测步数
    :param order: SARIMA参数
    :param seasonal_order: SARIMA季节性参数
    :return: 预测值数组
    """
    model = SARIMAX(train_series, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
    results = model.fit(disp=False)
    forecast = results.forecast(steps=predict_steps)
    return forecast

# 4. 申购建模与预测
purchase_train = purchase_df[purchase_df['ds'] < train_end].set_index('ds')['y']
purchase_train.index = pd.DatetimeIndex(purchase_train.index, freq='D')
purchase_val_pred = fit_predict_sarima(purchase_train, len(val_dates))
purchase_pred = fit_predict_sarima(purchase_train, len(val_dates) + len(predict_dates))[-len(predict_dates):]

# 5. 赎回建模与预测
redeem_train = redeem_df[redeem_df['ds'] < train_end].set_index('ds')['y']
redeem_train.index = pd.DatetimeIndex(redeem_train.index, freq='D')
redeem_val_pred = fit_predict_sarima(redeem_train, len(val_dates))
redeem_pred = fit_predict_sarima(redeem_train, len(val_dates) + len(predict_dates))[-len(predict_dates):]

# 6. 合并预测结果，输出为竞赛格式
predict_df = pd.DataFrame({'report_date': predict_dates.strftime('%Y%m%d'),
                           'purchase': np.round(purchase_pred).astype(int),
                           'redeem': np.round(redeem_pred).astype(int)})
predict_df.to_csv('2.1_sarima_output/2.1_sarima_predict.csv', index=False, header=False, encoding='utf-8-sig')

# 7. 可视化历史与预测对比
plt.figure(figsize=(16,6))
plt.plot(purchase_df['ds'], purchase_df['y'], label='历史申购')
plt.plot(predict_dates, purchase_pred, label='预测申购')
plt.title('申购金额历史与预测对比（SARIMA）')
plt.legend()
plt.savefig('2.1_sarima_output/2.1_sarima_purchase_compare.png')
plt.close()

plt.figure(figsize=(16,6))
plt.plot(redeem_df['ds'], redeem_df['y'], label='历史赎回')
plt.plot(predict_dates, redeem_pred, label='预测赎回')
plt.title('赎回金额历史与预测对比（SARIMA）')
plt.legend()
plt.savefig('2.1_sarima_output/2.1_sarima_redeem_compare.png')
plt.close()

# 8. 验证集评分（2014-08-01~2014-08-31）
def calc_score(true, pred):
    rel_err = np.abs(true - pred) / np.maximum(true, 1)
    score = np.where(rel_err > 0.3, 0, 10)
    return rel_err, score

# 取出验证集真实值
purchase_val_true = purchase_df[(purchase_df['ds'] >= val_start) & (purchase_df['ds'] <= val_end)]['y'].values
redeem_val_true = redeem_df[(redeem_df['ds'] >= val_start) & (redeem_df['ds'] <= val_end)]['y'].values

# 计算相对误差和得分
purchase_rel_err, purchase_score = calc_score(purchase_val_true, purchase_val_pred)
redeem_rel_err, redeem_score = calc_score(redeem_val_true, redeem_val_pred)

purchase_final_score = purchase_score.sum() * 0.45 / len(purchase_score)
redeem_final_score = redeem_score.sum() * 0.55 / len(redeem_score)
total_score = purchase_final_score + redeem_final_score

# 输出验证集评分
score_report = f"验证集区间：2014-08-01~2014-08-31\n" \
               f"申购平均相对误差：{purchase_rel_err.mean():.4f}\n" \
               f"赎回平均相对误差：{redeem_rel_err.mean():.4f}\n" \
               f"申购得分：{purchase_final_score:.4f}\n" \
               f"赎回得分：{redeem_final_score:.4f}\n" \
               f"总得分：{total_score:.4f}\n"
print(score_report)
with open('2.1_sarima_output/2.1_sarima_val_score.txt', 'w', encoding='utf-8') as f:
    f.write(score_report)

print('2.1 SARIMA建模与预测及验证评分已完成，结果保存在2.1_sarima_output目录。') 