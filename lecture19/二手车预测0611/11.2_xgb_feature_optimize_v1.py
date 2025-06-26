"""
基于11.0_xgb_best.tuning.py的特征工程结果，进行特征工程的进一步优化
2000轮，早停轮次100轮
XGBoost模型重新训练完成。
重新训练模型在验证集上的 MAE: 0.1159
验证集 MAE: 519.8836
验证集 RMSE: 1235.0076
"""
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
import sys # 用于控制程序退出

def set_matplotlib_style():
    """
    :function: 设置matplotlib绘图风格和中文显示
    :return: 无
    """
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False
    plt.style.use('ggplot')

def load_data(train_path='11.0_xgb_best_train_features.csv', test_path='11.0_xgb_best_test_features.csv'):
    """
    :function: 加载训练和测试数据
    :param train_path: 训练集CSV文件路径
    :param test_path: 测试集CSV文件路径
    :return: train_df, test_df (加载后的DataFrame)
    """
    print("========== 正在加载特征工程结果数据 ==========")
    try:
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
    except FileNotFoundError as e:
        print(f"错误: 未找到文件 {e.filename}。请确保您已运行 11.0_xgb_best.tuning.py 并生成这些文件。")
        sys.exit() # 退出程序
    print("数据加载完成。")
    return train_df, test_df

def preprocess_and_feature_engineer(train_df, test_df):
    """
    :function: 进行数据预处理和增强特征工程
    :param train_df: 训练集DataFrame
    :param test_df: 测试集DataFrame
    :return: X, y, X_test, test_saleid (处理后的特征和标签)
    """
    print("\n========== 数据预处理和增强特征工程 ==========")

    # 处理brand列，确保是数值类型
    if 'brand' in train_df.columns:
        le = LabelEncoder()
        train_df['brand'] = le.fit_transform(train_df['brand'])
        test_df['brand'] = le.transform(test_df['brand'])

    # 增强特征工程 (新增内容)
    # 1. 对 v_0 和 v_12 进行多项式变换 (二次和三次)
    print("添加v_0和v_12的多项式特征...")
    train_df['v_0_sq'] = train_df['v_0']**2
    train_df['v_0_cub'] = train_df['v_0']**3
    train_df['v_12_sq'] = train_df['v_12']**2
    train_df['v_12_cub'] = train_df['v_12']**3

    test_df['v_0_sq'] = test_df['v_0']**2
    test_df['v_0_cub'] = test_df['v_0']**3
    test_df['v_12_sq'] = test_df['v_12']**2
    test_df['v_12_cub'] = test_df['v_12']**3

    # 2. 对 v_3 进行 Winsorization (缩尾处理)
    print("对v_3进行Winsorization处理...")
    # 计算训练集的1%和99%分位数
    lower_bound_v3 = train_df['v_3'].quantile(0.01)
    upper_bound_v3 = train_df['v_3'].quantile(0.99)
    print(f"v_3下限（1%分位数）: {lower_bound_v3:.4f}, 上限（99%分位数）: {upper_bound_v3:.4f}")

    # 应用缩尾到训练集和测试集
    train_df['v_3'] = train_df['v_3'].clip(lower=lower_bound_v3, upper=upper_bound_v3)
    test_df['v_3'] = test_df['v_3'].clip(lower=lower_bound_v3, upper=upper_bound_v3)

    # 分离特征和目标变量
    if 'price' not in train_df.columns:
        print("错误: 训练集中未找到 'price' 列。")
        sys.exit()

    y = train_df['price']
    train_df = train_df.drop('price', axis=1)

    # 确保训练集和测试集具有相同的列
    common_cols = list(set(train_df.columns) & set(test_df.columns))
    X = train_df[common_cols]
    X_test = test_df[common_cols]

    # 对于 SaleID，如果测试集中存在则保留，用于提交文件
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else None

    # 确保所有特征列的数据类型是XGBoost支持的数值类型
    for col in X.columns:
        if X[col].dtype == 'object':
            try:
                X[col] = pd.to_numeric(X[col], errors='coerce')
                X_test[col] = pd.to_numeric(X_test[col], errors='coerce')
            except ValueError:
                print(f"警告: 列 '{col}' 无法转换为数值类型，将被删除。")
                X = X.drop(columns=[col])
                X_test = X_test.drop(columns=[col])

    # 填充缺失值 (简单的均值填充，可根据实际情况优化)
    print("填充缺失值...")
    for col in X.columns:
        if X[col].isnull().any():
            mean_val = X[col].mean()
            X[col] = X[col].fillna(mean_val)
            X_test[col] = X_test[col].fillna(mean_val)
    
    print("数据预处理和增强特征工程完成。")
    return X, y, X_test, test_saleid


def train_and_evaluate_model(X, y, X_test, test_saleid):
    """
    :function: 训练XGBoost模型并进行评估，保存结果
    :param X: 训练特征集
    :param y: 训练标签集
    :param X_test: 测试特征集
    :param test_saleid: 测试集SaleID
    :return: 无
    """
    print("\n========== XGBoost模型训练 ==========")
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # 对数变换目标变量
    y_train_log = np.log1p(y_train)
    y_val_log = np.log1p(y_val)

    # 高价车加权策略 (新增内容)
    # 为实际价格 > 50000 的样本设置更高权重
    # 由于y_train_log是log1p变换后的值，需要将50000也进行log1p变换
    high_price_threshold_log = np.log1p(50000)
    sample_weight = np.ones(y_train_log.shape)
    sample_weight[y_train_log > high_price_threshold_log] = 2.0 # 将高价样本权重设置为2倍

    print(f"高价车权重阈值（log1p后）: {high_price_threshold_log:.4f}")
    print(f"高价样本数量: {np.sum(y_train_log > high_price_threshold_log)}")
    print(f"训练集总样本数量: {len(y_train_log)}")

    xgb = XGBRegressor(
        objective='reg:squarederror', # 适用于回归任务，直接优化MSE
        # objective='reg:absoluteerror', # 如果直接优化MAE，可以尝试此项
        eval_metric='mae',
        n_estimators=2000,
        learning_rate=0.03,
        max_depth=10,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        tree_method='hist', # 对于大数据集，hist更快
        early_stopping_rounds=100 # 早停
    )

    xgb.fit(X_train, y_train_log,
            eval_set=[(X_val, y_val_log)],
            verbose=100,
            sample_weight=sample_weight # 传入样本权重
           )

    print("XGBoost模型重新训练完成。")
    print(f"重新训练模型在验证集上的 MAE: {xgb.best_score:.4f}")

    # 评估
    val_pred_log = xgb.predict(X_val)
    val_pred = np.expm1(val_pred_log) # 反向变换回原始价格尺度

    mae = mean_absolute_error(y_val, val_pred)
    rmse = np.sqrt(mean_squared_error(y_val, val_pred))
    print(f"验证集 MAE: {mae:.4f}")
    print(f"验证集 RMSE: {rmse:.4f}")

    # 预测
    print("\n========== 预测测试集 ==========")
    test_pred_log = xgb.predict(X_test)
    test_pred = np.expm1(test_pred_log) # 反向变换

    # 确保预测值非负
    test_pred[test_pred < 0] = 0

    # 绘制预测结果散点图（针对验证集）
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=y_val, y=val_pred, alpha=0.3)
    plt.plot([y_val.min(), y_val.max()], [y_val.min(), y_val.max()], 'r--', lw=2, label='理想预测')
    plt.xlabel('实际价格')
    plt.ylabel('预测价格')
    plt.title('11.2_xgb_feature_optimize_v1_预测价格 vs 实际价格')
    plt.legend()
    plt.tight_layout()
    plt.savefig('11.2_xgb_feature_optimize_v1_price_pred_vs_true.png', dpi=150)
    plt.close()
    print('预测价格 vs 实际价格图已保存为 11.2_xgb_feature_optimize_v1_price_pred_vs_true.png')

    # 保存预测结果到CSV
    if test_saleid is not None:
        submission = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred})
        submission.to_csv('11.2_xgb_feature_optimize_v1_predict.csv', index=False)
        print('预测结果已保存为 11.2_xgb_feature_optimize_v1_predict.csv')
    else:
        print("警告: 测试集中没有 'SaleID' 列，无法保存预测结果到CSV。")

    # 特征重要性图
    print("\n========== 特征重要性分析 ==========")
    importances = xgb.feature_importances_
    features = X.columns
    
    # 将特征重要性与特征名称对应，并按重要性降序排列
    feature_importance_df = pd.DataFrame({'Feature': features, 'Importance': importances})
    feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)

    # 提取Top 30特征
    top_30_features = feature_importance_df.head(30)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x='Importance', y='Feature', data=top_30_features)
    plt.xlabel('特征重要性')
    plt.ylabel('特征')
    plt.title('11.2_xgb_feature_optimize_v1_XGBoost特征重要性Top30')
    plt.tight_layout()
    plt.savefig('11.2_xgb_feature_optimize_v1_importance_top30.png', dpi=150)
    plt.close()
    print('特征重要性Top30图已保存为 11.2_xgb_feature_optimize_v1_importance_top30.png')
    print("XGBoost特征工程优化v1 完成。")

def main():
    set_matplotlib_style()
    train_df, test_df = load_data()
    X, y, X_test, test_saleid = preprocess_and_feature_engineer(train_df, test_df)
    train_and_evaluate_model(X, y, X_test, test_saleid)

if __name__ == '__main__':
    main() 