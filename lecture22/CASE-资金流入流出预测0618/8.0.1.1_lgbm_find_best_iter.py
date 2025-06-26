# 8.0.1.1_lgbm_find_best_iter.py
# 功能: 在中等规模的抽样数据上，通过科学的"递归验证"方法，找到最佳的迭代次数（best_iter）
# 核心思路：
# 1. 随机抽取一部分用户（如5000名）的数据。
# 2. 在这部分数据上，运行带有"递归验证"的手动早停训练循环。
# 3. 脚本的唯一输出是申购和赎回模型的最佳迭代次数，用于第二步的最终训练。
# --- 最佳迭代次数搜索完毕 ---
# 请将以下值手动填入 8.0.1.2_lgbm_final_predict.py 文件中:
# best_iters = {'total_purchase_amt': 1, 'total_redeem_amt': 51}

import pandas as pd
import numpy as np
import lightgbm as lgb
from datetime import datetime, timedelta
import os
import gc
import matplotlib.pyplot as plt
import matplotlib
import chinese_calendar

# ========== 1. 环境与参数设置 ==========
def setup_environment():
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False   
    os.makedirs('8.0.1_feature_output', exist_ok=True)
    os.makedirs('8.0.1_lgbm_output', exist_ok=True)
    print("环境设置完毕，8.0.1输出目录已创建。")

def load_all_data():
    """加载所有需要的数据文件"""
    print("开始加载数据...")
    balance = pd.read_csv('user_balance_table.csv', parse_dates=['report_date'])
    interest = pd.read_csv('mfd_day_share_interest.csv', parse_dates=['mfd_date'])
    shibor = pd.read_csv('mfd_bank_shibor.csv', parse_dates=['mfd_date'])
    profile = pd.read_csv('user_profile_table.csv')
    
    balance = balance.rename(columns={'report_date': 'ds'})
    interest = interest.rename(columns={'mfd_date': 'ds'})
    shibor = shibor.rename(columns={'mfd_date': 'ds'})
    
    print("数据加载完成。")
    return balance, interest, shibor, profile

# ========== 2. 特征工程 ==========
def create_dynamic_features(df):
    """
    为给定的DataFrame创建动态的、依赖于历史交易的特征。
    这个函数现在被设计为可以在循环中高效重复调用。
    """
    print("    创建动态特征...")
    
    # --- 2.1 用户历史行为滞后特征 (近期) ---
    lag_targets = ['total_purchase_amt', 'total_redeem_amt']
    lags = [1, 2, 3, 7, 14] 
    for col in lag_targets:
        for lag in lags:
            df[f'{col}_lag{lag}'] = df.groupby('user_id')[col].shift(lag)

    # --- 2.2 滑动窗口特征 (近期) ---
    windows = [7, 14]
    for window in windows:
        for col in ['total_purchase_amt', 'total_redeem_amt']:
            shifted_data = df.groupby('user_id')[col].shift(1)
            rolling_stats = shifted_data.rolling(window=window, min_periods=1)
            df[f'{col}_mean_{window}d'] = df.groupby('user_id')[col].shift(1).rolling(window=window, min_periods=1).mean().reset_index(0,drop=True)
            df[f'{col}_sum_{window}d'] = df.groupby('user_id')[col].shift(1).rolling(window=window, min_periods=1).sum().reset_index(0,drop=True)
            df[f'{col}_std_{window}d'] = df.groupby('user_id')[col].shift(1).rolling(window=window, min_periods=1).std().reset_index(0,drop=True)
            
    # --- 2.3 填充 ---
    dynamic_feature_cols = [f'{c}_lag{l}' for c in lag_targets for l in lags] + \
                           [f'{c}_{s}_{w}d' for c in lag_targets for s in ['mean', 'sum', 'std'] for w in windows]
    
    for col in dynamic_feature_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    return df

# ========== 3. 模型训练与递归预测 ==========
def find_best_iteration(data):
    """在抽样数据上，通过递归验证找到最佳迭代次数"""
    print("模型训练与递归预测开始...")
    
    # --- 3.1 划分历史数据用于训练 ---
    train_start, train_end = '2014-03-01', '2014-07-31'
    valid_start, valid_end = '2014-08-01', '2014-08-31'

    train_valid_data = data[data['ds'] <= valid_end].copy()
    train_valid_data = create_dynamic_features(train_valid_data)
    
    train_df = train_valid_data[train_valid_data['ds'].between(train_start, train_end)]
    valid_df = train_valid_data[train_valid_data['ds'].between(valid_start, valid_end)]

    # --- 3.2 定义特征列和模型参数 ---
    features = [col for col in train_valid_data.columns if col not in ['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']]
    categorical_features = ['sex', 'city', 'constellation', 'weekday', 'month', 
                            'is_month_end', 'is_month_start', 'is_new_user', 'is_holiday', 
                            'is_next_workday', 'month_period', 'is_quarter_end', 'is_festival_eve']
    features = [f for f in features if f not in categorical_features] + [c for c in categorical_features if c in features]

    params = {
        'objective': 'regression_l2', 'metric': 'rmse', 'n_estimators': 1000, 'learning_rate': 0.01,
        'feature_fraction': 0.8, 'bagging_fraction': 0.8, 'bagging_freq': 1, 'lambda_l1': 0.1, 'lambda_l2': 0.1,
        'num_leaves': 31, 'verbose': -1, 'n_jobs': -1, 'seed': 42, 'boosting_type': 'gbdt',
    }

    # --- 3.3 带递归验证的手动早停训练 ---
    print("\n--- 开始进行带递归验证的训练 ---")
    best_iters = {}
    
    for target in ['total_purchase_amt', 'total_redeem_amt']:
        print(f"\n--- 正在寻找 {target} 模型的最佳迭代次数 ---")
        
        train_set = lgb.Dataset(train_df[features], label=train_df[target], categorical_feature='auto')
        
        model = lgb.Booster(params, train_set)
        best_rmse = float('inf')
        best_iter = -1
        patience = 0
        early_stopping_rounds = 50

        for i in range(params['n_estimators']):
            model.update()

            hist_for_validation = train_valid_data[train_valid_data['ds'] < valid_start].copy()
            validation_dates = pd.date_range(start=valid_start, end=valid_end, freq='D')
            
            recursive_valid_df = pd.concat([
                hist_for_validation,
                valid_df[valid_df['ds'].isin(validation_dates)][['user_id', 'ds'] + features]
            ]).sort_values(['user_id', 'ds']).reset_index(drop=True)

            for on_date in validation_dates:
                recursive_valid_df = create_dynamic_features(recursive_valid_df)
                today_df = recursive_valid_df[recursive_valid_df['ds'] == on_date]
                preds = model.predict(today_df[features])
                recursive_valid_df.loc[today_df.index, target] = np.maximum(0, preds)
            
            predicted_values = recursive_valid_df.loc[recursive_valid_df['ds'].isin(validation_dates), ['user_id', 'ds', target]]
            actual_values = valid_df.loc[valid_df['ds'].isin(validation_dates), ['user_id', 'ds', target]]
            eval_df = pd.merge(actual_values, predicted_values, on=['user_id', 'ds'], suffixes=('_actual', '_pred'))
            current_rmse = np.sqrt(np.mean((eval_df[f'{target}_actual'] - eval_df[f'{target}_pred'])**2))

            print(f"Iter {i+1}, Recursive Valid RMSE: {current_rmse:.2f}")

            if current_rmse < best_rmse:
                best_rmse = current_rmse
                best_iter = i + 1
                patience = 0
            else:
                patience += 1
            
            if patience >= early_stopping_rounds:
                print(f"Early stopping at iteration {i+1}. Best iteration: {best_iter} with RMSE: {best_rmse:.2f}")
                best_iters[target] = best_iter
                break
    
    print("\n\n" + "="*50)
    print("--- 最佳迭代次数搜索完毕 ---")
    print("请将以下值手动填入 8.0.1.2_lgbm_final_predict.py 文件中:")
    print(f"best_iters = {best_iters}")
    print("="*50 + "\n")


# ========== 4. 主函数 ==========
def main():
    setup_environment()
    balance, interest, shibor, profile = load_all_data()

    # --- 加速：随机抽取中等量用户进行全流程模拟 ---
    print("【注意：当前为中等量用户模式，抽取5000名用户以实现中等迭代，取得Best iteration值。】")
    SAMPLE_SIZE = 5000
    all_user_ids = profile['user_id'].unique()
    sampled_user_ids = np.random.choice(all_user_ids, SAMPLE_SIZE, replace=False)
    
    balance = balance[balance['user_id'].isin(sampled_user_ids)]
    profile = profile[profile['user_id'].isin(sampled_user_ids)]
    # interest 和 shibor 是全局数据，不需要抽样

    # --- 构建基础网格 ---
    start_date, end_date = '2014-03-01', '2014-09-30'
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    all_users = pd.DataFrame({'user_id': balance['user_id'].unique()})
    base_grid = pd.MultiIndex.from_product([all_users['user_id'], all_dates], names=['user_id', 'ds'])
    base_grid = pd.DataFrame(index=base_grid).reset_index()

    # --- 合并基础数据 ---
    data = pd.merge(base_grid, balance[['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']], 
                    on=['user_id', 'ds'], how='left')
    
    data.loc[data['ds'] < '2014-09-01', ['total_purchase_amt', 'total_redeem_amt']] = \
        data.loc[data['ds'] < '2014-09-01', ['total_purchase_amt', 'total_redeem_amt']].fillna(0)

    # --- 一次性创建所有静态特征 ---
    print("创建静态特征...")
    data = pd.merge(data, profile, on='user_id', how='left')
    data['constellation'] = data['constellation'].astype(str).fillna('Unknown')
    data['sex'] = data['sex'].fillna(-1)
    data['city'] = data['city'].fillna(-1)

    macro_features = pd.merge(interest, shibor, on='ds', how='left')
    macro_features_lag1 = macro_features.copy()
    macro_features_lag1['ds'] = macro_features_lag1['ds'] + timedelta(days=1)
    lag1_cols = {col: f'{col}_lag1' for col in macro_features_lag1.columns if col != 'ds'}
    macro_features_lag1 = macro_features_lag1.rename(columns=lag1_cols)
    data = pd.merge(data, macro_features_lag1, on='ds', how='left')

    data['weekday'] = data['ds'].dt.weekday
    data['day'] = data['ds'].dt.day
    data['month'] = data['ds'].dt.month
    data['is_month_end'] = data['ds'].dt.is_month_end.astype(int)
    data['is_month_start'] = data['ds'].dt.is_month_start.astype(int)
    data['is_holiday'] = data['ds'].apply(chinese_calendar.is_holiday).astype(int)
    data['is_next_workday'] = ((data['is_holiday'].shift(1) == 1) & (data['is_holiday'] == 0)).astype(int)
    data['month_period'] = data['ds'].apply(lambda x: 'begin' if x.day <= 10 else ('middle' if x.day <= 20 else 'end'))
    data['is_quarter_end'] = data['ds'].apply(lambda x: 1 if x.is_quarter_end else 0)
    data['is_festival_eve'] = ((data['is_holiday'].shift(-1) == 1) & (data['is_holiday'] == 0)).astype(int)
    holiday_len_map = data[data['is_holiday'] == 1].groupby((data['is_holiday'] == 0).cumsum()).cumcount() + 1
    data['holiday_len'] = holiday_len_map.reindex(data.index)
    data['holiday_len'] = data['holiday_len'].fillna(0)
    
    train_users = set(balance[balance['ds'] < '2014-09-01']['user_id'].unique())
    data['is_new_user'] = data.apply(lambda row: 1 if row['ds'].month == 9 and row['user_id'] not in train_users else 0, axis=1)

    data = data.fillna(0)

    categorical_features = ['sex', 'city', 'constellation', 'weekday', 'month', 
                            'is_month_end', 'is_month_start', 'is_new_user', 'is_holiday', 
                            'is_next_workday', 'month_period', 'is_quarter_end', 'is_festival_eve']
    for col in categorical_features:
        if col in data.columns:
            data[col] = data[col].astype('category')
    
    find_best_iteration(data)
    print("流程执行完毕。")

if __name__ == '__main__':
    main() 