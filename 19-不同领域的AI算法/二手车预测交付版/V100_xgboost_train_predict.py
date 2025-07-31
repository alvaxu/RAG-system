'''
程序说明：
## 1. 本程序仅负责读取特征工程输出的特征文件，完成XGBoost模型的训练、验证、预测、评估和结果输出。
## 2. 与旧版 main_model.py 相比，去除了所有特征工程相关的代码，结构更清晰，便于调试和模型优化。
[1999]  validation_0-mae:0.11535
XGBoost模型重新训练完成。
重新训练模型在验证集上的 MAE (xgb.best_score): 0.1153
验证集 MAE: 513.2641
验证集 RMSE: 1222.3724
[7649]  validation_0-mae:0.11432
XGBoost模型重新训练完成。
重新训练模型在验证集上的 MAE (xgb.best_score): 0.1143
验证集 MAE: 507.4029
验证集 RMSE: 1222.3729

成绩：493.0538
'''
# 只保留特征文件读取、模型训练、评估、预测、可视化、结果保存部分，去除特征工程相关内容。
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, KFold
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import sys
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)

def set_matplotlib_style():
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False
    plt.style.use('ggplot')

def load_data(train_path='V100_train_features.csv', test_path='V100_test_features.csv'):
    print("========== 正在加载特征工程结果数据 ==========")
    try:
        train_df = pd.read_csv(train_path, dtype={'model': str})
        test_df = pd.read_csv(test_path, dtype={'model': str})
    except FileNotFoundError as e:
        print(f"错误: 未找到文件 {e.filename}。请确保已运行特征工程脚本并生成这些文件。")
        sys.exit()
    print("数据加载完成。")
    return train_df, test_df

def train_and_evaluate_model(train_df, test_df):
    """
    :function: 训练XGBoost模型并进行评估，保存结果
    :param train_df: 训练集特征DataFrame（含price）
    :param test_df: 测试集特征DataFrame
    :return: 无
    """
    print("\n========== XGBoost模型训练 ==========")
    # 1. 特征与标签分离
    y = train_df['price']
    X = train_df.drop(['price'], axis=1)
    X_test = test_df.drop(['SaleID'], axis=1) if 'SaleID' in test_df.columns else test_df.copy()
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else np.arange(len(test_df))

    # 2. 划分训练集和验证集
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    y_train_log = np.log1p(y_train)
    y_val_log = np.log1p(y_val)

    # 3. XGBoost模型训练
    xgb = XGBRegressor(
        objective='reg:squarederror',
        eval_metric='mae',
        n_estimators=8000,
        learning_rate=0.03,
        max_depth=10,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        tree_method='hist',
        early_stopping_rounds=100
    )
    xgb.fit(X_train, y_train_log,
            eval_set=[(X_val, y_val_log)],
            verbose=100
           )
    print("XGBoost模型重新训练完成。")
    print(f"重新训练模型在验证集上的 MAE (xgb.best_score): {xgb.best_score:.4f}")

    # 4. 验证集评估
    val_pred_log = xgb.predict(X_val)
    val_pred = np.expm1(val_pred_log)
    mae = mean_absolute_error(y_val, val_pred)
    rmse = np.sqrt(mean_squared_error(y_val, val_pred))
    print(f"验证集 MAE: {mae:.4f}")
    print(f"验证集 RMSE: {rmse:.4f}")

    # 5. 测试集预测
    print("\n========== 预测测试集 ==========")
    test_pred_log = xgb.predict(X_test)
    test_pred = np.expm1(test_pred_log)
    test_pred[test_pred < 0] = 0

    # 6. 可视化预测结果
    print("生成预测价格 vs 实际价格图...")
    plt.figure(figsize=(10, 6))
    sns.regplot(x=y_val, y=val_pred, scatter_kws={'alpha':0.3})
    plt.title('验证集：预测价格 vs 实际价格')
    plt.xlabel('实际价格')
    plt.ylabel('预测价格')
    plt.savefig('V100_main_model_price_pred_vs_true.png')
    plt.close()
    print("预测价格 vs 实际价格图已保存为 V100_main_model_price_pred_vs_true.png")

    # 7. 保存预测结果
    submission = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred})
    submission.to_csv('V100_main_model_predict.csv', index=False)
    print(f"预测结果已保存为 V100_main_model_predict.csv")

    # 8. 保存验证集预测
    val_pred_df = pd.DataFrame({'SaleID': X_val['SaleID'] if 'SaleID' in X_val.columns else np.arange(len(X_val)), 'price': val_pred})
    val_pred_df.to_csv('V100_main_model_val_pred.csv', index=False)

    # 9. 特征重要性分析与可视化
    print("\n========== 特征重要性分析 ==========")
    feature_importance_df = pd.DataFrame({'feature': X.columns, 'importance': xgb.feature_importances_})
    feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)
    plt.figure(figsize=(12, 8))
    sns.barplot(x='importance', y='feature', data=feature_importance_df.head(30))
    plt.title('特征重要性 Top 30')
    plt.xlabel('重要性')
    plt.ylabel('特征')
    plt.savefig('V100_main_model_importance_top30.png')
    plt.close()
    print("特征重要性Top30图已保存为 V100_main_model_importance_top30.png")
    print("XGBoost特征工程优化完成。")

if __name__ == '__main__':
    set_matplotlib_style()
    train_df, test_df = load_data()
    train_and_evaluate_model(train_df, test_df) 