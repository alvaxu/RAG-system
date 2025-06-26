'''
11.6_xgb_feature_optimize_v5.py

基于11.1的MAE表现，放弃v3/v4版本中导致性能下降的特征工程措施（如多项式变换、Winsorization、高价车加权等）。
本次优化将专注于在现有特征基础上，新增交互特征和频率编码，以期提升模型性能。

11.6_xgb_feature_optimize_v5.py 所做的优化主要包括以下几点：
放弃了之前版本中导致性能下降的优化措施：
移除了 v_0 和 v_12 的多项式变换（二次和三次）。
移除了 v_3 的 Winsorization (缩尾处理)。
移除了高价车样本的加权策略。
移除了代码中显式的目标编码部分，因为我们回到 11.1 的基础，可能意味着输入数据已包含处理好的特征，或者当前手动实现的目标编码效果不佳。
新增并增强了有潜力的特征工程方向：
交互特征 v_0 * v_12：将两个高重要性特征进行乘积，以期捕捉更强的联合效应。
派生特征 power_per_year：计算 power / (2020 - regYear)，作为车辆“单位年限功率”的度量，反映车辆性能随年限的衰减。
新特征 v_3_abs：引入 v_3 的绝对值，以探索其可能对价格产生的非线性影响，尤其是在其负值区域。
频率编码：对高基数类别特征 brand 和 model 进行频率编码，将类别转换为其在数据中的出现频率，作为一种新的数值化表示。
总而言之，v5 版本旨在回归到 11.1 版本较好的性能基线，并通过引入新的、更具洞察力的交互特征和频率编码来进一步提升模型效果。

'''
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
import warnings # 用于控制警告信息

# 屏蔽FutureWarning
warnings.filterwarnings('ignore', category=FutureWarning)

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

    # 记录原始训练集大小以便后面分离
    train_size = len(train_df)
    # 临时合并，确保特征工程的一致性
    combined_df = pd.concat([train_df.assign(is_train=1), test_df.assign(is_train=0)], ignore_index=True)

    # --- 移除之前导致性能下降的特征工程措施 ---
    # 1. 移除 v_0 和 v_12 的多项式变换
    # 2. 移除 v_3 的 Winsorization (缩尾处理)
    # 3. 移除显式的目标编码 (假设input CSV已包含或不需要额外处理)

    # --- 新增特征工程 ---
    print("\n========== 添加增强特征 ==========") # 新增部分，用于加入交互特征和频率编码

    # 4. v_0 * v_12 交互特征
    if 'v_0' in combined_df.columns and 'v_12' in combined_df.columns:
        combined_df['v_0_v_12_inter'] = combined_df['v_0'] * combined_df['v_12']
        print("已添加特征 'v_0_v_12_inter'.")
    else:
        print("警告: 无法添加 'v_0_v_12_inter'，因为 'v_0' 或 'v_12' 列不存在。")


    # 5. power_per_year 特征
    if 'power' in combined_df.columns and 'regYear' in combined_df.columns:
        # 确保分母不为零，并处理潜在的无穷大/NaN
        combined_df['power_per_year'] = combined_df['power'] / (2020 - combined_df['regYear'].replace(2020, np.nan)) # 避免2020-2020=0
        combined_df['power_per_year'].replace([np.inf, -np.inf], np.nan, inplace=True) # 将inf替换为NaN，由后续填充处理
        print("已添加特征 'power_per_year'.")
    else:
        print("警告: 无法添加 'power_per_year'，因为 'power' 或 'regYear' 列不存在。")


    # 6. v_3_abs (v_3的绝对值) 特征
    if 'v_3' in combined_df.columns:
        combined_df['v_3_abs'] = combined_df['v_3'].abs()
        print("已添加特征 'v_3_abs'.")
    else:
        print("警告: 无法添加 'v_3_abs'，因为 'v_3' 列不存在。")


    # 7. 频率编码 (Frequency Encoding)
    features_for_freq_encode = ['brand', 'model'] # 高基数类别特征，适合频率编码
    for feature in features_for_freq_encode:
        if feature in combined_df.columns:
            # 基于组合数据计算频率，确保一致性
            freq_map = combined_df[feature].value_counts(normalize=True)
            combined_df[f'{feature}_freq_encoded'] = combined_df[feature].map(freq_map)
            # 对测试集中未出现的新类别填充0 (或均值)
            combined_df[f'{feature}_freq_encoded'].fillna(0, inplace=True) 
            print(f"已对特征 '{feature}' 进行频率编码。")
        else:
            print(f"警告: 无法对特征 '{feature}' 进行频率编码，因为该列不存在。")

    # 分离回训练集和测试集
    train_df_processed = combined_df[combined_df['is_train']==1].drop(columns=['is_train','price'])
    test_df_processed = combined_df[combined_df['is_train']==0].drop(columns=['is_train','price'])
    
    # 恢复原始的y
    y = train_df['price']
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else None

    # 确保训练集和测试集具有相同的列
    X = train_df_processed
    X_test = test_df_processed

    # 确保所有特征列的数据类型是XGBoost支持的数值类型
    for col in X.columns:
        if X[col].dtype == 'object': # Target Encoded 列可能不会是object
            try:
                X[col] = pd.to_numeric(X[col], errors='coerce')
                X_test[col] = pd.to_numeric(X_test[col], errors='coerce')
            except ValueError:
                print(f"警告: 列 '{col}' 无法转换为数值类型，将被删除。")
                X = X.drop(columns=[col])
                X_test = X_test.drop(columns=[col])
        # 将所有boolean列转换为int
        elif X[col].dtype == 'bool':
            X[col] = X[col].astype(int)
            X_test[col] = X_test[col].astype(int)

    # 填充缺失值 (简单的均值填充，可根据实际情况优化)
    print("填充缺失值...")
    for col in X.columns:
        if X[col].isnull().any():
            mean_val = X[col].mean()
            X[col] = X[col].fillna(mean_val)
            X_test[col] = X_test[col].fillna(mean_val)

    # 确保X和X_test的列顺序一致
    missing_in_test = set(X.columns) - set(X_test.columns)
    for col in missing_in_test:
        X_test[col] = 0 # 简单填充0
    missing_in_train = set(X_test.columns) - set(X.columns)
    for col in missing_in_train:
        X[col] = 0 # 简单填充0
    X_test = X_test[X.columns] # 确保列顺序一致

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

    # 移除高价车加权策略

    xgb = XGBRegressor(
        objective='reg:squarederror',
        eval_metric='mae',
        n_estimators=2000,
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
    plt.title('11.6_xgb_feature_optimize_v5_预测价格 vs 实际价格')
    plt.legend()
    plt.tight_layout()
    plt.savefig('11.6_xgb_feature_optimize_v5_price_pred_vs_true.png', dpi=150)
    plt.close()
    print('预测价格 vs 实际价格图已保存为 11.6_xgb_feature_optimize_v5_price_pred_vs_true.png')

    # 保存预测结果到CSV
    if test_saleid is not None:
        submission = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred})
        submission.to_csv('11.6_xgb_feature_optimize_v5_predict.csv', index=False)
        print('预测结果已保存为 11.6_xgb_feature_optimize_v5_predict.csv')
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
    plt.title('11.6_xgb_feature_optimize_v5_XGBoost特征重要性Top30')
    plt.tight_layout()
    plt.savefig('11.6_xgb_feature_optimize_v5_importance_top30.png', dpi=150)
    plt.close()
    print('特征重要性Top30图已保存为 11.6_xgb_feature_optimize_v5_importance_top30.png')
    print("XGBoost特征工程优化v5 完成。")

def main():
    set_matplotlib_style()
    train_df, test_df = load_data()
    X, y, X_test, test_saleid = preprocess_and_feature_engineer(train_df, test_df)
    train_and_evaluate_model(X, y, X_test, test_saleid)

if __name__ == '__main__':
    main() 