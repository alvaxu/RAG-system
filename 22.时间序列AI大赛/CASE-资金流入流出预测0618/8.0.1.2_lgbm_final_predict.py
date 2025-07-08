# 8.0.1.2_lgbm_final_predict.py
# 功能: 使用手动找到的最佳迭代次数，在全量数据上进行最终模型的训练，并生成预测结果。
# 核心思路：
# 1. 加载全量用户数据。
# 2. 在代码中手动填入从 8.0.1.1 脚本中找到的最佳迭代次数。
#  best_iters = {'total_purchase_amt': 1, 'total_redeem_amt': 51}
# 3. 使用一个高效、一次性的训练流程，在全部历史数据上训练出最终模型。
# 4. 在9月份数据上进行递归预测，生成最终的提交文件和对比图。

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

# ========== 3. 可视化函数 (无变化) ==========
def plot_predictions(plot_df, output_path):
    print("正在绘制预测结果对比图...")
    fig, axes = plt.subplots(2, 1, figsize=(20, 12), sharex=True)
    
    axes[0].plot(plot_df['ds'], plot_df['actual_purchase'], label='申购真实值', color='blue', linewidth=1.5)
    axes[0].plot(plot_df['ds'], plot_df['predicted_purchase'], label='申购预测值', color='red', linestyle='--', alpha=0.8)
    axes[0].set_title('每日申购总额：真实值 vs. LightGBM递归预测值')
    axes[0].legend()
    axes[0].axvspan(pd.to_datetime('2014-08-01'), pd.to_datetime('2014-08-31'), color='gray', alpha=0.2, label='验证集')
    axes[0].axvspan(pd.to_datetime('2014-09-01'), pd.to_datetime('2014-09-30'), color='orange', alpha=0.2, label='预测集')
    axes[0].grid(True, linestyle='--', alpha=0.5)
    
    axes[1].plot(plot_df['ds'], plot_df['actual_redeem'], label='赎回真实值', color='green', linewidth=1.5)
    axes[1].plot(plot_df['ds'], plot_df['predicted_redeem'], label='赎回预测值', color='red', linestyle='--', alpha=0.8)
    axes[1].set_title('每日赎回总额：真实值 vs. LightGBM递归预测值')
    axes[1].legend()
    axes[1].axvspan(pd.to_datetime('2014-08-01'), pd.to_datetime('2014-08-31'), color='gray', alpha=0.2)
    axes[1].axvspan(pd.to_datetime('2014-09-01'), pd.to_datetime('2014-09-30'), color='orange', alpha=0.2)
    axes[1].grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"对比图已保存至: {output_path}")

# ========== 4. 模型训练与递归预测 ==========
def train_and_predict_final(data):
    """在全量数据上，使用最佳迭代次数训练并进行最终预测"""
    print("最终模型训练与预测开始...")
    
    # --- 4.1 划分历史数据用于训练 ---
    train_start, train_end = '2014-03-01', '2014-07-31'
    valid_start, valid_end = '2014-08-01', '2014-08-31'

    # 使用全部历史数据进行一次性特征创建和训练
    train_valid_data = data[data['ds'] <= valid_end].copy()
    train_valid_data = create_dynamic_features(train_valid_data)
    
    # --- 4.2 定义特征列和模型参数 ---
    features = [col for col in train_valid_data.columns if col not in ['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']]
    categorical_features = ['sex', 'city', 'constellation', 'weekday', 'month', 
                            'is_month_end', 'is_month_start', 'is_new_user', 'is_holiday', 
                            'is_next_workday', 'month_period', 'is_quarter_end', 'is_festival_eve']
    features = [f for f in features if f not in categorical_features] + [c for c in categorical_features if c in features]

    params = {
        'objective': 'regression_l2', 'metric': 'rmse', 'learning_rate': 0.01,
        'feature_fraction': 0.8, 'bagging_fraction': 0.8, 'bagging_freq': 1, 'lambda_l1': 0.1, 'lambda_l2': 0.1,
        'num_leaves': 31, 'verbose': -1, 'n_jobs': -1, 'seed': 42, 'boosting_type': 'gbdt',
    }
    
    # --- 4.3 最终模型训练：使用找到的最佳迭代次数进行一次性训练 ---
    print("\n--- 使用找到的最佳迭代次数进行最终模型训练 ---")
    
    # 【手动输入】请在此处填入从 8.0.1.1 脚本中找到的最佳迭代次数
    best_iters = {
        'total_purchase_amt': 21,  # 示例值，请替换
        'total_redeem_amt': 51  # 示例值，请替换
    }
    print(f"将使用以下迭代次数进行训练: {best_iters}")

    models = {}
    full_train_set_data = train_valid_data[train_valid_data['ds'] <= valid_end]
    for target in ['total_purchase_amt', 'total_redeem_amt']:
        print(f"--- 正在训练 {target} 模型，迭代次数: {best_iters[target]} ---")
        
        full_train_set = lgb.Dataset(full_train_set_data[features], 
                                     label=full_train_set_data[target],
                                     categorical_feature='auto')
        
        final_model = lgb.train(params, 
                                full_train_set,
                                num_boost_round=best_iters.get(target))
        models[target] = final_model


    # --- 4.4 逐日递归预测 (测试集) ---
    print("\n--- 开始逐日递归预测 (测试集) ---")
    predict_start, predict_end = '2014-09-01', '2014-09-30'
    prediction_dates = pd.date_range(start=predict_start, end=predict_end, freq='D')

    # 1. 先保存一份历史真实值（3-8月）
    history_data = data[data['ds'] < predict_start].copy()
    # 2. 初始化递归预测区间（9月），目标列为0
    future_data = data[data['ds'] >= predict_start].copy()
    future_data['total_purchase_amt'] = 0
    future_data['total_redeem_amt'] = 0

    # 3. 递归预测
    for on_date in prediction_dates:
        print(f"  正在预测: {on_date.date()}")
        # 合并历史和已预测的未来，保证lag特征引用正确
        combined = pd.concat([history_data, future_data], ignore_index=True)
        combined = create_dynamic_features(combined)
        today_df = combined[combined['ds'] == on_date].copy()

        # 预测
        pred_purchase = models['total_purchase_amt'].predict(today_df[features])
        pred_redeem = models['total_redeem_amt'].predict(today_df[features])

        # 只更新future_data中对应日期的目标列
        idx = future_data[future_data['ds'] == on_date].index
        future_data.loc[idx, 'total_purchase_amt'] = np.maximum(0, pred_purchase)
        future_data.loc[idx, 'total_redeem_amt'] = np.maximum(0, pred_redeem)

    # 4. 合并历史和预测区间，供后续聚合与输出
    all_data = pd.concat([history_data, future_data], ignore_index=True)

    # --- 4.5 聚合与评估 ---
    print("聚合每日总量用于可视化和提交...")
    
    valid_features_df = train_valid_data[train_valid_data['ds'].between(valid_start, valid_end, inclusive='both')]
    valid_predictions = valid_features_df[['user_id', 'ds']].copy()
    valid_predictions['predicted_purchase'] = models['total_purchase_amt'].predict(valid_features_df[features])
    valid_predictions['predicted_redeem'] = models['total_redeem_amt'].predict(valid_features_df[features])

    test_predictions = all_data[all_data['ds'] >= predict_start][['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']].copy()
    test_predictions.rename(columns={'total_purchase_amt': 'predicted_purchase', 'total_redeem_amt': 'predicted_redeem'}, inplace=True)
    
    daily_actuals = data.groupby('ds').agg(
        actual_purchase=('total_purchase_amt', 'sum'),
        actual_redeem=('total_redeem_amt', 'sum')
    ).reset_index()

    all_predictions = pd.concat([valid_predictions, test_predictions])
    daily_predictions = all_predictions.groupby('ds').agg(
        predicted_purchase=('predicted_purchase', 'sum'),
        predicted_redeem=('predicted_redeem', 'sum')
    ).reset_index()

    daily_aggregated = pd.merge(daily_actuals, daily_predictions, on='ds', how='outer')

    plot_predictions(daily_aggregated, '8.0.1_lgbm_output/8.0.1_lgbm_compare.png')

    # --- 4.6 生成提交文件 ---
    submit_df = daily_aggregated[daily_aggregated['ds'] >= predict_start].copy()
    submit_df['report_date'] = submit_df['ds'].dt.strftime('%Y%m%d')
    submit_df['purchase'] = np.round(submit_df['predicted_purchase']).astype(int)
    submit_df['redeem'] = np.round(submit_df['predicted_redeem']).astype(int)
    submit_df[['report_date', 'purchase', 'redeem']].to_csv('8.0.1_lgbm_output/8.0.1_lgbm_predict.csv', index=False, header=False)
    print("提交文件已生成: 8.0.1_lgbm_output/8.0.1_lgbm_predict.csv")

# ========== 5. 主函数 ==========
def main():
    setup_environment()
    balance, interest, shibor, profile = load_all_data()

    # --- 在全量数据上运行 ---
    
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
    
    train_and_predict_final(data)
    print("流程执行完毕。")

if __name__ == '__main__':
    main() 