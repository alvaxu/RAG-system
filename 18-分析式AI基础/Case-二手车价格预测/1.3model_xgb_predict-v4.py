'''
1. **对price取对数建模**，预测后再还原，减少极端值影响。
2. **增加特征交互**，如品牌-车型组合（brand_model）。
3. **PCA主成分数量提升到10**，更充分利用匿名特征信息。
4. **XGBoost参数调优**，增加迭代次数、加深树深、降低学习率、提升子采样比例。
5. 代码中保留详细中文注释，便于理解和扩展。

增加更多特征交互：
新增品牌-车身类型组合（brand_bodyType）。
注册年份分桶（regYear_bin）。
模型融合：
集成 XGBoost、LightGBM、CatBoost 三个模型，预测结果简单加权平均融合。
特征选择：
保留了丰富的类别特征、交互特征、时间特征和PCA主成分。
保留对数回归和详细中文注释。
'''

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

"""
:function: 融合多模型与更多特征交互的二手车价格预测
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
    data['creatMonth'] = data['creatDate'].astype(str).str[4:6].astype(int)
    data['car_age'] = data['creatYear'] - data['regYear']
    # 注册年份分桶
    data['regYear_bin'] = pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False)

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

    # 5. 特征交互：品牌-车型组合、品牌-车身类型组合
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_model'] = LabelEncoder().fit_transform(data['brand_model'])
    data['brand_bodyType'] = LabelEncoder().fit_transform(data['brand_bodyType'])

    # 6. 类别特征编码
    cat_cols = ['brand', 'model', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType', 'brand_model', 'brand_bodyType', 'regYear_bin']
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

    # 9. 特征选择
    features = cat_cols + ['power', 'kilometer', 'car_age', 'regYear', 'regMonth', 'creatYear', 'creatMonth'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]

    # 10. 划分训练集和测试集
    train = data[data['price'] != -1].copy()
    test = data[data['price'] == -1].copy()
    X = train[features]
    y = train['price']
    X_test = test[features]

    # 11. 对price取对数，提升回归精度
    y_log = np.log1p(y)

    # 12. XGBoost建模
    X_train, X_val, y_train, y_val = train_test_split(X, y_log, test_size=0.2, random_state=42)
    model_xgb = XGBRegressor(n_estimators=600, max_depth=10, learning_rate=0.03, subsample=0.85, colsample_bytree=0.85, random_state=42, n_jobs=-1)
    model_xgb.fit(X_train, y_train)
    y_pred_xgb = np.expm1(model_xgb.predict(X_val))

    # 13. LightGBM建模
    model_lgb = LGBMRegressor(n_estimators=600, max_depth=10, learning_rate=0.03, subsample=0.85, colsample_bytree=0.85, random_state=42, n_jobs=-1)
    model_lgb.fit(X_train, y_train)
    y_pred_lgb = np.expm1(model_lgb.predict(X_val))

    # 14. CatBoost建模
    model_cat = CatBoostRegressor(iterations=600, depth=10, learning_rate=0.03, subsample=0.85, random_state=42, verbose=0)
    model_cat.fit(X_train, y_train)
    y_pred_cat = np.expm1(model_cat.predict(X_val))

    # 15. 融合预测（简单加权平均）
    y_pred = (y_pred_xgb + y_pred_lgb + y_pred_cat) / 3
    y_val_true = np.expm1(y_val)
    print('融合模型 MAE:', mean_absolute_error(y_val_true, y_pred))
    print('融合模型 RMSE:', np.sqrt(mean_squared_error(y_val_true, y_pred)))

    # 16. 测试集预测并保存结果（还原对数，融合）
    test_pred_xgb = np.expm1(model_xgb.predict(X_test))
    test_pred_lgb = np.expm1(model_lgb.predict(X_test))
    test_pred_cat = np.expm1(model_cat.predict(X_test))
    test_pred = (test_pred_xgb + test_pred_lgb + test_pred_cat) / 3
    result = test[['SaleID']].copy()
    result['price'] = test_pred
    result.to_csv('used_car_sample_submit.csv', index=False)
    print('融合预测结果已保存到used_car_sample_submit.csv')

if __name__ == "__main__":
    main()
