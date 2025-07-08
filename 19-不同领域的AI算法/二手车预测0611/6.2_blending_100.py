'''
在6.1基础上,增加特征值：v3_car_age_interaction，v12_power_log_interaction，region_brand_price和其统计特征

Blending验证集 MAE: 463.9022
Blending验证集 RMSE: 1076.8712

成绩：627
'''



import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, make_scorer
import shap
import matplotlib.pyplot as plt
import joblib
import matplotlib
import time
from catboost import CatBoostRegressor
import lightgbm as lgbm
from lightgbm import LGBMRegressor
from sklearn.linear_model import LinearRegression

"""
:function: 采用优化后的特征，进行XGBoost模型训练
:param 无
:return: 无
"""
def main():
    # ========== 解决matplotlib中文乱码 ==========
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

    # 1. 数据读取与基础特征工程
    print("\n========== 开始数据读取与基础特征工程 ==========")
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    # 添加标识列区分训练集和测试集
    train['is_test'] = 0
    test['is_test'] = 1
    data = pd.concat([train, test], ignore_index=True)

    # 根据用户要求，总是删除 'seller' 和 'offerType' 特征
    drop_always_cols = ['seller', 'offerType']
    for col in drop_always_cols:
        if col in data.columns:
            print(f"根据用户要求，已删除特征 '{col}'。")
            data = data.drop(col, axis=1)
    # 提前去除常量特征 (此处的逻辑将不再处理 seller 和 offerType)
    print("常量特征处理完成，当前数据 shape:", data.shape)

    # ========== kilometer 放大处理 ==========
    # 4.2.1是以万为单位分箱，但原始数据是以万为单位，4.2.1未放大，这里不放大
    # data['kilometer'] = data['kilometer'] * 10000  # 注释掉放大

    # ================== 特征工程（与4.2.1保持一致） ==================
    print("\n========== 开始时间特征处理 ==========")
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
    print("时间特征处理完成。")

    # ========== 缺失值处理与缺失标记（与4.2.1一致） ==========
    all_missing_cols = ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage',
                        'power', 'kilometer', 'v_0', 'v_1', 'v_2', 'v_3', 'v_4', 'v_5', 'v_6', 'v_7', 'v_8', 'v_9', 'v_10', 'v_11', 'v_12', 'v_13', 'v_14']
    for col in all_missing_cols:
        data[f'{col}_missing'] = data[col].isnull().astype(int)
        if data[col].isnull().sum() > 0:
            if str(data[col].dtype) in ['float64', 'int64', 'float32', 'int32']:
                data[col] = data[col].fillna(data[col].median())
            else:
                data[col] = data[col].fillna(data[col].mode()[0])
    print("缺失值处理与缺失标记完成。")

    # ========== 异常值处理（与4.2.1一致） ==========
    data = data[(data['is_test'] == 1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['is_test'] == 1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['is_test'] == 1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]
    for col in ['power', 'kilometer', 'v_0']:
        Q1 = data[col].quantile(0.05)
        Q3 = data[col].quantile(0.95)
        IQR = Q3 - Q1
        data[f'{col}_outlier'] = ((data[col] < (Q1 - 1.5 * IQR)) | (data[col] > (Q3 + 1.5 * IQR))).astype(int)
        data[col] = data[col].clip(Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)
    print("异常值处理完成。")

    # ========== 统计特征（与4.2.1一致） ==========
    train_idx = data[data['is_test'] == 0].index
    brand_stats = data.iloc[train_idx].groupby('brand').agg(
        brand_price_mean=('price', 'mean'),
        brand_price_median=('price', 'median'),
        brand_price_std=('price', 'std'),
        brand_price_count=('price', 'count')
    ).reset_index()
    data = data.merge(brand_stats, on='brand', how='left')
    data['brand_price_ratio'] = data['brand_price_mean'] / data['brand_price_mean'].mean()

    # ========== 特征交互（与4.2.1一致，增加新特征） ==========
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)
    data['km_age'] = data['kilometer'] * data['car_age']
    data['power_age'] = data['power'] * data['car_age']
    data['power_log'] = np.log1p(data['power'])
    data['kilometer_log'] = np.log1p(data['kilometer'])
    data['car_age_log'] = np.log1p(data['car_age'])
    # 新增特征
    data['v3_car_age_interaction'] = data['v_3'] * data['car_age']
    data['v12_power_log_interaction'] = data['v_12'] * data['power_log']

    # ========== 区域品牌统计特征 ==========
    region_brand_stats = data.iloc[train_idx].groupby(['regionCode', 'brand'])['price'].agg(region_brand_price_mean='mean', region_brand_price_std='std').reset_index()
    data = data.merge(region_brand_stats, on=['regionCode', 'brand'], how='left')
    for col_suffix in ['mean', 'std']:
        col_name = f'region_brand_price_{col_suffix}'
        if col_name in data.columns:
            global_median = data.iloc[train_idx][col_name].median()
            data[col_name] = data[col_name].fillna(global_median)

    # ========== 高基数类别特征频数编码（与4.2.1一致） ==========
    high_card_cols = ['model', 'brand_model', 'brand_power_bin', 'brand_age_segment']
    for col in high_card_cols:
        if col in data.columns:
            freq_encoding = data.groupby(col).size() / len(data)
            data[f'{col}_freq'] = data[col].map(freq_encoding)
    print("高基数类别特征频数编码完成。")

    # ========== 其它类别特征LabelEncoder（与4.2.1一致） ==========
    categorical_features = [
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage'
    ]
    for col in categorical_features:
        if col in data.columns:
            le = LabelEncoder()
            data[col] = le.fit_transform(data[col].astype(str))
    print("其余类别特征LabelEncoder编码完成。")

    # ========== 匿名特征PCA降维（与4.2.1一致） ==========
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]
    print("匿名特征PCA降维完成。")

    # ========== 数值归一化（与4.2.1一致） ==========
    num_cols = ['power', 'kilometer', 'car_age', 'km_per_year', 'power_log', 'kilometer_log', 'car_age_log', 'km_age', 'power_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])
    print("数值归一化完成。")

    # ========== 构建最终特征列表（增加新特征） ==========
    features = [
        'model_freq', 'brand_model_freq', 'brand_power_bin_freq', 'brand_age_segment_freq',
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage',
        'power', 'kilometer', 'car_age', 'regYear', 'regMonth', 'creatYear', 'creatMonth',
        'regDay', 'creatDay', 'is_new_car', 'regYear_from_now', 'creatYear_from_now',
        'regSeason', 'creatSeason', 'km_per_year',
        'brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio',
        'km_age', 'power_age', 'power_log', 'kilometer_log', 'car_age_log',
        'v3_car_age_interaction', 'v12_power_log_interaction',
        'region_brand_price_mean', 'region_brand_price_std',
        *v_cols,
        *[f'v_pca_{i}' for i in range(v_pca.shape[1])],
        *[f'{col}_missing' for col in all_missing_cols if f'{col}_missing' in data.columns],
        *[f'{col}_outlier' for col in ['power', 'kilometer', 'v_0'] if f'{col}_outlier' in data.columns],
    ]
    features = list(dict.fromkeys([f for f in features if f in data.columns]))

    train_df = data[data['is_test'] == 0].copy()
    test_df = data[data['is_test'] == 1].copy()
    X = train_df[features]
    y = train_df['price']
    X_test = test_df[features]
    test_saleid = test_df['SaleID'] if 'SaleID' in test_df.columns else None

    for col in X.columns:
        if X[col].dtype == 'object':
            raise TypeError(f"特征 '{col}' 仍然是 'object' 类型，XGBoost不支持。请检查特征工程步骤。")
    for col in X_test.columns:
        if X_test[col].dtype == 'object':
            raise TypeError(f"测试集特征 '{col}' 仍然是 'object' 类型，XGBoost不支持。请检查特征工程步骤。")

    duplicated_cols = X.columns[X.columns.duplicated()].tolist()
    if len(duplicated_cols) > 0:
        print('存在重复特征名:', duplicated_cols)
        X = X.loc[:, ~X.columns.duplicated()]
        X_test = X_test.loc[:, X.columns]
    print(f"最终特征数量: {X.shape[1]}")
    print("数据集划分完成。")


    # ========== 最终训练特征概览 ==========
    with open("6.2_blending_100_features.txt", "w", encoding="utf-8") as f:
        f.write("========== 最终训练特征概览 ==========" + "\n")
        f.write(f"总计 {len(X.columns)} 个特征将参与训练。\n")
        for col in X.columns:
            f.write(f"\n特征: {col} (数据类型: {X[col].dtype})\n")
            if X[col].nunique() <= 20:
                f.write(f"  唯一值数量: {X[col].nunique()}\n")
                f.write(f"  唯一值: {X[col].unique()}\n")
            else:
                f.write("  描述性统计:\n")
                f.write(str(X[col].describe()) + "\n")
            

    # 2. 划分训练集和验证集（70%模型训练，30%用于blending）
    X_train_all, X_blend, y_train_all, y_blend = train_test_split(X, y, test_size=0.3, random_state=42)
    


    # 3. XGBoost模型训练
    print("\n========== XGBoost模型训练 ==========")
    xgb = XGBRegressor(
        max_depth=10, learning_rate=0.03, n_estimators=4000, subsample=0.8, colsample_bytree=0.9,
        random_state=42, n_jobs=-1, eval_metric='rmse', early_stopping_rounds=100
    )
    xgb.fit(X_train_all, np.log1p(y_train_all), eval_set=[(X_blend, np.log1p(y_blend))], verbose=100)
    print("XGBoost训练完成。")
    joblib.dump(xgb, '6.2_blending_100_xgb_model.joblib')
    print('XGBoost模型已保存到 6.2_blending_100_xgb_model.joblib')

    # 4. CatBoost模型训练
    print("\n========== CatBoost模型训练 ==========")
    cat = CatBoostRegressor(
        iterations=4000, learning_rate=0.03, depth=10, subsample=0.8, colsample_bylevel=0.9,
        random_seed=42, verbose=100, loss_function='RMSE', early_stopping_rounds=100
    )
    cat.fit(X_train_all, np.log1p(y_train_all), eval_set=(X_blend, np.log1p(y_blend)), use_best_model=True)
    print("CatBoost训练完成。")
    joblib.dump(cat, '6.2_blending_100_cat_model.joblib')
    print('CatBoost模型已保存到 6.2_blending_100_cat_model.joblib')

     # 5. LightGBM模型训练
    print("\n========== LightGBM模型训练 ==========")
    lgb = LGBMRegressor(
        n_estimators=4000, learning_rate=0.03, max_depth=10, subsample=0.8, colsample_bytree=0.9,
        random_state=42, n_jobs=-1,verbosity=0
    )
    # 设置回调函数（包含早停）
    callbacks = [
        lgbm.early_stopping(stopping_rounds=100),  # 早停轮数
        lgbm.log_evaluation(period=100)  # 每100轮输出日志
    ]
    lgb.fit(X_train_all, np.log1p(y_train_all), eval_set=[(X_blend, np.log1p(y_blend))], eval_metric='rmse',callbacks=callbacks)

    print("LightGBM训练完成。")
    joblib.dump(lgb, '6.2_blending_100_lgb_model.joblib')
    print('LightGBM模型已保存到 6.2_blending_100_lgb_model.joblib')

    # 6. 三模型在blending集上的预测
    print("\n========== 三模型在blending集上的预测 ==========")
    xgb_pred_blend = np.expm1(xgb.predict(X_blend))
    cat_pred_blend = np.expm1(cat.predict(X_blend))
    lgb_pred_blend = np.expm1(lgb.predict(X_blend))
    blend_X = np.vstack([xgb_pred_blend, cat_pred_blend, lgb_pred_blend]).T
    blend_y = y_blend.values

    # 7. 线性回归blending
    print("\n========== 线性回归blending加权 ==========")
    lr_blend = LinearRegression(fit_intercept=True)
    lr_blend.fit(blend_X, blend_y)
    print(f"blending权重: {lr_blend.coef_}, 截距: {lr_blend.intercept_}")
    print(f"三模型blending权重分别为: XGBoost: {lr_blend.coef_[0]:.4f}, CatBoost: {lr_blend.coef_[1]:.4f}, LightGBM: {lr_blend.coef_[2]:.4f}")

    # 8. 在验证集上评估blending效果
    blend_pred = lr_blend.predict(blend_X)
    mae = mean_absolute_error(blend_y, blend_pred)
    rmse = np.sqrt(mean_squared_error(blend_y, blend_pred))
    print(f'Blending验证集 MAE: {mae:.4f}')
    print(f'Blending验证集 RMSE: {rmse:.4f}')

    # 9. 三模型在测试集上的预测并blending
    print("\n========== 三模型在测试集上的预测并blending ==========")
    xgb_pred_test = np.expm1(xgb.predict(X_test))
    cat_pred_test = np.expm1(cat.predict(X_test))
    lgb_pred_test = np.expm1(lgb.predict(X_test))
    test_blend_X = np.vstack([xgb_pred_test, cat_pred_test, lgb_pred_test]).T
    blend_test_pred = lr_blend.predict(test_blend_X)

    # 10. 保存blending预测结果
    result = pd.DataFrame({'SaleID': test_saleid, 'price': blend_test_pred}) if test_saleid is not None else pd.DataFrame({'price': blend_test_pred})
    result.to_csv('6.2_blending_100_predict.csv', index=False)
    print('Blending预测结果已保存到 6.2_blending_100_predict.csv')

    # 8. 绘制特征重要性top50
    importances = xgb.feature_importances_
    feat_names = X.columns
    indices = np.argsort(importances)[::-1][:50]
    plt.figure(figsize=(10,6))
    plt.barh(range(50), importances[indices][::-1], align='center')
    plt.yticks(range(50), [feat_names[i] for i in indices][::-1])
    plt.xlabel('特征重要性')
    plt.title('6.2_blending_100_XGBoost特征重要性Top50')
    plt.tight_layout()
    plt.savefig('6.2_blending_100_importance_top50.png', dpi=150)
    plt.close()
    print('特征重要性Top50图已保存为 6.2_blending_100_importance_top50.png')
   

if __name__ == "__main__":
    main() 