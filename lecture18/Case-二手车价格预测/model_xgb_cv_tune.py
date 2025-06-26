import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, make_scorer
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

    # 2. 特征交互与分桶
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)
    data['brand_km_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['kilometer'], bins=[0,5,10,12,14,15], labels=False).astype(str)
    data['power_bin'] = pd.cut(data['power'], bins=[0,50,100,150,200,300,600], labels=False)

    # 编码
    for col in ['brand_model','brand_bodyType','brand_regYear_bin','brand_km_bin','power_bin']:
        data[col] = LabelEncoder().fit_transform(data[col].astype(str))
    cat_cols = ['brand', 'model', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
                'brand_model', 'brand_bodyType', 'regYear_bin', 'brand_regYear_bin', 'brand_km_bin', 'power_bin']
    for col in cat_cols:
        data[col] = LabelEncoder().fit_transform(data[col].astype(str))

    # 匿名特征PCA
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    # 数值归一化
    num_cols = ['power', 'kilometer', 'car_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])

    # 特征列表
    features = cat_cols + ['power', 'kilometer', 'car_age', 'regYear', 'regMonth', 'creatYear', 'creatMonth'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]

    # 训练集/测试集
    train = data[data['price'] != -1].copy()
    test = data[data['price'] == -1].copy()
    X = train[features]
    y = train['price']
    X_test = test[features]
    y_log = np.log1p(y)

    # 3. XGBoost参数调优+K折交叉验证
    param_grid = {
        'max_depth': [6, 8, 10],
        'learning_rate': [0.01, 0.03, 0.05],
        'n_estimators': [800, 1000],
        'subsample': [0.8, 0.9],
        'colsample_bytree': [0.8, 0.9]
    }
    xgb = XGBRegressor(random_state=42, n_jobs=-1)
    scorer = make_scorer(mean_absolute_error, greater_is_better=False)
    grid = GridSearchCV(xgb, param_grid, scoring=scorer, cv=5, verbose=2, n_jobs=-1)
    grid.fit(X, y_log)
    print('最优参数:', grid.best_params_)
    print('最优MAE:', -grid.best_score_)

    # 4. 用最优参数做5折交叉验证评估
    best_xgb = grid.best_estimator_
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    maes = []
    rmses = []
    for train_idx, val_idx in kf.split(X):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y_log.iloc[train_idx], y_log.iloc[val_idx]
        best_xgb.fit(X_tr, y_tr)
        y_pred_log = best_xgb.predict(X_val)
        y_pred = np.expm1(y_pred_log)
        y_val_true = np.expm1(y_val)
        maes.append(mean_absolute_error(y_val_true, y_pred))
        rmses.append(np.sqrt(mean_squared_error(y_val_true, y_pred)))
    print(f'5折CV MAE均值: {np.mean(maes):.4f}, RMSE均值: {np.mean(rmses):.4f}')

    # 5. SHAP特征重要性分析
    explainer = shap.Explainer(best_xgb, X)
    shap_values = explainer(X)
    shap.summary_plot(shap_values, X, max_display=20, show=False)
    plt.savefig('shap_feature_importance.png', bbox_inches='tight', dpi=150)
    print('SHAP特征重要性图已保存为shap_feature_importance.png')

    # 6. 用最优模型预测测试集
    best_xgb.fit(X, y_log)
    test_pred_log = best_xgb.predict(X_test)
    test_pred = np.expm1(test_pred_log)
    result = test[['SaleID']].copy()
    result['price'] = test_pred
    result.to_csv('used_car_sample_submit_xgb_cv_tune.csv', index=False)
    print('最终预测结果已保存到used_car_sample_submit_xgb_cv_tune.csv')

if __name__ == "__main__":
    main() 