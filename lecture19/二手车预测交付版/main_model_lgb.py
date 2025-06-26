"""
main_model_lgb.py

基于LightGBM的二手车价格预测最终模型代码。
20000次迭代
[10300] train's l1: 89.045      valid's l1: 550.856
Early stopping, best iteration is:
[10282] train's l1: 89.2381     valid's l1: 550.847
LightGBM模型训练完成。
验证集 MAE: 550.8472
验证集 RMSE: 1243.1121
成绩：530.6459
"""
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

# 屏蔽FutureWarning
warnings.filterwarnings('ignore', category=FutureWarning)

def set_matplotlib_style():
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False
    plt.style.use('ggplot')

def load_data(train_path='train_features.csv', test_path='test_features.csv'):
    print("========== 正在加载特征工程结果数据 ==========")
    try:
        train_df = pd.read_csv(train_path, dtype={'model': str})
        test_df = pd.read_csv(test_path, dtype={'model': str})
    except FileNotFoundError as e:
        print(f"错误: 未找到文件 {e.filename}。请确保您已运行 `feature_engineering.py` 并生成这些文件。")
        sys.exit()
    print("数据加载完成。")
    return train_df, test_df

def preprocess_and_feature_engineer(train_df, test_df):
    print("\n========== 数据预处理和增强特征工程 ==========")
    train_size = len(train_df)
    combined_df = pd.concat([train_df.assign(is_train=1), test_df.assign(is_train=0)], ignore_index=True)

    # LightGBM支持类别特征，找出所有类别型特征（只选object或int类型，排除float）
    cat_features = []
    for col in combined_df.columns:
        if col not in ['price', 'SaleID', 'is_train']:
            if combined_df[col].dtype == 'object':
                cat_features.append(col)
            elif pd.api.types.is_integer_dtype(combined_df[col]) and combined_df[col].nunique() < 1000:
                cat_features.append(col)

    # 填充缺失值
    for col in combined_df.columns:
        if combined_df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(combined_df[col]):
                median_val = combined_df[col].median()
                combined_df[col] = combined_df[col].fillna(median_val)
            else:
                mode_val = combined_df[col].mode()
                if not mode_val.empty:
                    mode_val = mode_val[0]
                    combined_df[col] = combined_df[col].fillna(mode_val)

    # 将所有类别特征转为 category 类型（LightGBM要求）
    for col in cat_features:
        combined_df[col] = combined_df[col].astype('category')

    # 特征选择（去除无关列）
    exclude_cols = ['is_train', 'price', 'SaleID']
    features = [col for col in combined_df.columns if col not in exclude_cols]

    X = combined_df[combined_df['is_train']==1][features]
    X_test = combined_df[combined_df['is_train']==0][features]
    y = train_df['price']
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else None

    print("\n========== 数据预处理和增强特征工程完成。==========\n")
    return X, y, X_test, test_saleid, cat_features

def train_and_evaluate_model(X, y, X_test, test_saleid, cat_features):
    print("\n========== LightGBM模型训练 ==========")
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # LightGBM支持原生类别特征
    lgb_train = lgb.Dataset(X_train, y_train, categorical_feature=cat_features, free_raw_data=False)
    lgb_val = lgb.Dataset(X_val, y_val, categorical_feature=cat_features, reference=lgb_train, free_raw_data=False)

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
        num_boost_round=20000,
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

    # 保存验证集预测
    val_pred_df = pd.DataFrame({'SaleID': X_val['SaleID'] if 'SaleID' in X_val.columns else np.arange(len(X_val)), 'price': val_pred})
    val_pred_df.to_csv('main_model_lgb_val_pred.csv', index=False)

    # 预测
    print("\n========== 预测测试集 ==========")
    test_pred = model.predict(X_test, num_iteration=model.best_iteration)
    test_pred[test_pred < 0] = 0

    # 可视化预测结果
    print("生成预测价格 vs 实际价格图...")
    plt.figure(figsize=(10, 6))
    sns.regplot(x=y_val, y=val_pred, scatter_kws={'alpha':0.3})
    plt.title('验证集：预测价格 vs 实际价格')
    plt.xlabel('实际价格')
    plt.ylabel('预测价格')
    plt.savefig('main_model_lgb_price_pred_vs_true.png')
    plt.close()
    print("预测价格 vs 实际价格图已保存为 main_model_lgb_price_pred_vs_true.png")

    # 保存预测结果
    submission = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred})
    submission.to_csv('main_model_lgb_predict.csv', index=False)
    print(f"预测结果已保存为 main_model_lgb_predict.csv")

    # 特征重要性分析与可视化
    print("\n========== 特征重要性分析 ==========")
    feature_importance_df = pd.DataFrame({'feature': X.columns, 'importance': model.feature_importance()})
    feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)

    plt.figure(figsize=(12, 8))
    sns.barplot(x='importance', y='feature', data=feature_importance_df.head(30))
    plt.title('特征重要性 Top 30 (LightGBM)')
    plt.xlabel('重要性')
    plt.ylabel('特征')
    plt.savefig('main_model_lgb_importance_top30.png')
    plt.close()
    print("特征重要性Top30图已保存为 main_model_lgb_importance_top30.png")

    print("LightGBM特征工程优化完成。")

def main():
    set_matplotlib_style()
    train_df, test_df = load_data()
    X, y, X_test, test_saleid, cat_features = preprocess_and_feature_engineer(train_df, test_df)
    train_and_evaluate_model(X, y, X_test, test_saleid, cat_features)

if __name__ == '__main__':
    main() 