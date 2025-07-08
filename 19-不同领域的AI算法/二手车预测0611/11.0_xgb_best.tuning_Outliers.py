import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor # 需要重新训练模型以获取验证集预测
from sklearn.metrics import mean_absolute_error, mean_squared_error

def main():
    # 1. 解决matplotlib中文乱码
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False

    print("========== 正在加载特征工程结果数据 ==========")
    # 加载特征工程后的训练集数据（包含特征和目标变量price）
    # 这个CSV文件是 11.0_xgb_best.tuning.py 停止前输出的完整训练数据（包含price）
    train_df_path = '11.0_xgb_best_train_features.csv'
    try:
        data = pd.read_csv(train_df_path)
    except FileNotFoundError:
        print(f"错误: 未找到文件 {train_df_path}。请确保您已运行 11.0_xgb_best.tuning.py 并生成此文件。")
        return

    # 从加载的数据中分离特征和目标变量
    # 假设 'price' 是目标变量，其余是特征
    features_cols = [col for col in data.columns if col != 'price']
    X = data[features_cols]
    y = data['price']

    # 重新进行训练集和验证集划分，以重现模型训练环境
    print("========== 重新划分训练集和验证集 (85%训练, 15%验证) ==========")
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42)

    # 重新训练XGBoost模型以获取验证集预测结果
    # 此步骤旨在复现验证集预测数据，以便进行高价车分析
    print("========== 重新训练XGBoost模型以获取验证集预测 ==========")
    xgb = XGBRegressor(
        max_depth=10, learning_rate=0.03, n_estimators=2000, subsample=0.8, colsample_bytree=0.9,
        random_state=42, n_jobs=-1, eval_metric='mae', early_stopping_rounds=100
    )
    xgb.fit(X_train, np.log1p(y_train), eval_set=[(X_val, np.log1p(y_val))], verbose=100)
    print("XGBoost模型重新训练完成。")

    # 验证集预测
    y_val_pred = np.expm1(xgb.predict(X_val))

    # 评估模型（MAE、RMSE），用于确认模型性能与报告一致
    mae = mean_absolute_error(y_val, y_val_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
    print(f'重新训练模型在验证集上的 MAE: {mae:.4f}, RMSE: {rmse:.4f}')

    print("\n========== 针对高价车进行深入分析 ==========")
    # 合并实际价格和预测价格，方便分析
    val_results_df = pd.DataFrame({'actual_price': y_val, 'predicted_price': y_val_pred})
    # 保留原始数据的SaleID，方便追溯。y_val的索引就是原训练集的SaleID
    val_results_df['SaleID'] = y_val.index
    val_results_df['error'] = np.abs(val_results_df['actual_price'] - val_results_df['predicted_price'])

    # 设置高价车阈值
    high_price_threshold = 50000
    high_price_samples = val_results_df[val_results_df['actual_price'] > high_price_threshold].copy()

    if high_price_samples.empty:
        print(f"在验证集中没有实际价格高于 {high_price_threshold} 的样本。请尝试降低阈值。")
    else:
        print(f"找到 {len(high_price_samples)} 个实际价格高于 {high_price_threshold} 的样本。")

        # 可视化：绘制高价车的预测价格 vs 实际价格散点图
        plt.figure(figsize=(10, 8))
        plt.scatter(high_price_samples['actual_price'], high_price_samples['predicted_price'], alpha=0.5, s=20)
        # 绘制 y=x 参考线
        min_price = high_price_samples['actual_price'].min()
        max_price = high_price_samples['actual_price'].max()
        plt.plot([min_price, max_price], [min_price, max_price], 'r--', lw=2, label='理想预测')
        plt.xlabel('实际价格')
        plt.ylabel('预测价格')
        plt.title(f'高价车 ({high_price_threshold} 以上) 预测价格 vs 实际价格')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plot_filename = '11.0_xgb_best_high_price_pred_vs_true.png'
        plt.savefig(plot_filename, dpi=150)
        plt.close()
        print(f'高价车预测价格对比图已保存为 {plot_filename}')

        # 数据分析：筛选预测误差最大的前 N 个高价样本
        N = 20 # 可以根据需要调整显示的样本数量
        top_error_high_price_samples = high_price_samples.sort_values(by='error', ascending=False).head(N)

        print(f"\n预测误差最大的前 {N} 个高价样本 (实际价格 > {high_price_threshold}):")
        # 为了展示这些样本的特征，需要将X_val与top_error_high_price_samples合并
        # 使用SaleID（即原始索引）进行合并
        display_df = top_error_high_price_samples.set_index('SaleID').join(X_val) # join会根据索引合并

        # 打印部分关键特征，可以根据需要调整显示哪些特征
        # 这些特征是从之前EDA报告的Top30特征中选取的部分，假设它们存在于X_val中
        display_features_subset = [
            'actual_price', 'predicted_price', 'error', 
            'v_3', 'v_12', 'v_0', 'power_bin', 'notRepairedDamage', 
            'km_age', 'car_age_log', 'regYear', 'brand_price_std'
        ]
        # 过滤掉不存在的特征，确保代码健壮性
        display_features_subset = [f for f in display_features_subset if f in display_df.columns]

        print(display_df[display_features_subset].to_string()) # 使用to_string()避免截断显示
        
        # 同时将详细分析结果保存到CSV文件，方便后续更细致的查看
        detailed_analysis_filename = '11.0_xgb_best_top_error_high_price_samples.csv'
        display_df.to_csv(detailed_analysis_filename, index=True) # 保持SaleID作为索引
        print(f'\n预测误差最大的高价样本详细分析已保存到 {detailed_analysis_filename}')

if __name__ == "__main__":
    main() 