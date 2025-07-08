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
:function: XGBoost参数调优+特征工程优化+特征重要性分析
:param 无
:return: 无
"""
def main():
    # ========== 解决matplotlib中文乱码 ==========
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

    # 1. 数据读取与基础特征工程
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    # 添加标识列区分训练集和测试集
    train['is_test'] = 0
    test['is_test'] = 1
    data = pd.concat([train, test], ignore_index=True)

    # ================== 特征工程（全面梳理与优化） ==================
    # 1. 时间特征处理
    data['regDate_dt'] = pd.to_datetime(data['regDate'], format='%Y%m%d', errors='coerce')
    data['creatDate_dt'] = pd.to_datetime(data['creatDate'], format='%Y%m%d', errors='coerce')
    # 车辆使用年限（天/年）
    data['car_age_days'] = (data['creatDate_dt'] - data['regDate_dt']).dt.days
    data['car_age'] = data['car_age_days'] / 365.25
    # 若有负值或缺失，填充为中位数
    median_car_age = data['car_age'].median()
    data['car_age'] = data['car_age'].apply(lambda x: median_car_age if pd.isnull(x) or x < 0 else x)
    # 注册/创建年月日
    data['regYear'] = data['regDate_dt'].dt.year
    data['regMonth'] = data['regDate_dt'].dt.month
    data['regDay'] = data['regDate_dt'].dt.day
    data['creatYear'] = data['creatDate_dt'].dt.year
    data['creatMonth'] = data['creatDate_dt'].dt.month
    data['creatDay'] = data['creatDate_dt'].dt.day
    # 是否为新车
    data['is_new_car'] = (data['car_age'] < 1).astype(int)
    # 相对年份特征
    current_year = pd.Timestamp.now().year
    data['regYear_from_now'] = current_year - data['regYear']
    data['creatYear_from_now'] = current_year - data['creatYear']
    # 季节特征
    data['regSeason'] = data['regMonth'].apply(lambda x: (x%12 + 3)//3)
    data['creatSeason'] = data['creatMonth'].apply(lambda x: (x%12 + 3)//3)
    # 每年行驶的公里数
    data['km_per_year'] = data['kilometer'] / (data['car_age'] + 0.1)
    # 车龄分段
    data['age_segment'] = pd.cut(data['car_age'], bins=[-0.01, 1, 3, 5, 10, 100], labels=['0-1年', '1-3年', '3-5年', '5-10年', '10年以上'])
    # 注册年份分段
    data['regYear_bin'] = pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False)
    # 公里数分段
    data['km_bin'] = pd.cut(data['kilometer'], bins=[0,5,10,12,14,15], labels=False)
    # 功率分段
    data['power_bin'] = pd.cut(data['power'], bins=[0,50,100,150,200,300,600], labels=False)
    # 品牌与公里数分段
    data['brand_km_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['kilometer'], bins=[0,5,10,12,14,15], labels=False).astype(str)
    # 品牌与功率分段
    data['brand_power_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['power'], bins=[0,50,100,150,200,300,600], labels=False).astype(str)
    # 品牌与车龄分段
    data['brand_age_segment'] = data['brand'].astype(str) + '_' + data['age_segment'].astype(str)
    # 品牌与注册年份分段
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)

    # 添加车型代际特征 (需确保 model 列存在且 regYear 已提取)
    # 计算每个model的首次注册年份
    model_first_year_dict = data.groupby('model')['regYear'].min().to_dict()
    data['model_first_year'] = data['model'].map(model_first_year_dict)
    data['model_generation'] = (data['regYear'] - data['model_first_year']) // 5 # 假设每5年更新一代
    data['model_generation'] = data['model_generation'].fillna(0).astype(int) # 填充缺失值
    data['is_first_gen'] = (data['model_generation'] == 0).astype(int) # 添加是否为首年款标志
    # 移除临时的model_first_year列
    data = data.drop('model_first_year', axis=1)

    # ========== 缺失值处理与缺失标记优化 ==========
    # 需要处理的特征列表
    all_missing_cols = ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage',
                        'power', 'kilometer', 'v_0', 'v_1', 'v_2', 'v_3', 'v_4', 'v_5', 'v_6', 'v_7', 'v_8', 'v_9', 'v_10', 'v_11', 'v_12', 'v_13', 'v_14']
    for col in all_missing_cols:
        # 增加缺失标记
        data[f'{col}_missing'] = data[col].isnull().astype(int)
        # 数值型用中位数填充，类别型用众数填充
        if data[col].isnull().sum() > 0:
            if str(data[col].dtype) in ['float64', 'int64', 'float32', 'int32']:
                data[col] = data[col].fillna(data[col].median())
            else:
                data[col] = data[col].fillna(data[col].mode()[0])

    # 3. 异常值处理（仅对训练集）
    data = data[(data['is_test'] == 1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['is_test'] == 1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['is_test'] == 1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]
    # 异常值标记
    for col in ['power', 'kilometer', 'v_0']:
        Q1 = data[col].quantile(0.05)
        Q3 = data[col].quantile(0.95)
        IQR = Q3 - Q1
        data[f'{col}_outlier'] = ((data[col] < (Q1 - 1.5 * IQR)) | (data[col] > (Q3 + 1.5 * IQR))).astype(int)
        data[col] = data[col].clip(Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)

    # 4. 统计特征（品牌均值/中位数/计数/标准差等）
    # 使用is_test字段区分训练集
    train_idx = data[data['is_test'] == 0].index

    brand_stats = data.iloc[train_idx].groupby('brand').agg(
        brand_price_mean=('price', 'mean'),
        brand_price_median=('price', 'median'),
        brand_price_std=('price', 'std'),
        brand_price_count=('price', 'count')
    ).reset_index()
    data = data.merge(brand_stats, on='brand', how='left')
    data['brand_price_ratio'] = data['brand_price_mean'] / data['brand_price_mean'].mean()
    # 保存训练集品牌统计特征
    joblib.dump(brand_stats, 'train_brand_stats.joblib')
    print('训练集品牌统计特征已保存到 train_brand_stats.joblib')

    # 新增不涉及目标变量泄漏的"折旧"相关特征
    brand_age_km_stats = data.iloc[train_idx].groupby('brand').agg(
        brand_mean_car_age=('car_age', 'mean'),
        brand_mean_kilometer=('kilometer', 'mean')
    ).reset_index()
    data = data.merge(brand_age_km_stats, on='brand', how='left')
    # 填充NaN值，这些NaN值可能因为测试集中有训练集中没有的品牌导致
    data['brand_mean_car_age'] = data['brand_mean_car_age'].fillna(data['brand_mean_car_age'].mean())
    data['brand_mean_kilometer'] = data['brand_mean_kilometer'].fillna(data['brand_mean_kilometer'].mean())

    data['car_age_ratio_to_brand_mean_age'] = data['car_age'] / (data['brand_mean_car_age'] + 1e-6)
    data['kilometer_ratio_to_brand_mean_km'] = data['kilometer'] / (data['brand_mean_kilometer'] + 1e-6)
    
    # 保存品牌车龄里程统计特征
    joblib.dump(brand_age_km_stats, 'train_brand_age_km_stats.joblib')
    print('训练集品牌车龄里程统计特征已保存到 train_brand_age_km_stats.joblib')

    # 地区-品牌联合统计（需确保仅在训练集计算）
    region_brand_stats = data.iloc[train_idx].groupby(['regionCode', 'brand'])['price'].agg(region_brand_price_mean='mean', region_brand_price_std='std').reset_index()
    data = data.merge(region_brand_stats, on=['regionCode', 'brand'], how='left')
    # 填充NaN值，这些NaN值可能因为测试集中有训练集中没有的地区-品牌组合导致
    for col_suffix in ['mean', 'std']:
        col_name = f'region_brand_price_{col_suffix}'
        if col_name in data.columns:
            # 使用训练集该列的全局中位数进行填充
            global_median = data.iloc[train_idx][col_name].median()
            data[col_name] = data[col_name].fillna(global_median)
    # 保存地区-品牌统计特征
    joblib.dump(region_brand_stats, 'train_region_brand_stats.joblib')
    print('训练集地区-品牌统计特征已保存到 train_region_brand_stats.joblib')

    # 5. 特征交互
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)
    # 交互特征
    data['km_age'] = data['kilometer'] * data['car_age']
    data['power_age'] = data['power'] * data['car_age']
    data['power_log'] = np.log1p(data['power'])
    data['kilometer_log'] = np.log1p(data['kilometer'])
    data['car_age_log'] = np.log1p(data['car_age'])
    # 三阶交互：品牌+车型+车龄分段
    data['brand_model_age'] = data['brand'].astype(str) + '_' + data['model'].astype(str) + '_' + data['age_segment'].astype(str)
    # 动力系统组合：燃油类型+变速箱+功率分段
    data['powertrain_type'] = data['fuelType'].astype(str) + '_' + data['gearbox'].astype(str) + '_' + data['power_bin'].astype(str)

    # 对连续特征增加分箱版本
    # 使用 qcut 进行等频分箱，防止power值重复导致错误，使用 duplicates='drop'
    data['power_10bins'] = pd.qcut(data['power'], q=10, labels=False, duplicates='drop')

    # ========== 文本特征利用 (从 name 字段提取) ==========
    data['has_sport'] = data['name'].astype(str).str.contains('sport', case=False, na=False).astype(int)
    data['has_premium'] = data['name'].astype(str).str.contains('luxury|premium', regex=True, case=False, na=False).astype(int)

    # ========== 业务规则特征 ==========
    # 年均里程是否过高
    data['is_high_mileage'] = (data['km_per_year'] > 2).astype(int) # 年均2万公里为阈值

    # ========== 高基数类别特征采用频数编码 ==========
    high_card_cols = ['model', 'brand_model', 'brand_power_bin', 'brand_age_segment', 'brand_model_age', 'powertrain_type']
    for col in high_card_cols:
        if col in data.columns:
            freq_encoding = data.groupby(col).size() / len(data)
            data[f'{col}_freq'] = data[col].map(freq_encoding)
            # 保存频数编码映射
            joblib.dump(freq_encoding, f'{col}_freq_encoding_map.joblib')
            print(f'{col}频数编码映射已保存到 {col}_freq_encoding_map.joblib')

    # 其余类别特征用LabelEncoder
    categorical_features = [
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage'
    ]
    for col in categorical_features:
        if col in data.columns:
            le = LabelEncoder() # 在循环内部创建新实例
            data[col] = le.fit_transform(data[col].astype(str))
            # 保存LabelEncoder实例
            joblib.dump(le, f'{col}_label_encoder.joblib')
            print(f'{col}的LabelEncoder已保存到 {col}_label_encoder.joblib')

    # ========== 匿名特征及PCA降维 ==========
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]
    # 保存PCA模型
    joblib.dump(pca, 'pca_model.joblib')
    print('PCA模型已保存到 pca_model.joblib')

    # ========== 数值归一化 ==========
    num_cols = ['power', 'kilometer', 'car_age', 'km_per_year', 'power_log', 'kilometer_log', 'car_age_log', 'km_age', 'power_age'] + \
               [f'v_pca_{i}' for i in range(v_pca.shape[1])] + \
               ['brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio', \
                'region_brand_price_mean', 'region_brand_price_std', 
                'car_age_ratio_to_brand_mean_age', 'kilometer_ratio_to_brand_mean_km']
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])
    # 保存StandardScaler模型
    joblib.dump(scaler, 'scaler_model.joblib')
    print('StandardScaler模型已保存到 scaler_model.joblib')

    # ========== 最终特征列表 ==========
    features = [
        # 高基数特征频数编码
        'model_freq', 'brand_model_freq', 'brand_power_bin_freq', 'brand_age_segment_freq',
        # 其余类别特征 (LabelEncoder编码)
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage',
        # 数值特征 (经过标准化处理)
        'power', 'kilometer', 'car_age', 'km_per_year',
        'power_log', 'kilometer_log', 'car_age_log',
        'km_age', 'power_age',
        'brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio',
        'region_brand_price_mean', 'region_brand_price_std',
        'car_age_ratio_to_brand_mean_age', 'kilometer_ratio_to_brand_mean_km',
        # 匿名特征 (所有v_cols)
        *v_cols, # 原始v_cols保留，因为PCA只取了10个主成分
        # PCA降维特征
        *[f'v_pca_{i}' for i in range(v_pca.shape[1])],
        # 缺失/异常/频率特征 (确保这些列存在)
        *[f'{col}_missing' for col in all_missing_cols if f'{col}_missing' in data.columns],
        *[f'{col}_outlier' for col in ['power', 'kilometer', 'v_0'] if f'{col}_outlier' in data.columns],
        # 新增的交互特征 (频数编码后)
        'brand_model_age_freq', 'powertrain_type_freq',
        # 新增的文本特征 (二值)
        'has_sport', 'has_premium',
        # 新增的业务规则特征 (二值)
        'is_high_mileage',
        # 新增的时间特征深化 (数值)
        'model_generation', 'is_first_gen',
        # 新增的分箱特征 (数值)
        'power_10bins',
        # 原始的年份/月份/日期特征 (未标准化)
        'regYear', 'regMonth', 'creatYear', 'creatMonth',
        'regDay', 'creatDay',
        'regYear_from_now', 'creatYear_from_now',
        'regSeason', 'creatSeason'
    ]
    # 去重，保证特征唯一且存在于数据中
    features = list(dict.fromkeys([f for f in features if f in data.columns]))

    # 11. 训练集/测试集（此时还保留price和SaleID列，便于后续处理）
    train_df = data[data['is_test'] == 0].copy()
    test_df = data[data['is_test'] == 1].copy()
    
    X = train_df[features]
    y = train_df['price'] # y现在是合法的
    X_test = test_df[features]
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else None

    # 确保所有特征列的数据类型是XGBoost支持的数值类型 (之前的 LabelEncoder 已经处理了大部分)
    # 这里进行一次最终检查，确保没有 object 类型遗留
    for col in X.columns:
        if X[col].dtype == 'object':
            raise TypeError(f"特征 '{col}' 仍然是 'object' 类型，XGBoost不支持。请检查特征工程步骤。")
    for col in X_test.columns:
        if X_test[col].dtype == 'object':
            raise TypeError(f"测试集特征 '{col}' 仍然是 'object' 类型，XGBoost不支持。请检查特征工程步骤。")

    # 检查特征名唯一性，若有重复则去重并打印
    duplicated_cols = X.columns[X.columns.duplicated()].tolist()
    if len(duplicated_cols) > 0:
        print('存在重复特征名:', duplicated_cols)
        X = X.loc[:, ~X.columns.duplicated()]
        X_test = X_test.loc[:, X.columns]  # 保证测试集特征顺序和训练集一致

    # # ========== 特征选择强化：删除高相关性特征 ==========
    # # 计算训练集特征相关性矩阵
    # corr_matrix = X.corr().abs()
    # # 选取上三角矩阵
    # upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    # # 找出相关性大于0.95的列
    # to_drop_corr = [column for column in upper.columns if any(upper[column] > 0.95)]
    #
    # if len(to_drop_corr) > 0:
    #     print(f'发现并即将删除高相关性特征: {to_drop_corr}')
    #     X = X.drop(columns=to_drop_corr, errors='ignore')
    #     X_test = X_test.drop(columns=to_drop_corr, errors='ignore')
    #     print('高相关性特征已删除。')
    # else:
    #     print('未发现高相关性特征 (阈值 > 0.95)。')

    # 2. 划分训练集和验证集
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42)

    # 3. XGBoost模型训练
    start_time = time.time() # 记录开始时间
    print(f"XGBoost模型训练开始，开始时间: {time.ctime(start_time)}\n") # 打印开始时间
    xgb = XGBRegressor(
        max_depth=10, learning_rate=0.02, n_estimators=5000, subsample=0.8, colsample_bytree=0.9,
        random_state=42, n_jobs=-1, eval_metric='rmse'
    )
    # 兼容不同XGBoost版本的early_stopping
    xgb.fit(X_train, np.log1p(y_train), eval_set=[(X_val, np.log1p(y_val))], early_stopping_rounds=100, verbose=100)
    end_time = time.time() # 记录结束时间
    print(f"XGBoost模型训练结束，结束时间: {time.ctime(end_time)}\n") # 打印结束时间
    print(f"总训练时长: {end_time - start_time:.2f}秒") # 打印总时长
    # 4. 保存模型
    joblib.dump(xgb, 'xgb_model_final_optimize_5.joblib')
    print('模型已保存到 xgb_model_final_optimize_5.joblib')

    # 5. 预测
    y_val_pred_log = xgb.predict(X_val)
    y_val_pred = np.expm1(y_val_pred_log)
    test_pred_log = xgb.predict(X_test)
    test_pred = np.expm1(test_pred_log)

    # 6. 保存预测结果
    result = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred}) if test_saleid is not None else pd.DataFrame({'price': test_pred})
    result.to_csv('xgb_save_train_result_optimize_5.csv', index=False)
    print('预测结果已保存到 xgb_save_train_result_optimize_5.csv')

    # 7. 评估模型（MAE、RMSE）
    mae = mean_absolute_error(y_val, y_val_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
    print(f'验证集 MAE: {mae:.4f}, RMSE: {rmse:.4f}')

    # 8. 绘制预测价格和实际价格对比图
    plt.figure(figsize=(8,6))
    plt.scatter(y_val, y_val_pred, alpha=0.3)
    plt.plot([y_val.min(), y_val.max()], [y_val.min(), y_val.max()], 'r--', lw=2)
    plt.xlabel('实际价格')
    plt.ylabel('预测价格')
    plt.title('预测价格 vs 实际价格')
    plt.tight_layout()
    plt.savefig('price_pred_vs_true_optimize_5.png', dpi=150)
    plt.close()
    print('预测价格与实际价格对比图已保存为 price_pred_vs_true_optimize_5.png')

    # 9. 绘制特征重要性top20
    importances = xgb.feature_importances_
    feat_names = X.columns
    indices = np.argsort(importances)[::-1][:20]
    plt.figure(figsize=(10,6))
    plt.barh(range(20), importances[indices][::-1], align='center')
    plt.yticks(range(20), [feat_names[i] for i in indices][::-1])
    plt.xlabel('特征重要性')
    plt.title('XGBoost特征重要性Top20')
    plt.tight_layout()
    plt.savefig('xgb_feature_importance_top20_optimize_5.png', dpi=150)
    plt.close()
    print('特征重要性Top20图已保存为 xgb_feature_importance_top20_optimize_5.png')

if __name__ == "__main__":
    main() 