"""
11.14_xgb_feature_optimize_v13.py

基于11.13版本，恢复brand和model的交叉验证目标编码（无平滑），
新增regionCode的频率编码，并探索regYear和power之间的新交互特征。
"""
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, KFold
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
import sys
import warnings

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
        train_df = pd.read_csv(train_path, dtype={'model': str})
        test_df = pd.read_csv(test_path, dtype={'model': str})
    except FileNotFoundError as e:
        print(f"错误: 未找到文件 {e.filename}。请确保您已运行 11.0_xgb_best.tuning.py 并生成这些文件。")
        sys.exit()
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
    # 3. 移除高价车加权策略

    # --- 新增特征工程 ---
    print("\n========== 添加增强特征 ==========") # 新增部分，用于加入交互特征和目标编码

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

    # 7. 恢复交叉验证目标编码 (Target Encoding)
    # 恢复 brand 和 model 的目标编码
    target_encode_cols = ['brand', 'model'] 
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    global_overall_mean = train_df['price'].mean() # 全局目标均值，用于新类别填充
    
    for col in target_encode_cols:
        col_encoded_name = f'{col}_target_encoded'
        combined_df[col_encoded_name] = np.nan # 初始化为NaN，后续填充
        
        # 强制转换为字符串类型，以防万一
        combined_df[col] = combined_df[col].astype(str)

        # 对训练集部分进行交叉验证目标编码
        train_indices = combined_df[combined_df['is_train'] == 1].index
        train_temp_df = combined_df.loc[train_indices, :].copy()
        y_train_temp = train_df['price'].copy() # 确保y_train_temp与训练集数据对应

        for fold, (train_idx, val_idx) in enumerate(kf.split(train_temp_df)):
            # 在训练折上计算目标均值 (无平滑)
            mean_target = y_train_temp.iloc[train_idx].groupby(train_temp_df.iloc[train_idx][col]).mean()
            # 将均值映射到验证折上
            train_temp_df.loc[train_temp_df.iloc[val_idx].index, col_encoded_name] = train_temp_df.iloc[val_idx][col].map(mean_target)
        
        # 将处理后的训练集目标编码结果更新回combined_df
        combined_df.loc[train_indices, col_encoded_name] = train_temp_df[col_encoded_name]

        # 对整个combined_df（包括测试集）使用全量训练集的目标均值进行编码 (无平滑)
        global_mean_target = y_train_temp.groupby(train_df[col]).mean()
        
        # 填充combined_df中的目标编码列（测试集和训练集中的NaN，即新类别或未处理部分）
        combined_df[col_encoded_name] = combined_df[col].map(global_mean_target)
        combined_df[col_encoded_name].fillna(global_overall_mean, inplace=True) # 填充新类别或缺失值，使用全局目标均值

        print(f"已对特征 '{col}' 进行交叉验证目标编码 (无平滑)。")

    # 8. regionCode 频率编码
    if 'regionCode' in combined_df.columns:
        freq_encoding_region = combined_df.groupby('regionCode').size() / len(combined_df)
        combined_df['regionCode_freq'] = combined_df['regionCode'].map(freq_encoding_region)
        print("已添加特征 'regionCode_freq'.")
    else:
        print("警告: 无法添加 'regionCode_freq'，因为 'regionCode' 列不存在。")

    # 9. 新的交互特征：regYear * power
    if 'regYear' in combined_df.columns and 'power' in combined_df.columns:
        combined_df['regYear_power_inter'] = combined_df['regYear'] * combined_df['power']
        print("已添加特征 'regYear_power_inter'.")
    else:
        print("警告: 无法添加 'regYear_power_inter'，因为 'regYear' 或 'power' 列不存在。")


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
    # 对于非数值的列，尝试转换为数值类型，如果失败则删除
    cols_to_drop = []
    for col in X.columns:
        if X[col].dtype == 'object': 
            try:
                # 原始的'model'和'brand'列以及其他由11.0处理的类别特征应该在此处被转换为数值类型
                X[col] = pd.to_numeric(X[col], errors='raise') # 严格模式，如果无法转换会报错
                X_test[col] = pd.to_numeric(X_test[col], errors='raise')
            except ValueError:
                print(f"警告: 列 '{col}' 无法转换为数值类型，将被删除。")
                cols_to_drop.append(col)
        # 将所有boolean列转换为int
        elif X[col].dtype == 'bool':
            X[col] = X[col].astype(int)
            X_test[col] = X_test[col].astype(int)
    if cols_to_drop:
        X = X.drop(columns=cols_to_drop)
        X_test = X_test.drop(columns=cols_to_drop)

    # 填充缺失值 (优化为数值型中位数，非数值型众数填充)
    print("填充缺失值...")
    for col in X.columns:
        if X[col].isnull().any():
            if pd.api.types.is_numeric_dtype(X[col]):
                median_val = X[col].median()
                X[col] = X[col].fillna(median_val)
                X_test[col] = X_test[col].fillna(median_val)
            else: 
                # 对于非数值型，使用众数填充，并确保众数存在
                mode_val = X[col].mode()
                if not mode_val.empty:
                    mode_val = mode_val[0]
                    X[col] = X[col].fillna(mode_val)
                    X_test[col] = X_test[col].fillna(mode_val)
                else:
                    print(f"警告: 列 '{col}' 没有众数，无法填充缺失值。")

    # 确保X和X_test的列顺序一致
    missing_in_test = set(X.columns) - set(X.columns) 
    for col in missing_in_test:
        X_test[col] = 0 
    missing_in_train = set(X.columns) - set(X.columns) 
    for col in missing_in_train:
        X[col] = 0 
    X_test = X_test[X.columns] # 确保列顺序一致

    # 最终特征列表：移除所有目标编码特征，保留原始特征和其他增强特征
    final_features = [col for col in X.columns if col not in ['price', 'SaleID']]
    # 确保目标编码特征在最终特征列表中
    final_features.extend([f'{col}_target_encoded' for col in target_encode_cols])
    # 确保频率编码特征在最终特征列表中
    if 'regionCode_freq' in combined_df.columns: # 使用combined_df，因为freq编码在其中生成
        final_features.append('regionCode_freq')
    # 确保新的交互特征在最终特征列表中
    if 'regYear_power_inter' in combined_df.columns: # 使用combined_df
        final_features.append('regYear_power_inter')

    # 确保特征唯一且存在于数据中
    final_features = list(dict.fromkeys([f for f in final_features if f in X.columns]))

    # Ensure X and X_test only contain final_features
    X = X[final_features]
    X_test = X_test[final_features]

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

    # 可视化预测结果
    print("生成预测价格 vs 实际价格图...")
    plt.figure(figsize=(10, 6))
    sns.regplot(x=y_val, y=val_pred, scatter_kws={'alpha':0.3})
    plt.title('验证集：预测价格 vs 实际价格')
    plt.xlabel('实际价格')
    plt.ylabel('预测价格')
    plt.savefig('11.14_xgb_feature_optimize_v13_price_pred_vs_true.png')
    plt.close()
    print("预测价格 vs 实际价格图已保存为 11.14_xgb_feature_optimize_v13_price_pred_vs_true.png")

    # 保存预测结果
    submission = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred})
    submission.to_csv('11.14_xgb_feature_optimize_v13_predict.csv', index=False)
    print(f"预测结果已保存为 11.14_xgb_feature_optimize_v13_predict.csv")

    # 特征重要性分析与可视化
    print("\n========== 特征重要性分析 ==========")
    feature_importance_df = pd.DataFrame({'feature': X.columns, 'importance': xgb.feature_importances_})
    feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)

    plt.figure(figsize=(12, 8))
    sns.barplot(x='importance', y='feature', data=feature_importance_df.head(30))
    plt.title('特征重要性 Top 30')
    plt.xlabel('重要性')
    plt.ylabel('特征')
    plt.savefig('11.14_xgb_feature_optimize_v13_importance_top30.png')
    plt.close()
    print("特征重要性Top30图已保存为 11.14_xgb_feature_optimize_v13_importance_top30.png")

    print("XGBoost特征工程优化v13 完成。")

def main():
    set_matplotlib_style()
    train_df, test_df = load_data()
    X, y, X_test, test_saleid = preprocess_and_feature_engineer(train_df, test_df)
    train_and_evaluate_model(X, y, X_test, test_saleid)

if __name__ == '__main__':
    main() 