import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, make_scorer
import shap
import matplotlib.pyplot as plt
import joblib
import matplotlib
import time

"""
:function: XGBoost模型优化程序：结合K折交叉验证和超参数调优，并进行SHAP特征重要性分析
:param 无
:return: 无
"""
def main():
    # ========== 解决matplotlib中文乱码 ==========
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

    # 1. 数据读取与基础特征工程
    print("\n========== 开始数据读取与基础特征工程 ==========")
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    # 添加标识列区分训练集和测试集
    train['is_test'] = 0
    test['is_test'] = 1
    data = pd.concat([train, test], ignore_index=True)

    # 根据用户要求，总是删除 'seller' 和 'offerType' 特征
    drop_always_cols = ['seller', 'offerType']
    for col in drop_always_cols:
        if col in data.columns:
            print(f"根据用户要求，已删除特征 '{col}'。")
            data = data.drop(col, axis=1)
    # 提前去除常量特征 (此处的逻辑将不再处理 seller 和 offerType)
    print("常量特征处理完成，当前数据 shape:", data.shape)

    # ================== 特征工程（全面梳理与优化） ==================
    print("\n========== 开始时间特征处理 ==========")
    data['regDate_dt'] = pd.to_datetime(data['regDate'], format='%Y%m%d', errors='coerce')
    data['creatDate_dt'] = pd.to_datetime(data['creatDate'], format='%Y%m%d', errors='coerce')
    data['car_age_days'] = (data['creatDate_dt'] - data['regDate_dt']).dt.days
    data['car_age'] = data['car_age_days'] / 365.25
    median_car_age = data['car_age'].median()
    data['car_age'] = data['car_age'].apply(lambda x: median_car_age if pd.isnull(x) or x < 0 else x)
    data['regYear'] = data['regDate_dt'].dt.year
    data['regMonth'] = data['regDate_dt'].dt.month
    # 移除立即填充 regMonth 的缺失值，统一在 all_missing_cols 中处理
    data['regDay'] = data['regDate_dt'].dt.day
    data['creatYear'] = data['creatDate_dt'].dt.year
    data['creatMonth'] = data['creatDate_dt'].dt.month
    # 移除立即填充 creatMonth 的缺失值，统一在 all_missing_cols 中处理
    data['creatDay'] = data['creatDate_dt'].dt.day
    data['is_new_car'] = (data['car_age'] < 1).astype(int)
    current_year = pd.Timestamp.now().year
    data['regYear_from_now'] = current_year - data['regYear']
    data['creatYear_from_now'] = current_year - data['creatYear']
    data['regSeason'] = data['regMonth'].apply(lambda x: (x%12 + 3)//3)
    # 移除立即填充 regSeason 的缺失值，统一在 all_missing_cols 中处理
    data['creatSeason'] = data['creatMonth'].apply(lambda x: (x%12 + 3)//3)
    # 移除立即填充 creatSeason 的缺失值，统一在 all_missing_cols 中处理
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

    # 定义不同缺失值处理策略的列
    categorical_cols_for_new_category = ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage']
    numerical_cols_for_group_median = ['power', 'kilometer'] # 这些特征可以从按品牌分组填充中位数中受益
    numerical_cols_for_global_median = [f'v_{i}' for i in range(15)] + ['regMonth', 'creatMonth', 'regSeason', 'creatSeason']

    # 综合所有可能包含缺失值的列，用于创建缺失指示符和后续填充
    all_missing_cols_for_indicators = list(set(categorical_cols_for_new_category + numerical_cols_for_group_median + numerical_cols_for_global_median))

    for col in all_missing_cols_for_indicators:
        # 首先创建缺失指示符特征
        data[f'{col}_missing'] = data[col].isnull().astype(int)

        if data[col].isnull().sum() > 0:
            print(f"  正在处理特征 '{col}' 的缺失值。原始缺失数量: {data[col].isnull().sum()}")
            if col in categorical_cols_for_new_category:
                # 类别特征填充新类别
                data[col] = data[col].fillna('Unknown')
            elif col in numerical_cols_for_group_median:
                # 数值特征：按品牌分组中位数填充，如果品牌组为空则回退到全局中位数
                data[col] = data.groupby('brand')[col].transform(lambda x: x.fillna(x.median()))
                # 处理分组填充后可能仍存在的 NaN (例如，测试集中出现训练集中未见的品牌，或整个品牌组该列都为 NaN)
                if data[col].isnull().sum() > 0:
                    data[col] = data[col].fillna(data[col].median())
            elif col in numerical_cols_for_global_median:
                # 数值特征：全局中位数填充
                data[col] = data[col].fillna(data[col].median())
            print(f"  特征 '{col}' 缺失值处理后，剩余缺失数量: {data[col].isnull().sum()}")
    print("缺失值处理与缺失标记完成。")

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

    print("\n========== 开始统计特征生成 ==========")
    train_idx = data[data['is_test'] == 0].index
    brand_stats = data.iloc[train_idx].groupby('brand').agg(
        brand_price_mean=('price', 'mean'),
        brand_price_median=('price', 'median'),
        brand_price_std=('price', 'std'),
        brand_price_count=('price', 'count')
    ).reset_index()
    data = data.merge(brand_stats, on='brand', how='left')
    data['brand_price_ratio'] = data['brand_price_mean'] / data['brand_price_mean'].mean()
    joblib.dump(brand_stats, 'train_brand_stats.joblib')

    brand_age_km_stats = data.iloc[train_idx].groupby('brand').agg(
        brand_mean_car_age=('car_age', 'mean'),
        brand_mean_kilometer=('kilometer', 'mean')
    ).reset_index()
    data = data.merge(brand_age_km_stats, on='brand', how='left')
    data['brand_mean_car_age'] = data['brand_mean_car_age'].fillna(data['brand_mean_car_age'].mean())
    data['brand_mean_kilometer'] = data['brand_mean_kilometer'].fillna(data['brand_mean_kilometer'].mean())
    data['car_age_ratio_to_brand_mean_age'] = data['car_age'] / (data['brand_mean_car_age'] + 1e-6)
    data['kilometer_ratio_to_brand_mean_km'] = data['kilometer'] / (data['brand_mean_kilometer'] + 1e-6)
    joblib.dump(brand_age_km_stats, 'train_brand_age_km_stats.joblib')

    brand_v3_stats = data.iloc[train_idx].groupby('brand').agg(
        brand_v3_mean=('v_3', 'mean'),
        brand_v3_median=('v_3', 'median'),
        brand_v3_std=('v_3', 'std')
    ).reset_index()
    data = data.merge(brand_v3_stats, on='brand', how='left')
    for col in ['brand_v3_mean', 'brand_v3_median', 'brand_v3_std']:
        global_median = data.iloc[train_idx][col].median()
        data[col] = data[col].fillna(global_median)
    joblib.dump(brand_v3_stats, 'train_brand_v3_stats.joblib')

    region_brand_stats = data.iloc[train_idx].groupby(['regionCode', 'brand'])['price'].agg(region_brand_price_mean='mean', region_brand_price_std='std').reset_index()
    data = data.merge(region_brand_stats, on=['regionCode', 'brand'], how='left')
    for col_suffix in ['mean', 'std']:
        col_name = f'region_brand_price_{col_suffix}'
        if col_name in data.columns:
            global_median = data.iloc[train_idx][col_name].median()
            data[col_name] = data[col_name].fillna(global_median)
    joblib.dump(region_brand_stats, 'train_region_brand_stats.joblib')
    print("统计特征生成完成。")

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

    print("\n========== 开始高基数类别特征频数编码 ==========")
    high_card_cols = ['model', 'brand_model', 'brand_power_bin', 'brand_age_segment', 'brand_model_age', 'powertrain_type', 'regionCode']
    for col in high_card_cols:
        if col in data.columns:
            freq_encoding = data.groupby(col).size() / len(data)
            data[f'{col}_freq'] = data[col].map(freq_encoding)
            joblib.dump(freq_encoding, f'{col}_freq_encoding_map.joblib')
    print("高基数类别特征频数编码完成。")

    print("\n========== 开始其余类别特征LabelEncoder编码 ==========")
    categorical_features = [
        'brand', 'bodyType', 'fuelType', 'gearbox', # 'regionCode' 已移至高基数类别特征
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage'
    ]
    for col in categorical_features:
        if col in data.columns:
            le = LabelEncoder()
            data[col] = le.fit_transform(data[col].astype(str))
            joblib.dump(le, f'{col}_label_encoder.joblib')
    print("其余类别特征LabelEncoder编码完成。")

    print("\n========== 开始匿名特征PCA降维 ==========")
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]
    joblib.dump(pca, 'pca_model.joblib')
    print("匿名特征PCA降维完成。")

    print("\n========== 开始数值归一化 ==========")
    num_cols = ['power', 'kilometer', 'car_age', 'km_per_year', 'power_log', 'kilometer_log', 'car_age_log', 'km_age', 'power_age'] + \
               [f'v_pca_{i}' for i in range(v_pca.shape[1])] + \
               ['brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio', \
                'region_brand_price_mean', 'region_brand_price_std', 
                'car_age_ratio_to_brand_mean_age', 'kilometer_ratio_to_brand_mean_km',
                'v3_car_age_interaction', 'v12_power_log_interaction',
                'brand_v3_mean', 'brand_v3_median', 'brand_v3_std']
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])
    joblib.dump(scaler, 'scaler_model.joblib')
    print("数值归一化完成。")

    print("\n========== 构建最终特征列表并划分数据集 ==========")
    features = [
        'model_freq', 'brand_model_freq', 'brand_power_bin_freq', 'brand_age_segment_freq',
        'regionCode_freq', # regionCode 改为频数编码后的特征
        'brand', 'bodyType', 'fuelType', 'gearbox',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage',
        'power', 'kilometer', 'car_age', 'km_per_year',
        'power_log', 'kilometer_log', 'car_age_log',
        'km_age', 'power_age',
        'brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio',
        'region_brand_price_mean', 'region_brand_price_std',
        'car_age_ratio_to_brand_mean_age', 'kilometer_ratio_to_brand_mean_km',
        *v_cols,
        *[f'v_pca_{i}' for i in range(v_pca.shape[1])],
        *[f'{col}_missing' for col in all_missing_cols_for_indicators if f'{col}_missing' in data.columns],
        *[f'{col}_outlier' for col in ['power', 'kilometer', 'v_0'] if f'{col}_outlier' in data.columns],
        'brand_model_age_freq', 'powertrain_type_freq',
        'has_sport', 'has_premium',
        'is_high_mileage',
        'power_10bins',
        'v3_car_age_interaction', 'v12_power_log_interaction',
        'brand_v3_mean', 'brand_v3_median', 'brand_v3_std',
        'regYear', 'regMonth', 'creatYear', 'creatMonth',
        # 'regDay', 'creatDay', # 用户要求删除
        'regYear_from_now', 'creatYear_from_now',
        'regSeason', 'creatSeason'
    ]
    features = list(dict.fromkeys([f for f in features if f in data.columns]))

    train_df = data[data['is_test'] == 0].copy()
    test_df = data[data['is_test'] == 1].copy()
    
    X = train_df[features]
    y = train_df['price']
    X_test = test_df[features]
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else None

    for col in X.columns:
        if X[col].dtype == 'object':
            raise TypeError(f"特征 '{col}' 仍然是 'object' 类型，XGBoost不支持。请检查特征工程步骤。")
    for col in X_test.columns:
        if X_test[col].dtype == 'object':
            raise TypeError(f"测试集特征 '{col}' 仍然是 'object' 类型，XGBoost不支持。请检查特征工程步骤。")

    duplicated_cols = X.columns[X.columns.duplicated()].tolist()
    if len(duplicated_cols) > 0:
        print('存在重复特征名:', duplicated_cols)
        X = X.loc[:, ~X.columns.duplicated()]
        X_test = X_test.loc[:, X.columns]
    print(f"最终特征数量: {X.shape[1]}")
    print("数据集划分完成。")

    # ========== 特征选择强化：删除高相关性特征 ==========
    print("\n========== 开始特征选择强化：删除高相关性特征 ==========")
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop_corr = [column for column in upper.columns if any(upper[column] > 0.95)]
    v_cols = [f'v_{i}' for i in range(15)] # 重新定义 v_cols
    features_to_retain = ['regYear', 'v_6', 'brand_price_ratio'] + v_cols # 将所有 v_cols 添加到保留列表
    to_drop_corr = [f for f in to_drop_corr if f not in features_to_retain]

    if len(to_drop_corr) > 0:
        print(f'发现并即将删除高相关性特征: {to_drop_corr}')
        X = X.drop(columns=to_drop_corr, errors='ignore')
        X_test = X_test.drop(columns=to_drop_corr, errors='ignore')
        print('高相关性特征已删除(阈值 > 0.95)，并确保保留特定特征。')
    else:
        print('未发现高相关性特征 (阈值 > 0.95)。')
    print(f"特征选择完成，最终用于训练的特征数量: {X.shape[1]}")

    # ========== 最终训练特征概览 ==========
    print("\n========== 最终训练特征概览 ==========")
    print(f"总计 {len(X.columns)} 个特征将参与训练。")
    for col in X.columns:
        print(f"\n特征: {col} (数据类型: {X[col].dtype})")
        if X[col].nunique() <= 20: # 对于离散或唯一值较少的特征，打印所有唯一值
            print(f"  唯一值数量: {X[col].nunique()}")
            print(f"  唯一值: {X[col].unique()}")
        else: # 对于连续或唯一值较多的特征，打印描述性统计
            print("  描述性统计:")
            print(X[col].describe())
            

            
    # ========== 超参数调优与K折交叉验证 ==========
    print("\n========== 开始超参数调优与K折交叉验证 ==========")
    start_time_tuning = time.time()
    xgb_model = XGBRegressor(
        max_depth=10, subsample=0.8, colsample_bytree=0.9,
        random_state=42, n_jobs=-1, eval_metric='rmse'
    )

    param_grid = {
        'learning_rate': [0.02, 0.03],
        'n_estimators': [3000, 4000] 
    }

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    mae_scorer = make_scorer(mean_absolute_error, greater_is_better=False)

    grid_search = GridSearchCV(
        estimator=xgb_model,
        param_grid=param_grid,
        scoring=mae_scorer,
        cv=kf,
        verbose=2, 
        n_jobs=-1 
    )

    print(f"开始网格搜索训练，参数组合数量: {len(param_grid['learning_rate']) * len(param_grid['n_estimators'])}，共 {kf.n_splits} 折交叉验证。")
    grid_search.fit(X, np.log1p(y))
    end_time_tuning = time.time()
    print(f"网格搜索训练完成，耗时: {end_time_tuning - start_time_tuning:.2f}秒")

    print("\n========== 超参数调优结果 ==========")
    print(f"最佳MAE (负值): {grid_search.best_score_:.4f}")
    print(f"最佳MAE: {-grid_search.best_score_:.4f}")
    print(f"最佳参数组合: {grid_search.best_params_}")

    best_xgb_model = grid_search.best_estimator_
    joblib.dump(best_xgb_model, 'optimized_xgb_model.joblib')
    print('最佳模型已保存到 optimized_xgb_model.joblib')

    # ========== SHAP特征重要性分析 ========== 
    print("\n========== 开始SHAP特征重要性分析 ==========")
    start_time_shap = time.time()
    explainer = shap.TreeExplainer(best_xgb_model)
    shap_values = explainer.shap_values(X)
    end_time_shap = time.time()
    print(f"SHAP值计算完成，耗时: {end_time_shap - start_time_shap:.2f}秒")

    print("\n========== 绘制SHAP特征重要性图 (bar plot) ==========")
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.title('SHAP Feature Importance (Optimized Model)')
    plt.tight_layout()
    plt.savefig('shap_feature_importance_optimized.png', dpi=150)
    plt.close()
    print('SHAP特征重要性图已保存为 shap_feature_importance_optimized.png')

    print("\n========== 绘制SHAP Summary Plot (dot plot) ==========")
    plt.figure(figsize=(10, 7))
    shap.summary_plot(shap_values, X, show=False)
    plt.title('SHAP Summary Plot (Optimized Model)')
    plt.tight_layout()
    plt.savefig('shap_summary_plot_optimized.png', dpi=150)
    plt.close()
    print('SHAP Summary Plot已保存为 shap_summary_plot_optimized.png')

    print("\n优化程序执行完毕。")
    print("您可以根据'最佳参数组合'和'SHAP特征重要性图'来更新 `4.3 model_xgb_more_feature_optimize_2_save_train_result_1.py`。")
    print("具体来说，更新 `learning_rate` 和 `n_estimators` 为最佳参数。")
    print("并根据SHAP图，考虑移除重要性较低的特征。")

if __name__ == "__main__":
    main() 