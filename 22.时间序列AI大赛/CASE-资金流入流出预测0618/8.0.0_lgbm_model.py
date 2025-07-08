# 8.0.0_lgbm_model.py
# 功能: 实施方案一，构建用户级梯度提升回归模型(LightGBM)
# 核心思路：
# 1. 以 (user_id, date) 为单位构建样本
# 2. 构建丰富的用户级、时间、宏观经济特征
# 3. 区分处理新老用户
# 4. 使用LightGBM分别对申购和赎回进行建模
# 5. 聚合用户预测至每日总量

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
    """初始化环境，创建输出目录"""
    os.makedirs('8.0.0_feature_output', exist_ok=True)
    os.makedirs('8.0.0_lgbm_output', exist_ok=True)
    print("环境设置完毕，输出目录已创建。")

def load_all_data():
    """加载所有需要的数据文件"""
    print("开始加载数据...")
    balance = pd.read_csv('user_balance_table.csv', parse_dates=['report_date'])
    interest = pd.read_csv('mfd_day_share_interest.csv', parse_dates=['mfd_date'])
    shibor = pd.read_csv('mfd_bank_shibor.csv', parse_dates=['mfd_date'])
    profile = pd.read_csv('user_profile_table.csv')
    
    # 标准化日期列名
    balance = balance.rename(columns={'report_date': 'ds'})
    interest = interest.rename(columns={'mfd_date': 'ds'})
    shibor = shibor.rename(columns={'mfd_date': 'ds'})
    
    print("数据加载完成。")
    return balance, interest, shibor, profile

# ========== 2. 特征工程 ==========
def feature_engineering(balance, interest, shibor, profile):
    """
    核心特征工程函数
    :return: 包含所有特征的DataFrame
    """
    print("特征工程开始...")
    
    # --- 2.1 创建基础网格：所有用户在所有日期的组合 ---
    # 时间范围：从2014-03-01到2014-09-30，覆盖训练、验证和预测
    start_date = '2014-03-01'
    end_date = '2014-09-30'
    
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    all_users = pd.DataFrame({'user_id': balance['user_id'].unique()})
    
    # 笛卡尔积，创建 (user_id, ds) 网格
    base_grid = pd.MultiIndex.from_product([all_users['user_id'], all_dates], names=['user_id', 'ds'])
    base_grid = pd.DataFrame(index=base_grid).reset_index()
    
    # --- 2.2 合并基础数据和用户画像 ---
    # 合并用户每日交易数据，purchase和redeem是我们的目标变量
    data = pd.merge(base_grid, balance[['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']], 
                    on=['user_id', 'ds'], how='left')
    data[['total_purchase_amt', 'total_redeem_amt']] = data[['total_purchase_amt', 'total_redeem_amt']].fillna(0)
    
    # 合并用户画像，对缺失值（代表新用户）进行填充
    data = pd.merge(data, profile, on='user_id', how='left')
    data['constellation'] = data['constellation'].fillna('Unknown') # 字符串类别填充为'Unknown'
    data['sex'] = data['sex'].fillna(-1) # 数字类别填充为-1
    data['city'] = data['city'].fillna(-1) # 数字类别填充为-1

    # --- 2.3 合并宏观经济数据（使用滞后特征）---
    macro_features = pd.merge(interest, shibor, on='ds', how='left')
    
    # 创建 lag=1 的特征，用于预测第二天
    macro_features_lag1 = macro_features.copy()
    macro_features_lag1['ds'] = macro_features_lag1['ds'] + timedelta(days=1)
    lag1_cols = {col: f'{col}_lag1' for col in macro_features_lag1.columns if col != 'ds'}
    macro_features_lag1 = macro_features_lag1.rename(columns=lag1_cols)
    
    data = pd.merge(data, macro_features_lag1, on='ds', how='left')
    
    # --- 2.4 创建时间特征 ---
    data['weekday'] = data['ds'].dt.weekday
    data['day'] = data['ds'].dt.day
    data['month'] = data['ds'].dt.month
    data['is_month_end'] = data['ds'].dt.is_month_end.astype(int)
    data['is_month_start'] = data['ds'].dt.is_month_start.astype(int)

    # --- 2.5 创建节假日特征 ---
    print("正在创建节假日特征...")
    data['is_holiday'] = data['ds'].apply(chinese_calendar.is_holiday).astype(int)
    # 节后第一个工作日
    data['is_next_workday'] = ((data['is_holiday'].shift(1) == 1) & (data['is_holiday'] == 0)).astype(int)

    # --- 2.6 补充更多来自4.0模型的周期特征 ---
    print("正在创建更多时间周期特征...")
    # 月初/中/末
    data['month_period'] = data['ds'].apply(lambda x: 'begin' if x.day <= 10 else ('middle' if x.day <= 20 else 'end'))
    # 季末
    data['is_quarter_end'] = data['ds'].apply(lambda x: 1 if x.is_quarter_end else 0)
    # 节日前夕
    data['is_festival_eve'] = ((data['is_holiday'].shift(-1) == 1) & (data['is_holiday'] == 0)).astype(int)
    # 假期长度
    holiday_len_map = data[data['is_holiday'] == 1].groupby((data['is_holiday'] == 0).cumsum()).cumcount() + 1
    data['holiday_len'] = holiday_len_map
    data['holiday_len'] = data['holiday_len'].fillna(0)

    # --- 2.7 创建用户历史行为滞后特征 ---
    # 按user_id分组，计算滞后特征
    print("正在创建用户历史滞后特征 (lag)...")
    lag_targets = ['total_purchase_amt', 'total_redeem_amt']
    # 修改lags，回溯到31天前，避免在预测期引用到自身
    lags = [31, 38, 45, 60]
    
    # 先填充目标列的NaN，再计算lag，避免NaN扩散
    data[lag_targets] = data[lag_targets].fillna(0)
    for col in lag_targets:
        for lag in lags:
            data[f'{col}_lag{lag}'] = data.groupby('user_id')[col].shift(lag)

    # --- 2.8 创建滑动窗口特征 ---
    print("正在创建滑动窗口特征 (rolling)...")
    windows = [7, 14, 30]
    for window in windows:
        for col in ['total_purchase_amt', 'total_redeem_amt']:
            # shift(31)确保我们只用31天前的数据. reset_index()用于对齐
            shifted_data = data.groupby('user_id')[col].shift(31)
            rolling_stats = shifted_data.rolling(window=window, min_periods=1)
            
            data[f'{col}_mean_{window}d'] = rolling_stats.mean().reset_index(0, drop=True)
            data[f'{col}_sum_{window}d'] = rolling_stats.sum().reset_index(0, drop=True)
            data[f'{col}_std_{window}d'] = rolling_stats.std().reset_index(0, drop=True)
            
    # --- 2.9 创建新用户标识特征 ---
    # 训练期（3-8月）的用户
    train_users = set(balance[balance['ds'] < '2014-09-01']['user_id'].unique())
    # 标记9月份的用户是否为新用户
    data['is_new_user'] = data.apply(lambda row: 1 if row['ds'].month == 9 and row['user_id'] not in train_users else 0, axis=1)

    # --- 2.10 填充所有NaN并转换数据类型 ---
    # 在转换category类型前，填充所有滞后和合并操作产生的NaN值
    data = data.fillna(0)
    
    # 将所有类别特征转换为 'category' 类型，这是LGBM处理类别特征的最佳实践
    categorical_features = ['sex', 'city', 'constellation', 'weekday', 'month', 
                            'is_month_end', 'is_month_start', 'is_new_user', 'is_holiday', 
                            'is_next_workday', 'month_period', 'is_quarter_end', 'is_festival_eve']
    for col in categorical_features:
        data[col] = data[col].astype('category')

    # --- 2.11 清理与保存 ---
    # 节省内存
    del base_grid, balance, interest, shibor, profile, macro_features, macro_features_lag1
    gc.collect()

    print("特征工程完成。")
    feature_path = '8.0.0_feature_output/8.0.0_features.parquet'
    print(f"特征数据保存至: {feature_path}")
    data.to_parquet(feature_path, index=False)
    
    return data

# ========== 3. 可视化函数 ==========
def plot_predictions(plot_df, output_path):
    """
    绘制申购和赎回的真实值与预测值对比图
    :param plot_df: 包含日期、真实值、预测值的DataFrame
    :param output_path: 图片保存路径
    """
    print("正在绘制预测结果对比图...")
    fig, axes = plt.subplots(2, 1, figsize=(20, 12), sharex=True)
    
    # 申购图
    axes[0].plot(plot_df['ds'], plot_df['actual_purchase'], label='申购真实值', color='blue', linewidth=1.5)
    axes[0].plot(plot_df['ds'], plot_df['predicted_purchase'], label='申购预测值', color='red', linestyle='--', alpha=0.8)
    axes[0].set_title('每日申购总额：真实值 vs. LightGBM预测值')
    axes[0].legend()
    axes[0].axvspan(pd.to_datetime('2014-08-01'), pd.to_datetime('2014-08-31'), color='gray', alpha=0.2, label='验证集')
    axes[0].axvspan(pd.to_datetime('2014-09-01'), pd.to_datetime('2014-09-30'), color='orange', alpha=0.2, label='预测集')
    axes[0].grid(True, linestyle='--', alpha=0.5)
    
    # 赎回图
    axes[1].plot(plot_df['ds'], plot_df['actual_redeem'], label='赎回真实值', color='green', linewidth=1.5)
    axes[1].plot(plot_df['ds'], plot_df['predicted_redeem'], label='赎回预测值', color='red', linestyle='--', alpha=0.8)
    axes[1].set_title('每日赎回总额：真实值 vs. LightGBM预测值')
    axes[1].legend()
    axes[1].axvspan(pd.to_datetime('2014-08-01'), pd.to_datetime('2014-08-31'), color='gray', alpha=0.2)
    axes[1].axvspan(pd.to_datetime('2014-09-01'), pd.to_datetime('2014-09-30'), color='orange', alpha=0.2)
    axes[1].grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"对比图已保存至: {output_path}")

# ========== 4. 模型训练与预测 ==========
def train_and_predict(data):
    """训练LightGBM模型并进行预测"""
    print("模型训练与预测开始...")
    
    # --- 3.1 划分数据集 ---
    train_start, train_end = '2014-03-01', '2014-07-31'
    valid_start, valid_end = '2014-08-01', '2014-08-31'
    predict_start, predict_end = '2014-09-01', '2014-09-30'
    
    train_df = data[(data['ds'] >= train_start) & (data['ds'] <= train_end)]
    valid_df = data[(data['ds'] >= valid_start) & (data['ds'] <= valid_end)]
    predict_df = data[(data['ds'] >= predict_start) & (data['ds'] <= predict_end)].copy()
    
    # --- 3.2 定义特征列和目标列 ---
    # 移除目标和非特征列
    features = [col for col in data.columns if col not in ['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']]
    categorical_features = ['sex', 'city', 'constellation', 'weekday', 'month', 
                            'is_month_end', 'is_month_start', 'is_new_user', 'is_holiday', 
                            'is_next_workday', 'month_period', 'is_quarter_end', 'is_festival_eve']
    
    targets = ['total_purchase_amt', 'total_redeem_amt']
    
    # LightGBM参数
    # 由于用户级数据是稀疏的，并且远期特征预测能力有限，
    # L1损失函数(MAE)倾向于预测中位数(0)，导致模型不学习。
    # 因此我们统一使用L2损失函数(MSE)，其平方误差项能迫使模型关注稀疏的高额交易事件。
    params = {
        'objective': 'regression_l2', # MSE
        'metric': 'rmse',
        'n_estimators': 200,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 1,
        'lambda_l1': 0.1,
        'lambda_l2': 0.1,
        'num_leaves': 31,
        'verbose': -1,
        'n_jobs': -1,
        'seed': 42,
        'boosting_type': 'gbdt',
    }

    # --- 3.3 训练与预测 ---
    for target in targets:
        print(f"--- 正在训练 {target} 模型 ---")
        
        train_set = lgb.Dataset(train_df[features], label=train_df[target], categorical_feature=categorical_features)
        valid_set = lgb.Dataset(valid_df[features], label=valid_df[target], categorical_feature=categorical_features, reference=train_set)
        
        model = lgb.train(
            params,
            train_set,
            valid_sets=[train_set, valid_set],
            callbacks=[lgb.early_stopping(100, verbose=True)]
        )
        
        # --- 3.3.1 对所有数据集进行预测 ---
        print(f"--- 正在对所有数据集进行 {target} 的预测 ---")
        train_df[f'pred_{target}'] = np.maximum(0, model.predict(train_df[features]))
        valid_df[f'pred_{target}'] = np.maximum(0, model.predict(valid_df[features]))
        predict_df[f'pred_{target}'] = np.maximum(0, model.predict(predict_df[features]))
        
        # 保存特征重要性
        importance_df = pd.DataFrame({
            'feature': model.feature_name(),
            'importance': model.feature_importance(),
        }).sort_values('importance', ascending=False)
        importance_path = f'8.0.0_lgbm_output/8.0.0_{target}_feature_importance.csv'
        importance_df.to_csv(importance_path, index=False)
        print(f"特征重要性已保存至: {importance_path}")

    # --- 3.4 聚合每日总量 ---
    print("聚合每日总量用于可视化和提交...")
    all_predictions_df = pd.concat([train_df, valid_df, predict_df], ignore_index=True)
    daily_aggregated = all_predictions_df.groupby('ds').agg(
        actual_purchase=('total_purchase_amt', 'sum'),
        predicted_purchase=('pred_total_purchase_amt', 'sum'),
        actual_redeem=('total_redeem_amt', 'sum'),
        predicted_redeem=('pred_total_redeem_amt', 'sum')
    ).reset_index()

    # --- 3.5 绘制可视化图表 ---
    plot_path = '8.0.0_lgbm_output/8.0.0_lgbm_compare.png'
    plot_predictions(daily_aggregated, plot_path)

    # --- 3.6 生成提交文件 ---
    print("生成提交文件...")
    # 只选择预测期（9月）的数据进行提交
    submit_df_source = daily_aggregated[daily_aggregated['ds'] >= predict_start].copy()
    
    # 格式化输出
    submit_df = pd.DataFrame()
    submit_df['report_date'] = submit_df_source['ds'].dt.strftime('%Y%m%d')
    submit_df['purchase'] = np.round(submit_df_source['predicted_purchase']).astype(int)
    submit_df['redeem'] = np.round(submit_df_source['predicted_redeem']).astype(int)
    
    submit_path = '8.0.0_lgbm_output/8.0.0_lgbm_predict.csv'
    submit_df.to_csv(submit_path, index=False, header=False)
    print(f"提交文件已生成: {submit_path}")

# ========== 5. 主函数 ==========
if __name__ == '__main__':
    setup_environment()
    
    feature_path = '8.0.0_feature_output/8.0.0_features.parquet'
    if os.path.exists(feature_path):
        print(f"发现已生成的特征文件，直接加载: {feature_path}")
        all_feature_data = pd.read_parquet(feature_path)
    else:
        print("未发现特征文件，开始执行完整特征工程...")
        balance, interest, shibor, profile = load_all_data()
        all_feature_data = feature_engineering(balance, interest, shibor, profile)
        
    train_and_predict(all_feature_data)
    print("流程执行完毕。") 