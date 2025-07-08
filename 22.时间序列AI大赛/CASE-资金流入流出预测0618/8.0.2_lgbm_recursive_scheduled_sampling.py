# -*- coding: utf-8 -*-
"""
:功能: 用户级LightGBM递归训练/混合训练（Scheduled Sampling）主脚本（8.0.2版，极致调试模式）
:说明: 先实现极致调试模式（只抽样500用户、只用7月训练、只递归3天），保证代码能快速跑通且无语法错误。结构清晰，便于后续切换到正式模式。
:作者: AI助手
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import random
from tqdm import tqdm
import os
import matplotlib.pyplot as plt
import matplotlib

def ensure_output_dir():
    """
    :function: 自动创建输出目录
    :return: None
    """
    os.makedirs('8.0.2_lgbm_output', exist_ok=True)

# ========== 配置区 ==========
DEBUG = False  # True为极致调试模式，False为正式模式
SAMPLE_USER_NUM = 500 if DEBUG else None  # 调试时只抽样500用户
TRAIN_MONTH = [7] if DEBUG else [3,4,5,6,7,8]  # 调试时只用7月
RECURSIVE_DAYS = 3 if DEBUG else 30  # 调试时只递归3天
SCHEDULED_SAMPLING_PROB = 0.5  # 混合训练时用预测值替换真实lag的概率
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# 递归验证得到的最佳迭代次数（请根据实际结果填写）
best_iters = {'total_purchase_amt': 4, 'total_redeem_amt': 4}  # 示例值，请替换为你实际的best_iter

# ========== 数据加载（请根据实际路径调整） ==========
# 假设已生成用户级特征数据: user_level_features.csv
FEATURE_PATH = '8.0.0_feature_output/8.0.0_features.parquet'  # 需提前生成
TARGET_PURCHASE = 'total_purchase_amt'
TARGET_REDEEM = 'total_redeem_amt'
USER_ID = 'user_id'
DATE = 'ds'

# ========== 读取数据 ==========
print('读取特征数据...')
df = pd.read_parquet(FEATURE_PATH)

# ========== 用户抽样 ==========
if SAMPLE_USER_NUM is not None:
    users = df[USER_ID].drop_duplicates().sample(SAMPLE_USER_NUM, random_state=SEED)
    df = df[df[USER_ID].isin(users)]
    print(f'调试模式：仅抽样{SAMPLE_USER_NUM}个用户')

# ========== 训练/验证/预测区间 ==========
df[DATE] = pd.to_datetime(df[DATE])
df['month'] = df[DATE].dt.month
train_df = df[df['month'].isin(TRAIN_MONTH)]
# 预测区间：9月1日到9月30日
predict_start = pd.Timestamp('2014-09-01')
predict_days = 30
predict_dates = pd.date_range(predict_start, periods=predict_days)
predict_df = df[df[DATE].isin(predict_dates)]

# ========== 特征列 ==========
# 过滤掉目标、用户、日期等非特征列
NON_FEATURES = [USER_ID, DATE, TARGET_PURCHASE, TARGET_REDEEM, 'month']
FEATURES = [c for c in train_df.columns if c not in NON_FEATURES]
LAG_FEATURES = [c for c in FEATURES if 'lag' in c]

# ========== 递归训练/混合训练主流程 ==========
def scheduled_sampling_train(train_df, target_col, features, lag_features, prob=0.5, n_rounds=10):
    """
    :function: 递归训练/混合训练主流程
    :param train_df: 训练集DataFrame
    :param target_col: 目标列名
    :param features: 特征列名列表
    :param lag_features: lag特征列名列表
    :param prob: 用预测值替换真实lag的概率
    :param n_rounds: 训练轮数
    :return: 训练好的LightGBM模型
    """
    df = train_df.copy()
    for round in range(n_rounds):
        print(f'混合训练第{round+1}轮...')
        lgb_train = lgb.Dataset(df[features], df[target_col])
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'learning_rate': 0.1,
            'seed': SEED,
            'verbosity': -1,
        }
        gbm = lgb.train(params, lgb_train, num_boost_round=30)
        # 生成预测值
        preds = gbm.predict(df[features])
        # 按概率用预测值替换lag特征
        for lag_col in lag_features:
            mask = np.random.rand(len(df)) < prob
            df.loc[mask, lag_col] = preds[mask]
            
    return gbm

# ========== 训练申购模型 ==========
print('训练申购模型...')
purchase_n_rounds = 3 if DEBUG else best_iters['total_purchase_amt']
purchase_model = scheduled_sampling_train(train_df, TARGET_PURCHASE, FEATURES, LAG_FEATURES, prob=SCHEDULED_SAMPLING_PROB, n_rounds=purchase_n_rounds)

# ========== 训练赎回模型 ==========
print('训练赎回模型...')
redeem_n_rounds = 3 if DEBUG else best_iters['total_redeem_amt']
redeem_model = scheduled_sampling_train(train_df, TARGET_REDEEM, FEATURES, LAG_FEATURES, prob=SCHEDULED_SAMPLING_PROB, n_rounds=redeem_n_rounds)

# ========== 递归预测主流程 ==========
def recursive_predict(model, base_df, features, lag_features, predict_dates, user_col, date_col, target_col):
    """
    :function: 递归预测主流程
    :param model: 训练好的LightGBM模型
    :param base_df: 包含历史真实数据的DataFrame
    :param features: 特征列名列表
    :param lag_features: lag特征列名列表
    :param predict_dates: 预测日期列表
    :param user_col: 用户ID列名
    :param date_col: 日期列名
    :param target_col: 目标列名
    :return: 预测结果DataFrame
    """
    df = base_df.copy()
    results = []
    for d in predict_dates:
        day_df = df[df[date_col]==d].copy()
        if day_df.empty:
            continue
        # 预测
        day_df['pred'] = model.predict(day_df[features])
        results.append(day_df[[user_col, date_col, 'pred']])
        # lag特征递归更新
        for lag_col in lag_features:
            # 只更新当天的lag1（如有），更高阶lag可按需实现
            if 'lag1' in lag_col:
                idx = (df[date_col]==d)
                df.loc[idx, lag_col] = day_df['pred'].values
    return pd.concat(results, ignore_index=True)

# ========== 递归预测申购 ==========
print('递归预测申购...')
purchase_pred = recursive_predict(purchase_model, df, FEATURES, LAG_FEATURES, predict_dates, USER_ID, DATE, TARGET_PURCHASE)

# ========== 递归预测赎回 ==========
print('递归预测赎回...')
redeem_pred = recursive_predict(redeem_model, df, FEATURES, LAG_FEATURES, predict_dates, USER_ID, DATE, TARGET_REDEEM)

# ========== 输出结果 ==========
ensure_output_dir()
purchase_pred.to_csv('8.0.2_lgbm_output/8.0.2_lgbm_purchase_pred_debug.csv', index=False)
redeem_pred.to_csv('8.0.2_lgbm_output/8.0.2_lgbm_redeem_pred_debug.csv', index=False)
print('调试模式预测完成！')

# ========== 正式输出与可视化 ==========
def aggregate_and_save(purchase_pred, redeem_pred=None, df_all=None):
    """
    :function: 聚合每日总量并输出正式预测csv，同时聚合真实值，保证3-9月所有日期都在daily
    :param purchase_pred: 申购预测DataFrame（user_id, ds, pred）
    :param redeem_pred: 赎回预测DataFrame（user_id, ds, pred），可选
    :param df_all: 全量原始特征DataFrame（含真实值）
    :return: 聚合后的DataFrame，含真实值
    """
    # 聚合真实值（以所有日期为主）
    if df_all is not None:
        actual = df_all.groupby('ds').agg(
            actual_purchase=(TARGET_PURCHASE, 'sum'),
            actual_redeem=(TARGET_REDEEM, 'sum')
        ).reset_index()
        actual['report_date'] = pd.to_datetime(actual['ds']).dt.strftime('%Y%m%d')
        all_dates = actual[['report_date', 'actual_purchase', 'actual_redeem']]
    else:
        all_dates = None
    # 聚合每日申购预测
    purchase_daily = purchase_pred.groupby('ds')['pred'].sum().reset_index()
    purchase_daily = purchase_daily.rename(columns={'pred': 'purchase'})
    purchase_daily['report_date'] = pd.to_datetime(purchase_daily['ds']).dt.strftime('%Y%m%d')
    # 赎回预测
    if redeem_pred is not None:
        redeem_daily = redeem_pred.groupby('ds')['pred'].sum().reset_index()
        redeem_daily = redeem_daily.rename(columns={'pred': 'redeem'})
        redeem_daily['report_date'] = pd.to_datetime(redeem_daily['ds']).dt.strftime('%Y%m%d')
        pred_df = pd.merge(purchase_daily[['report_date', 'purchase']], redeem_daily[['report_date', 'redeem']], on='report_date', how='outer')
    else:
        pred_df = purchase_daily[['report_date', 'purchase']]
        pred_df['redeem'] = 0
    # 合并所有日期（以真实值为主，外连接预测结果）
    if all_dates is not None:
        daily = pd.merge(all_dates, pred_df, on='report_date', how='left')
    else:
        daily = pred_df
    # 输出csv（无表头，三列：日期、申购、赎回）
    out_path = '8.0.2_lgbm_output/8.0.2_lgbm_predict.csv'
    daily[['report_date', 'purchase', 'redeem']].to_csv(out_path, index=False, header=False)
    print(f'正式预测结果已保存至: {out_path}')
    return daily


def plot_compare(daily):
    """
    :function: 生成申购/赎回对比图，x轴覆盖所有日期，真实值曲线完整画出，预测值只在有数据区间画出
    :param daily: 聚合后的DataFrame，含report_date, purchase, redeem, actual_purchase, actual_redeem
    :return: None
    """
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(2, 1, figsize=(20, 12), sharex=True)
    ds = pd.to_datetime(daily['report_date'])
    # 申购
    if 'actual_purchase' in daily.columns:
        axes[0].plot(ds, daily['actual_purchase'], label='申购真实值', color='blue')
    mask_pred_purchase = ~daily['purchase'].isna()
    axes[0].plot(ds[mask_pred_purchase], daily['purchase'][mask_pred_purchase], label='申购预测值', color='red', linestyle='--')
    axes[0].set_title('每日申购总额：真实值 vs. LightGBM递归预测值')
    axes[0].legend()
    # 赎回
    if 'actual_redeem' in daily.columns:
        axes[1].plot(ds, daily['actual_redeem'], label='赎回真实值', color='green')
    mask_pred_redeem = ~daily['redeem'].isna()
    axes[1].plot(ds[mask_pred_redeem], daily['redeem'][mask_pred_redeem], label='赎回预测值', color='red', linestyle='--')
    axes[1].set_title('每日赎回总额：真实值 vs. LightGBM递归预测值')
    axes[1].legend()
    # 背景色区间自动判断
    min_date = ds.min()
    max_date = ds.max()
    train_start = pd.to_datetime('2014-03-01')
    train_end = pd.to_datetime('2014-07-31')
    valid_start = pd.to_datetime('2014-08-01')
    valid_end = pd.to_datetime('2014-08-31')
    pred_start = pd.to_datetime('2014-09-01')
    pred_end = pd.to_datetime('2014-09-30')
    if (train_start <= max_date and train_end >= min_date):
        axes[0].axvspan(max(train_start, min_date), min(train_end, max_date), color='lightblue', alpha=0.15, label='训练集')
        axes[1].axvspan(max(train_start, min_date), min(train_end, max_date), color='lightblue', alpha=0.15)
    if (valid_start <= max_date and valid_end >= min_date):
        axes[0].axvspan(max(valid_start, min_date), min(valid_end, max_date), color='gray', alpha=0.2, label='验证集')
        axes[1].axvspan(max(valid_start, min_date), min(valid_end, max_date), color='gray', alpha=0.2)
    if (pred_start <= max_date and pred_end >= min_date):
        axes[0].axvspan(max(pred_start, min_date), min(pred_end, max_date), color='orange', alpha=0.2, label='预测集')
        axes[1].axvspan(max(pred_start, min_date), min(pred_end, max_date), color='orange', alpha=0.2)
    axes[0].grid(True, linestyle='--', alpha=0.5)
    axes[1].grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    out_path = '8.0.2_lgbm_output/8.0.2_lgbm_compare.png'
    plt.savefig(out_path)
    plt.close()
    print(f'对比图已保存至: {out_path}')

# ========== 正式流程示例调用 ==========
if not DEBUG:
    ensure_output_dir()
    daily = aggregate_and_save(purchase_pred, redeem_pred, df_all=df)
    plot_compare(daily)

# ========== 说明 ==========
# 1. 本脚本为极致调试模式，正式模式请将DEBUG=False，并调整相关参数。
# 2. 赎回模型训练与申购类似，可仿照实现。
# 3. 递归预测时可加上下限保护，lag特征窗口可扩展。
# 4. 需提前准备好用户级特征数据（如8.0.0_feature_output/8.0.0_features.parquet）。 