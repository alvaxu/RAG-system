'''
自动调参：网格搜索order和seasonal_order参数，使验证集score_report总得分最高
最优参数：order=(4, 1, 0), seasonal_order=(1, 0, 0, 7), 验证集总得分=8.0968
2.3 SARIMA自动调参建模与预测已完成，结果保存在2.3_sarima_output目录。

'''
import pandas as pd
import numpy as np
import os
import matplotlib
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
import chinese_calendar
from itertools import product

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('2.3_sarima_output', exist_ok=True)

# 1. 读取特征工程输出
purchase_df = pd.read_csv('2.0_feature_output/2.0_sarima_purchase.csv', parse_dates=['ds'])
purchase_df = purchase_df.set_index('ds').asfreq('D')
redeem_df = pd.read_csv('2.0_feature_output/2.0_sarima_redeem.csv', parse_dates=['ds'])
redeem_df = redeem_df.set_index('ds').asfreq('D')

# 生成节假日和周末特征
def make_calendar_features(df):
    df = df.copy()
    df['is_holiday'] = df.index.to_series().apply(lambda x: 1 if chinese_calendar.is_holiday(x) else 0)
    df['is_weekend'] = df.index.weekday >= 5
    df['is_weekend'] = df['is_weekend'].astype(int)
    return df

purchase_df = make_calendar_features(purchase_df)
redeem_df = make_calendar_features(redeem_df)

# 补全索引到2014-09-30，确保预测区间存在
full_dates = pd.date_range(purchase_df.index.min(), '2014-09-30', freq='D')
purchase_df = purchase_df.reindex(full_dates)
redeem_df = redeem_df.reindex(full_dates)

# 再生成特征，补全新日期的节假日/周末特征
purchase_df = make_calendar_features(purchase_df)
redeem_df = make_calendar_features(redeem_df)

# y值缺失填0
purchase_df['y'] = purchase_df['y'].fillna(0)
redeem_df['y'] = redeem_df['y'].fillna(0)

# 区间设置
train_end = pd.to_datetime('2014-08-01')
val_start = pd.to_datetime('2014-08-01')
val_end = pd.to_datetime('2014-08-31')
predict_start = pd.to_datetime('2014-09-01')
predict_end = pd.to_datetime('2014-09-30')
val_dates = pd.date_range(val_start, val_end)
predict_dates = pd.date_range(predict_start, predict_end)

# SARIMA建模与预测函数（带exog）
def fit_predict_sarima(train_series, train_exog, predict_exog, predict_steps, order, seasonal_order):
    try:
        model = SARIMAX(train_series, exog=train_exog, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
        results = model.fit(disp=False)
        forecast = results.forecast(steps=predict_steps, exog=predict_exog)
        return forecast
    except Exception as e:
        return None

# 评分函数
def calc_score(true, pred):
    rel_err = np.abs(true - pred) / np.maximum(true, 1)
    score = np.where(rel_err > 0.3, 0, 10)
    return rel_err, score

# 网格参数范围（可根据实际情况调整）
order_grid = list(product([1,2,3,4,5], [0,1], [0,1]))  # p,d,q
seasonal_order_grid = list(product([0,1], [0,1], [0,1,2], [7]))  # P,D,Q,s

best_score = -1
best_params = None
best_preds = None

# 只对申购和赎回分别调参，最后用最优参数预测9月
for order in order_grid:
    for seasonal_order in seasonal_order_grid:
        # 申购
        purchase_train = purchase_df[purchase_df.index < train_end]['y']
        purchase_exog = purchase_df[['is_holiday', 'is_weekend']]
        purchase_train_exog = purchase_exog.loc[purchase_train.index]
        purchase_val_exog = purchase_exog.loc[val_dates]
        purchase_pred_exog = purchase_exog.loc[val_dates.union(predict_dates)]
        purchase_val_pred = fit_predict_sarima(purchase_train, purchase_train_exog, purchase_val_exog, len(val_dates), order, seasonal_order)
        if purchase_val_pred is None:
            continue
        # 赎回
        redeem_train = redeem_df[redeem_df.index < train_end]['y']
        redeem_exog = redeem_df[['is_holiday', 'is_weekend']]
        redeem_train_exog = redeem_exog.loc[redeem_train.index]
        redeem_val_exog = redeem_exog.loc[val_dates]
        redeem_pred_exog = redeem_exog.loc[val_dates.union(predict_dates)]
        redeem_val_pred = fit_predict_sarima(redeem_train, redeem_train_exog, redeem_val_exog, len(val_dates), order, seasonal_order)
        if redeem_val_pred is None:
            continue
        # 评分
        purchase_val_true = purchase_df.loc[(purchase_df.index >= val_start) & (purchase_df.index <= val_end), 'y'].values
        redeem_val_true = redeem_df.loc[(redeem_df.index >= val_start) & (redeem_df.index <= val_end), 'y'].values
        purchase_rel_err, purchase_score = calc_score(purchase_val_true, purchase_val_pred)
        redeem_rel_err, redeem_score = calc_score(redeem_val_true, redeem_val_pred)
        purchase_final_score = purchase_score.sum() * 0.45 / len(purchase_score)
        redeem_final_score = redeem_score.sum() * 0.55 / len(redeem_score)
        total_score = purchase_final_score + redeem_final_score
        if total_score > best_score:
            best_score = total_score
            best_params = (order, seasonal_order)
            best_preds = {
                'purchase': (purchase_train, purchase_train_exog, purchase_pred_exog),
                'redeem': (redeem_train, redeem_train_exog, redeem_pred_exog)
            }

# 用最优参数做9月预测
if best_params is not None:
    order, seasonal_order = best_params
    print(f'最优参数：order={order}, seasonal_order={seasonal_order}, 验证集总得分={best_score:.4f}')
    # 申购
    purchase_train, purchase_train_exog, purchase_pred_exog = best_preds['purchase']
    purchase_pred = fit_predict_sarima(purchase_train, purchase_train_exog, purchase_pred_exog, len(val_dates) + len(predict_dates), order, seasonal_order)
    purchase_pred = purchase_pred[-len(predict_dates):]
    # 赎回
    redeem_train, redeem_train_exog, redeem_pred_exog = best_preds['redeem']
    redeem_pred = fit_predict_sarima(redeem_train, redeem_train_exog, redeem_pred_exog, len(val_dates) + len(predict_dates), order, seasonal_order)
    redeem_pred = redeem_pred[-len(predict_dates):]
    # 输出预测结果
    predict_df = pd.DataFrame({'report_date': predict_dates.strftime('%Y%m%d'),
                               'purchase': np.round(purchase_pred).astype(int),
                               'redeem': np.round(redeem_pred).astype(int)})
    predict_df.to_csv('2.3_sarima_output/2.3_sarima_predict.csv', index=False, header=False, encoding='utf-8-sig')
    # 可视化
    plt.figure(figsize=(16,6))
    plt.plot(purchase_df.index, purchase_df['y'], label='历史申购')
    plt.plot(predict_dates, purchase_pred, label='预测申购')
    plt.title(f'申购金额历史与预测对比（SARIMA自动调参）')
    plt.legend()
    plt.savefig('2.3_sarima_output/2.3_sarima_purchase_compare.png')
    plt.close()
    plt.figure(figsize=(16,6))
    plt.plot(redeem_df.index, redeem_df['y'], label='历史赎回')
    plt.plot(predict_dates, redeem_pred, label='预测赎回')
    plt.title(f'赎回金额历史与预测对比（SARIMA自动调参）')
    plt.legend()
    plt.savefig('2.3_sarima_output/2.3_sarima_redeem_compare.png')
    plt.close()
    # 输出最优参数和得分
    with open('2.3_sarima_output/2.3_sarima_best_params.txt', 'w', encoding='utf-8') as f:
        f.write(f'最优order: {order}\n最优seasonal_order: {seasonal_order}\n验证集总得分: {best_score:.4f}\n')
else:
    print('未找到可用的SARIMA参数组合，请调整参数范围或检查数据！')

print('2.3 SARIMA自动调参建模与预测已完成，结果保存在2.3_sarima_output目录。') 