import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import shap
import matplotlib.pyplot as plt
import joblib
import matplotlib
import time
import os

"""
:function: 加载模型、评估并进行SHAP特征重要性分析
:param 无
:return: 无
"""
def main():
    # ========== 解决matplotlib中文乱码 ==========
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

    # 1. 数据读取与基础特征工程 (复制自 5.2_xgb_optimize_train.py，确保特征一致性)
    print("\n========== 重新执行数据读取与基础特征工程以确保特征一致性 ==========")
    # 检查原始数据文件是否存在
    if not os.path.exists('used_car_train_20200313.csv') or not os.path.exists('used_car_testB_20200421.csv'):
        print("错误: 原始数据文件 'used_car_train_20200313.csv' 或 'used_car_testB_20200421.csv' 未找到。请确保它们与脚本在同一目录下。")
        return

    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    train['is_test'] = 0
    test['is_test'] = 1
    data = pd.concat([train, test], ignore_index=True)

    drop_always_cols = ['seller', 'offerType']
    for col in drop_always_cols:
        if col in data.columns:
            data = data.drop(col, axis=1)

    # ================== 特征工程（全面梳理与优化） - 复制自 5.2_xgb_optimize_train.py ==================
    print("\n========== 开始时间特征处理 ==========")
    data['regDate_dt'] = pd.to_datetime(data['regDate'], format='%Y%m%d', errors='coerce')
    data['creatDate_dt'] = pd.to_datetime(data['creatDate'], format='%Y%m%d', errors='coerce')
    data['car_age_days'] = (data['creatDate_dt'] - data['regDate_dt']).dt.days
    data['car_age'] = data['car_age_days'] / 365.25
    median_car_age = data['car_age'].median()
    data['car_age'] = data['car_age'].apply(lambda x: median_car_age if pd.isnull(x) or x < 0 else x)
    data['regYear'] = data['regDate_dt'].dt.year
    data['regMonth'] = data['regDate_dt'].dt.month
    data['regDay'] = data['regDate_dt'].dt.day
    data['creatYear'] = data['creatDate_dt'].dt.year
    data['creatMonth'] = data['creatDate_dt'].dt.month
    data['creatDay'] = data['creatDate_dt'].dt.day
    data['is_new_car'] = (data['car_age'] < 1).astype(int)
    current_year = pd.Timestamp.now().year
    data['regYear_from_now'] = current_year - data['regYear']
    data['creatYear_from_now'] = current_year - data['creatYear']
    data['regSeason'] = data['regMonth'].apply(lambda x: (x%12 + 3)//3)
    data['creatSeason'] = data['creatMonth'].apply(lambda x: (x%12 + 3)//3)
    data['km_per_year'] = data['kilometer'] / (data['car_age'] + 0.1)
    data['age_segment'] = pd.cut(data['car_age'], bins=[-0.01, 1, 3, 5, 10, 100], labels=['0-1年', '1-3年', '3-5年', '5-10年', '10年以上'])
    data['regYear_bin'] = pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False)
    data['km_bin'] = pd.cut(data['kilometer'], bins=[0,5,10,12,14,15], labels=False)
    data['power_bin'] = pd.cut(data['power'], bins=[0,50,100,150,200,300,600], labels=False)
    data['brand_km_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['kilometer'], bins=[0,5,10,12,14,15], labels=False).astype(str)
    data['brand_power_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['power'], bins=[0,50,100,150,200,300,600], labels=False).astype(str)
    data['brand_age_segment'] = data['brand'].astype(str) + '_' + data['age_segment'].astype(str)
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)
    print("时间特征处理完成。")

    print("\n========== 开始缺失值处理与缺失标记 ==========")
    categorical_cols_for_new_category = ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage']
    numerical_cols_for_group_median = ['power', 'kilometer']
    numerical_cols_for_global_median = [f'v_{i}' for i in range(15)] + ['regMonth', 'creatMonth', 'regSeason', 'creatSeason']
    all_missing_cols_for_indicators = list(set(categorical_cols_for_new_category + numerical_cols_for_group_median + numerical_cols_for_global_median))

    for col in all_missing_cols_for_indicators:
        data[f'{col}_missing'] = data[col].isnull().astype(int)
        if data[col].isnull().sum() > 0:
            if col in categorical_cols_for_new_category:
                data[col] = data[col].fillna('Unknown')
            elif col in numerical_cols_for_group_median:
                data[col] = data.groupby('brand')[col].transform(lambda x: x.fillna(x.median()))
                if data[col].isnull().sum() > 0:
                    data[col] = data[col].fillna(data[col].median())
            elif col in numerical_cols_for_global_median:
                data[col] = data[col].fillna(data[col].median())
    print("缺失值处理与缺失标记完成。")

    print("\n========== 开始强制类型转换 (Int32) ==========")
    cols_to_int32 = ['regYear', 'regMonth', 'regSeason', 'creatYear', 'creatMonth', 'creatSeason']
    for col in cols_to_int32:
        if col in data.columns:
            if data[col].isnull().any():
                data[col] = data[col].fillna(data[col].median())
            data[col] = data[col].astype('int32')
    print("强制类型转换完成。")

    print("\n========== 开始异常值处理 ==========")
    data = data[(data['is_test'] == 1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['is_test'] == 1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['is_test'] == 1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]
    for col in ['power', 'kilometer', 'v_0']:
        Q1 = data[col].quantile(0.05)
        Q3 = data[col].quantile(0.95)
        IQR = Q3 - Q1
        data[f'{col}_outlier'] = ((data[col] < (Q1 - 1.5 * IQR)) | (data[col] > (Q3 + 1.5 * IQR))).astype(int)
        data[col] = data[col].clip(Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)
    print("异常值处理完成。")

    print("\n========== 开始加载统计特征并生成 ==========")
    #train_idx_data = data[data['is_test'] == 0].copy() # Get training data for statistics
    try:
        brand_stats = joblib.load('train_brand_stats.joblib')
        data = data.merge(brand_stats, on='brand', how='left')
        # Ensure brand_price_ratio is calculated using the mean from the training data only
        train_brand_price_mean_overall = brand_stats['brand_price_mean'].mean()
        data['brand_price_ratio'] = data['brand_price_mean'] / train_brand_price_mean_overall

        brand_age_km_stats = joblib.load('train_brand_age_km_stats.joblib')
        data = data.merge(brand_age_km_stats, on='brand', how='left')
        # Fill NaNs using median from the training data portion
        data['brand_mean_car_age'] = data['brand_mean_car_age'].fillna(data[data['is_test'] == 0]['brand_mean_car_age'].median())
        data['brand_mean_kilometer'] = data['brand_mean_kilometer'].fillna(data[data['is_test'] == 0]['brand_mean_kilometer'].median())
        data['car_age_ratio_to_brand_mean_age'] = data['car_age'] / (data['brand_mean_car_age'] + 1e-6)
        data['kilometer_ratio_to_brand_mean_km'] = data['kilometer'] / (data['brand_mean_kilometer'] + 1e-6)

        brand_v3_stats = joblib.load('train_brand_v3_stats.joblib')
        data = data.merge(brand_v3_stats, on='brand', how='left')
        for col in ['brand_v3_mean', 'brand_v3_median', 'brand_v3_std']:
            global_median_train = data[data['is_test'] == 0][col].median()
            data[col] = data[col].fillna(global_median_train)

        region_brand_stats = joblib.load('train_region_brand_stats.joblib')
        data = data.merge(region_brand_stats, on=['regionCode', 'brand'], how='left')
        for col_suffix in ['mean', 'std']:
            col_name = f'region_brand_price_{col_suffix}'
            if col_name in data.columns:
                global_median_train = data[data['is_test'] == 0][col_name].median()
                data[col_name] = data[col_name].fillna(global_median_train)
        print("统计特征加载与生成完成。")
    except FileNotFoundError as e:
        print(f"错误: 统计特征文件未找到，请确保已运行 5.2_xgb_optimize_train.py 并生成了这些文件。{e}")
        return

    print("\n========== 开始特征交互生成 ==========")
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)
    data['km_age'] = data['kilometer'] * data['car_age']
    data['power_age'] = data['power'] * data['car_age']
    data['power_log'] = np.log1p(data['power'])
    data['kilometer_log'] = np.log1p(data['kilometer'])
    data['car_age_log'] = np.log1p(data['car_age'])
    data['brand_model_age'] = data['brand'].astype(str) + '_' + data['model'].astype(str) + '_' + data['age_segment'].astype(str)
    data['powertrain_type'] = data['fuelType'].astype(str) + '_' + data['gearbox'].astype(str) + '_' + data['power_bin'].astype(str)
    data['v3_car_age_interaction'] = data['v_3'] * data['car_age']
    data['v12_power_log_interaction'] = data['v_12'] * data['power_log']
    data['power_10bins'] = pd.qcut(data['power'], q=10, labels=False, duplicates='drop')
    print("特征交互生成完成。")

    print("\n========== 开始文本特征与业务规则特征生成 ==========")
    data['has_sport'] = data['name'].astype(str).str.contains('sport', case=False, na=False).astype(int)
    data['has_premium'] = data['name'].astype(str).str.contains('luxury|premium', regex=True, case=False, na=False).astype(int)
    data['is_high_mileage'] = (data['km_per_year'] > 2).astype(int)
    print("文本特征与业务规则特征生成完成。")

    print("\n========== 开始高基数类别特征频数编码 (加载编码器) ==========")
    high_card_cols = ['model', 'brand_model', 'brand_power_bin', 'brand_age_segment', 'brand_model_age', 'powertrain_type', 'regionCode']
    for col in high_card_cols:
        if col in data.columns:
            try:
                freq_encoding = joblib.load(f'{col}_freq_encoding_map.joblib')
                data[f'{col}_freq'] = data[col].map(freq_encoding).fillna(0)
            except FileNotFoundError:
                print(f"警告: 频数编码文件 '{col}_freq_encoding_map.joblib' 未找到，该特征的频数编码将填充0。")
                data[f'{col}_freq'] = 0
    print("高基数类别特征频数编码完成。")

    print("\n========== 开始其余类别特征LabelEncoder编码 (加载编码器) ==========")
    categorical_features = [
        'brand', 'bodyType', 'fuelType', 'gearbox',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage'
    ]
    for col in categorical_features:
        if col in data.columns:
            try:
                le = joblib.load(f'{col}_label_encoder.joblib')
                data[col] = data[col].astype(str).apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
            except FileNotFoundError:
                print(f"警告: LabelEncoder 文件 '{col}_label_encoder.joblib' 未找到，该特征将使用pd.factorize进行编码。")
                data[col] = pd.factorize(data[col])[0]
    print("其余类别特征LabelEncoder编码完成。")

    print("\n========== 开始匿名特征PCA降维 (加载PCA模型) ==========")
    v_cols = [f'v_{i}' for i in range(15)]
    v_cols_present = [col for col in v_cols if col in data.columns]
    try:
        if v_cols_present:
            pca = joblib.load('pca_model.joblib')
            v_pca = pca.transform(data[v_cols_present])
            for i in range(v_pca.shape[1]):
                data[f'v_pca_{i}'] = v_pca[:, i]
        else:
            print("警告: 原始v_cols特征不存在，跳过PCA降维。")
    except FileNotFoundError:
        print(f"警告: PCA模型文件 'pca_model.joblib' 未找到，跳过PCA降维。")
    print("匿名特征PCA降维完成。")

    print("\n========== 开始数值归一化 (加载Scaler模型) ==========")
    num_cols = ['power', 'kilometer', 'car_age', 'km_per_year', 'power_log', 'kilometer_log', 'car_age_log', 'km_age', 'power_age'] + \
               [f'v_pca_{i}' for i in range(10)] + \
               ['brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio', \
                'region_brand_price_mean', 'region_brand_price_std',
                'car_age_ratio_to_brand_mean_age', 'kilometer_ratio_to_brand_mean_km',
                'v3_car_age_interaction', 'v12_power_log_interaction',
                'brand_v3_mean', 'brand_v3_median', 'brand_v3_std']
    num_cols_present = [col for col in num_cols if col in data.columns]
    try:
        if num_cols_present:
            scaler = joblib.load('scaler_model.joblib')
            data[num_cols_present] = scaler.transform(data[num_cols_present])
        else:
            print("警告: 无数值特征可归一化。")
    except FileNotFoundError:
        print(f"警告: Scaler模型文件 'scaler_model.joblib' 未找到，跳过数值归一化。")
    print("数值归一化完成。")

    # ========== 构建最终特征列表并划分数据集 ==========
    print("\n========== 构建最终特征列表并划分数据集 ==========")
    features = [
        'model_freq', 'brand_model_freq', 'brand_power_bin_freq', 'brand_age_segment_freq',
        'regionCode_freq',
        'brand', 'bodyType', 'fuelType', 'gearbox',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage',
        'power', 'kilometer', 'car_age', 'km_per_year',
        'power_log', 'kilometer_log', 'car_age_log',
        'km_age', 'power_age',
        'brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio',
        'region_brand_price_mean', 'region_brand_price_std',
        'car_age_ratio_to_brand_mean_age', 'kilometer_ratio_to_brand_mean_km',
        'v_0', 'v_3', 'v_10', 'v_12',
        *[f'v_pca_{i}' for i in range(10)],
        'v3_car_age_interaction', 'v12_power_log_interaction',
        *[f'{col}_missing' for col in all_missing_cols_for_indicators if f'{col}_missing' in data.columns],
        *[f'{col}_outlier' for col in ['power', 'kilometer', 'v_0'] if f'{col}_outlier' in data.columns],
        'brand_model_age_freq', 'powertrain_type_freq',
        'has_sport', 'has_premium',
        'is_high_mileage',
        'power_10bins',
        'brand_v3_mean', 'brand_v3_median', 'brand_v3_std',
        'regYear', 'regMonth', 'creatYear', 'creatMonth',
        'regYear_from_now', 'creatYear_from_now',
        'regSeason', 'creatSeason'
    ]
    features = list(dict.fromkeys([f for f in features if f in data.columns]))

    train_df = data[data['is_test'] == 0].copy()
    test_df = data[data['is_test'] == 1].copy()

    X = train_df[features]
    y = train_df['price']

    duplicated_cols = X.columns[X.columns.duplicated()].tolist()
    if len(duplicated_cols) > 0:
        print(f'警告: 存在重复特征名，已移除: {duplicated_cols}')
        X = X.loc[:, ~X.columns.duplicated()]
        test_df = test_df.loc[:, [f for f in features if f in test_df.columns]]
        test_df = test_df.loc[:, X.columns]

    X_test_final = test_df.loc[:, X.columns]

    print(f"最终特征数量: {X.shape[1]}")
    print("数据集划分完成。")

    # ========== 特征选择强化：删除高相关性特征 (需要确保与训练时一致) ==========
    print("\n========== 重新执行特征选择强化：删除高相关性特征 ==========")
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop_corr = [column for column in upper.columns if any(upper[column] > 0.95)]
    features_to_retain_for_corr_pruning = ['regYear', 'v_6', 'brand_price_ratio'] + \
                                            [f for f in features if f.startswith('v_') or f.startswith('v_pca_') or f.endswith('_interaction')]
    features_to_retain_for_corr_pruning = list(set(features_to_retain_for_corr_pruning))

    to_drop_corr = [f for f in to_drop_corr if f not in features_to_retain_for_corr_pruning]

    if len(to_drop_corr) > 0:
        X = X.drop(columns=to_drop_corr, errors='ignore')
        X_test_final = X_test_final.drop(columns=to_drop_corr, errors='ignore')
        print(f'高相关性特征已删除(阈值 > 0.95)，并确保保留特定特征。')
    else:
        print('未发现高相关性特征 (阈值 > 0.95)。')
    print(f"特征选择完成，最终用于分析的特征数量: {X.shape[1]}")

    # 2. 划分训练集和验证集 (与原始训练时保持一致)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42)
    print("训练集和验证集划分完成。")

    # 1. 打印模型调优后的超参
    print("\n========== 加载模型并打印超参数 ==========")
    try:
        best_xgb_model = joblib.load('optimized_xgb_model.joblib')
        print("最佳模型已成功加载。")
        print("模型调优后的超参数:")
        print(f"  learning_rate: {best_xgb_model.learning_rate}")
        print(f"  n_estimators: {best_xgb_model.n_estimators}")
        print(f"  max_depth: {best_xgb_model.max_depth}")
        print(f"  subsample: {best_xgb_model.subsample}")
        print(f"  colsample_bytree: {best_xgb_model.colsample_bytree}")
        print(f"  random_state: {best_xgb_model.random_state}")
        print(f"  n_jobs: {best_xgb_model.n_jobs}")
    except FileNotFoundError:
        print("错误: optimized_xgb_model.joblib 文件未找到。请确保已运行 5.2_xgb_optimize_train.py 并保存了模型。")
        return

    # 2. 打印评估模型（MAE、RMSE）
    print("\n========== 评估模型 (MAE、RMSE) ==========")
    y_val_pred_log = best_xgb_model.predict(X_val)
    y_val_pred = np.expm1(y_val_pred_log)

    mae = mean_absolute_error(y_val, y_val_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
    print(f'验证集 MAE: {mae:.4f}')
    print(f'验证集 RMSE: {rmse:.4f}')

    # 3. 完成SHAP特征重要性分析
    print("\n========== 开始SHAP特征重要性分析 ==========")
    start_time_shap = time.time()
    explainer = shap.TreeExplainer(best_xgb_model)
    shap_values = explainer.shap_values(X_train)
    end_time_shap = time.time()
    print(f"SHAP值计算完成，耗时: {end_time_shap - start_time_shap:.2f}秒")

    print("\n========== 绘制SHAP特征重要性图 (bar plot) ==========")
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, X_train, plot_type="bar", show=False)
    plt.title('SHAP Feature Importance (Optimized Model)')
    plt.tight_layout()
    plt.savefig('shap_feature_importance_analysis.png', dpi=150)
    plt.close()
    print('SHAP特征重要性图已保存为 shap_feature_importance_analysis.png')

    print("\n========== 绘制SHAP Summary Plot (dot plot) ==========")
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, X_train, show=False)
    plt.title('SHAP Summary Plot (Optimized Model)')
    plt.tight_layout()
    plt.savefig('shap_summary_plot_analysis.png', dpi=150)
    plt.close()
    print('SHAP Summary Plot已保存为 shap_summary_plot_analysis.png')

    print("\n分析程序执行完毕。")

if __name__ == "__main__":
    main()
