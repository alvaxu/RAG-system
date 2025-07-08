'''
请直接修改@model_xgb_predict.py 中的时间特征处理过程，car_age不能只是data['creatYear'] - data['regYear']的结果，应该考虑年月日的信息，把car_age的值进行更精确的处理。
MAE反而高了。请直接修改@model_xgb_predict.py ，将'creatYear', 'creatMonth'，'regYear', 'regMonth'也作为特征值考虑进去
'''


import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

"""
:function: 优化后的特征工程与XGBoost建模预测流程，提升预测精度
:param 无
:return: 无
"""
def main():
    # 1. 数据读取
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    test['price'] = -1  # 测试集无标签，补充一列方便拼接
    data = pd.concat([train, test], ignore_index=True)

    # 2. 时间特征处理（精确到天，计算car_age为年，保留小数）
    data['regDate_dt'] = pd.to_datetime(data['regDate'], format='%Y%m%d', errors='coerce')
    data['creatDate_dt'] = pd.to_datetime(data['creatDate'], format='%Y%m%d', errors='coerce')
    # 精确计算车辆使用年限（天数/365.25）
    data['car_age'] = (data['creatDate_dt'] - data['regDate_dt']).dt.days / 365.25
    # 若有负值或缺失，填充为中位数
    median_car_age = data['car_age'].median()
    data['car_age'] = data['car_age'].apply(lambda x: median_car_age if pd.isnull(x) or x < 0 else x)
    # 额外保留注册月、注册日等特征
    data['regYear'] = data['regDate_dt'].dt.year
    data['regMonth'] = data['regDate_dt'].dt.month
    data['regDay'] = data['regDate_dt'].dt.day
    data['creatYear'] = data['creatDate_dt'].dt.year
    data['creatMonth'] = data['creatDate_dt'].dt.month
    data['creatDay'] = data['creatDate_dt'].dt.day

    # 3. 缺失值处理
    data['notRepairedDamage'] = data['notRepairedDamage'].replace('-', np.nan).astype(float)
    for col in ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage']:
        if data[col].isnull().sum() > 0:
            if data[col].dtype == 'float' or data[col].dtype == 'int':
                data[col] = data[col].fillna(data[col].median())
            else:
                data[col] = data[col].fillna(data[col].mode()[0])

    # 4. 异常值处理（仅对训练集）
    data = data[(data['price'] == -1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['price'] == -1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['price'] == -1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]

    # 5. 特征交互：品牌-车型组合
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_model'] = LabelEncoder().fit_transform(data['brand_model'])

    # 6. 类别特征编码
    cat_cols = ['brand', 'model', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType', 'brand_model']
    for col in cat_cols:
        data[col] = LabelEncoder().fit_transform(data[col].astype(str))

    # 7. 匿名特征PCA降维（增加主成分数量到10）
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    # 8. 特征归一化
    num_cols = ['power', 'kilometer', 'car_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])

    # 9. 特征选择（将creatYear, creatMonth, regYear, regMonth加入特征）
    features = cat_cols + ['power', 'kilometer', 'car_age', 'regYear', 'regMonth', 'creatYear', 'creatMonth'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]

    # 10. 划分训练集和测试集
    train = data[data['price'] != -1].copy()
    test = data[data['price'] == -1].copy()
    X = train[features]
    y = train['price']
    X_test = test[features]

    # 11. 对price取对数，提升回归精度
    y_log = np.log1p(y)

    # 12. XGBoost建模（增加迭代次数，适当调参）
    X_train, X_val, y_train, y_val = train_test_split(X, y_log, test_size=0.2, random_state=42)
    model = XGBRegressor(n_estimators=600, max_depth=10, learning_rate=0.03, subsample=0.85, colsample_bytree=0.85, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 13. 验证集评估（还原对数）
    y_pred_log = model.predict(X_val)
    y_pred = np.expm1(y_pred_log)
    y_val_true = np.expm1(y_val)
    print('MAE:', mean_absolute_error(y_val_true, y_pred))
    print('RMSE:', np.sqrt(mean_squared_error(y_val_true, y_pred)))

    # 14. 测试集预测并保存结果（还原对数）
    test_pred_log = model.predict(X_test)
    test_pred = np.expm1(test_pred_log)
    result = test[['SaleID']].copy()
    result['price'] = test_pred
    result.to_csv('used_car_sample_submit.csv', index=False)
    print('预测结果已保存到used_car_sample_submit.csv')

if __name__ == "__main__":
    main()
