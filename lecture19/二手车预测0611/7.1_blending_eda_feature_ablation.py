'''
在7.0_blending_eda.py基础上，进行XGBoost单模型特征递归消融（RFE）实验
n_estimators=2000，只做前30轮，每次去除最不重要的特征，记录验证集MAE和RMSE
'''

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib
from sklearn.feature_selection import VarianceThreshold
import warnings
warnings.filterwarnings('ignore')

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
    features = [col for col in data.columns if col not in ['is_test', 'price', 'SaleID', 'regDate', 'creatDate', 'regDate_dt', 'creatDate_dt'] and np.issubdtype(data[col].dtype, np.number)]
    train_df = data[data['is_test'] == 0].copy()
    test_df = data[data['is_test'] == 1].copy()
    X = train_df[features]
    y = train_df['price']
    # 3. 按XGBoost特征重要性排序（先训练一次XGBoost）
    X_train_all, X_blend, y_train_all, y_blend = train_test_split(X, y, test_size=0.3, random_state=42)
    xgb = XGBRegressor(
        max_depth=10, learning_rate=0.03, n_estimators=2000, subsample=0.8, colsample_bytree=0.9,
        random_state=42, n_jobs=-1, eval_metric='rmse', early_stopping_rounds=50
    )
    xgb.fit(X_train_all, np.log1p(y_train_all), eval_set=[(X_blend, np.log1p(y_blend))], verbose=False)
    importances = xgb.feature_importances_
    feat_names = np.array(X.columns)
    sorted_idx = np.argsort(importances)[::-1]
    sorted_feats = feat_names[sorted_idx]
    # 4. 递归消融实验（只做前30轮）
    results = []
    remain_feats = list(sorted_feats)
    max_steps = min(30, len(remain_feats))
    for step in range(max_steps):
        # 训练XGBoost单模型
        X_train_all, X_blend, y_train_all, y_blend = train_test_split(X[remain_feats], y, test_size=0.3, random_state=42)
        xgb = XGBRegressor(
            max_depth=10, learning_rate=0.03, n_estimators=2000, subsample=0.8, colsample_bytree=0.9,
            random_state=42, n_jobs=-1, eval_metric='rmse', early_stopping_rounds=50
        )
        xgb.fit(X_train_all, np.log1p(y_train_all), eval_set=[(X_blend, np.log1p(y_blend))], verbose=False)
        pred = np.expm1(xgb.predict(X_blend))
        mae = mean_absolute_error(y_blend, pred)
        rmse = np.sqrt(mean_squared_error(y_blend, pred))
        results.append({
            'step': step+1,
            'num_features': len(remain_feats),
            'features': remain_feats.copy(),
            'mae': mae,
            'rmse': rmse
        })
        print(f"[第{step+1}轮] 剩余特征数: {len(remain_feats)}, MAE: {mae:.4f}, RMSE: {rmse:.4f}, 去除特征: {remain_feats[-1] if len(remain_feats)>1 else '无'}")
        # 重新计算特征重要性，去除当前最不重要的特征
        if len(remain_feats) > 1 and step < max_steps-1:
            importances = xgb.feature_importances_
            sorted_idx = np.argsort(importances)[::-1]
            remain_feats = list(np.array(remain_feats)[sorted_idx][:-1])
    # 5. 保存结果
    ablation_df = pd.DataFrame(results)
    ablation_df.to_csv('7.1_blending_eda_xgb_ablation_results.csv', index=False)
    print('XGBoost单模型特征递归消融实验结果已保存到 7.1_blending_eda_xgb_ablation_results.csv')

if __name__ == "__main__":
    main() 