import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.ensemble import StackingRegressor
import shap
import matplotlib.pyplot as plt

"""
:function: XGBoost参数调优+特征工程优化+K折交叉验证+SHAP特征重要性分析
:param 无
:return: 无
"""
def main():
    # 1. 数据读取与基础特征工程
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    test['price'] = -1
    data = pd.concat([train, test], ignore_index=True)

    # 时间特征
    data['regYear'] = data['regDate'].astype(str).str[:4].astype(int)
    data['regMonth'] = data['regDate'].astype(str).str[4:6].astype(int)
    data['creatYear'] = data['creatDate'].astype(str).str[:4].astype(int)
    data['creatMonth'] = data['creatDate'].astype(str).str[4:6].astype(int)
    data['car_age'] = data['creatYear'] - data['regYear']
    data['regYear_bin'] = pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False)

    # 缺失值处理
    data['notRepairedDamage'] = data['notRepairedDamage'].replace('-', np.nan).astype(float)
    for col in ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage']:
        if data[col].isnull().sum() > 0:
            if data[col].dtype == 'float' or data[col].dtype == 'int':
                data[col] = data[col].fillna(data[col].median())
            else:
                data[col] = data[col].fillna(data[col].mode()[0])

    # 异常值处理
    data = data[(data['price'] == -1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['price'] == -1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['price'] == -1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]

    # 重要特征分桶与交互
    data['power_log'] = np.log1p(data['power'])
    data['kilometer_log'] = np.log1p(data['kilometer'])
    data['car_age_log'] = np.log1p(data['car_age'])
    data['km_age'] = data['kilometer'] * data['car_age']
    data['power_age'] = data['power'] * data['car_age']

    # 匿名特征PCA
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=6, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    # 只保留SHAP重要性高的特征
    features = [
        'v_pca_0', 'v_pca_1', 'v_pca_2', 'v_pca_3', 'v_pca_4', 'power', 'power_log', 'kilometer', 'kilometer_log',
        'car_age', 'car_age_log', 'km_age', 'power_age', 'bodyType', 'regYear_bin', 'brand', 'regYear', 'regMonth', 'fuelType'
    ]

    # 编码
    for col in ['bodyType', 'regYear_bin', 'brand', 'fuelType']:
        data[col] = LabelEncoder().fit_transform(data[col].astype(str))

    # 数值归一化
    scaler = StandardScaler()
    data[features] = scaler.fit_transform(data[features])

    # 训练集/测试集
    train = data[data['price'] != -1].copy()
    test = data[data['price'] == -1].copy()
    X = train[features]
    y = train['price']
    X_test = test[features]
    y_log = np.log1p(y)

    # 2. Stacking集成模型
    xgb = XGBRegressor(
        max_depth=10, learning_rate=0.03, n_estimators=100, subsample=0.8, colsample_bytree=0.9,
        min_child_weight=3, gamma=0.1, reg_alpha=0.5, reg_lambda=1.0, random_state=42, n_jobs=-1
    )
    lgb = LGBMRegressor(
        max_depth=10, learning_rate=0.03, n_estimators=100, subsample=0.8, colsample_bytree=0.9,
        reg_alpha=0.5, reg_lambda=1.0, random_state=42, n_jobs=-1
    )
    cat = CatBoostRegressor(
        iterations=100, depth=10, learning_rate=0.03, subsample=0.8, random_state=42, verbose=0,
        l2_leaf_reg=3.0
    )
    stack = StackingRegressor(
        estimators=[('xgb', xgb), ('lgb', lgb), ('cat', cat)],
        final_estimator=XGBRegressor(
            max_depth=6, learning_rate=0.03, n_estimators=300, subsample=0.8, colsample_bytree=0.9, random_state=42, n_jobs=-1
        ),
        n_jobs=-1
    )

    # 3. K折交叉验证评估
    kf = KFold(n_splits=2, shuffle=True, random_state=42)
    maes, rmses = [], []
    for train_idx, val_idx in kf.split(X):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y_log.iloc[train_idx], y_log.iloc[val_idx]
        stack.fit(X_tr, y_tr)
        y_pred_log = stack.predict(X_val)
        y_pred = np.expm1(y_pred_log)
        y_val_true = np.expm1(y_val)
        maes.append(mean_absolute_error(y_val_true, y_pred))
        rmses.append(np.sqrt(mean_squared_error(y_val_true, y_pred)))
    print(f'Stacking 2折CV MAE均值: {np.mean(maes):.4f}, RMSE均值: {np.mean(rmses):.4f}')

    # # 4. SHAP特征重要性分析（以XGBoost为例）
    # xgb.fit(X, y_log)
    # explainer = shap.Explainer(xgb, X)
    # shap_values = explainer(X)
    # shap.summary_plot(shap_values, X, max_display=20, show=False)
    # plt.savefig('shap_feature_importance_stacking.png', bbox_inches='tight', dpi=150)
    # print('SHAP特征重要性图已保存为shap_feature_importance_stacking.png')

    # 5. 用集成模型预测测试集
    stack.fit(X, y_log)
    test_pred_log = stack.predict(X_test)
    test_pred = np.expm1(test_pred_log)
    result = test[['SaleID']].copy()
    result['price'] = test_pred
    result.to_csv('used_car_sample_submit_stacking.csv', index=False)
    print('最终预测结果已保存到used_car_sample_submit_stacking.csv')

if __name__ == "__main__":
    main() 