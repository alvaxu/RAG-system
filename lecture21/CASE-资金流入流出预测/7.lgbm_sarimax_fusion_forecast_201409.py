"""
:function: 融合LightGBM与SARIMAX模型预测申购和赎回金额（加权平均融合）
:param balance_csv_path: 用户余额表CSV文件路径
输出：7.lgbm_sarimax_fusion_forecast_201409.csv（无表头），7.lgbm_sarimax_fusion_trend_201409.png
成绩:100.5005

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from feature_engine_v2 import load_and_engineer_features
from statsmodels.tsa.statespace.sarimax import SARIMAX
import lightgbm as lgbm
from datetime import date

warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ====== 融合权重设置 ======
LGBM_WEIGHT = 0.5  # LightGBM权重
SARIMAX_WEIGHT = 0.5  # SARIMAX权重

"""
:function: 判断日期是否为法定节假日（2014年中国大陆主要节假日）或周末
:param date_obj: datetime.date 对象
:return: True 如果是节假日或周末，否则 False
"""
def is_special_day(date_obj):
    holidays_2014 = [
        date(2014, 1, 1),
        date(2014, 1, 31), date(2014, 2, 1), date(2014, 2, 2), date(2014, 2, 3), date(2014, 2, 4), date(2014, 2, 5), date(2014, 2, 6),
        date(2014, 4, 5), date(2014, 4, 6), date(2014, 4, 7),
        date(2014, 5, 1), date(2014, 5, 2), date(2014, 5, 3),
        date(2014, 5, 31), date(2014, 6, 1), date(2014, 6, 2),
        date(2014, 9, 6), date(2014, 9, 7), date(2014, 9, 8),
        date(2014, 10, 1), date(2014, 10, 2), date(2014, 10, 3), date(2014, 10, 4), date(2014, 10, 5), date(2014, 10, 6), date(2014, 10, 7)
    ]
    if date_obj.weekday() in [5, 6]:
        return True
    if date_obj in holidays_2014:
        return True
    return False

"""
:function: 训练SARIMAX模型并预测未来30天
:param grouped_hist: 历史聚合数据（DataFrame，index为日期）
:param target_col: 目标列名（'total_purchase_amt'或'total_redeem_amt'）
:param exog_hist: 历史外部变量（DataFrame）
:param exog_future: 未来外部变量（DataFrame）
:param order: SARIMAX非季节性参数
:param seasonal_order: SARIMAX季节性参数
:return: 预测值（pd.Series，index为未来日期）
"""
def sarimax_predict(grouped_hist, target_col, exog_hist, exog_future, order, seasonal_order):
    model = SARIMAX(grouped_hist[target_col], exog=exog_hist, order=order, seasonal_order=seasonal_order,
                    enforce_stationarity=False, enforce_invertibility=False)
    results = model.fit(disp=False)
    forecast = results.get_forecast(steps=30, exog=exog_future)
    return forecast.predicted_mean

"""
:function: 训练LightGBM模型并预测未来30天
:param df_features: 特征工程后的DataFrame
:param target_col: 目标列名
:param feature_cols: 特征列名列表
:param train_idx: 训练集索引
:param predict_idx: 预测集索引
:return: 预测值（list，长度为30）
"""
def lightgbm_predict(df_features, target_col, feature_cols, train_idx, predict_idx):
    X_train = df_features.loc[train_idx, feature_cols]
    y_train = df_features.loc[train_idx, target_col]
    X_pred = df_features.loc[predict_idx, feature_cols]
    lgb_params = {
        'objective': 'regression',
        'metric': 'rmse',
        'n_estimators': 1000,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 1,
        'lambda_l1': 0.1,
        'lambda_l2': 0.1,
        'num_leaves': 63,
        'verbose': -1,
        'n_jobs': -1,
        'seed': 42
    }
    model = lgbm.LGBMRegressor(**lgb_params)
    model.fit(X_train, y_train, eval_set=[(X_train, y_train)], eval_metric='rmse',
              callbacks=[lgbm.early_stopping(100, verbose=False)])
    y_pred = model.predict(X_pred)
    y_pred = [int(round(max(0, x))) for x in y_pred]
    return y_pred

if __name__ == '__main__':
    # ====== 1. 加载数据和特征 ======
    user_balance_path = 'user_balance_table.csv'
    mfd_day_share_interest_path = 'mfd_day_share_interest.csv'
    mfd_bank_shibor_path = 'mfd_bank_shibor.csv'
    
    forecast_start_date = pd.Timestamp(2014, 9, 1)
    forecast_end_date = pd.Timestamp(2014, 9, 30)
    
    # 特征工程
    df_features = load_and_engineer_features(
        balance_csv_path=user_balance_path,
        interest_csv_path=mfd_day_share_interest_path,
        shibor_csv_path=mfd_bank_shibor_path
    )
    
    # 历史区间
    train_start = pd.Timestamp(2014, 3, 1)
    train_end = pd.Timestamp(2014, 8, 31)
    train_idx = (df_features.index >= train_start) & (df_features.index <= train_end)
    predict_idx = (df_features.index >= forecast_start_date) & (df_features.index <= forecast_end_date)
    
    # ====== 2. 构造SARIMAX外部变量 ======
    grouped_hist = df_features.loc[train_idx, ['total_purchase_amt', 'total_redeem_amt']]
    exog_hist = pd.DataFrame(index=grouped_hist.index)
    exog_hist['weekday'] = exog_hist.index.weekday
    exog_hist['is_holiday'] = exog_hist.index.map(is_special_day).astype(int)
    exog_hist = pd.get_dummies(exog_hist, columns=['weekday'], prefix='weekday').astype(int)
    
    future_dates = pd.date_range(start=forecast_start_date, end=forecast_end_date, freq='D')
    exog_future = pd.DataFrame(index=future_dates)
    exog_future['weekday'] = exog_future.index.weekday
    exog_future['is_holiday'] = exog_future.index.map(is_special_day).astype(int)
    exog_future = pd.get_dummies(exog_future, columns=['weekday'], prefix='weekday')
    for col in exog_hist.columns:
        if col not in exog_future.columns:
            exog_future[col] = 0
    exog_future = exog_future[exog_hist.columns].astype(int)
    
    # ====== 3. SARIMAX预测 ======
    sarimax_purchase = sarimax_predict(grouped_hist, 'total_purchase_amt', exog_hist, exog_future, order=(5,0,1), seasonal_order=(1,0,0,7))
    sarimax_redeem = sarimax_predict(grouped_hist, 'total_redeem_amt', exog_hist, exog_future, order=(5,1,2), seasonal_order=(1,0,0,7))
    
    # ====== 4. LightGBM预测 ======
    # 特征列（排除目标变量）
    feature_cols = [col for col in df_features.columns if col not in ['total_purchase_amt', 'total_redeem_amt']]
    for i in range(7):
        if f'weekday_{i}' not in feature_cols:
            feature_cols.append(f'weekday_{i}')
    X_train_idx = df_features.index[(df_features.index >= train_start) & (df_features.index <= train_end)]
    X_pred_idx = df_features.index[(df_features.index >= forecast_start_date) & (df_features.index <= forecast_end_date)]
    lgbm_purchase = lightgbm_predict(df_features, 'total_purchase_amt', feature_cols, X_train_idx, X_pred_idx)
    lgbm_redeem = lightgbm_predict(df_features, 'total_redeem_amt', feature_cols, X_train_idx, X_pred_idx)
    
    # ====== 5. 融合结果 ======
    fusion_purchase = [int(round(LGBM_WEIGHT * l + SARIMAX_WEIGHT * s)) for l, s in zip(lgbm_purchase, sarimax_purchase)]
    fusion_redeem = [int(round(LGBM_WEIGHT * l + SARIMAX_WEIGHT * s)) for l, s in zip(lgbm_redeem, sarimax_redeem)]
    
    # ====== 6. 输出CSV ======
    forecast_df = pd.DataFrame({
        'report_date': future_dates.strftime('%Y%m%d'),
        'purchase': fusion_purchase,
        'redeem': fusion_redeem
    })
    forecast_df.to_csv('7.lgbm_sarimax_fusion_forecast_201409.csv', index=False, header=False, encoding='utf-8')
    print('融合预测结果已保存到 7.lgbm_sarimax_fusion_forecast_201409.csv')
    
    # ====== 7. 绘制趋势图 ======
    plt.figure(figsize=(20, 8))
    # 历史
    plt.plot(grouped_hist.index, grouped_hist['total_purchase_amt'], label='申购金额-历史', color='tab:blue')
    plt.plot(grouped_hist.index, grouped_hist['total_redeem_amt'], label='赎回金额-历史', color='tab:orange')
    # 预测
    plt.plot(future_dates, fusion_purchase, label='申购金额-融合预测', color='tab:blue', linestyle='--')
    plt.plot(future_dates, fusion_redeem, label='赎回金额-融合预测', color='tab:orange', linestyle='--')
    plt.plot(future_dates, lgbm_purchase, label='申购金额-LightGBM', color='tab:green', linestyle=':')
    plt.plot(future_dates, lgbm_redeem, label='赎回金额-LightGBM', color='tab:red', linestyle=':')
    plt.plot(future_dates, sarimax_purchase, label='申购金额-SARIMAX', color='tab:cyan', linestyle='-.')
    plt.plot(future_dates, sarimax_redeem, label='赎回金额-SARIMAX', color='tab:purple', linestyle='-.')
    plt.xlabel('日期')
    plt.ylabel('金额')
    plt.title('【LightGBM+SARIMAX加权融合预测】2014-03~2014-08及未来30天每日申购与赎回金额趋势')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('7.lgbm_sarimax_fusion_trend_201409.png')
    plt.show()
    print('趋势图已保存到 7.lgbm_sarimax_fusion_trend_201409.png') 