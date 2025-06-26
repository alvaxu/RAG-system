'''
程序说明：
## 1. 本文件为8.0.5版资金流入流出预测的主流程脚本，整合了全量特征工程、训练、递归预测与输出。
## 2. 支持调试/正式模式一键切换，特征工程结果可缓存复用。
## 3. 代码结构清晰，便于后续扩展和优化。
'''
import pandas as pd
import numpy as np
import lightgbm as lgb
import random
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib
import chinese_calendar


# ========== 配置区 ==========
DEBUG = False  # True为调试模式，False为正式模式
SAMPLE_USER_NUM = 100 if DEBUG else None  # 调试时只抽样100个用户
TRAIN_MONTH = [3, 4] if DEBUG else [3,4,5,6,7,8]  # 调试时只用3、4月
PREDICT_DAYS = 5 if DEBUG else 30
SEED = 42
np.random.seed(SEED)
random.seed(SEED)
# 新增：分别设置申购和赎回模型的训练轮数
PURCHASE_N_ROUNDS = 4 if DEBUG else 30
REDEEM_N_ROUNDS = 4 if DEBUG else 30

# 路径与常量
FEATURE_PATH = '8.0.5_feature_output/8.0.5_features.parquet'
OUTPUT_DIR = '8.0.5_lgbm_output'
PREDICT_CSV = f'{OUTPUT_DIR}/8.0.5_lgbm_predict.csv'
PLOT_PATH = f'{OUTPUT_DIR}/8.0.5_lgbm_compare.png'
TARGET_PURCHASE = 'total_purchase_amt'
TARGET_REDEEM = 'total_redeem_amt'
USER_ID = 'user_id'
DATE = 'ds'

os.makedirs('8.0.5_feature_output', exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== 特征工程 ==========
def load_all_data():
    balance = pd.read_csv('user_balance_table.csv', parse_dates=['report_date'])
    balance = balance.rename(columns={'report_date': 'ds'})
    interest = pd.read_csv('mfd_day_share_interest.csv', parse_dates=['mfd_date'])
    interest = interest.rename(columns={'mfd_date': 'ds'})
    shibor = pd.read_csv('mfd_bank_shibor.csv', parse_dates=['mfd_date'])
    shibor = shibor.rename(columns={'mfd_date': 'ds'})
    profile = pd.read_csv('user_profile_table.csv')
    return balance, interest, shibor, profile

def feature_engineering(balance, interest, shibor, profile, debug=False):
    """
    :function: 生成全量特征，支持调试/正式模式
    :param balance: 用户申购赎回明细表
    :param interest: 余额宝收益率表
    :param shibor: 银行间利率表
    :param profile: 用户画像表
    :param debug: 是否为调试模式
    :return: 包含所有特征的DataFrame
    """
    # 1. 基础网格
    start_date = '2014-03-01'
    end_date = '2014-09-30'
    if debug:
        all_dates = pd.date_range(start=start_date, end='2014-03-10', freq='D')
    else:
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
    # 10. 滞后特征（只保留lag1和lag3）
    for lag in [1, 3]:
        data[f'total_purchase_amt_lag{lag}'] = data.groupby('user_id')['total_purchase_amt'].shift(lag)
        data[f'total_redeem_amt_lag{lag}'] = data.groupby('user_id')['total_redeem_amt'].shift(lag)
    # 11. 滑动窗口特征（只保留7天窗口）
    for window in [7]:
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
    return data

# ========== 数据加载与特征工程 ==========
if os.path.exists(FEATURE_PATH):
    print(f"发现已生成的特征文件，直接加载: {FEATURE_PATH}")
    df = pd.read_parquet(FEATURE_PATH)
else:
    print("未发现特征文件，开始执行完整特征工程...")
    balance, interest, shibor, profile = load_all_data()
    df = feature_engineering(balance, interest, shibor, profile, debug=DEBUG)
    df.to_parquet(FEATURE_PATH, index=False)

if DEBUG:
    print("[诊断] 特征工程后数据基本信息：")
    print(df.info())
    print("[诊断] 部分数据预览：")
    print(df.head())

# ========== 用户抽样 ==========
if SAMPLE_USER_NUM is not None:
    users = df[USER_ID].drop_duplicates().sample(SAMPLE_USER_NUM, random_state=SEED)
    df = df[df[USER_ID].isin(users)]
    print(f'调试模式：仅抽样{SAMPLE_USER_NUM}个用户')

# ========== 训练/验证/预测区间 ==========
df[DATE] = pd.to_datetime(df[DATE])
df['month'] = df[DATE].dt.month

# ========== 1. 目标变量clip到99分位数 ==========
PURCHASE_CLIP = df[TARGET_PURCHASE].quantile(0.99)
REDEEM_CLIP = df[TARGET_REDEEM].quantile(0.99)
df[TARGET_PURCHASE] = np.clip(df[TARGET_PURCHASE], 0, PURCHASE_CLIP)
df[TARGET_REDEEM] = np.clip(df[TARGET_REDEEM], 0, REDEEM_CLIP)

# ========== 2. 连续特征clip到99分位数 ==========
# 只对float和int类型且非目标变量、非用户ID、非month的特征clip
cont_cols = [col for col in df.columns if (df[col].dtype in [np.float32, np.float64, np.int32, np.int64]) and (col not in [TARGET_PURCHASE, TARGET_REDEEM, USER_ID, 'month'])]
for col in cont_cols:
    clip_val = df[col].quantile(0.99)
    df[col] = np.clip(df[col], 0, clip_val)

train_df = df[df['month'].isin(TRAIN_MONTH)]
predict_start = pd.Timestamp('2014-09-01')
predict_days = PREDICT_DAYS
predict_dates = pd.date_range(predict_start, periods=predict_days)
predict_df = df[df[DATE].isin(predict_dates)]

# ========== 特征列 ==========
NON_FEATURES = [USER_ID, DATE, TARGET_PURCHASE, TARGET_REDEEM, 'month']
# 申购Top20特征
PURCHASE_TOP20 = [
    'Interest_1_W_lag1', 'Interest_6_M_lag1', 'Interest_1_Y_lag1', 'Interest_2_W_lag1', 'mfd_daily_yield_lag1',
    'Interest_1_M_lag1', 'Interest_9_M_lag1', 'total_purchase_amt_lag1', 'Interest_O_N_lag1', 'Interest_3_M_lag1',
    'total_redeem_amt_lag1', 'mfd_7daily_yield_lag1', 'total_purchase_amt_lag3', 'total_purchase_amt_lag7',
    'total_purchase_amt_lag30', 'purchase_amt_bin', 'total_purchase_amt_lag14', 'total_redeem_amt_lag3',
    'constellation', 'day'
]
# 赎回Top20特征
REDEEM_TOP20 = [
    'mfd_daily_yield_lag1', 'Interest_3_M_lag1', 'total_redeem_amt_lag1', 'Interest_1_Y_lag1', 'total_purchase_amt_lag1',
    'Interest_1_W_lag1', 'Interest_9_M_lag1', 'mfd_7daily_yield_lag1', 'Interest_1_M_lag1', 'Interest_2_W_lag1',
    'Interest_O_N_lag1', 'Interest_6_M_lag1', 'sex_weekday', 'total_redeem_amt_lag3', 'total_purchase_amt_lag3',
    'constellation', 'total_purchase_amt_lag7', 'total_redeem_amt_lag7', 'total_purchase_amt_lag30', 'total_purchase_amt_lag14'
]
# 只保留Top20特征
PURCHASE_FEATURES = [f for f in PURCHASE_TOP20 if f in train_df.columns]
REDEEM_FEATURES = [f for f in REDEEM_TOP20 if f in train_df.columns]
PURCHASE_LAG_FEATURES = [f for f in PURCHASE_FEATURES if 'lag' in f]
REDEEM_LAG_FEATURES = [f for f in REDEEM_FEATURES if 'lag' in f]

print("==========================")
print("【特征工程阶段】")
print("--------------------------")
print(f"申购Top20特征数: {len(PURCHASE_FEATURES)}")
print("申购Top20特征名:")
print(PURCHASE_FEATURES)
print(f"赎回Top20特征数: {len(REDEEM_FEATURES)}")
print("赎回Top20特征名:")
print(REDEEM_FEATURES)
print("--------------------------")

# ========== 递归训练/混合训练主流程 ==========
def scheduled_sampling_train(train_df, target_col, features, lag_features, prob=0.5, n_rounds=4):
    df = train_df.copy()
    # 训练前目标变量clip
    clip_val = df[target_col].quantile(0.99)
    df[target_col] = np.clip(df[target_col], 0, clip_val)
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
        preds = gbm.predict(df[features])
        for lag_col in lag_features:
            mask = np.random.rand(len(df)) < prob
            df.loc[mask, lag_col] = preds[mask]
        rmse = np.sqrt(np.mean((preds - df[target_col])**2))
        print(f"[训练效果] 第{round+1}轮训练后RMSE: {rmse:.2f}")
        if round == n_rounds - 1:
            importance = gbm.feature_importance()
            feature_names = gbm.feature_name()
            print("[全部特征名]:")
            print(list(feature_names))
            print("[特征重要性Top20]:")
            for i in np.argsort(importance)[::-1][:20]:
                print(f"{feature_names[i]}: {importance[i]}")
    return gbm

# ========== 训练申购/赎回模型 ==========
print('训练申购模型...')
purchase_model = scheduled_sampling_train(train_df, TARGET_PURCHASE, PURCHASE_FEATURES, PURCHASE_LAG_FEATURES, prob=0.8, n_rounds=PURCHASE_N_ROUNDS)
print('训练赎回模型...')
redeem_model = scheduled_sampling_train(train_df, TARGET_REDEEM, REDEEM_FEATURES, REDEEM_LAG_FEATURES, prob=0.8, n_rounds=REDEEM_N_ROUNDS)

# ========== 递归预测主流程 ==========
def recursive_predict(model, base_df, features, lag_features, predict_dates, user_col, date_col, target_col):
    df = base_df.copy()
    results = []
    # 递归预测时clip
    clip_val = df[target_col].quantile(0.99)
    for d in tqdm(predict_dates, desc=f'递归预测{target_col}'):
        day_df = df[df[date_col]==d].copy()
        if day_df.empty:
            continue
        day_df['pred'] = model.predict(day_df[features])
        day_df['pred'] = np.clip(day_df['pred'], 0, clip_val)
        results.append(day_df[[user_col, date_col, 'pred']])
        for lag_col in lag_features:
            if 'lag1' in lag_col:
                idx = (df[date_col]==d)
                df.loc[idx, lag_col] = day_df['pred'].values
    return pd.concat(results, ignore_index=True)

# ========== 递归预测申购/赎回 ==========
print('递归预测申购...')
purchase_pred = recursive_predict(purchase_model, df, PURCHASE_FEATURES, PURCHASE_LAG_FEATURES, predict_dates, USER_ID, DATE, TARGET_PURCHASE)
print('递归预测赎回...')
redeem_pred = recursive_predict(redeem_model, df, REDEEM_FEATURES, REDEEM_LAG_FEATURES, predict_dates, USER_ID, DATE, TARGET_REDEEM)

# ========== 输出结果 ==========
def save_predict_csv(p_pred, r_pred, path):
    p_daily = p_pred.groupby('ds')['pred'].sum().reset_index().rename(columns={'pred': 'purchase'})
    r_daily = r_pred.groupby('ds')['pred'].sum().reset_index().rename(columns={'pred': 'redeem'})
    pred_df = pd.merge(p_daily, r_daily, on='ds', how='outer').fillna(0)
    pred_df['ds'] = pd.to_datetime(pred_df['ds']).dt.strftime('%Y%m%d')
    pred_df = pred_df.rename(columns={'ds': 'report_date'})
    pred_df[['report_date', 'purchase', 'redeem']].to_csv(path, index=False, header=False)
    print(f'预测结果已保存至: {path}')

save_predict_csv(purchase_pred, redeem_pred, PREDICT_CSV)

# ========== 可视化 ==========
def plot_compare(purchase_pred, redeem_pred, df_all):
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
    actual = df_all.groupby('ds').agg(
        actual_purchase=(TARGET_PURCHASE, 'sum'),
        actual_redeem=(TARGET_REDEEM, 'sum')
    ).reset_index()
    actual['report_date'] = pd.to_datetime(actual['ds']).dt.strftime('%Y%m%d')
    purchase_daily = purchase_pred.groupby('ds')['pred'].sum().reset_index()
    purchase_daily['report_date'] = pd.to_datetime(purchase_daily['ds']).dt.strftime('%Y%m%d')
    redeem_daily = redeem_pred.groupby('ds')['pred'].sum().reset_index()
    redeem_daily['report_date'] = pd.to_datetime(redeem_daily['ds']).dt.strftime('%Y%m%d')
    daily = pd.merge(actual[['report_date', 'actual_purchase', 'actual_redeem']],
                     purchase_daily[['report_date', 'pred']], on='report_date', how='left')
    daily = pd.merge(daily, redeem_daily[['report_date', 'pred']], on='report_date', how='left', suffixes=('_purchase', '_redeem'))
    ds = pd.to_datetime(daily['report_date'])
    fig, axes = plt.subplots(2, 1, figsize=(20, 12), sharex=True)
    axes[0].plot(ds, daily['actual_purchase'], label='申购真实值', color='blue')
    mask_pred_purchase = ~daily['pred_purchase'].isna()
    axes[0].plot(ds[mask_pred_purchase], daily['pred_purchase'][mask_pred_purchase], label='申购预测值', color='red', linestyle='--')
    axes[0].set_title('每日申购总额：真实值 vs. LightGBM递归预测值')
    axes[0].legend()
    axes[1].plot(ds, daily['actual_redeem'], label='赎回真实值', color='green')
    mask_pred_redeem = ~daily['pred_redeem'].isna()
    axes[1].plot(ds[mask_pred_redeem], daily['pred_redeem'][mask_pred_redeem], label='赎回预测值', color='red', linestyle='--')
    axes[1].set_title('每日赎回总额：真实值 vs. LightGBM递归预测值')
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(PLOT_PATH)
    plt.close()
    print(f'对比图已保存至: {PLOT_PATH}')

plot_compare(purchase_pred, redeem_pred, df) 