'''
程序说明：
## 1. 本程序仅负责读取V100_feature_engineering_only.py输出的特征文件，完成LightGBM模型的训练、验证、预测、评估和结果输出。
## 2. 与旧版 main_model_lgb.py 相比，输入输出文件名均以V100_开头，且不再包含原始字符串型model列，只用数值型特征，结构更清晰，便于调试和模型优化。
[20000] train's l1: 33.4474     valid's l1: 520.307
Did not meet early stopping. Best iteration is:
[19999] train's l1: 33.4509     valid's l1: 520.307
LightGBM模型训练完成。
验证集 MAE: 520.3067
验证集 RMSE: 1219.7252
[24100] train's l1: 22.7278     valid's l1: 519.616
Early stopping, best iteration is:
[24023] train's l1: 22.8891     valid's l1: 519.615
LightGBM模型训练完成。
验证集 MAE: 519.6147
验证集 RMSE: 1219.9107
分数:495.0750
'''
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import sys
import warnings
import lightgbm as lgb

warnings.filterwarnings('ignore', category=FutureWarning)

def set_matplotlib_style():
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False
    plt.style.use('ggplot')

def load_data(train_path='V100_train_features.csv', test_path='V100_test_features.csv'):
    print("========== 正在加载特征工程结果数据 ==========")
    try:
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
    except FileNotFoundError as e:
        print(f"错误: 未找到文件 {e.filename}。请确保已运行特征工程脚本并生成这些文件。")
        sys.exit()
    print("数据加载完成。")
    return train_df, test_df

def train_and_evaluate_model(train_df, test_df):
    print("\n========== LightGBM模型训练 ==========")
    y = train_df['price']
    X = train_df.drop(['price'], axis=1)
    X_test = test_df.drop(['SaleID'], axis=1) if 'SaleID' in test_df.columns else test_df.copy()
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else np.arange(len(test_df))

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    lgb_train = lgb.Dataset(X_train, y_train, free_raw_data=False)
    lgb_val = lgb.Dataset(X_val, y_val, reference=lgb_train, free_raw_data=False)

    params = {
        'objective': 'regression',
        'metric': 'mae',
        'boosting_type': 'gbdt',
        'learning_rate': 0.03,
        'num_leaves': 64,
        'max_depth': 10,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 1,
        'seed': 42,
        'verbose': -1,
        'n_jobs': -1
    }

    model = lgb.train(
        params,
        lgb_train,
        num_boost_round=30000,
        valid_sets=[lgb_train, lgb_val],
        valid_names=['train', 'valid'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=100),
            lgb.log_evaluation(period=100)
        ]
    )

    print("LightGBM模型训练完成。")
    val_pred = model.predict(X_val, num_iteration=model.best_iteration)
    mae = mean_absolute_error(y_val, val_pred)
    rmse = np.sqrt(mean_squared_error(y_val, val_pred))
    print(f"验证集 MAE: {mae:.4f}")
    print(f"验证集 RMSE: {rmse:.4f}")

    val_pred_df = pd.DataFrame({'SaleID': X_val['SaleID'] if 'SaleID' in X_val.columns else np.arange(len(X_val)), 'price': val_pred})
    val_pred_df.to_csv('V100_main_model_lgb_val_pred.csv', index=False)

    print("\n========== 预测测试集 ==========")
    test_pred = model.predict(X_test, num_iteration=model.best_iteration)
    test_pred[test_pred < 0] = 0

    print("生成预测价格 vs 实际价格图...")
    plt.figure(figsize=(10, 6))
    sns.regplot(x=y_val, y=val_pred, scatter_kws={'alpha':0.3})
    plt.title('验证集：预测价格 vs 实际价格')
    plt.xlabel('实际价格')
    plt.ylabel('预测价格')
    plt.savefig('V100_main_model_lgb_price_pred_vs_true.png')
    plt.close()
    print("预测价格 vs 实际价格图已保存为 V100_main_model_lgb_price_pred_vs_true.png")

    submission = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred})
    submission.to_csv('V100_main_model_lgb_predict.csv', index=False)
    print(f"预测结果已保存为 V100_main_model_lgb_predict.csv")

    print("\n========== 特征重要性分析 ==========")
    feature_importance_df = pd.DataFrame({'feature': X.columns, 'importance': model.feature_importance()})
    feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)
    plt.figure(figsize=(12, 8))
    sns.barplot(x='importance', y='feature', data=feature_importance_df.head(30))
    plt.title('特征重要性 Top 30 (LightGBM)')
    plt.xlabel('重要性')
    plt.ylabel('特征')
    plt.savefig('V100_main_model_lgb_importance_top30.png')
    plt.close()
    print("特征重要性Top30图已保存为 V100_main_model_lgb_importance_top30.png")
    print("LightGBM特征工程优化完成。")

if __name__ == '__main__':
    set_matplotlib_style()
    train_df, test_df = load_data()
    train_and_evaluate_model(train_df, test_df) 