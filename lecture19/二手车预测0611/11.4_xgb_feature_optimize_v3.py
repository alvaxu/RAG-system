'''
11.4_xgb_feature_optimize_v3.py






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

def target_encode_features(df, target_col, features_to_encode):
    """
    :function: 对指定特征进行目标编码
    :param df: 包含特征和目标变量的DataFrame
    :param target_col: 目标变量的列名
    :param features_to_encode: 需要进行目标编码的特征列表
    :return: 处理后的DataFrame
    """
    for feature in features_to_encode:
        # 计算每个类别的目标均值
        # 注意：这里直接在整个DataFrame上计算，存在数据泄露风险。
        # 在交叉验证中，应在训练折叠上计算，应用于验证折叠和测试集。
        mapping = df.groupby(feature)[target_col].mean()
        df[f'{feature}_target_encoded'] = df[feature].map(mapping)

        # 对于测试集或新的数据，需要处理训练集中未出现的新类别，简单填充训练集均值
        global_mean = df[target_col].mean()
        df[f'{feature}_target_encoded'].fillna(global_mean, inplace=True)
        
        print(f"已对特征 '{feature}' 进行目标编码。")
    return df

def preprocess_and_feature_engineer(train_df, test_df):
    """
    :function: 进行数据预处理和增强特征工程
    :param train_df: 训练集DataFrame
    :param test_df: 测试集DataFrame
    :return: X, y, X_test, test_saleid (处理后的特征和标签)
    """
    print("\n========== 数据预处理和增强特征工程 ==========")

    # 合并训练集和测试集以便进行统一的特征工程（注意特征工程的顺序和数据泄露风险）
    # 在此处执行LabelEncoder可能导致Target Encoding不准确，所以先删除LabelEncoder部分。
    # combined_df = pd.concat([train_df.drop('price', axis=1), test_df], ignore_index=True)

    # 确保brand是数值类型（如果之前是字符串），以便目标编码能正确处理
    # 这里不再使用LabelEncoder因为将使用Target Encoding
    # if 'brand' in train_df.columns and train_df['brand'].dtype == 'object':
    #     le = LabelEncoder()
    #     train_df['brand'] = le.fit_transform(train_df['brand'])
    #     test_df['brand'] = le.transform(test_df['brand'])

    # 记录原始训练集大小以便后面分离
    train_size = len(train_df)
    # 临时合并，确保特征工程的一致性
    combined_df = pd.concat([train_df.assign(is_train=1), test_df.assign(is_train=0)], ignore_index=True)

    # 1. 对 v_0 和 v_12 进行多项式变换 (二次和三次)
    print("添加v_0和v_12的多项式特征...")
    combined_df['v_0_sq'] = combined_df['v_0']**2
    # combined_df['v_0_cub'] = combined_df['v_0']**3 # 移除v_0的三次项
    combined_df['v_12_sq'] = combined_df['v_12']**2
    combined_df['v_12_cub'] = combined_df['v_12']**3

    # 2. 对 v_3 进行 Winsorization (缩尾处理)
    print("对v_3进行Winsorization处理...")
    # 计算训练集的1%和99%分位数 (只使用训练集数据来计算分位数，避免数据泄露)
    lower_bound_v3 = train_df['v_3'].quantile(0.01)
    upper_bound_v3 = train_df['v_3'].quantile(0.99)
    print(f"v_3下限（1%分位数）: {lower_bound_v3:.4f}, 上限（99%分位数）: {upper_bound_v3:.4f}")

    # 应用缩尾到合并后的数据
    combined_df['v_3'] = combined_df['v_3'].clip(lower=lower_bound_v3, upper=upper_bound_v3)

    # 3. 目标编码 (Target Encoding) - 引入平滑处理
    print("对类别特征进行目标编码 (含平滑处理)...")
    categorical_features_to_encode = ['brand', 'model', 'bodyType', 'fuelType', 'gearbox', 'notRepairedDamage']
    # 将非字符串的类别特征转换为字符串以便groupby能正确处理
    for col in categorical_features_to_encode:
        if col in combined_df.columns:
            combined_df[col] = combined_df[col].astype(str)
    
    train_temp = combined_df[combined_df['is_train']==1].copy()
    train_temp['price'] = train_df['price'] # 确保price列存在于temp_train_df
    
    global_mean = train_temp['price'].mean()
    smoothing_factor = 500 # 提高平滑因子，减少高基数类别特征（如model）的过拟合风险

    for feature in categorical_features_to_encode:
        if feature in train_temp.columns:
            # 计算每个类别的目标均值和计数
            agg_stats = train_temp.groupby(feature)['price'].agg(['mean', 'count'])
            # 应用平滑公式
            smoothed_mapping = (agg_stats['mean'] * agg_stats['count'] + global_mean * smoothing_factor) / \
                               (agg_stats['count'] + smoothing_factor)
            
            combined_df[f'{feature}_target_encoded'] = combined_df[feature].map(smoothed_mapping)
            # 对于测试集或新数据中训练集未出现的类别，填充训练集的目标均值
            combined_df[f'{feature}_target_encoded'] = combined_df[f'{feature}_target_encoded'].fillna(global_mean)
            print(f"已对特征 '{feature}' 进行目标编码（平滑处理）。")

    # 分离回训练集和测试集
    train_df_processed = combined_df[combined_df['is_train']==1].drop(columns=['is_train','price'])
    test_df_processed = combined_df[combined_df['is_train']==0].drop(columns=['is_train','price'])
    
    # 恢复原始的y
    y = train_df['price']
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else None

    # 确保训练集和测试集具有相同的列（在Target Encoding后会有新列）
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

    # 高价车加权策略 (调整权重为5.0)
    high_price_threshold_log = np.log1p(50000)
    sample_weight = np.ones(y_train_log.shape)
    sample_weight[y_train_log > high_price_threshold_log] = 5.0 # 将高价样本权重设置为5倍

    print(f"高价车权重阈值（log1p后）: {high_price_threshold_log:.4f}")
    print(f"高价样本数量: {np.sum(y_train_log > high_price_threshold_log)}")
    print(f"训练集总样本数量: {len(y_train_log)}")

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
            verbose=100,
            sample_weight=sample_weight # 传入样本权重
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
    plt.title('11.4_xgb_feature_optimize_v3_预测价格 vs 实际价格')
    plt.legend()
    plt.tight_layout()
    plt.savefig('11.4_xgb_feature_optimize_v3_price_pred_vs_true.png', dpi=150)
    plt.close()
    print('预测价格 vs 实际价格图已保存为 11.4_xgb_feature_optimize_v3_price_pred_vs_true.png')

    # 保存预测结果到CSV
    if test_saleid is not None:
        submission = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred})
        submission.to_csv('11.4_xgb_feature_optimize_v3_predict.csv', index=False)
        print('预测结果已保存为 11.4_xgb_feature_optimize_v3_predict.csv')
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
    plt.title('11.4_xgb_feature_optimize_v3_XGBoost特征重要性Top30')
    plt.tight_layout()
    plt.savefig('11.4_xgb_feature_optimize_v3_importance_top30.png', dpi=150)
    plt.close()
    print('特征重要性Top30图已保存为 11.4_xgb_feature_optimize_v3_importance_top30.png')
    print("XGBoost特征工程优化v3 完成。")

def main():
    set_matplotlib_style()
    train_df, test_df = load_data()
    X, y, X_test, test_saleid = preprocess_and_feature_engineer(train_df, test_df)
    train_and_evaluate_model(X, y, X_test, test_saleid)

if __name__ == '__main__':
    main() 