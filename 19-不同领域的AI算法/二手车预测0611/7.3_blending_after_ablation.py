'''
基于消融实验推荐的68个最优特征集，三模型（XGBoost、CatBoost、LightGBM）blending二手车预测脚本

Blending验证集 MAE: 536.6219
Blending验证集 RMSE: 1183.7875
blending权重: [0.772673   0.1478923  0.09048943], 截距: 18.864845599114233
三模型blending权重分别为: XGBoost: 0.7727, CatBoost: 0.1479, LightGBM: 0.0905
XGBoost验证集 MAE: 534.1615, RMSE: 1194.2353
CatBoost验证集 MAE: 547.7361, RMSE: 1269.3587
LightGBM验证集 MAE: 588.3218, RMSE: 1258.2977

成绩：527.6734
'''

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.linear_model import LinearRegression
import matplotlib
import matplotlib.pyplot as plt
from sklearn.feature_selection import VarianceThreshold
import warnings
warnings.filterwarnings('ignore')

# 推荐的最优特征组合（第9轮68个特征）
BEST_FEATURES = [
    'v_3', 'v_12', 'v_0', 'v_pca_2', 'power_bin', 'v_pca_0', 'notRepairedDamage', 'v_pca_1', 'v_10', 'km_age',
    'car_age_log', 'power_log', 'power', 'age_segment', 'km_bin', 'notRepairedDamage_missing', 'v_8', 'car_age',
    'car_age_days', 'kilometer', 'regYear_from_now', 'kilometer_log', 'v_1', 'brand_price_std', 'v_6', 'bodyType',
    'v_9', 'brand_price_ratio', 'v_11', 'v_pca_3', 'brand_regYear_bin', 'brand_model_freq', 'v_pca_4', 'v_14',
    'brand_price_count', 'regYear', 'gearbox_missing', 'brand_power_bin_freq', 'v_2', 'v_5', 'gearbox',
    'brand_price_mean', 'brand_bodyType', 'km_per_year', 'power_age', 'fuelType', 'brand_age_segment_freq',
    'v_13', 'model_freq', 'brand_price_median', 'fuelType_missing', 'v_7', 'v_pca_8', 'brand_km_bin', 'v_pca_5',
    'v_pca_6', 'name', 'v_pca_7', 'v_4', 'regionCode', 'creatMonth', 'model', 'v_pca_9', 'brand', 'creatDay',
    'regMonth', 'regDay', 'regSeason'
]

def main():
    # 1. 解决matplotlib中文乱码
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False

    # 2. 数据读取与特征工程（与7.0_blending_eda.py一致，略去部分注释）
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    train['is_test'] = 0
    test['is_test'] = 1
    data = pd.concat([train, test], ignore_index=True)
    drop_always_cols = ['seller', 'offerType']
    for col in drop_always_cols:
        if col in data.columns:
            data = data.drop(col, axis=1)
    if 'notRepairedDamage' in data.columns:
        data['notRepairedDamage'] = data['notRepairedDamage'].replace('-', np.nan)
    all_missing_cols = ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage',
                        'power', 'kilometer', 'v_0', 'v_1', 'v_2', 'v_3', 'v_4', 'v_5', 'v_6', 'v_7', 'v_8', 'v_9', 'v_10', 'v_11', 'v_12', 'v_13', 'v_14', 'name']
    for col in all_missing_cols:
        data[f'{col}_missing'] = data[col].isnull().astype(int)
        if data[col].isnull().sum() > 0:
            if str(data[col].dtype) in ['float64', 'int64', 'float32', 'int32']:
                data[col] = data[col].fillna(data[col].median())
            else:
                data[col] = data[col].fillna(data[col].mode()[0])
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
    data = data[(data['is_test'] == 1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['is_test'] == 1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['is_test'] == 1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]
    for col in ['power', 'kilometer', 'v_0']:
        Q1 = data[col].quantile(0.05)
        Q3 = data[col].quantile(0.95)
        IQR = Q3 - Q1
        data[f'{col}_outlier'] = ((data[col] < (Q1 - 1.5 * IQR)) | (data[col] > (Q3 + 1.5 * IQR))).astype(int)
        data[col] = data[col].clip(Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)
    data['car_age'] = data['car_age'].clip(1, 15)
    train_idx = data[data['is_test'] == 0].index
    brand_stats = data.iloc[train_idx].groupby('brand').agg(
        brand_price_mean=('price', 'mean'),
        brand_price_median=('price', 'median'),
        brand_price_std=('price', 'std'),
        brand_price_count=('price', 'count')
    ).reset_index()
    data = data.merge(brand_stats, on='brand', how='left')
    data['brand_price_ratio'] = data['brand_price_mean'] / data['brand_price_mean'].mean()
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)
    data['km_age'] = data['kilometer'] * data['car_age']
    data['power_age'] = data['power'] * data['car_age']
    data['power_log'] = np.log1p(data['power'])
    data['kilometer_log'] = np.log1p(data['kilometer'])
    data['car_age_log'] = np.log1p(data['car_age'])
    high_card_cols = ['model', 'brand_model', 'brand_power_bin', 'brand_age_segment', 'name']
    for col in high_card_cols:
        if col in data.columns:
            freq_encoding = data.groupby(col).size() / len(data)
            data[f'{col}_freq'] = data[col].map(freq_encoding)
    categorical_features = [
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage', 'name'
    ]
    for col in categorical_features:
        if col in data.columns:
            le = LabelEncoder()
            data[col] = le.fit_transform(data[col].astype(str))
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]
    num_cols = ['power', 'kilometer', 'car_age', 'km_per_year', 'power_log', 'kilometer_log', 'car_age_log', 'km_age', 'power_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])
    nunique = data.nunique()
    drop_unique = nunique[nunique <= 1].index.tolist()
    if drop_unique:
        data = data.drop(columns=drop_unique)
    data = data.loc[:, ~data.T.duplicated()]
    feature_cols = [col for col in data.columns if col not in ['is_test', 'price', 'SaleID', 'regDate', 'creatDate', 'regDate_dt', 'creatDate_dt']]
    data_features = data[feature_cols].select_dtypes(include=[np.number])
    selector = VarianceThreshold(threshold=1e-5)
    selector.fit(data_features)
    selected_cols = data_features.columns[selector.get_support(indices=True)].tolist()
    for col in feature_cols:
        if col not in selected_cols:
            data = data.drop(col, axis=1)
    # 只保留最优特征组合
    features = [col for col in BEST_FEATURES if col in data.columns]
    train_df = data[data['is_test'] == 0].copy()
    test_df = data[data['is_test'] == 1].copy()
    X = train_df[features]
    y = train_df['price']
    X_test = test_df[features]
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else None

    # 3. 划分训练集和验证集（70%训练，30%blending）
    X_train_all, X_blend, y_train_all, y_blend = train_test_split(X, y, test_size=0.3, random_state=42)

    # 4. 三模型训练
    print("\n========== XGBoost模型训练 ==========")
    xgb = XGBRegressor(
        max_depth=10, learning_rate=0.03, n_estimators=2000, subsample=0.8, colsample_bytree=0.9,
        random_state=42, n_jobs=-1, eval_metric='rmse', early_stopping_rounds=50
    )
    xgb.fit(X_train_all, np.log1p(y_train_all), eval_set=[(X_blend, np.log1p(y_blend))], verbose=50)
    print("XGBoost训练完成。")

    print("\n========== LightGBM模型训练 ==========")
    lgb = LGBMRegressor(
        n_estimators=2000, learning_rate=0.03, max_depth=10, subsample=0.8, colsample_bytree=0.9,
        random_state=42, n_jobs=-1, verbosity=0
    )
    lgb.fit(X_train_all, np.log1p(y_train_all), eval_set=[(X_blend, np.log1p(y_blend))], eval_metric='rmse', callbacks=[
        lambda env: None
    ])
    print("LightGBM训练完成。")

    print("\n========== CatBoost模型训练 ==========")
    cat = CatBoostRegressor(
        iterations=2000, learning_rate=0.03, depth=10, subsample=0.8, colsample_bylevel=0.9,
        random_seed=42, verbose=50, loss_function='RMSE', early_stopping_rounds=50
    )
    cat.fit(X_train_all, np.log1p(y_train_all), eval_set=(X_blend, np.log1p(y_blend)), use_best_model=True)
    print("CatBoost训练完成。")

    # 5. 各模型在blending集上的预测
    xgb_pred_blend = np.expm1(xgb.predict(X_blend))
    cat_pred_blend = np.expm1(cat.predict(X_blend))
    lgb_pred_blend = np.expm1(lgb.predict(X_blend))
    blend_X = np.vstack([xgb_pred_blend, cat_pred_blend, lgb_pred_blend]).T
    blend_y = y_blend.values

    # 6. 线性回归blending
    lr_blend = LinearRegression(fit_intercept=True)
    lr_blend.fit(blend_X, blend_y)
    blend_pred = lr_blend.predict(blend_X)
    mae = mean_absolute_error(blend_y, blend_pred)
    rmse = np.sqrt(mean_squared_error(blend_y, blend_pred))
    print(f'Blending验证集 MAE: {mae:.4f}')
    print(f'Blending验证集 RMSE: {rmse:.4f}')
    print(f'blending权重: {lr_blend.coef_}, 截距: {lr_blend.intercept_}')
    print(f'三模型blending权重分别为: XGBoost: {lr_blend.coef_[0]:.4f}, CatBoost: {lr_blend.coef_[1]:.4f}, LightGBM: {lr_blend.coef_[2]:.4f}')

    # 7. 各模型单独评估
    print(f'XGBoost验证集 MAE: {mean_absolute_error(blend_y, xgb_pred_blend):.4f}, RMSE: {np.sqrt(mean_squared_error(blend_y, xgb_pred_blend)):.4f}')
    print(f'CatBoost验证集 MAE: {mean_absolute_error(blend_y, cat_pred_blend):.4f}, RMSE: {np.sqrt(mean_squared_error(blend_y, cat_pred_blend)):.4f}')
    print(f'LightGBM验证集 MAE: {mean_absolute_error(blend_y, lgb_pred_blend):.4f}, RMSE: {np.sqrt(mean_squared_error(blend_y, lgb_pred_blend)):.4f}')

    # 8. 测试集预测并blending
    xgb_pred_test = np.expm1(xgb.predict(X_test))
    cat_pred_test = np.expm1(cat.predict(X_test))
    lgb_pred_test = np.expm1(lgb.predict(X_test))
    test_blend_X = np.vstack([xgb_pred_test, cat_pred_test, lgb_pred_test]).T
    blend_test_pred = lr_blend.predict(test_blend_X)
    result = pd.DataFrame({'SaleID': test_saleid, 'price': blend_test_pred}) if test_saleid is not None else pd.DataFrame({'price': blend_test_pred})
    result.to_csv('7.3_blending_after_ablation_predict.csv', index=False)
    print('Blending测试集预测结果已保存到 7.3_blending_after_ablation_predict.csv')

    # 9. XGBoost特征重要性Top30图
    importances = xgb.feature_importances_
    indices = np.argsort(importances)[::-1][:30]
    plt.figure(figsize=(10,6))
    plt.barh(range(30), importances[indices][::-1], align='center')
    plt.yticks(range(30), [features[i] for i in indices][::-1])
    plt.xlabel('特征重要性')
    plt.title('7.3_blending_after_ablation_XGBoost特征重要性Top30')
    plt.tight_layout()
    plt.savefig('7.3_blending_after_ablation_importance_top30.png', dpi=150)
    plt.close()
    print('XGBoost特征重要性Top30图已保存为 7.3_blending_after_ablation_importance_top30.png')

if __name__ == "__main__":
    main() 