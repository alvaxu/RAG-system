import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

def main():
    # 数据读取与特征工程（与融合模型一致）
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    test['price'] = -1
    data = pd.concat([train, test], ignore_index=True)

    data['regYear'] = data['regDate'].astype(str).str[:4].astype(int)
    data['regMonth'] = data['regDate'].astype(str).str[4:6].astype(int)
    data['creatYear'] = data['creatDate'].astype(str).str[:4].astype(int)
    data['creatMonth'] = data['creatDate'].astype(str).str[4:6].astype(int)
    data['car_age'] = data['creatYear'] - data['regYear']
    data['regYear_bin'] = pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False)

    data['notRepairedDamage'] = data['notRepairedDamage'].replace('-', np.nan).astype(float)
    for col in ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage']:
        if data[col].isnull().sum() > 0:
            if data[col].dtype == 'float' or data[col].dtype == 'int':
                data[col] = data[col].fillna(data[col].median())
            else:
                data[col] = data[col].fillna(data[col].mode()[0])

    data = data[(data['price'] == -1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['price'] == -1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['price'] == -1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]

    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_model'] = LabelEncoder().fit_transform(data['brand_model'])
    data['brand_bodyType'] = LabelEncoder().fit_transform(data['brand_bodyType'])

    cat_cols = ['brand', 'model', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType', 'brand_model', 'brand_bodyType', 'regYear_bin']
    for col in cat_cols:
        data[col] = LabelEncoder().fit_transform(data[col].astype(str))

    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    num_cols = ['power', 'kilometer', 'car_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])

    features = cat_cols + ['power', 'kilometer', 'car_age', 'regYear', 'regMonth', 'creatYear', 'creatMonth'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]

    train = data[data['price'] != -1].copy()
    test = data[data['price'] == -1].copy()
    X = train[features]
    y = train['price']
    X_test = test[features]

    y_log = np.log1p(y)
    X_train, X_val, y_train, y_val = train_test_split(X, y_log, test_size=0.2, random_state=42)
    model = XGBRegressor(n_estimators=600, max_depth=10, learning_rate=0.03, subsample=0.85, colsample_bytree=0.85, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred_log = model.predict(X_val)
    y_pred = np.expm1(y_pred_log)
    y_val_true = np.expm1(y_val)
    print('XGBoost MAE:', mean_absolute_error(y_val_true, y_pred))
    print('XGBoost RMSE:', np.sqrt(mean_squared_error(y_val_true, y_pred)))

    test_pred_log = model.predict(X_test)
    test_pred = np.expm1(test_pred_log)
    result = test[['SaleID']].copy()
    result['price'] = test_pred
    result.to_csv('used_car_sample_submit_xgb.csv', index=False)
    print('XGBoost预测结果已保存到used_car_sample_submit_xgb.csv')

if __name__ == "__main__":
    main()
