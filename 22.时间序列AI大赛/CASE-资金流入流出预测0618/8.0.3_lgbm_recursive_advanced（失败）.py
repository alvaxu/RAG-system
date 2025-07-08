# -*- coding: utf-8 -*-
"""
:功能: 8.0.3版 用户级LightGBM递归训练/混合训练主脚本（进阶优化可运行版）
:说明: 完整特征工程（整合8.0.0与8.0.3新增特征），递归训练/混合训练参数优化，结构清晰，注释详细。
:作者: AI助手
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import random
import os
import matplotlib.pyplot as plt
import matplotlib
import chinese_calendar
from tqdm import tqdm
import time

# ========== 配置区 ==========
DEBUG = False  # True为调试模式，False为正式模式
SAMPLE_USER_NUM = 100 if DEBUG else None  # 调试时只抽样100个用户
TRAIN_MONTH = [3, 4] if DEBUG else [3,4,5,6,7,8]  # 调试时只用3、4月
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# 递归训练/混合训练参数
SCHEDULED_SAMPLING_PROB = 0.5  # 混合概率
LAG_LIST = [1, 3, 7, 14, 30]  # 递归窗口
best_iters = {'total_purchase_amt': 2 if DEBUG else 21, 'total_redeem_amt': 2 if DEBUG else 51}  # 调试时训练轮数极小

# 目标变量变换
APPLY_LOG1P = True  # 是否对目标做log1p变换

# ========== 路径与常量 ==========
FEATURE_PATH = '8.0.3_feature_output/8.0.3_features.parquet'
OUTPUT_DIR = '8.0.3_lgbm_output'
PURCHASE_CSV = f'{OUTPUT_DIR}/8.0.3_lgbm_purchase_pred.csv'
REDEEM_CSV = f'{OUTPUT_DIR}/8.0.3_lgbm_redeem_pred.csv'
PLOT_PATH = f'{OUTPUT_DIR}/8.0.3_lgbm_compare.png'
TARGET_PURCHASE = 'total_purchase_amt'
TARGET_REDEEM = 'total_redeem_amt'
USER_ID = 'user_id'
DATE = 'ds'

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== 完整特征工程 ==========
def feature_engineering(balance, interest, shibor, profile):
    """
    :function: 全量特征工程，合并原始数据，生成所有特征
    :param balance: 用户申购赎回明细表
    :param interest: 余额宝收益率表
    :param shibor: 银行间利率表
    :param profile: 用户画像表
    :return: 包含所有特征的DataFrame
    """
    print("特征工程开始...")
    # 1. 创建基础网格：所有用户在所有日期的组合
    start_date = '2014-03-01'
    end_date = '2014-09-30'
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    all_users = pd.DataFrame({'user_id': balance['user_id'].unique()})
    base_grid = pd.MultiIndex.from_product([all_users['user_id'], all_dates], names=['user_id', 'ds'])
    base_grid = pd.DataFrame(index=base_grid).reset_index()
    # 2. 合并目标变量
    data = pd.merge(base_grid, balance[['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']], on=['user_id', 'ds'], how='left')
    data[['total_purchase_amt', 'total_redeem_amt']] = data[['total_purchase_amt', 'total_redeem_amt']].fillna(0)
    # 3. 合并用户画像
    data = pd.merge(data, profile, on='user_id', how='left')
    data['constellation'] = data['constellation'].astype(str).fillna('Unknown')
    data['sex'] = data['sex'].fillna(-1)
    data['city'] = data['city'].fillna(-1)
    data['constellation'] = data['constellation'].astype('category')
    data['sex'] = data['sex'].astype('category')
    data['city'] = data['city'].astype('category')
    # 4. 合并宏观经济数据（lag1）
    macro_features = pd.merge(interest, shibor, on='ds', how='left')
    macro_features_lag1 = macro_features.copy()
    macro_features_lag1['ds'] = macro_features_lag1['ds'] + pd.Timedelta(days=1)
    lag1_cols = {col: f'{col}_lag1' for col in macro_features_lag1.columns if col != 'ds'}
    macro_features_lag1 = macro_features_lag1.rename(columns=lag1_cols)
    data = pd.merge(data, macro_features_lag1, on='ds', how='left')
    # 5. 时间特征
    data['weekday'] = data['ds'].dt.weekday
    data['day'] = data['ds'].dt.day
    data['month'] = data['ds'].dt.month
    data['is_month_end'] = data['ds'].dt.is_month_end.astype(int)
    data['is_month_start'] = data['ds'].dt.is_month_start.astype(int)
    data['is_quarter_end'] = data['ds'].dt.is_quarter_end.astype(int)
    # 6. 节假日特征
    print('正在创建节假日特征...')
    data['is_holiday'] = data['ds'].apply(chinese_calendar.is_holiday).astype(int)
    data['is_next_workday'] = ((data['is_holiday'].shift(1) == 1) & (data['is_holiday'] == 0)).astype(int)
    data['month_period'] = data['ds'].apply(lambda x: 'begin' if x.day <= 10 else ('middle' if x.day <= 20 else 'end'))
    data['is_festival_eve'] = ((data['is_holiday'].shift(-1) == 1) & (data['is_holiday'] == 0)).astype(int)
    # 7. 冷启动特征
    train_users = set(balance[balance['ds'] < '2014-09-01']['user_id'].unique())
    data['is_new_user'] = data.apply(lambda row: 1 if row['ds'].month == 9 and row['user_id'] not in train_users else 0, axis=1)
    # 8. 交互特征
    data['city_is_holiday'] = data['city'].astype(str) + '_' + data['is_holiday'].astype(str)
    data['sex_weekday'] = data['sex'].astype(str) + '_' + data['weekday'].astype(str)
    # 9. 用户活跃度特征
    data = data.sort_values(['user_id', 'ds'])
    data['days_since_last_purchase'] = data.groupby('user_id')['ds'].diff().dt.days.fillna(0)
    data['purchase_count_30d'] = data.groupby('user_id')['total_purchase_amt'].shift(1).rolling(window=30, min_periods=1).apply(lambda x: (x>0).sum()).reset_index(level=0, drop=True)
    data['purchase_amt_bin'] = pd.qcut(data['total_purchase_amt'].shift(1)+1, 5, labels=False, duplicates='drop')
    # 10. 滞后特征
    for lag in LAG_LIST:
        data[f'total_purchase_amt_lag{lag}'] = data.groupby('user_id')['total_purchase_amt'].shift(lag)
        data[f'total_redeem_amt_lag{lag}'] = data.groupby('user_id')['total_redeem_amt'].shift(lag)
    # 11. 滑动窗口特征
    for window in [7, 14, 30]:
        data[f'total_purchase_amt_mean_{window}d'] = data.groupby('user_id')['total_purchase_amt'].shift(1).rolling(window=window, min_periods=1).mean().reset_index(0, drop=True)
        data[f'total_redeem_amt_mean_{window}d'] = data.groupby('user_id')['total_redeem_amt'].shift(1).rolling(window=window, min_periods=1).mean().reset_index(0, drop=True)
        data[f'total_purchase_amt_sum_{window}d'] = data.groupby('user_id')['total_purchase_amt'].shift(1).rolling(window=window, min_periods=1).sum().reset_index(0, drop=True)
        data[f'total_redeem_amt_sum_{window}d'] = data.groupby('user_id')['total_redeem_amt'].shift(1).rolling(window=window, min_periods=1).sum().reset_index(0, drop=True)
        data[f'total_purchase_amt_std_{window}d'] = data.groupby('user_id')['total_purchase_amt'].shift(1).rolling(window=window, min_periods=1).std().reset_index(0, drop=True)
        data[f'total_redeem_amt_std_{window}d'] = data.groupby('user_id')['total_redeem_amt'].shift(1).rolling(window=window, min_periods=1).std().reset_index(0, drop=True)
    # 12. 缺失值填充和类型转换
    num_cols = data.select_dtypes(include=[np.number]).columns
    data[num_cols] = data[num_cols].fillna(0)
    obj_cols = data.select_dtypes(include=['object']).columns
    for col in obj_cols:
        data[col] = data[col].fillna('Unknown')
        data[col] = data[col].astype('category')
    # category类型不做0填充，已在上面处理
    print("特征工程完成。")
    return data

# ========== 加载原始数据函数 ========== 
def load_all_data():
    """
    :function: 读取所有原始csv数据，返回标准化后的DataFrame
    :return: balance, interest, shibor, profile
    """
    print("开始加载原始数据...")
    # 用户申购赎回明细
    balance = pd.read_csv('user_balance_table.csv', parse_dates=['report_date'])
    balance = balance.rename(columns={'report_date': 'ds'})
    # 余额宝收益率
    interest = pd.read_csv('mfd_day_share_interest.csv', parse_dates=['mfd_date'])
    interest = interest.rename(columns={'mfd_date': 'ds'})
    # 银行间利率
    shibor = pd.read_csv('mfd_bank_shibor.csv', parse_dates=['mfd_date'])
    shibor = shibor.rename(columns={'mfd_date': 'ds'})
    # 用户画像
    profile = pd.read_csv('user_profile_table.csv')
    print("原始数据加载完成。")
    return balance, interest, shibor, profile

# ========== 数据加载 ==========
if os.path.exists(FEATURE_PATH):
    print(f"发现已生成的特征文件，直接加载: {FEATURE_PATH}")
    df = pd.read_parquet(FEATURE_PATH)
else:
    print("未发现特征文件，开始执行完整特征工程...")
    # 读取原始数据
    balance, interest, shibor, profile = load_all_data()
    df = feature_engineering(balance, interest, shibor, profile)
    os.makedirs('8.0.3_feature_output', exist_ok=True)
    df.to_parquet(FEATURE_PATH, index=False)

# ========== 诊断：特征工程后数据检查 ==========
if DEBUG:
    print("\n[诊断] 特征工程后数据基本信息：")
    print(df.info())
    print("[诊断] 部分数据预览：")
    print(df.head())
    print("[诊断] 缺失值统计：")
    print(df.isnull().sum())
    print("[诊断] 目标变量申购/赎回描述统计：")
    print(df[['total_purchase_amt', 'total_redeem_amt']].describe())

# ========== 用户抽样 ==========
if SAMPLE_USER_NUM is not None:
    users = df[USER_ID].drop_duplicates().sample(SAMPLE_USER_NUM, random_state=SEED)
    df = df[df[USER_ID].isin(users)]
    print(f'调试模式：仅抽样{SAMPLE_USER_NUM}个用户')

# ========== 训练/验证/预测区间 ==========
df[DATE] = pd.to_datetime(df[DATE])
df['month'] = df[DATE].dt.month
train_df = df[df['month'].isin(TRAIN_MONTH)]
predict_start = pd.Timestamp('2014-09-01')
predict_days = 5 if DEBUG else 30  # 调试时只预测5天
predict_dates = pd.date_range(predict_start, periods=predict_days)
predict_df = df[df[DATE].isin(predict_dates)]

# ========== 目标变量变换 ==========
def transform_target(y):
    if APPLY_LOG1P:
        y = np.log1p(y)
    return y

def inverse_transform_target(y):
    if APPLY_LOG1P:
        y = np.expm1(y)
    return y

# ========== 递归训练/混合训练主流程 ==========
def scheduled_sampling_train(train_df, target_col, features, lag_features, prob=0.5, n_rounds=10):
    """
    :function: 递归训练/混合训练主流程，支持混合概率、递归窗口、目标变换
    :param train_df: 训练集DataFrame
    :param target_col: 目标列名
    :param features: 特征列名列表
    :param lag_features: lag特征列名列表
    :param prob: 用预测值替换真实lag的概率
    :param n_rounds: 训练轮数
    :return: 训练好的LightGBM模型
    """
    df = train_df.copy()
    y = transform_target(df[target_col])
    for round in range(n_rounds):
        print(f'混合训练第{round+1}轮...')
        lgb_train = lgb.Dataset(df[features], y)
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'learning_rate': 0.1,
            'seed': SEED,
            'verbosity': -1,
        }
        gbm = lgb.train(params, lgb_train, num_boost_round=30)
        preds = gbm.predict(df[features])
        # 按概率用预测值替换lag特征
        for lag_col in lag_features:
            mask = np.random.rand(len(df)) < prob
            df.loc[mask, lag_col] = inverse_transform_target(preds[mask])
        # ========== 诊断：训练过程 ==========
        if DEBUG:
            rmse = np.sqrt(np.mean((inverse_transform_target(preds) - df[target_col])**2))
            print(f"[诊断] 第{round+1}轮训练后RMSE: {rmse:.2f}")
            if round == n_rounds - 1:
                importance = gbm.feature_importance()
                feature_names = gbm.feature_name()
                print("[诊断] 特征重要性Top10：")
                for i in np.argsort(importance)[::-1][:10]:
                    print(f"{feature_names[i]}: {importance[i]}")
    return gbm

# ========== 训练申购/赎回模型 ==========
print('训练申购模型...')
purchase_n_rounds = best_iters['total_purchase_amt']

# BUG FIX: Decouple models and remove incorrectly handled rolling window features.
# This is the definitive fix for the flat-line prediction issue.
all_features = [c for c in train_df.columns if c not in [USER_ID, DATE, TARGET_PURCHASE, TARGET_REDEEM]]

# 1. Isolate base features (no purchase or redeem history)
base_features = [c for c in all_features if 'purchase' not in c and 'redeem' not in c]

# 2. Create feature set for Purchase model
# Only use purchase-related history and only use lag features (which are updated correctly in recursion)
purchase_history_features = [c for c in all_features if 'purchase' in c and 'lag' in c]
purchase_features = base_features + purchase_history_features
purchase_lag_features = [c for c in purchase_features if 'lag' in c]
print(f"申购模型将使用 {len(purchase_features)} 个特征。")

purchase_model = scheduled_sampling_train(train_df, TARGET_PURCHASE, purchase_features, purchase_lag_features, prob=SCHEDULED_SAMPLING_PROB, n_rounds=purchase_n_rounds)

print('训练赎回模型...')
redeem_n_rounds = best_iters['total_redeem_amt']
# 3. Create feature set for Redeem model
# Only use redeem-related history and only use lag features
redeem_history_features = [c for c in all_features if 'redeem' in c and 'lag' in c]
redeem_features = base_features + redeem_history_features
redeem_lag_features = [c for c in redeem_features if 'lag' in c]
print(f"赎回模型将使用 {len(redeem_features)} 个特征。")

redeem_model = scheduled_sampling_train(train_df, TARGET_REDEEM, redeem_features, redeem_lag_features, prob=SCHEDULED_SAMPLING_PROB, n_rounds=redeem_n_rounds)

# ========== 递归预测主流程（向量化重构，大幅提速） ==========
def recursive_predict(model, base_df, features, lag_features, predict_dates, user_col, date_col, target_col):
    """
    :function: (向量化重构版)递归预测主流程，大幅提升性能
    :param model: 训练好的LightGBM模型
    :param base_df: 包含历史真实数据的DataFrame
    :param features: 特征列名列表
    :param lag_features: lag特征名列表（此版本中未使用，通过target_col和LAG_LIST自动生成）
    :param predict_dates: 预测日期列表
    :param user_col: 用户ID列名
    :param date_col: 日期列名
    :param target_col: 目标列名
    :return: 预测结果DataFrame（所有用户、所有预测天）
    """
    df = base_df.copy()
    results = []
    start_time = time.time()
    total_days = len(predict_dates)

    for idx, d in enumerate(tqdm(predict_dates, desc=f'递归预测 {target_col}')):
        # 1. 获取当天的特征矩阵
        day_idx = df[date_col] == d
        day_df = df.loc[day_idx]
        if day_df.empty:
            continue

        # 2. 预测
        day_preds = inverse_transform_target(model.predict(day_df[features]))

        # 3. 保存结果
        result_df = pd.DataFrame({user_col: day_df[user_col].values, date_col: d, 'pred': day_preds})
        results.append(result_df)

        # 4. (核心优化) 向量化更新未来日期的lag特征
        # 将当日预测结果转换为以user_id为索引的Series，便于高效匹配
        preds_for_merge = result_df.set_index(user_col)['pred']
        
        for lag in LAG_LIST:
            future_date = d + pd.Timedelta(days=lag)
            if future_date > predict_dates[-1]:
                continue
            
            # 定位未来日期的行索引
            future_day_idx = df.index[df[date_col] == future_date]
            if future_day_idx.empty:
                continue

            # 获取未来日期的用户，并匹配上当天的预测值
            future_users = df.loc[future_day_idx, user_col]
            mapped_preds = future_users.map(preds_for_merge).fillna(0)
            
            # 使用.loc和索引进行高效的列更新，这是性能提升的关键
            df.loc[future_day_idx, f'{target_col}_lag{lag}'] = mapped_preds.values

        # 进度反馈
        elapsed = time.time() - start_time
        avg_per_day = elapsed / (idx + 1)
        eta = avg_per_day * (total_days - idx - 1)
        tqdm.write(f"\n[递归预测进度] {target_col}: 第{idx+1}/{total_days}天 {d.date()} 已完成, 耗时{elapsed:.1f}s, 预计剩余{eta:.1f}s")

    return pd.concat(results, ignore_index=True)

# ========== 递归预测申购/赎回 ==========
print('递归预测申购...')
purchase_pred = recursive_predict(purchase_model, df, purchase_features, purchase_lag_features, predict_dates, USER_ID, DATE, TARGET_PURCHASE)
print('递归预测赎回...')
redeem_pred = recursive_predict(redeem_model, df, redeem_features, redeem_lag_features, predict_dates, USER_ID, DATE, TARGET_REDEEM)

# ========== 诊断：预测结果 ==========
if DEBUG:
    print("[诊断] 申购预测结果统计：")
    print(purchase_pred['pred'].describe())
    print("[诊断] 赎回预测结果统计：")
    print(redeem_pred['pred'].describe())

# ========== 输出结果 ==========
ensure_output_dir()
purchase_pred.to_csv(PURCHASE_CSV, index=False)
redeem_pred.to_csv(REDEEM_CSV, index=False)
print('预测结果已保存！')

# ========== 诊断：输出文件检查 ==========
if DEBUG:
    import os
    print(f"[诊断] 申购预测文件大小: {os.path.getsize(PURCHASE_CSV)/1024:.1f} KB")
    print(f"[诊断] 赎回预测文件大小: {os.path.getsize(REDEEM_CSV)/1024:.1f} KB")
    print("[诊断] 申购预测文件前5行：")
    print(pd.read_csv(PURCHASE_CSV).head())
    print("[诊断] 赎回预测文件前5行：")
    print(pd.read_csv(REDEEM_CSV).head())

# ========== 可视化 ==========
def plot_compare(purchase_pred, redeem_pred, df_all):
    """
    :function: 生成申购/赎回对比图，x轴覆盖所有日期，真实值曲线完整画出，预测值只在有数据区间画出
    """
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
    # 聚合真实值
    actual = df_all.groupby('ds').agg(
        actual_purchase=(TARGET_PURCHASE, 'sum'),
        actual_redeem=(TARGET_REDEEM, 'sum')
    ).reset_index()
    actual['report_date'] = pd.to_datetime(actual['ds']).dt.strftime('%Y%m%d')
    # 聚合预测值
    purchase_daily = purchase_pred.groupby('ds')['pred'].sum().reset_index()
    purchase_daily['report_date'] = pd.to_datetime(purchase_daily['ds']).dt.strftime('%Y%m%d')
    redeem_daily = redeem_pred.groupby('ds')['pred'].sum().reset_index()
    redeem_daily['report_date'] = pd.to_datetime(redeem_daily['ds']).dt.strftime('%Y%m%d')
    # 合并
    daily = pd.merge(actual[['report_date', 'actual_purchase', 'actual_redeem']],
                     purchase_daily[['report_date', 'pred']], on='report_date', how='left')
    daily = pd.merge(daily, redeem_daily[['report_date', 'pred']], on='report_date', how='left', suffixes=('_purchase', '_redeem'))
    ds = pd.to_datetime(daily['report_date'])
    fig, axes = plt.subplots(2, 1, figsize=(20, 12), sharex=True)
    # 申购
    axes[0].plot(ds, daily['actual_purchase'], label='申购真实值', color='blue')
    mask_pred_purchase = ~daily['pred_purchase'].isna()
    axes[0].plot(ds[mask_pred_purchase], daily['pred_purchase'][mask_pred_purchase], label='申购预测值', color='red', linestyle='--')
    axes[0].set_title('每日申购总额：真实值 vs. LightGBM递归预测值')
    axes[0].legend()
    # 赎回
    axes[1].plot(ds, daily['actual_redeem'], label='赎回真实值', color='green')
    mask_pred_redeem = ~daily['pred_redeem'].isna()
    axes[1].plot(ds[mask_pred_redeem], daily['pred_redeem'][mask_pred_redeem], label='赎回预测值', color='red', linestyle='--')
    axes[1].set_title('每日赎回总额：真实值 vs. LightGBM递归预测值')
    axes[1].legend()
    # 背景色区间
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
    plt.savefig(PLOT_PATH)
    plt.close()
    print(f'对比图已保存至: {PLOT_PATH}')

# ========== 可视化调用 ==========
if not DEBUG:
    plot_compare(purchase_pred, redeem_pred, df)

# ========== 说明 ==========
# 1. 本脚本为进阶优化可运行版，后续可继续完善特征工程、目标变换、递归窗口、混合概率等。
# 2. 需提前准备好用户级特征数据（如8.0.0_feature_output/8.0.0_features.parquet）。 