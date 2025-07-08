import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

"""
:function: 使用最优参数和最优特征的XGBoost模型进行二手车价格预测
:param 无
:return: 无
"""
def main():
    # 1. 数据读取
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    test['price'] = -1
    data = pd.concat([train, test], ignore_index=True)

    # 2. 时间特征处理
    data['regYear'] = data['regDate'].astype(str).str[:4].astype(int)
    data['regMonth'] = data['regDate'].astype(str).str[4:6].astype(int)
    data['creatYear'] = data['creatDate'].astype(str).str[:4].astype(int)
    data['car_age'] = data['creatYear'] - data['regYear']
    data['regYear_bin'] = pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False)
    data['regYear_bin'] = data['regYear_bin'].fillna(0).astype(int)

    # 3. 缺失值处理
    data['notRepairedDamage'] = data['notRepairedDamage'].replace('-', np.nan).astype(float)
    for col in ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage']:
        if data[col].isnull().sum() > 0:
            if data[col].dtype == 'float' or data[col].dtype == 'int':
                data[col] = data[col].fillna(data[col].median())
            else:
                data[col] = data[col].fillna(data[col].mode()[0])

    # 4. 异常值处理
    data = data[(data['price'] == -1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['price'] == -1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['price'] == -1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]

    # 5. 特征交互
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_model'] = LabelEncoder().fit_transform(data['brand_model'])

    # 6. 类别特征编码
    cat_cols = ['brand', 'model', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType', 'brand_model']
    for col in cat_cols:
        data[col] = LabelEncoder().fit_transform(data[col].astype(str))

    # 7. 匿名特征PCA降维
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    # 8. 特征归一化
    num_cols = ['power', 'kilometer', 'car_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])

    # 9. 只保留SHAP前20特征
    features = [
        'v_pca_2', 'v_pca_1', 'v_pca_0', 'power', 'v_pca_4', 'kilometer', 'car_age', 'v_pca_3',
        'bodyType', 'regYear_bin', 'brand', 'v_pca_5', 'v_pca_8', 'v_pca_6', 'regYear',
        'v_pca_7', 'brand_model', 'regMonth', 'v_pca_9', 'fuelType'
    ]

    # 10. 划分训练集和测试集
    train_data = data[data['price'] != -1].copy()
    test_data = data[data['price'] == -1].copy()
    X = train_data[features]
    y = train_data['price']
    X_test = test_data[features]

    # 11. 对price取对数，提升回归精度
    y_log = np.log1p(y)

    # 12. XGBoost最优参数建模
    model = XGBRegressor(
        n_estimators=1000, max_depth=10, learning_rate=0.03, subsample=0.8, colsample_bytree=0.9,
        reg_alpha=0, reg_lambda=1, random_state=42, n_jobs=-1
    )
    model.fit(X, y_log)

    # 13. 训练集评估，计算MAE和RMSE
    train_pred_log = model.predict(X)
    train_pred = np.expm1(train_pred_log)
    y_true = np.expm1(y_log)
    mae = mean_absolute_error(y_true, train_pred)
    rmse = np.sqrt(mean_squared_error(y_true, train_pred))
    print(f'训练集MAE: {mae:.4f}')
    print(f'训练集RMSE: {rmse:.4f}')

    # 14. 测试集预测并保存结果
    test_pred_log = model.predict(X_test)
    test_pred = np.expm1(test_pred_log)
    result = test_data[['SaleID']].copy()
    result['price'] = test_pred
    result.to_csv('used_car_sample_submit_best_model.csv', index=False)
    print('最终预测结果已保存到used_car_sample_submit_best_model.csv')

if __name__ == "__main__":
    main() 