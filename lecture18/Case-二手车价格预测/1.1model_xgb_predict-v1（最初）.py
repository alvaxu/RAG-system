
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

"""
:function: 完整的特征工程与XGBoost建模预测流程
:param 无
:return: 无
"""
def main():
    # 1. 数据读取
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    test['price'] = -1  # 测试集无标签，补充一列方便拼接
    data = pd.concat([train, test], ignore_index=True)

    # 2. 时间特征处理
    data['regYear'] = data['regDate'].astype(str).str[:4].astype(int)
    data['regMonth'] = data['regDate'].astype(str).str[4:6].astype(int)
    data['creatYear'] = data['creatDate'].astype(str).str[:4].astype(int)
    data['car_age'] = data['creatYear'] - data['regYear']

    # 3. 缺失值处理
    data['notRepairedDamage'] = data['notRepairedDamage'].replace('-', np.nan).astype(float)
    for col in ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage']:
        if data[col].isnull().sum() > 0:
            if data[col].dtype == 'float' or data[col].dtype == 'int':
                data[col] = data[col].fillna(data[col].median())
            else:
                data[col] = data[col].fillna(data[col].mode()[0])

    # 4. 异常值处理（仅对训练集）
    train_idx = data['price'] != -1
    data = data[(data['price'] == -1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['price'] == -1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['price'] == -1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]

    # 5. 类别特征编码
    cat_cols = ['brand', 'model', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType']
    for col in cat_cols:
        data[col] = LabelEncoder().fit_transform(data[col].astype(str))

    # 6. 匿名特征PCA降维
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=6, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    # 7. 特征归一化
    num_cols = ['power', 'kilometer', 'car_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])

    # 8. 特征选择
    features = cat_cols + ['power', 'kilometer', 'car_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]

    # 9. 划分训练集和测试集
    train = data[data['price'] != -1].copy()
    test = data[data['price'] == -1].copy()
    X = train[features]
    y = train['price']
    X_test = test[features]

    # 10. XGBoost建模（去除early_stopping_rounds和eval_set参数）
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(n_estimators=300, max_depth=8, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 11. 验证集评估
    y_pred = model.predict(X_val)
    print('MAE:', mean_absolute_error(y_val, y_pred))
    print('RMSE:', np.sqrt(mean_squared_error(y_val, y_pred)))

    # 12. 测试集预测并保存结果
    test_pred = model.predict(X_test)
    result = test[['SaleID']].copy()
    result['price'] = test_pred
    result.to_csv('xgb_testB_submit.csv', index=False)
    print('预测结果已保存到xgb_testB_submit.csv')

if __name__ == "__main__":
    main()
