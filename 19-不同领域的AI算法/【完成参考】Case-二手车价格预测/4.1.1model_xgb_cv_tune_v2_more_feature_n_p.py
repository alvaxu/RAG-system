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
import xgboost as xgb

"""
:function: XGBoost参数调优+特征工程优化+特征重要性分析
:param 无
:return: 无
"""
def main():
    # ========== 解决matplotlib中文乱码 ==========
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

    # 1. 数据读取与基础特征工程
    train = pd.read_csv('used_car_train_20200313.csv', sep=' ')
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    test['price'] = -1
    data = pd.concat([train, test], ignore_index=True)

    # ================== 特征工程（全面梳理与优化） ==================
    # 1. 时间特征处理
    data['regDate_dt'] = pd.to_datetime(data['regDate'], format='%Y%m%d', errors='coerce')
    data['creatDate_dt'] = pd.to_datetime(data['creatDate'], format='%Y%m%d', errors='coerce')
    # 车辆使用年限（天/年）
    data['car_age_days'] = (data['creatDate_dt'] - data['regDate_dt']).dt.days
    data['car_age'] = data['car_age_days'] / 365.25
    # 若有负值或缺失，填充为中位数
    median_car_age = data['car_age'].median()
    data['car_age'] = data['car_age'].apply(lambda x: median_car_age if pd.isnull(x) or x < 0 else x)
    # 注册/创建年月日
    data['regYear'] = data['regDate_dt'].dt.year
    data['regMonth'] = data['regDate_dt'].dt.month
    data['regDay'] = data['regDate_dt'].dt.day
    data['creatYear'] = data['creatDate_dt'].dt.year
    data['creatMonth'] = data['creatDate_dt'].dt.month
    data['creatDay'] = data['creatDate_dt'].dt.day
    # 是否为新车
    data['is_new_car'] = (data['car_age'] < 1).astype(int)
    # 相对年份特征
    current_year = pd.Timestamp.now().year
    data['regYear_from_now'] = current_year - data['regYear']
    data['creatYear_from_now'] = current_year - data['creatYear']
    # 季节特征
    data['regSeason'] = data['regMonth'].apply(lambda x: (x%12 + 3)//3)
    data['creatSeason'] = data['creatMonth'].apply(lambda x: (x%12 + 3)//3)
    # 每年行驶的公里数
    data['km_per_year'] = data['kilometer'] / (data['car_age'] + 0.1)
    # 车龄分段
    data['age_segment'] = pd.cut(data['car_age'], bins=[-0.01, 1, 3, 5, 10, 100], labels=['0-1年', '1-3年', '3-5年', '5-10年', '10年以上'])
    # 注册年份分段
    data['regYear_bin'] = pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False)
    # 公里数分段
    data['km_bin'] = pd.cut(data['kilometer'], bins=[0,5,10,12,14,15], labels=False)
    # 功率分段
    data['power_bin'] = pd.cut(data['power'], bins=[0,50,100,150,200,300,600], labels=False)
    # 品牌与公里数分段
    data['brand_km_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['kilometer'], bins=[0,5,10,12,14,15], labels=False).astype(str)
    # 品牌与功率分段
    data['brand_power_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['power'], bins=[0,50,100,150,200,300,600], labels=False).astype(str)
    # 品牌与车龄分段
    data['brand_age_segment'] = data['brand'].astype(str) + '_' + data['age_segment'].astype(str)
    # 品牌与注册年份分段
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)

    # ========== 缺失值处理与缺失标记优化 ==========
    # 需要处理的特征列表
    all_missing_cols = ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage',
                        'power', 'kilometer', 'v_0', 'v_1', 'v_2', 'v_3', 'v_4', 'v_5', 'v_6', 'v_7', 'v_8', 'v_9', 'v_10', 'v_11', 'v_12', 'v_13', 'v_14']
    for col in all_missing_cols:
        # 增加缺失标记
        data[f'{col}_missing'] = data[col].isnull().astype(int)
        # 数值型用中位数填充，类别型用众数填充
        if data[col].isnull().sum() > 0:
            if str(data[col].dtype) in ['float64', 'int64', 'float32', 'int32']:
                data[col] = data[col].fillna(data[col].median())
            else:
                data[col] = data[col].fillna(data[col].mode()[0])

    # 3. 异常值处理（仅对训练集）
    data = data[(data['price'] == -1) | ((data['price'] >= 100) & (data['price'] <= 100000))]
    data = data[(data['price'] == -1) | ((data['power'] > 0) & (data['power'] < 600))]
    data = data[(data['price'] == -1) | ((data['kilometer'] > 0) & (data['kilometer'] <= 15))]
    # 异常值标记
    for col in ['power', 'kilometer', 'v_0']:
        Q1 = data[col].quantile(0.05)
        Q3 = data[col].quantile(0.95)
        IQR = Q3 - Q1
        data[f'{col}_outlier'] = ((data[col] < (Q1 - 1.5 * IQR)) | (data[col] > (Q3 + 1.5 * IQR))).astype(int)
        data[col] = data[col].clip(Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)

    # 4. 统计特征（品牌均值/中位数/计数/标准差等）
    train_idx = data[data['price'] != -1].index
    brand_stats = data.iloc[train_idx].groupby('brand').agg(
        brand_price_mean=('price', 'mean'),
        brand_price_median=('price', 'median'),
        brand_price_std=('price', 'std'),
        brand_price_count=('price', 'count')
    ).reset_index()
    data = data.merge(brand_stats, on='brand', how='left')
    data['brand_price_ratio'] = data['brand_price_mean'] / data['brand_price_mean'].mean()

    # 5. 特征交互
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)
    # 交互特征
    data['km_age'] = data['kilometer'] * data['car_age']
    data['power_age'] = data['power'] * data['car_age']
    data['power_log'] = np.log1p(data['power'])
    data['kilometer_log'] = np.log1p(data['kilometer'])
    data['car_age_log'] = np.log1p(data['car_age'])

    # ========== 高基数类别特征采用频数编码 ==========
    high_card_cols = ['model', 'brand_model', 'brand_power_bin', 'brand_age_segment']
    for col in high_card_cols:
        if col in data.columns:
            freq_encoding = data.groupby(col).size() / len(data)
            data[f'{col}_freq'] = data[col].map(freq_encoding)

    # 其余类别特征用LabelEncoder
    categorical_features = [
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage'
    ]
    for col in categorical_features:
        if col in data.columns:
            data[col] = LabelEncoder().fit_transform(data[col].astype(str))

    # ========== 匿名特征及PCA降维 ==========
    v_cols = [f'v_{i}' for i in range(15)]
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    # ========== 数值归一化 ==========
    num_cols = ['power', 'kilometer', 'car_age', 'km_per_year', 'power_log', 'kilometer_log', 'car_age_log', 'km_age', 'power_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])

    # ========== 最终特征列表 ==========
    features = [
        # 高基数特征频数编码
        'model_freq', 'brand_model_freq', 'brand_power_bin_freq', 'brand_age_segment_freq',
        # 其余类别特征
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage',
        # 数值特征
        'power', 'kilometer', 'car_age', 'regYear', 'regMonth', 'creatYear', 'creatMonth',
        'regDay', 'creatDay', 'is_new_car', 'regYear_from_now', 'creatYear_from_now',
        'regSeason', 'creatSeason', 'km_per_year',
        'brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio',
        'km_age', 'power_age', 'power_log', 'kilometer_log', 'car_age_log',
        # 匿名特征
        *v_cols,
        # PCA降维特征
        *[f'v_pca_{i}' for i in range(v_pca.shape[1])],
        # 缺失/异常/频率特征
        *[f'{col}_missing' for col in all_missing_cols],
        *[f'{col}_outlier' for col in ['power', 'kilometer', 'v_0']],
        *[f'{col}_freq' for col in ['model', 'brand', 'bodyType', 'fuelType', 'gearbox', 'notRepairedDamage']]
    ]
    # 去重，保证特征唯一
    features = list(dict.fromkeys([f for f in features if f in data.columns]))

    # 11. 训练集/测试集（此时还保留price和SaleID列，便于后续处理）
    train = data[data['price'] != -1].copy()
    test = data[data['price'] == -1].copy()
    X = train[features]
    y = train['price']
    X_test = test[features]
    test_saleid = test['SaleID'] if 'SaleID' in test.columns else None

    # 检查特征名唯一性，若有重复则去重并打印
    duplicated_cols = X.columns[X.columns.duplicated()].tolist()
    if len(duplicated_cols) > 0:
        print('存在重复特征名:', duplicated_cols)
        X = X.loc[:, ~X.columns.duplicated()]
        X_test = X_test.loc[:, X.columns]  # 保证测试集特征顺序和训练集一致

    # 之后再删除不需要的列
    drop_cols = ['regDate', 'creatDate', 'SaleID', 'name', 'offerType', 'seller', 'regDate_dt', 'creatDate_dt', 'price']
    data = data.drop(drop_cols, axis=1, errors='ignore')

    # 定义RMSE评分函数，兼容旧版本sklearn
    def rmse_scorer_func(y_true, y_pred):
        # 确保预测值和真实值维度一致
        if len(y_true) != len(y_pred):
            return 1e9 # 返回一个较大的值，表示评分很差
        return np.sqrt(mean_squared_error(y_true, y_pred))

    # 使用make_scorer创建评分器，greater_is_better=False表示希望最小化该评分
    rmse_scorer = make_scorer(rmse_scorer_func, greater_is_better=False)

    # 2. 参数调优 (使用 GridSearchCV)
    print("\n====== 开始参数调优 (GridSearchCV) ======")
    # 定义参数网格 - 为了演示，这里只选择部分参数进行调优
    param_grid = {
        'max_depth': [6, 8, 10], # 尝试不同最大深度
        'learning_rate': [0.01, 0.03, 0.05], # 尝试不同学习率
        'subsample': [0.7, 0.8, 0.9], # 尝试不同子采样比例
        'colsample_bytree': [0.7, 0.8, 0.9], # 尝试不同列采样比例
    }

    # 定义XGBoost模型，这里n_estimators可以先给一个较大的值
    xgb_grid = XGBRegressor(
        objective='reg:squarederror', # XGBoost的回归目标
        eval_metric='rmse', # 评估指标
        n_estimators=1000, # GridSearchCV内部使用，固定迭代次数
        random_state=42,
        n_jobs=-1,
        tree_method='hist', # 推荐使用'hist'，速度更快
        enable_categorical=True # 尝试启用类别特征支持
    )

    # 设置GridSearchCV的交叉验证
    print("开始运行GridSearchCV...")
    grid_search = GridSearchCV(estimator=xgb_grid, param_grid=param_grid, scoring=rmse_scorer, cv=KFold(n_splits=3, shuffle=True, random_state=42), verbose=2, n_jobs=-1)

    # 在log1p转换后的目标变量y上进行拟合和评估
    grid_search.fit(X, np.log1p(y))
    print("GridSearchCV运行结束.")

    print("\n最佳参数: ", grid_search.best_params_)
    print("最佳交叉验证得分 (RMSE): ", -grid_search.best_score_)

    # 获取最佳参数
    best_params = grid_search.best_params_

    # 3. 使用最佳参数进行K折交叉验证训练（确定最佳迭代次数并生成OOF预测）
    print("\n====== 使用最佳参数进行K折交叉验证训练 (确定最佳迭代次数) ======")
    kf = KFold(n_splits=5, shuffle=True, random_state=42) # 恢复使用5折
    oof_preds = np.zeros(X.shape[0])
    test_preds_cv = np.zeros(X_test.shape[0]) # 存储CV的测试集预测，与最终模型预测区分
    feature_importances = pd.DataFrame(index=X.columns)
    best_iterations = []

    start_time_cv = time.time()
    print(f"XGBoost模型交叉验证训练开始，开始时间: {time.ctime(start_time_cv)}")

    for fold, (train_index, val_index) in enumerate(kf.split(X, y)):
        print(f"====== 开始训练 Fold {fold+1} ======")
        X_train, X_val = X.iloc[train_index], X.iloc[val_index]
        y_train, y_val = y.iloc[train_index], y.iloc[val_index]

        # 使用GridSearchCV找到的最佳参数初始化XGBoost模型
        xgb_fold = XGBRegressor(
            objective='reg:squarederror',
            eval_metric='rmse',
            n_estimators=5000, # 增加迭代次数，配合early stopping
            max_depth=best_params['max_depth'], # 使用最佳参数
            learning_rate=best_params['learning_rate'], # 使用最佳参数
            subsample=best_params['subsample'], # 使用最佳参数
            colsample_bytree=best_params['colsample_bytree'], # 使用最佳参数
            random_state=42 + fold, # 不同折使用不同随机种子
            n_jobs=-1,
            tree_method='hist',
            enable_categorical=True,
        )

        # XGBoost的fit方法使用eval_set或valid_sets进行早停，使用callbacks
        xgb_fold.fit(X_train, np.log1p(y_train),
                     eval_set=[(X_val, np.log1p(y_val))],
                     callbacks=[xgb.callback.EarlyStopping(rounds=50, metric_name='rmse', data_name='validation_0', maximize=False, save_best=True)], # 早停回调
                     verbose=False # 设置verbose为False以减少日志输出
                    )

        oof_preds[val_index] = np.expm1(xgb_fold.predict(X_val)) # 对验证集进行预测，并expm1转换
        test_preds_cv += np.expm1(xgb_fold.predict(X_test)) / kf.n_splits # 对测试集进行预测，并累加

        # 记录当前折叠的最佳迭代次数和特征重要性
        best_iterations.append(xgb_fold.best_iteration)
        feature_importances[f'fold_{fold+1}'] = xgb_fold.feature_importances_

    end_time_cv = time.time()
    print(f"XGBoost模型交叉验证训练结束，结束时间: {time.ctime(end_time_cv)}")
    print(f"总训练时长: {end_time_cv - start_time_cv:.2f}秒")

    # 计算平均特征重要性
    feature_importances['average'] = feature_importances.mean(axis=1)
    feature_importances = feature_importances.sort_values('average', ascending=False)

    # 计算平均最佳迭代次数
    avg_best_iteration = int(np.mean(best_iterations))
    print(f"平均最佳迭代次数 (基于最佳参数): {avg_best_iteration}")

    # 4. 使用全部训练数据和最佳参数+平均最佳迭代次数重新训练最终模型并保存
    print(f"\n====== 使用全部数据和最佳参数进行最终模型训练 ======")
    print(f"迭代次数: {avg_best_iteration}")
    final_xgb = XGBRegressor(
        objective='reg:squarederror',
        eval_metric='rmse',
        n_estimators=avg_best_iteration, # 使用平均最佳迭代次数
        max_depth=best_params['max_depth'], # 使用最佳参数
        learning_rate=best_params['learning_rate'], # 使用最佳参数
        subsample=best_params['subsample'], # 使用最佳参数
        colsample_bytree=best_params['colsample_bytree'], # 使用最佳参数
        random_state=42, # 最终模型使用固定随机种子
        n_jobs=-1,
        tree_method='hist',
        enable_categorical=True,
    )

    start_time_final = time.time()
    final_xgb.fit(X, np.log1p(y)) # 使用全部训练数据进行训练
    end_time_final = time.time()
    print(f"最终模型训练结束，时长: {end_time_final - start_time_final:.2f}秒")

    # 保存最终模型
    model_filename = f'xgb_model_final_tuned_iter_{avg_best_iteration}.joblib'
    joblib.dump(final_xgb, model_filename)
    print(f'最终模型已保存到 {model_filename}')

    # 5. 使用交叉验证的out-of-fold预测结果进行评估和可视化
    print(f'\n====== 交叉验证 OOF 结果评估和可视化 ======\n') # 添加换行符
    mae = mean_absolute_error(y, oof_preds)
    rmse = np.sqrt(mean_squared_error(y, oof_preds))
    print(f'交叉验证 OOF MAE: {mae:.4f}, OOF RMSE: {rmse:.4f}')

    # 绘制预测价格和实际价格对比图（使用out-of-fold预测）
    plt.figure(figsize=(8,6))
    plt.scatter(y, oof_preds, alpha=0.3)
    plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', lw=2)
    plt.xlabel('实际价格')
    plt.ylabel('预测价格')
    plt.title('XGBoost交叉验证 OOF预测价格 vs 实际价格 (调优后)') # 修改标题
    plt.tight_layout()
    plt.savefig('price_pred_vs_true_xgb_cv_tuned.png', dpi=150) # 修改文件名
    plt.close()
    print('XGBoost交叉验证 OOF预测价格与实际价格对比图已保存为 price_pred_vs_true_xgb_cv_tuned.png') # 修改打印信息

    # 绘制特征重要性top20 (使用平均重要性)
    plt.figure(figsize=(10,6))
    top20_importances = feature_importances['average'].head(20)[::-1]
    plt.barh(range(20), top20_importances.values, align='center')
    plt.yticks(range(20), top20_importances.index.tolist())
    plt.xlabel('特征重要性 (平均)')
    plt.title('XGBoost交叉验证 特征重要性Top20 (调优后)') # 修改标题
    plt.tight_layout()
    plt.savefig('xgb_feature_importance_top20_cv_tuned.png', dpi=150) # 修改文件名
    plt.close()
    print('XGBoost交叉验证 特征重要性Top20图已保存为 xgb_feature_importance_top20_cv_tuned.png') # 修改打印信息

    # 6. 使用最终模型对测试集进行预测并保存结果
    print("\n====== 最终模型测试集预测 ======")
    test_pred_final = np.expm1(final_xgb.predict(X_test))
    result_final = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred_final}) if test_saleid is not None else pd.DataFrame({'price': test_pred_final})
    result_filename = f'used_car_sample_submit_xgb_final_tuned_iter_{avg_best_iteration}.csv'
    result_final.to_csv(result_filename, index=False)
    print(f'最终模型预测结果已保存到 {result_filename}')

    # 7. 打印最终模型的参数
    print("\n====== 最终模型参数 ======")
    final_model_params = final_xgb.get_params()
    tuned_params_to_print = {
        'n_estimators': avg_best_iteration,
        'objective': final_model_params['objective'],
        'eval_metric': final_model_params['eval_metric'],
        'max_depth': best_params['max_depth'],
        'learning_rate': best_params['learning_rate'],
        'subsample': best_params['subsample'],
        'colsample_bytree': best_params['colsample_bytree'],
        'random_state': final_model_params['random_state'],
        'n_jobs': final_model_params['n_jobs'],
        'tree_method': final_model_params['tree_method'],
        'enable_categorical': final_model_params['enable_categorical'],
    }
    for param, value in tuned_params_to_print.items():
        print(f"{param}: {value}")

if __name__ == "__main__":
    main() 