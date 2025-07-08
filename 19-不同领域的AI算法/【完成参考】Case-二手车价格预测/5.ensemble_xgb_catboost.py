import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
import joblib
import matplotlib.pyplot as plt
import matplotlib
import time
from catboost import CatBoostRegressor # 导入CatBoostRegressor
from xgboost import XGBRegressor # 导入XGBRegressor

"""
:function: XGBoost和CatBoost模型融合预测
:param 无
:return: 无
"""
def main():
    # ========== 解决matplotlib中文乱码 ==========
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

    # 1. 数据读取
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    # 为了保持特征工程代码一致性，给测试集增加一个price列并设置为-1
    test['price'] = -1
    data = pd.concat([train, test], ignore_index=True) # 合并训练集和测试集进行统一的特征工程

    # ================== 特征工程（与训练时保持一致） ==================
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
    data['age_segment'] = pd.cut(data['car_age'], bins=[-0.01, 1, 3, 5, 10, 100], labels=False) # 使用LabelEncoder时需要False，CatBoost直接处理string
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
    data['brand_age_segment'] = data['brand'].astype(str) + '_' + pd.cut(data['car_age'], bins=[-0.01, 1, 3, 5, 10, 100], labels=False).astype(str) # 使用LabelEncoder时需要False，CatBoost直接处理string
    # 品牌与注册年份分段
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False).astype(str)

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

    # 3. 异常值处理（在合并后的数据上进行，与训练一致）
    data = data[(data['price'] == -1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['price'] == -1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['price'] == -1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]
    # 异常值标记和clip (在合并数据上进行)
    for col in ['power', 'kilometer', 'v_0']:
        Q1 = data[col].quantile(0.05)
        Q3 = data[col].quantile(0.95)
        IQR = Q3 - Q1
        data[f'{col}_outlier'] = ((data[col] < (Q1 - 1.5 * IQR)) | (data[col] > (Q3 + 1.5 * IQR))).astype(int)
        data[col] = data[col].clip(Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)

    # 4. 统计特征（在训练集部分计算统计量，应用到整个数据集）
    train_data_for_stats = data[data['price'] != -1].copy() # 仅用训练集部分计算统计量
    brand_stats = train_data_for_stats.groupby('brand').agg(
        brand_price_mean=('price', 'mean'),
        brand_price_median=('price', 'median'),
        brand_price_std=('price', 'std'),
        brand_price_count=('price', 'count')
    ).reset_index()
    data = data.merge(brand_stats, on='brand', how='left')
    data['brand_price_ratio'] = data['brand_price_mean'] / data['brand_price_mean'].mean()
    # 对NaN（新品牌）进行填充
    for stat_col in ['brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio']:
         if data[stat_col].isnull().sum() > 0:
             data[stat_col] = data[stat_col].fillna(data[stat_col].median())

    # 5. 特征交互
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False).astype(str)
    # 交互特征
    data['km_age'] = data['kilometer'] * data['car_age']
    data['power_age'] = data['power'] * data['car_age']
    data['power_log'] = np.log1p(data['power'])
    data['kilometer_log'] = np.log1p(data['kilometer'])
    data['car_age_log'] = np.log1p(data['car_age'])

    # ========== 高基数类别特征采用频数编码（在合并数据上计算和应用） ==========
    high_card_cols = ['model', 'brand_model', 'brand_power_bin', 'brand_age_segment']
    for col in high_card_cols:
        if col in data.columns:
            # 计算频数编码（在整个合并数据集上）
            freq_encoding = data[col].value_counts(normalize=True)
            data[f'{col}_freq'] = data[col].map(freq_encoding).fillna(0) # 填充新出现的类别为0

    # 其余类别特征用LabelEncoder (for XGBoost) - 在合并数据上拟合和转换
    categorical_features_xgb = [
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage'
    ]
    label_encoders = {}
    for col in categorical_features_xgb:
        if col in data.columns:
            # 在整个合并数据集上拟合LabelEncoder
            le = LabelEncoder()
            data[col] = le.fit_transform(data[col].astype(str))
            label_encoders[col] = le # 保存encoder备用（虽然这里不需要，但良好习惯）

    # ========== 匿名特征及PCA降维（在合并数据上拟合和转换） ==========
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    # 在整个合并数据集上拟合和转换PCA
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    # ========== 数值归一化（在合并数据上拟合和转换） ==========
    # num_cols 需要包含PCA后的特征
    num_cols = ['power', 'kilometer', 'car_age', 'km_per_year', 'power_log', 'kilometer_log', 'car_age_log', 'km_age', 'power_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    scaler = StandardScaler()
    # 在整个合并数据集上拟合和转换StandardScaler
    data[num_cols] = scaler.fit_transform(data[num_cols])

    # ========== 确保CatBoost类别特征为string类型 ==========
    # CatBoost支持的类别特征列表，这些特征在XGBoost处理后可能会变成数值，需要恢复或单独处理原始列
    # 更好的方式是，在LabelEncoder和FreqEncoder之前就确定好CatBoost的特征列表
    # 然后复制这些原始列，用于CatBoost的预测
    # 为了简化，这里先假设原始列还在，并转换为string
    catboost_cat_features = [
        'brand', 'model', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_model', 'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin',
        'brand_power_bin', 'brand_age_segment', 'notRepairedDamage'
    ]
    # 创建一个副本用于CatBoost，保留原始类别特征
    data_catboost = data.copy()
    for col in catboost_cat_features:
         if col in data_catboost.columns:
             data_catboost[col] = data_catboost[col].astype(str) # 确保是string类型

    # ========== 最终特征列表 (需要根据训练脚本来确定) ==========
    # 这里应该严格复制训练脚本中的最终特征列表
    features_xgb = [
        # 高基数特征频数编码
        'model_freq', 'brand_model_freq', 'brand_power_bin_freq', 'brand_age_segment_freq',
        # 其余类别特征 (LabelEncoded)
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage',
        # 数值特征 (StandardScaled)
        'power', 'kilometer', 'car_age', 'regYear', 'regMonth', 'creatYear', 'creatMonth',
        'regDay', 'creatDay', 'is_new_car', 'regYear_from_now', 'creatYear_from_now',
        'regSeason', 'creatSeason', 'km_per_year',
        'brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio',
        'km_age', 'power_age', 'power_log', 'kilometer_log', 'car_age_log',
        # 匿名特征 (StandardScaled)
        *v_cols,
        # PCA降维特征 (StandardScaled)
        *[f'v_pca_{i}' for i in range(pca.n_components)], # 使用pca.n_components确保数量一致
        # 缺失/异常标记
        *[f'{col}_missing' for col in all_missing_cols],
        *[f'{col}_outlier' for col in ['power', 'kilometer', 'v_0']],
        # 之前频率编码遗漏的几个低基数类别特征的freq编码 (如果XGBoost训练时用了)
        *[f'{col}_freq' for col in ['brand', 'bodyType', 'fuelType', 'gearbox', 'notRepairedDamage']] # 确保和XGB训练时一致
    ]

    # CatBoost的特征列表 - 包含原始类别特征和频数编码、数值特征等
    features_catboost = [
         # 高基数特征频数编码
        'model_freq', 'brand_model_freq', 'brand_power_bin_freq', 'brand_age_segment_freq',
        # 其余类别特征 (原始string类型)
        'brand', 'model', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_model', 'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin',
        'brand_power_bin', 'brand_age_segment', 'notRepairedDamage',
        # 数值特征 (StandardScaled)
        'power', 'kilometer', 'car_age', 'regYear', 'regMonth', 'creatYear', 'creatMonth',
        'regDay', 'creatDay', 'is_new_car', 'regYear_from_now', 'creatYear_from_now',
        'regSeason', 'creatSeason', 'km_per_year',
        'brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio',
        'km_age', 'power_age', 'power_log', 'kilometer_log', 'car_age_log',
        # 匿名特征 (StandardScaled)
        *v_cols,
        # PCA降维特征 (StandardScaled)
        *[f'v_pca_{i}' for i in range(pca.n_components)], # 使用pca.n_components确保数量一致
         # 缺失/异常标记
        *[f'{col}_missing' for col in all_missing_cols],
        *[f'{col}_outlier' for col in ['power', 'kilometer', 'v_0']],
         # 之前频率编码遗漏的几个低基数类别特征的freq编码 (如果CatBoost训练时用了)
         *[f'{col}_freq' for col in ['brand', 'bodyType', 'fuelType', 'gearbox', 'notRepairedDamage']] # 确保和CatBoost训练时一致
    ]

    # 去重并确保列存在于合并后的数据中
    features_xgb = list(dict.fromkeys([f for f in features_xgb if f in data.columns]))
    features_catboost = list(dict.fromkeys([f for f in features_catboost if f in data_catboost.columns])) # 注意这里使用data_catboost

    # 划分回训练集和测试集
    train_processed = data[data['price'] != -1].copy()
    test_processed = data[data['price'] == -1].copy() # 用于XGBoost
    test_processed_catboost = data_catboost[data_catboost['price'] == -1].copy() # 用于CatBoost

    # 提取测试集特征
    X_test_xgb = test_processed[features_xgb]
    X_test_catboost = test_processed_catboost[features_catboost]

    # 记录SaleID
    test_saleid = test['SaleID'] if 'SaleID' in test.columns else None

    # ========== 加载模型 ==========
    print("加载XGBoost模型...")
    xgb_model = joblib.load('xgb_model_final_4000.joblib')
    print("XGBoost模型加载成功.")

    print("加载CatBoost模型...")
    # CatBoost加载模型需要指定model_file路径
    catboost_model = CatBoostRegressor()
    catboost_model.load_model('catboost_model_final_5000.cbm')
    print("CatBoost模型加载成功.")

    # ========== 进行预测 ==========
    print("使用XGBoost模型进行预测...")
    # 检查XGBoost测试集特征数量是否匹配
    if X_test_xgb.shape[1] != xgb_model.n_features_in_: # 使用n_features_in_来获取模型训练时的特征数量
        print(f"Error: XGBoost测试集特征数量不匹配. Expected: {xgb_model.n_features_in_}, Got: {X_test_xgb.shape[1]}")
        print("XGBoost测试集特征: ", X_test_xgb.columns.tolist())
        # 可以选择在这里退出或尝试找出差异
        # exit() # 如果需要严格退出
        # 尝试找出差异特征
        xgb_train_features = xgb_model.get_booster().feature_names # 获取模型训练时的特征名
        missing_in_test_xgb = set(xgb_train_features) - set(X_test_xgb.columns)
        extra_in_test_xgb = set(X_test_xgb.columns) - set(xgb_train_features)
        print("XGBoost训练集有但测试集没有的特征:", missing_in_test_xgb)
        print("XGBoost测试集有但训练集没有的特征:", extra_in_test_xgb)
        # 尝试只保留训练时有的特征（可能会导致特征数量减少，但至少不会因为多余特征报错）
        X_test_xgb = X_test_xgb[xgb_train_features] # 重新排序和选择特征
        print("已根据XGBoost训练特征重新对齐测试集.")

    test_pred_log_xgb = xgb_model.predict(X_test_xgb)
    test_pred_xgb = np.expm1(test_pred_log_xgb)
    print("XGBoost预测完成.")

    print("使用CatBoost模型进行预测...")
    # CatBoost预测时，如果训练时指定了cat_features，这里传入的X_test_catboost需要有相同的列以及列类型
    # 确保CatBoost测试集特征数量和顺序与训练时一致
    # CatBoost模型没有直接暴露训练时的特征名称列表，但可以通过加载模型后的内部属性获取
    # 或者最好的方式是：严格保证features_catboost列表与训练脚本一致
    # 为了确保代码运行，这里先假设features_catboost是正确的
    # 如果CatBoost预测报错，可能需要检查cat_features参数或列类型
    test_pred_log_catboost = catboost_model.predict(X_test_catboost)
    test_pred_catboost = np.expm1(test_pred_log_catboost)
    print("CatBoost预测完成.")

    # ========== 结果融合 ==========
    xgb_weight = 0.55
    catboost_weight = 0.45
    ensemble_pred = xgb_weight * test_pred_xgb + catboost_weight * test_pred_catboost
    print(f"预测结果融合完成，XGBoost权重: {xgb_weight}, CatBoost权重: {catboost_weight}")

    # ========== 保存预测结果 ==========
    result = pd.DataFrame({'SaleID': test_saleid, 'price': ensemble_pred}) if test_saleid is not None else pd.DataFrame({'price': ensemble_pred})
    result.to_csv('used_car_sample_submit_ensemble_xgb_catboost.csv', index=False)
    print('融合预测结果已保存到 used_car_sample_submit_ensemble_xgb_catboost.csv')

if __name__ == "__main__":
    main() 