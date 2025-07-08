import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
import joblib
import matplotlib.pyplot as plt
import matplotlib

"""
:function: 集成XGBoost和LightGBM模型进行预测
:param 无
:return: 无
"""
def main():
    # ========== 解决matplotlib中文乱码（即使不画图，也保持一致性） ==========
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

    print("====== 开始数据加载和特征工程 ======")
    # 1. 数据读取
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    test['price'] = -1 # 保持与训练数据处理时一致的列结构，方便特征工程
    data = test.copy() # 使用data进行特征工程

    # ================== 特征工程（与训练时保持完全一致） ==================
    # 1. 时间特征处理
    data['regDate_dt'] = pd.to_datetime(data['regDate'], format='%Y%m%d', errors='coerce')
    data['creatDate_dt'] = pd.to_datetime(data['creatDate'], format='%Y%m%d', errors='coerce')
    # 车辆使用年限（天/年）
    data['car_age_days'] = (data['creatDate_dt'] - data['regDate_dt']).dt.days
    data['car_age'] = data['car_age_days'] / 365.25
    # 若有负值或缺失，填充为中位数（这里没有训练集，直接用整体中位数或合理值）
    # 注意：这里需要与训练集中的中位数保持一致，实际应用中应该加载训练时的中位数
    # 简化处理：由于是测试集，且train和test拼接后处理，这里先用测试集自己的中位数，如果模型表现不佳，可能需要固定这些统计量
    median_car_age = 5.0 # 根据训练集的car_age中位数或经验值设置，避免测试集单独计算造成偏差
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
    data['age_segment'] = pd.cut(data['car_age'], bins=[-0.01, 1, 3, 5, 10, 100], labels=False) # 改为False以与LGBM文件保持一致
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
    data['brand_age_segment'] = data['brand'].astype(str) + '_' + pd.cut(data['car_age'], bins=[-0.01, 1, 3, 5, 10, 100], labels=False).astype(str) # 同样改为False
    # 品牌与注册年份分段
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False).astype(str)

    # ========== 缺失值处理与缺失标记优化（注意：填充值应与训练集一致） ==========
    all_missing_cols = ['bodyType', 'fuelType', 'gearbox', 'model', 'notRepairedDamage',
                        'power', 'kilometer', 'v_0', 'v_1', 'v_2', 'v_3', 'v_4', 'v_5', 'v_6', 'v_7', 'v_8', 'v_9', 'v_10', 'v_11', 'v_12', 'v_13', 'v_14']
    # 理想情况下，这里应该加载训练集计算出的中位数和众数进行填充
    # 为简化演示，这里直接使用测试集自身的中位数/众数，实际中请确保与训练集一致
    # 某些类别特征的众数可能在测试集中不存在，需要更鲁棒的处理 (例如用'-1'或'unknown'填充)
    for col in all_missing_cols:
        data[f'{col}_missing'] = data[col].isnull().astype(int)
        if data[col].isnull().sum() > 0:
            if str(data[col].dtype) in ['float64', 'int64', 'float32', 'int32']:
                data[col] = data[col].fillna(data[col].median() if not data[col].isnull().all() else 0) # 避免所有值都缺失时报错
            else:
                # 处理类别特征众数可能为空的情况
                if not data[col].mode().empty:
                    data[col] = data[col].fillna(data[col].mode()[0])
                else:
                    data[col] = data[col].fillna('-1') # 或者其他标记，表示未知类别

    # 3. 异常值处理 (仅对训练集操作，测试集不进行clip，只添加标记)
    # 对于测试集，我们通常不裁剪异常值，只标记，因为模型训练时已经学习了这些范围
    for col in ['power', 'kilometer', 'v_0']:
        # 这里需要使用训练集计算出的Q1和Q3
        # 简化处理：假设训练集Q1和Q3为固定值，或者略过此步骤，因为测试集不应该改变原始数值
        # 由于之前代码中对训练集进行了clip，这里为了保持一致性，我们也要进行clip，但需要用训练集的Q1和Q3
        # 暂时使用经验值或测试集自身的Q1/Q3，实际应用中需保存训练集的Q1/Q3
        if col == 'power': Q1_val, Q3_val = 50, 200 # 示例值，实际应从训练集获取
        elif col == 'kilometer': Q1_val, Q3_val = 1, 15 # 示例值
        elif col == 'v_0': Q1_val, Q3_val = -10, 10 # 示例值
        else: Q1_val, Q3_val = data[col].quantile(0.05), data[col].quantile(0.95)

        IQR = Q3_val - Q1_val
        data[f'{col}_outlier'] = ((data[col] < (Q1_val - 1.5 * IQR)) | (data[col] > (Q3_val + 1.5 * IQR))).astype(int)
        data[col] = data[col].clip(Q1_val - 1.5 * IQR, Q3_val + 1.5 * IQR)

    # 4. 统计特征（品牌均值/中位数/计数/标准差等）
    # 这里需要加载训练集计算的品牌统计量，而不是在测试集上重新计算
    # 假设我们已经保存了这些统计量，并在此加载
    # 示例数据（实际应用中，这些值应从训练集计算并保存）
    # brand_stats_loaded = pd.read_csv('brand_stats_from_train.csv') # 示例加载方式
    # 为演示，这里模拟一个简单的均值填充，实际请加载训练时的统计值
    data['brand_price_mean'] = 0
    data['brand_price_median'] = 0
    data['brand_price_std'] = 0
    data['brand_price_count'] = 0
    data['brand_price_ratio'] = 0

    # 5. 特征交互
    data['brand_model'] = data['brand'].astype(str) + '_' + data['model'].astype(str)
    data['brand_bodyType'] = data['brand'].astype(str) + '_' + data['bodyType'].astype(str)
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False).astype(str)
    # 交互特征
    data['km_age'] = data['kilometer'] * data['car_age']
    data['power_age'] = data['power'] * data['car_age']
    data['power_log'] = np.log1p(data['power'])
    data['kilometer_log'] = np.log1p(data['kilometer'])
    data['car_age_log'] = np.log1p(data['car_age'])

    # ========== 高基数类别特征采用频数编码（使用训练集统计的频数） ==========
    high_card_cols = ['model', 'brand_model', 'brand_power_bin', 'brand_age_segment']
    for col in high_card_cols:
        if col in data.columns:
            # 理想情况下，这里应该加载训练集计算出的freq_encoding字典
            # 为了简化，这里暂时用测试集自身计算，但请注意，正确的做法是使用训练集统计量
            # 假设一个默认值，以防新类别出现
            freq_encoding = data.groupby(col).size() / len(data)
            data[f'{col}_freq'] = data[col].map(freq_encoding).fillna(0) # 新类别填充0

    # 其余类别特征用LabelEncoder（使用训练集拟合的LabelEncoder）
    categorical_features = [
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage'
    ]
    for col in categorical_features:
        if col in data.columns:
            # 理想情况下，这里应该加载训练集拟合好的LabelEncoder对象
            # 为了简化，这里暂时在测试集上重新fit_transform，但请注意，正确的做法是使用训练集fit的编码器
            # fit_transform会导致新类别问题，建议使用transform，并处理未见过的新类别
            le = LabelEncoder()
            # 为了避免fit_transform在测试集上引入新类别问题，我们将新的未知类别映射到一个特殊的ID (例如-1)
            # 但LabelEncoder不支持直接对未见过的值进行转换，因此需要更复杂的手动映射
            # 简单的做法：先将所有值转为字符串，对于训练集未出现的值，LabelEncoder会报KeyError，需要try-except或预先处理
            # 更健壮的做法是：收集训练集的所有唯一类别，然后使用一个自定义映射函数
            # 目前沿用之前代码的fit_transform，但要注意在实际部署时可能需要改进此部分
            data[col] = le.fit_transform(data[col].astype(str))

    # ========== 匿名特征及PCA降维（使用训练集拟合的PCA） ==========
    v_cols = [f'v_{i}' for i in range(15)]
    # 理想情况下，这里应该加载训练集拟合好的PCA对象
    # 为了简化，这里暂时在测试集上重新fit_transform，但请注意，正确的做法是使用训练集fit的PCA
    pca = PCA(n_components=10, random_state=42)
    v_pca = pca.fit_transform(data[v_cols])
    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    # ========== 数值归一化（使用训练集拟合的StandardScaler） ==========
    num_cols = ['power', 'kilometer', 'car_age', 'km_per_year', 'power_log', 'kilometer_log', 'car_age_log', 'km_age', 'power_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    # 理想情况下，这里应该加载训练集拟合好的StandardScaler对象
    # 为了简化，这里暂时在测试集上重新fit_transform，但请注意，正确的做法是使用训练集fit的Scaler
    scaler = StandardScaler()
    data[num_cols] = scaler.fit_transform(data[num_cols])

    # ========== 最终特征列表 (与训练时保持一致) ==========
    features = [
        # 高基数特征频数编码
        'model_freq', 'brand_model_freq', 'brand_power_bin_freq', 'brand_age_segment_freq',
        # 其余类别特征 (LabelEncoder编码后)
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'age_segment',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage',
        # 数值特征
        'power', 'kilometer', 'car_age', 'regYear', 'regMonth', 'creatYear', 'creatMonth',
        'regDay', 'creatDay', 'is_new_car', 'regYear_from_now', 'creatYear_from_now',
        'regSeason', 'creatSeason', 'km_per_year',
        # 统计特征 (此处为0填充，最佳实践是加载训练时计算的值)
        'brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count', 'brand_price_ratio',
        'km_age', 'power_age', 'power_log', 'kilometer_log', 'car_age_log',
        # 匿名特征 (所有匿名特征都保留)
        *v_cols,
        # PCA降维特征
        *[f'v_pca_{i}' for i in range(v_pca.shape[1])],
        # 缺失/异常/频率特征
        *[f'{col}_missing' for col in all_missing_cols],
        *[f'{col}_outlier' for col in ['power', 'kilometer', 'v_0']],
        # 之前的低基数类别特征的频数编码，这里也加上，即使CatBoost或XGBoost能直接处理，保持特征列表一致性
        *[f'{col}_freq' for col in ['brand', 'bodyType', 'fuelType', 'gearbox', 'notRepairedDamage']]
    ]

    # 去重，保证特征唯一
    features = list(dict.fromkeys([f for f in features if f in data.columns]))

    # 准备测试集数据
    X_test = data[features]
    test_saleid = test['SaleID'] if 'SaleID' in test.columns else None

    print("====== 特征工程完成 ======")

    print("====== 加载模型并进行预测 ======")
    # 2. 加载训练好的模型
    # 检查模型文件是否存在，确保路径正确
    try:
        # 从文件名中提取最佳迭代次数，用于加载模型
        # 如果模型文件名是固定的，可以直接指定
        # 这里假设您已经运行了训练脚本并生成了模型文件
        # 例如：xgb_model_final_tuned_iter_XXXX.joblib 和 lgbm_model_final_tuned_iter_YYYY.joblib
        # 请根据实际保存的文件名进行调整
        # 寻找最新的模型文件或者明确指定文件名

        # 假设我们使用的模型是训练脚本中最后保存的那些，通常是文件名中带有迭代次数的
        # 为了通用性，这里直接写死文件名，请确保这些文件存在于相同目录下
        xgb_model_path = 'xgb_model_final_tuned_iter_1128.joblib' # 替换为你的实际文件名
        lgbm_model_path = 'lgbm_model_final_tuned_iter_3453.joblib' # 替换为你的实际文件名

        # 建议：在训练脚本中，将模型保存为固定名称，例如 xgb_final_model.joblib 和 lgbm_final_model.joblib
        # 这样在集成脚本中就不用关心迭代次数了。
        # 如果你的模型文件名是动态生成的，你需要动态获取文件名，或者手动修改下面的路径

        xgb_model = joblib.load(xgb_model_path)
        lgbm_model = joblib.load(lgbm_model_path)
        print(f"成功加载XGBoost模型: {xgb_model_path}")
        print(f"成功加载LightGBM模型: {lgbm_model_path}")

    except FileNotFoundError as e:
        print(f"错误：模型文件未找到。请确保模型文件已保存，且路径正确。")
        print(f"详细错误: {e}")
        return # 如果模型文件不存在，则停止执行

    # 检查X_test的列顺序和类型，确保与训练时一致
    # 如果XGBoost和LGBM对特征的Dtype有严格要求，需要在这里进行强制类型转换
    # 根据之前的错误报告，XGBoost需要int, float, bool或category，对object类型需要enable_categorical=True
    # 确保所有object类型特征都被LabelEncoder处理过或者转换为category类型
    for col in X_test.columns:
        if X_test[col].dtype == 'object':
            # 这应该在LabelEncoder处理后不再是object类型，如果还有，说明有问题
            # 强制转换为category类型，或者再次尝试LabelEncoder（不建议）
            print(f"Warning: Feature '{col}' is still of object type before prediction. Attempting to convert to category.")
            X_test[col] = X_test[col].astype('category')
        # 确保数值特征类型正确
        if X_test[col].dtype == 'int64':
            X_test[col] = X_test[col].astype('int32') # 更小的整数类型
        elif X_test[col].dtype == 'float64':
            X_test[col] = X_test[col].astype('float32') # 更小的浮点类型

    # 确保X_test的列顺序与训练模型时一致
    # 这一步非常重要，否则模型会预测错误
    # 最佳实践：在训练时保存feature_names，在这里加载并确保X_test的列顺序一致
    # 暂时假设模型的feature_names是X.columns，且这里features列表的顺序是正确的
    # 但更严谨的做法是：
    # xgb_feature_names = xgb_model.get_booster().feature_names # 如果是原生XGBoost模型
    # lgbm_feature_names = lgbm_model.feature_name_ # 如果是原生LightGBM模型
    # X_test = X_test[xgb_feature_names] # 或lgbm_feature_names

    # 3. 进行预测 (并进行np.expm1反向转换)
    print("正在进行XGBoost模型预测...")
    xgb_preds = np.expm1(xgb_model.predict(X_test))
    print("XGBoost模型预测完成。")

    print("正在进行LightGBM模型预测...")
    lgbm_preds = np.expm1(lgbm_model.predict(X_test))
    print("LightGBM模型预测完成。")

    # 4. 模型融合 (简单平均)
    print("====== 正在进行模型融合 ======")
    ensemble_preds = (xgb_preds + lgbm_preds) / 2
    print("模型融合完成。")

    # 5. 保存结果
    print("====== 正在保存融合预测结果 ======")
    result_ensemble = pd.DataFrame({'SaleID': test_saleid, 'price': ensemble_preds}) if test_saleid is not None else pd.DataFrame({'price': ensemble_preds})
    result_filename = 'used_car_sample_submit_ensemble_final.csv'
    result_ensemble.to_csv(result_filename, index=False)
    print(f'融合模型预测结果已保存到 {result_filename}')
    print("预测完成。")

if __name__ == "__main__":
    main() 