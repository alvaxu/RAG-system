'''
1. **对price取对数建模**，预测后再还原，减少极端值影响。
2. **增加特征交互**，如品牌-车型组合（brand_model）。
3. **PCA主成分数量提升到10**，更充分利用匿名特征信息。
4. **XGBoost参数调优**，增加迭代次数、加深树深、降低学习率、提升子采样比例。
5. 代码中保留详细中文注释，便于理解和扩展。

根据@model_xgb_cv_tune的结果，最优参数: {'colsample_bytree': 0.9, 'learning_rate': 0.03, 'max_depth': 10, 'n_estimators': 1000, 'subsample': 0.8}
'''

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost.callback import EarlyStopping

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

    # 9. 特征选择（只保留SHAP前20特征）
    features = [
        'v_pca_2', 'v_pca_1', 'v_pca_0', 'power', 'v_pca_4', 'kilometer', 'car_age', 'v_pca_3',
        'bodyType', 'regYear_bin', 'brand', 'v_pca_5', 'v_pca_8', 'v_pca_6', 'regYear',
        'v_pca_7', 'brand_model', 'regMonth', 'v_pca_9', 'fuelType'
    ]
    # 若部分特征未生成，需补充生成
    if 'regYear_bin' not in data.columns:
        data['regYear_bin'] = pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False)
        data['regYear_bin'] = data['regYear_bin'].fillna(0).astype(int)
    if 'regMonth' not in data.columns:
        data['regMonth'] = data['regDate'].astype(str).str[4:6].astype(int)

    # 10. 划分训练集和测试集
    train_data = data[data['price'] != -1].copy()
    test_data = data[data['price'] == -1].copy()
    X = train_data[features]
    y = train_data['price']
    X_test = test_data[features]

    # 11. 对price取对数，提升回归精度
    y_log = np.log1p(y)

    # 12. XGBoost建模（参数进一步优化，增加正则化，不使用early_stopping）
    from sklearn.model_selection import KFold
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    maes = []
    for train_idx, val_idx in kf.split(X):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y_log.iloc[train_idx], y_log.iloc[val_idx]
        model = XGBRegressor(
            n_estimators=1300, max_depth=10, learning_rate=0.025, subsample=0.9, colsample_bytree=0.9,
            reg_alpha=1, reg_lambda=2, min_child_weight=5, gamma=0.2, random_state=42, n_jobs=-1,
            eval_metric="mae"  # 直接在初始化时指定eval_metric
        )
        model.fit(
            X_tr, y_tr,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        y_pred_log = model.predict(X_val)
        y_pred = np.expm1(y_pred_log)
        y_val_true = np.expm1(y_val)
        maes.append(mean_absolute_error(y_val_true, y_pred))
    print(f'5折CV MAE均值: {np.mean(maes):.4f}')

    # 全量训练+预测
    model = XGBRegressor(
        n_estimators=1300, max_depth=10, learning_rate=0.025, subsample=0.9, colsample_bytree=0.9,
        reg_alpha=1, reg_lambda=2, min_child_weight=5, gamma=0.2, random_state=42, n_jobs=-1,
        eval_metric="mae"
    )
    model.fit(X, y_log)
    test_pred_log = model.predict(X_test)
    test_pred = np.expm1(test_pred_log)
    result = test_data[['SaleID']].copy()
    result['price'] = test_pred
    result.to_csv('used_car_sample_submit_xgb_v3.csv', index=False)
    print('最终预测结果已保存到used_car_sample_submit_xgb_v3.csv')

if __name__ == "__main__":
    main()
