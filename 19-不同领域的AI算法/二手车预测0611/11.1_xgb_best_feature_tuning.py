"""
基于11.0_xgb_best.tuning.py的特征工程结果，进行特征工程的进一步优化
2000轮，早停轮次100轮
XGBoost模型重新训练完成。
重新训练模型在验证集上的 MAE: 514.9951, RMSE: 1204.7838
"""
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns # 导入seaborn库用于高级可视化
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

def main():
    # 1. 解决matplotlib中文乱码
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False

    print("========== 正在加载特征工程结果数据 ==========")
    train_df_path = '11.0_xgb_best_train_features.csv'
    try:
        data = pd.read_csv(train_df_path)
    except FileNotFoundError:
        print(f"错误: 未找到文件 {train_df_path}。请确保您已运行 11.0_xgb_best.tuning.py 并生成此文件。")
        return

    # 从加载的数据中分离特征和目标变量
    features_cols = [col for col in data.columns if col != 'price']
    X = data[features_cols]
    y = data['price']

    # 重新进行训练集和验证集划分
    print("========== 重新划分训练集和验证集 (85%训练, 15%验证) ==========")
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42)

    # 重新训练XGBoost模型以获取验证集预测结果
    print("========== 重新训练XGBoost模型以获取验证集预测 ==========")
    xgb = XGBRegressor(
        max_depth=10, learning_rate=0.03, n_estimators=2000, subsample=0.8, colsample_bytree=0.9,
        random_state=42, n_jobs=-1, eval_metric='mae', early_stopping_rounds=100
    )
    xgb.fit(X_train, np.log1p(y_train), eval_set=[(X_val, np.log1p(y_val))], verbose=100)
    print("XGBoost模型重新训练完成。")

    # 验证集预测
    y_val_pred = np.expm1(xgb.predict(X_val))

    # 评估模型（MAE、RMSE），用于确认模型性能
    mae = mean_absolute_error(y_val, y_val_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
    print(f'重新训练模型在验证集上的 MAE: {mae:.4f}, RMSE: {rmse:.4f}')

    # 将验证集的实际价格、预测价格、SaleID和所有特征合并，方便后续分析
    val_analysis_df = pd.DataFrame({'actual_price': y_val, 'predicted_price': y_val_pred})
    val_analysis_df['SaleID'] = y_val.index
    val_analysis_df['error'] = np.abs(val_analysis_df['actual_price'] - val_analysis_df['predicted_price'])
    # 将X_val的特征也合并进来，以便分析
    val_analysis_df = val_analysis_df.set_index('SaleID').join(X_val)

    print("\n========== 5.1 针对高价车（Outliers）的深入分析 ==========")
    high_price_threshold = 50000
    high_price_samples = val_analysis_df[val_analysis_df['actual_price'] > high_price_threshold].copy()

    if high_price_samples.empty:
        print(f"在验证集中没有实际价格高于 {high_price_threshold} 的样本。请尝试降低阈值。")
    else:
        print(f"找到 {len(high_price_samples)} 个实际价格高于 {high_price_threshold} 的样本。")
        plt.figure(figsize=(10, 8))
        sns.scatterplot(x='actual_price', y='predicted_price', data=high_price_samples, alpha=0.5, s=20)
        min_price = high_price_samples['actual_price'].min()
        max_price = high_price_samples['actual_price'].max()
        plt.plot([min_price, max_price], [min_price, max_price], 'r--', lw=2, label='理想预测')
        plt.xlabel('实际价格')
        plt.ylabel('预测价格')
        plt.title(f'高价车 ({high_price_threshold} 以上) 预测价格 vs 实际价格')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plot_filename = '11.1_xgb_best_high_price_pred_vs_true.png'
        plt.savefig(plot_filename, dpi=150)
        plt.close()
        print(f'高价车预测价格对比图已保存为 {plot_filename}')

        N_top_errors = 20
        top_error_high_price_samples = high_price_samples.sort_values(by='error', ascending=False).head(N_top_errors)
        print(f"\n预测误差最大的前 {N_top_errors} 个高价样本 (实际价格 > {high_price_threshold}):")
        display_features_subset = [
            'actual_price', 'predicted_price', 'error', 
            'v_3', 'v_12', 'v_0', 'power_bin', 'notRepairedDamage', 
            'km_age', 'car_age_log', 'regYear', 'brand_price_std', 'brand', 'model'
        ]
        display_features_subset = [f for f in display_features_subset if f in top_error_high_price_samples.columns]
        print(top_error_high_price_samples[display_features_subset].to_string()) 
        detailed_analysis_filename = '11.1_xgb_best_top_error_high_price_samples.csv'
        top_error_high_price_samples.to_csv(detailed_analysis_filename, index=True) 
        print(f'\n预测误差最大的高价样本详细分析已保存到 {detailed_analysis_filename}')

    print("\n========== 5.2 匿名特征 (`v_cols`) 的更深层次探索 ==========")
    # 绘制 Top 匿名特征与 price 的散点图
    top_v_features = ['v_3', 'v_12', 'v_0']
    for v_feat in top_v_features:
        if v_feat in val_analysis_df.columns:
            plt.figure(figsize=(10, 6))
            sns.scatterplot(x=v_feat, y='actual_price', data=val_analysis_df, alpha=0.3, s=15)
            plt.xlabel(v_feat)
            plt.ylabel('实际价格')
            plt.title(f'{v_feat} vs 实际价格')
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            plot_filename = f'11.1_{v_feat}_price_scatter.png'
            plt.savefig(plot_filename, dpi=150)
            plt.close()
            print(f'{v_feat} vs 实际价格散点图已保存为 {plot_filename}')

            # 绘制这些特征的箱线图，按 brand 分组 (需要brand未被LabelEncoder转换成数字前的值，这里使用转换后的数字，但含义不变)
            # 注意：如果brand是连续的数字，箱线图可能意义不大，但这里LabelEncoder后仍然可以看作是类别
            if 'brand' in val_analysis_df.columns:
                plt.figure(figsize=(12, 6))
                sns.boxplot(x='brand', y=v_feat, data=val_analysis_df)
                plt.xlabel('品牌 (LabelEncoder编码)')
                plt.ylabel(v_feat)
                plt.title(f'{v_feat} 按品牌分组的箱线图')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plot_filename = f'11.1_{v_feat}_brand_boxplot.png'
                plt.savefig(plot_filename, dpi=150)
                plt.close()
                print(f'{v_feat} 按品牌分组的箱线图已保存为 {plot_filename}')

    print("\n========== 5.3 交互特征的进一步挖掘 ==========")
    # 绘制 km_age 与 price 的散点图，并使用颜色编码 brand
    if 'km_age' in val_analysis_df.columns and 'brand' in val_analysis_df.columns:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='km_age', y='actual_price', hue='brand', data=val_analysis_df, alpha=0.4, s=20)
        plt.xlabel('公里数*车龄 (km_age)')
        plt.ylabel('实际价格')
        plt.title('km_age vs 实际价格 (按品牌区分)')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend(title='品牌', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plot_filename = '11.1_km_age_price_brand_scatter.png'
        plt.savefig(plot_filename, dpi=150)
        plt.close()
        print(f'km_age vs 实际价格 (按品牌区分) 散点图已保存为 {plot_filename}')

    # 绘制 power 与 regYear 的散点图，并以 price 进行颜色编码
    if 'power' in val_analysis_df.columns and 'regYear' in val_analysis_df.columns:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='regYear', y='power', hue='actual_price', data=val_analysis_df, 
                        alpha=0.6, s=30, palette='viridis', legend='full')
        plt.xlabel('注册年份')
        plt.ylabel('功率')
        plt.title('功率 vs 注册年份 (按实际价格颜色编码)')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend(title='实际价格', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plot_filename = '11.1_power_regYear_price_scatter.png'
        plt.savefig(plot_filename, dpi=150)
        plt.close()
        print(f'功率 vs 注册年份 (按实际价格颜色编码) 散点图已保存为 {plot_filename}')

    print("\n========== 5.4 类别特征的编码策略优化可视化 ==========")
    # 绘制 brand 与 price 的箱线图
    if 'brand' in val_analysis_df.columns:
        plt.figure(figsize=(14, 7))
        sns.boxplot(x='brand', y='actual_price', data=val_analysis_df)
        plt.xlabel('品牌 (LabelEncoder编码)')
        plt.ylabel('实际价格')
        plt.title('品牌 vs 实际价格 箱线图')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plot_filename = '11.1_brand_price_boxplot.png'
        plt.savefig(plot_filename, dpi=150)
        plt.close()
        print(f'品牌 vs 实际价格 箱线图已保存为 {plot_filename}')

    # 绘制 model 与 price 的箱线图 (只选择出现次数最多的N个模型，否则图会非常拥挤)
    if 'model' in val_analysis_df.columns:
        top_N_models = 20 # 可以根据实际数据调整这个数量
        top_models = val_analysis_df['model'].value_counts().nlargest(top_N_models).index
        model_samples = val_analysis_df[val_analysis_df['model'].isin(top_models)]

        if not model_samples.empty:
            plt.figure(figsize=(16, 8))
            sns.boxplot(x='model', y='actual_price', data=model_samples)
            plt.xlabel('车型 (LabelEncoder编码)')
            plt.ylabel('实际价格')
            plt.title(f'Top {top_N_models} 车型 vs 实际价格 箱线图')
            plt.xticks(rotation=60, ha='right')
            plt.tight_layout()
            plot_filename = '11.1_model_price_boxplot.png'
            plt.savefig(plot_filename, dpi=150)
            plt.close()
            print(f'Top {top_N_models} 车型 vs 实际价格 箱线图已保存为 {plot_filename}')
        else:
            print(f"没有足够的数据来绘制 Top {top_N_models} 车型 vs 实际价格 箱线图。")

    print("\n========== 5.5 模型残差分析 ==========")
    # 计算残差
    val_analysis_df['residual'] = val_analysis_df['actual_price'] - val_analysis_df['predicted_price']

    # 绘制残差的直方图
    plt.figure(figsize=(10, 6))
    sns.histplot(val_analysis_df['residual'], kde=True, bins=50)
    plt.xlabel('残差 (实际价格 - 预测价格)')
    plt.ylabel('频率')
    plt.title('模型残差分布直方图')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plot_filename = '11.1_residual_hist.png'
    plt.savefig(plot_filename, dpi=150)
    plt.close()
    print(f'模型残差分布直方图已保存为 {plot_filename}')

    # 绘制残差与 v_3 的散点图
    if 'v_3' in val_analysis_df.columns:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x='v_3', y='residual', data=val_analysis_df, alpha=0.3, s=15)
        plt.axhline(0, color='r', linestyle='--', lw=1, label='零残差线')
        plt.xlabel('v_3 特征值')
        plt.ylabel('残差')
        plt.title('残差 vs v_3 特征')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plot_filename = '11.1_residual_vs_v3_scatter.png'
        plt.savefig(plot_filename, dpi=150)
        plt.close()
        print(f'残差 vs v_3 散点图已保存为 {plot_filename}')
    else:
        print("v_3 特征不存在，跳过残差 vs v_3 散点图绘制。")

    print("\n所有可视化和数据分析已完成，请检查生成的图片和CSV文件。")

if __name__ == "__main__":
    main() 