# 7.0_fusion_model.py
# 功能: 融合Prophet模型(3.2.5)和分组均值模型(4.0)的预测结果
# 1. 统一使用 chinese_calendar 生成节假日特征
# 2. 分别用两种模型生成预测
# 3. 在训练集上寻找最优的融合权重，以最小化RMSE
# 4. 使用最优权重进行加权融合，生成最终预测结果
# 5. 输出融合结果、最优权重和对比图

import pandas as pd
import numpy as np
import os
from prophet import Prophet
import chinese_calendar
import matplotlib.pyplot as plt
import matplotlib
import logging
from sklearn.metrics import mean_squared_error
from tqdm import tqdm

def setup_environment():
    """
    :function: 初始化环境，包括创建目录、设置matplotlib和日志
    """
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
    os.makedirs('7.0_fusion_output', exist_ok=True)
    os.makedirs('7.0_feature_output', exist_ok=True)
    
    # 屏蔽所有库的非错误日志
    for logger_name in ['prophet', 'cmdstanpy', 'matplotlib', 'pandas', 'numpy']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)
        logger.propagate = False
    plt.set_loglevel('error')

def load_and_prepare_data(file_path='user_balance_table.csv'):
    """
    :function: 加载并聚合原始数据
    :param file_path: 原始数据文件路径
    :return: 聚合后的每日申购赎回数据DataFrame
    """
    user_balance = pd.read_csv(file_path, encoding='utf-8')
    user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')
    daily_agg = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
    daily_agg = daily_agg.rename(columns={
        'report_date': 'ds',
        'total_purchase_amt': 'purchase',
        'total_redeem_amt': 'redeem'
    })
    return daily_agg

def create_holidays_and_features(start_date='2014-03-01', end_date='2014-09-30'):
    """
    :function: 使用chinese_calendar生成节假日，并为分组均值模型创建特征
    :param start_date: 特征起始日期
    :param end_date: 特征结束日期
    :return: (包含所有日期的特征DataFrame, Prophet使用的节假日DataFrame)
    """
    all_dates = pd.date_range(start_date, end_date, name='ds')
    
    # 1. 生成节假日和调休补班日 (for Prophet)
    holiday_list = []
    for d in all_dates:
        if chinese_calendar.is_holiday(d):
            holiday_list.append({'holiday': 'official_holiday', 'ds': d, 'lower_window': 0, 'upper_window': 0})
        elif chinese_calendar.is_workday(d) and d.weekday() >= 5:
            holiday_list.append({'holiday': 'workday_shift', 'ds': d, 'lower_window': 0, 'upper_window': 0})
    holidays_df = pd.DataFrame(holiday_list)
    holidays_df.to_csv('7.0_feature_output/7.0_holidays.csv', index=False, encoding='utf-8-sig')

    # 2. 生成分组均值模型所需的特征
    feature_df = pd.DataFrame({'ds': all_dates})
    holiday_set = set(holidays_df[holidays_df['holiday'] == 'official_holiday']['ds'])
    
    feature_df['is_holiday'] = feature_df['ds'].isin(holiday_set).astype(int)
    feature_df['weekday'] = feature_df['ds'].dt.weekday
    feature_df['month_period'] = feature_df['ds'].apply(lambda x: 'begin' if x.day<=10 else ('middle' if x.day<=20 else 'end'))
    feature_df['is_month_end'] = feature_df['ds'].dt.is_month_end.astype(int)
    
    feature_df['is_next_workday'] = 0
    # is_holiday列需要填充，所以先转为可修改的list
    is_holiday_list = feature_df['is_holiday'].tolist()
    is_next_workday_list = feature_df['is_next_workday'].tolist()
    for i in range(1, len(feature_df)):
        if is_holiday_list[i-1] == 1 and is_holiday_list[i] == 0:
            is_next_workday_list[i] = 1
    feature_df['is_next_workday'] = is_next_workday_list
    
    feature_df.to_csv('7.0_feature_output/7.0_daily_features.csv', index=False, encoding='utf-8-sig')
    
    return feature_df, holidays_df

def get_prophet_predictions(data_df, train_end, holidays_df):
    """
    :function: 训练Prophet模型并返回预测结果
    :param data_df: 包含ds和y列的数据
    :param train_end: 训练集结束日期
    :param holidays_df: 节假日DataFrame
    :return: 包含预测结果的DataFrame
    """
    train_df = data_df[data_df['ds'] <= train_end].copy()
    all_dates_df = pd.DataFrame({'ds': data_df['ds']})

    # Prophet模型参数 (来自 3.2.5)
    purchase_params = {
        'holidays': holidays_df, 'yearly_seasonality': False, 'weekly_seasonality': True,
        'daily_seasonality': False, 'changepoint_prior_scale': 0.10, 'seasonality_prior_scale': 10.0,
        'holidays_prior_scale': 5.0, 'seasonality_mode': 'additive', 'changepoint_range': 0.8, 'n_changepoints': 25
    }
    redeem_params = {
        'holidays': holidays_df, 'yearly_seasonality': False, 'weekly_seasonality': True,
        'daily_seasonality': False, 'changepoint_prior_scale': 0.05, 'seasonality_prior_scale': 15.0,
        'holidays_prior_scale': 5.0, 'seasonality_mode': 'additive', 'changepoint_range': 0.8, 'n_changepoints': 20
    }
    
    # 申购模型
    p_model = Prophet(**purchase_params)
    p_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    p_model.fit(train_df[['ds', 'purchase']].rename(columns={'purchase': 'y'}))
    p_forecast = p_model.predict(all_dates_df)

    # 赎回模型
    r_model = Prophet(**redeem_params)
    r_model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    r_model.fit(train_df[['ds', 'redeem']].rename(columns={'redeem': 'y'}))
    r_forecast = r_model.predict(all_dates_df)

    return pd.DataFrame({
        'ds': p_forecast['ds'],
        'prophet_purchase': p_forecast['yhat'],
        'prophet_redeem': r_forecast['yhat']
    })

def get_groupmean_predictions(data_df, train_end):
    """
    :function: 使用分组均值法生成预测
    :param data_df: 包含特征和真实值的DataFrame
    :param train_end: 训练集结束日期
    :return: 包含预测结果的DataFrame
    """
    train_df = data_df[data_df['ds'] <= train_end].copy()
    group_cols = ['weekday', 'month_period', 'is_holiday', 'is_next_workday', 'is_month_end']
    group_mean = train_df.groupby(group_cols)[['purchase', 'redeem']].mean().reset_index()
    
    def predict_row(row):
        for i in range(len(group_cols), 0, -1):
            current_cols = group_cols[:i]
            cond = pd.Series([True] * len(group_mean))
            for col in current_cols:
                cond &= (group_mean[col] == row[col])
            match = group_mean[cond]
            if not match.empty:
                return match.iloc[0]['purchase'], match.iloc[0]['redeem']
        return train_df['purchase'].mean(), train_df['redeem'].mean()
        
    predictions = data_df.apply(predict_row, axis=1)
    
    return pd.DataFrame({
        'ds': data_df['ds'],
        'groupmean_purchase': [p[0] for p in predictions],
        'groupmean_redeem': [p[1] for p in predictions]
    })
    
def find_optimal_weights(df):
    """
    :function: 在训练集上寻找最优融合权重
    :param df: 包含真实值和两个模型预测值的训练集DataFrame
    :return: (申购最优权重, 赎回最优权重, 申购最小RMSE, 赎回最小RMSE)
    """
    best_p_weight, min_p_rmse = 0, float('inf')
    best_r_weight, min_r_rmse = 0, float('inf')
    
    weights_to_check = np.arange(0, 1.01, 0.01)
    
    print("正在寻找申购模型最优权重...")
    for w in tqdm(weights_to_check):
        fused = w * df['prophet_purchase'] + (1 - w) * df['groupmean_purchase']
        rmse = np.sqrt(mean_squared_error(df['purchase'], fused))
        if rmse < min_p_rmse:
            min_p_rmse = rmse
            best_p_weight = w
            
    print("正在寻找赎回模型最优权重...")
    for w in tqdm(weights_to_check):
        fused = w * df['prophet_redeem'] + (1 - w) * df['groupmean_redeem']
        rmse = np.sqrt(mean_squared_error(df['redeem'], fused))
        if rmse < min_r_rmse:
            min_r_rmse = rmse
            best_r_weight = w
            
    return best_p_weight, best_r_weight, min_p_rmse, min_r_rmse

def plot_results(final_df, train_end, output_path):
    """
    :function: 绘制包含所有预测和真实值的对比图
    :param final_df: 包含所有数据的DataFrame
    :param train_end: 训练结束日期，用于划分背景色
    :param output_path: 图片保存路径
    """
    fig, axes = plt.subplots(2, 1, figsize=(20, 12), sharex=True)
    
    # 申购图
    axes[0].plot(final_df['ds'], final_df['purchase'], label='真实值', color='black', linewidth=1.5)
    axes[0].plot(final_df['ds'], final_df['prophet_purchase'], label='Prophet预测', color='blue', linestyle='--', alpha=0.7)
    axes[0].plot(final_df['ds'], final_df['groupmean_purchase'], label='分组均值预测', color='green', linestyle='--', alpha=0.7)
    axes[0].plot(final_df['ds'], final_df['fused_purchase'], label='融合预测', color='red', linewidth=2)
    axes[0].set_title('申购 - 真实值与各模型预测对比')
    axes[0].legend()
    axes[0].axvspan(final_df['ds'].min(), train_end, facecolor='gray', alpha=0.1, label='训练期')
    
    # 赎回图
    axes[1].plot(final_df['ds'], final_df['redeem'], label='真实值', color='black', linewidth=1.5)
    axes[1].plot(final_df['ds'], final_df['prophet_redeem'], label='Prophet预测', color='blue', linestyle='--', alpha=0.7)
    axes[1].plot(final_df['ds'], final_df['groupmean_redeem'], label='分组均值预测', color='green', linestyle='--', alpha=0.7)
    axes[1].plot(final_df['ds'], final_df['fused_redeem'], label='融合预测', color='red', linewidth=2)
    axes[1].set_title('赎回 - 真实值与各模型预测对比')
    axes[1].legend()
    axes[1].axvspan(final_df['ds'].min(), train_end, facecolor='gray', alpha=0.1, label='训练期')
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def main():
    """
    :function: 主执行函数
    """
    setup_environment()
    
    # 定义时间范围
    train_start = pd.to_datetime('2014-03-01')
    train_end = pd.to_datetime('2014-08-31')
    predict_start = pd.to_datetime('2014-09-01')
    predict_end = pd.to_datetime('2014-09-30')

    # 1. 加载和准备数据
    print("1. 正在加载和准备数据...")
    daily_agg = load_and_prepare_data()
    features_df, holidays_df = create_holidays_and_features(train_start, predict_end)
    full_df = pd.merge(features_df, daily_agg, on='ds', how='left')
    
    # 2. 生成各模型预测
    print("2. 正在生成Prophet模型预测...")
    prophet_preds = get_prophet_predictions(full_df, train_end, holidays_df)
    
    print("3. 正在生成分组均值模型预测...")
    groupmean_preds = get_groupmean_predictions(full_df, train_end)
    
    # 3. 合并所有数据
    final_df = pd.merge(full_df, prophet_preds, on='ds')
    final_df = pd.merge(final_df, groupmean_preds, on='ds')

    # 4. 寻找最优权重
    print("4. 正在寻找最优融合权重...")
    train_df_for_weighting = final_df[final_df['ds'] <= train_end].copy()
    p_w, r_w, p_rmse, r_rmse = find_optimal_weights(train_df_for_weighting)

    print("\n--- 最优权重结果 ---")
    print(f"申购最优权重 (Prophet): {p_w:.2f}, (分组均值): {1-p_w:.2f} | 对应训练集RMSE: {p_rmse:,.2f}")
    print(f"赎回最优权重 (Prophet): {r_w:.2f}, (分组均值): {1-r_w:.2f} | 对应训练集RMSE: {r_rmse:,.2f}")
    
    # 5. 生成最终融合预测
    print("\n5. 正在生成最终融合预测...")
    final_df['fused_purchase'] = p_w * final_df['prophet_purchase'] + (1 - p_w) * final_df['groupmean_purchase']
    final_df['fused_redeem'] = r_w * final_df['prophet_redeem'] + (1 - r_w) * final_df['groupmean_redeem']
    
    # 6. 保存输出
    print("6. 正在保存结果...")
    # 保存预测文件
    predict_output = final_df[final_df['ds'].between(predict_start, predict_end)].copy()
    predict_output['purchase'] = np.round(predict_output['fused_purchase']).astype(int)
    predict_output['redeem'] = np.round(predict_output['fused_redeem']).astype(int)
    predict_output['ds'] = predict_output['ds'].dt.strftime('%Y%m%d')
    predict_output[['ds', 'purchase', 'redeem']].to_csv('7.0_fusion_output/7.0_fusion_predict.csv', index=False, header=False)
    
    # 保存带权重的完整数据
    final_df.to_csv('7.0_fusion_output/7.0_all_predictions_data.csv', index=False, encoding='utf-8-sig')
    
    # 绘制对比图
    plot_results(final_df, train_end, '7.0_fusion_output/7.0_fusion_compare.png')

    print("\n融合模型执行完毕！结果已保存在 '7.0_fusion_output' 目录中。")

if __name__ == '__main__':
    main() 