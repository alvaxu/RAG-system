# 8.0.1_lgbm_recursive_model.py
# 功能: 实施方案一的进阶版，实现逐日递归预测
# 核心思路：
# 1. 训练一个能利用近期历史信息的基准模型。
# 2. 预测时，逐日进行，将前一天的预测结果作为后一天的历史输入，滚动生成特征并预测。
# 3. 解决了远期特征模型无法感知近期动态的问题。

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
    # 只需要填充本次计算产生的NaN
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
def train_and_predict_recursive(data):
    """训练LGBM模型并进行递归预测"""
    print("模型训练与递归预测开始...")
    
    # --- 4.1 划分历史数据用于训练 ---
    # 【调试模式】减少训练数据量并调整参数以加快调试
    # print("【注意：当前为调试模式，仅使用7月数据训练，并调整了LGBM参数。】")
    # train_start, train_end = '2014-07-01', '2014-07-31' # 只用7月训练
    # valid_start, valid_end = '2014-08-01', '2014-08-31'
    # # 计算特征需要的最早日期（7月1号往前推15天，保证lag14等特征的计算准确性）
    # features_start_date = pd.to_datetime(train_start) - timedelta(days=15)
    
    # 【恢复点1】要恢复完整数据训练，请注释掉以上5行，并取消下面2行的注释
    train_start, train_end = '2014-03-01', '2014-07-31'
    valid_start, valid_end = '2014-08-01', '2014-08-31'


    # 在训练和验证集上创建一次动态特征
    # 【调试优化】只截取需要的时间窗口的数据，大幅提高特征工程速度
    # train_valid_data = data[data['ds'] >= features_start_date].copy()
    
    # 【恢复点2】要恢复完整数据训练，请注释掉上面1行，并取消下面1行的注释
    train_valid_data = data[data['ds'] <= valid_end].copy()

    train_valid_data = create_dynamic_features(train_valid_data)
    
    train_df = train_valid_data[train_valid_data['ds'].between(train_start, train_end)]
    valid_df = train_valid_data[train_valid_data['ds'].between(valid_start, valid_end)]

    # --- 4.2 定义特征列和模型参数 ---
    features = [col for col in train_valid_data.columns if col not in ['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']]
    categorical_features = ['sex', 'city', 'constellation', 'weekday', 'month', 
                            'is_month_end', 'is_month_start', 'is_new_user', 'is_holiday', 
                            'is_next_workday', 'month_period', 'is_quarter_end', 'is_festival_eve']
    # 确保特征顺序一致
    features = [f for f in features if f not in categorical_features] + [c for c in categorical_features if c in features]

    # 调整参数以进行更精细的学习
    params = {
        'objective': 'regression_l2',
        'metric': 'rmse',
        'n_estimators': 1000,         # 增加迭代次数上限
        'learning_rate': 0.01,        # 降低学习率，进行更精细的学习
        'feature_fraction': 0.8, 'bagging_fraction': 0.8, 'bagging_freq': 1,
        'lambda_l1': 0.1, 'lambda_l2': 0.1,
        'num_leaves': 31, 'verbose': -1, 'n_jobs': -1, 'seed': 42, 'boosting_type': 'gbdt',
    }

    
    # --- 4.3 核心改造：带递归验证的手动早停训练 ---
    print("\n--- 开始进行带递归验证的训练 ---")
    models = {}
    
    for target in ['total_purchase_amt', 'total_redeem_amt']:
        print(f"\n--- 正在训练 {target} 模型 ---")
        
        # 准备训练集
        train_set = lgb.Dataset(train_df[features], label=train_df[target], categorical_feature='auto')
        
        # 初始化模型、最佳分数和耐心计数器
        model = lgb.Booster(params, train_set)
        best_rmse = float('inf')
        best_iter = -1
        patience = 0
        early_stopping_rounds = 50

        # 手动迭代训练
        for i in range(params['n_estimators']):
            model.update()

            # --- 内部循环：在验证集上进行递归预测以评估当前模型 ---
            # 准备用于递归验证的初始数据（包含训练期历史）
            hist_for_validation = train_valid_data[train_valid_data['ds'] < valid_start].copy()
            
            # 【调试模式】缩短验证日期以加快每轮评估
            validation_dates = pd.date_range(start=valid_start, end=valid_end, freq='D')
            # validation_dates = validation_dates[:3] # 只验证前3天
            
            # 合并历史和验证期的骨架，形成递归验证的初始DataFrame
            recursive_valid_df = pd.concat([
                hist_for_validation,
                valid_df[valid_df['ds'].isin(validation_dates)][['user_id', 'ds'] + features]
            ]).sort_values(['user_id', 'ds']).reset_index(drop=True)

            # 开始逐日递归验证
            for on_date in validation_dates:
                # 1. 动态特征创建
                recursive_valid_df = create_dynamic_features(recursive_valid_df)
                
                # 2. 获取当天样本并预测
                today_df = recursive_valid_df[recursive_valid_df['ds'] == on_date]
                preds = model.predict(today_df[features])
                
                # 3. 将预测结果写回，用于下一日的特征计算
                recursive_valid_df.loc[today_df.index, target] = np.maximum(0, preds)
                
            # --- 递归验证结束 ---
            
            # 计算当前迭代的真实RMSE
            predicted_values = recursive_valid_df.loc[recursive_valid_df['ds'].isin(validation_dates), ['user_id', 'ds', target]]
            actual_values = valid_df.loc[valid_df['ds'].isin(validation_dates), ['user_id', 'ds', target]]
            eval_df = pd.merge(actual_values, predicted_values, on=['user_id', 'ds'], suffixes=('_actual', '_pred'))
            current_rmse = np.sqrt(np.mean((eval_df[f'{target}_actual'] - eval_df[f'{target}_pred'])**2))

            print(f"Iter {i+1}, Recursive Valid RMSE: {current_rmse:.2f}")

            # 手动早停逻辑
            if current_rmse < best_rmse:
                best_rmse = current_rmse
                best_iter = i + 1
                patience = 0
            else:
                patience += 1
            
            if patience >= early_stopping_rounds:
                print(f"Early stopping at iteration {i+1}. Best iteration: {best_iter} with RMSE: {best_rmse:.2f}")
                break
        
        # --- 使用最佳迭代次数在完整训练数据上重新训练最终模型 ---
        print(f"使用最佳迭代次数 {best_iter} 在全部训练数据（含验证集）上重新训练最终模型...")
        full_train_set = lgb.Dataset(train_valid_data[train_valid_data['ds'] <= valid_end][features], 
                                     label=train_valid_data[train_valid_data['ds'] <= valid_end][target],
                                     categorical_feature='auto')
        final_model = lgb.train(params, full_train_set, num_boost_round=best_iter)
        models[target] = final_model

    # --- 4.4 逐日递归预测 (测试集) ---
    print("\n--- 开始逐日递归预测 (测试集) ---")
    predict_start, predict_end = '2014-09-01', '2014-09-30'
    prediction_dates = pd.date_range(start=predict_start, end=predict_end, freq='D')
    
    # 【调试模式】仅预测前3天以快速验证流程
    # print("【注意：当前为调试模式，仅预测3天以加快速度。】")
    # prediction_dates = prediction_dates[:3]
    
    # all_data 用于在循环中不断更新
    all_data = data.copy()

    for on_date in prediction_dates:
        print(f"  正在预测: {on_date.date()}")
        # 1. 为当前日期创建动态特征
        # 仅在需要预测的当天和相关的历史数据上计算特征，以提高效率
        # (这是一个简化，更高效的方式是只更新受影响的用户和日期)
        all_data = create_dynamic_features(all_data)
        
        # 2. 获取当天的预测样本
        today_df = all_data[all_data['ds'] == on_date].copy()
        
        # 3. 进行预测
        pred_purchase = models['total_purchase_amt'].predict(today_df[features])
        pred_redeem = models['total_redeem_amt'].predict(today_df[features])
        
        # 4. 将预测结果写回主数据框，作为下一天特征的来源 (核心)
        all_data.loc[today_df.index, 'total_purchase_amt'] = np.maximum(0, pred_purchase)
        all_data.loc[today_df.index, 'total_redeem_amt'] = np.maximum(0, pred_redeem)

    # --- 4.5 聚合与评估 ---
    print("聚合每日总量用于可视化和提交...")
    
    # 步骤 1: 准备预测数据
    # 8月份的预测值需要在这里生成
    valid_features_df = train_valid_data[train_valid_data['ds'].between(valid_start, valid_end, inclusive='both')]
    valid_predictions = valid_features_df[['user_id', 'ds']].copy()
    valid_predictions['predicted_purchase'] = models['total_purchase_amt'].predict(valid_features_df[features])
    valid_predictions['predicted_redeem'] = models['total_redeem_amt'].predict(valid_features_df[features])

    # 9月份的预测值在 all_data 的目标列里
    test_predictions = all_data[all_data['ds'] >= predict_start][['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']].copy()
    test_predictions.rename(columns={'total_purchase_amt': 'predicted_purchase', 'total_redeem_amt': 'predicted_redeem'}, inplace=True)
    
    # 步骤 2: 聚合真实值和预测值
    # 聚合真实值（来自未被修改的 `data` DataFrame）
    daily_actuals = data.groupby('ds').agg(
        actual_purchase=('total_purchase_amt', 'sum'),
        actual_redeem=('total_redeem_amt', 'sum')
    ).reset_index()

    # 聚合预测值（合并8月和9月的预测）
    all_predictions = pd.concat([valid_predictions, test_predictions])
    daily_predictions = all_predictions.groupby('ds').agg(
        predicted_purchase=('predicted_purchase', 'sum'),
        predicted_redeem=('predicted_redeem', 'sum')
    ).reset_index()

    # 步骤 3: 合并用于绘图
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

    # --- 【调试模式一】极致加速：随机抽取少量用户进行全流程模拟 ---
    # print("【注意：当前为极致调试模式，仅抽取500名用户以实现秒级迭代。】")
    # SAMPLE_SIZE = 500
    # all_user_ids = profile['user_id'].unique()
    # sampled_user_ids = np.random.choice(all_user_ids, SAMPLE_SIZE, replace=False)
    
    # balance = balance[balance['user_id'].isin(sampled_user_ids)]
    # profile = profile[profile['user_id'].isin(sampled_user_ids)]
    # interest 和 shibor 是全局数据，不需要抽样
    
        # --- 【调试模式二】加速：随机抽取中等量用户进行全流程模拟 ---
    print("【注意：当前为中等量用户模式，抽取5000名用户以实现中等迭代，取得Best iteration值。】")
    SAMPLE_SIZE = 5000
    all_user_ids = profile['user_id'].unique()
    sampled_user_ids = np.random.choice(all_user_ids, SAMPLE_SIZE, replace=False)
    
    balance = balance[balance['user_id'].isin(sampled_user_ids)]
    profile = profile[profile['user_id'].isin(sampled_user_ids)]
    interest 和 shibor 是全局数据，不需要抽样

    # 【恢复点0】要恢复全量用户运行，请注释掉以上所有带“【调试模式】”和“SAMPLE_SIZE”的8行代码
    
    # --- 构建基础网格 ---
    start_date, end_date = '2014-03-01', '2014-09-30'
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    all_users = pd.DataFrame({'user_id': balance['user_id'].unique()})
    base_grid = pd.MultiIndex.from_product([all_users['user_id'], all_dates], names=['user_id', 'ds'])
    base_grid = pd.DataFrame(index=base_grid).reset_index()

    # --- 合并基础数据 ---
    data = pd.merge(base_grid, balance[['user_id', 'ds', 'total_purchase_amt', 'total_redeem_amt']], 
                    on=['user_id', 'ds'], how='left')
    
    # 仅填充历史数据的NaN为0，9月份的NaN保持，因为它们将被预测值填充
    data.loc[data['ds'] < '2014-09-01', ['total_purchase_amt', 'total_redeem_amt']] = \
        data.loc[data['ds'] < '2014-09-01', ['total_purchase_amt', 'total_redeem_amt']].fillna(0)

    # --- 一次性创建所有静态特征 ---
    print("创建静态特征...")
    # 合并用户画像
    data = pd.merge(data, profile, on='user_id', how='left')
    data['constellation'] = data['constellation'].astype(str).fillna('Unknown')
    data['sex'] = data['sex'].fillna(-1)
    data['city'] = data['city'].fillna(-1)

    # 合并宏观经济数据
    macro_features = pd.merge(interest, shibor, on='ds', how='left')
    macro_features_lag1 = macro_features.copy()
    macro_features_lag1['ds'] = macro_features_lag1['ds'] + timedelta(days=1)
    lag1_cols = {col: f'{col}_lag1' for col in macro_features_lag1.columns if col != 'ds'}
    macro_features_lag1 = macro_features_lag1.rename(columns=lag1_cols)
    data = pd.merge(data, macro_features_lag1, on='ds', how='left')

    # 创建时间、节假日、周期特征
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
    
    # 标记新用户
    train_users = set(balance[balance['ds'] < '2014-09-01']['user_id'].unique())
    data['is_new_user'] = data.apply(lambda row: 1 if row['ds'].month == 9 and row['user_id'] not in train_users else 0, axis=1)

    # 在转换数据类型前，填充所有剩余的NaN
    # 这主要是为了处理宏观经济特征和shift操作在首尾产生的NaN
    data = data.fillna(0)

    # 转换所有类别特征
    categorical_features = ['sex', 'city', 'constellation', 'weekday', 'month', 
                            'is_month_end', 'is_month_start', 'is_new_user', 'is_holiday', 
                            'is_next_workday', 'month_period', 'is_quarter_end', 'is_festival_eve']
    for col in categorical_features:
        if col in data.columns:
            data[col] = data[col].astype('category')
    
    train_and_predict_recursive(data)
    print("流程执行完毕。")

if __name__ == '__main__':
    main() 