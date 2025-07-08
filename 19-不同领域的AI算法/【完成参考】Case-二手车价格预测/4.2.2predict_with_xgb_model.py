import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRegressor
import joblib
import matplotlib.pyplot as plt
import matplotlib

"""
:function: 使用预训练的XGBoost模型对测试集进行预测
:param 无
:return: 无
"""
def main():
    # ========== 解决matplotlib中文乱码 (可选，如果需要绘制图表) ==========
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

    # 1. 数据读取
    test = pd.read_csv('used_car_testB_20200421.csv', sep=' ')
    test['price'] = -1 # 添加price列，在concat之前设置为-1
    # 为了进行特征工程，需要一个完整的data帧，这里我们只关心test部分
    # 但为了确保特征工程的一致性，我们需要模拟训练时的数据结构，包括训练集的某些列
    # 最简单的方法是加载一个空的训练集或者只加载测试集，然后进行特征工程
    # 考虑到特征工程中可能依赖训练集的数据（如brand_stats），这里选择将test视为完整数据的一部分进行处理
    # 如果实际训练时是concat了训练集和测试集，这里也需要模拟
    # 这里为了简化，假设测试集自身包含所有进行特征工程所需的信息，如果模型训练依赖全体数据的统计量，则可能需要调整
    data = test.copy() # 只处理测试集数据，不进行与训练集合并

    # ================== 特征工程（与训练时保持一致） ==================
    # 1. 时间特征处理
    data['regDate_dt'] = pd.to_datetime(data['regDate'], format='%Y%m%d', errors='coerce')
    data['creatDate_dt'] = pd.to_datetime(data['creatDate'], format='%Y%m%d', errors='coerce')
    # 车辆使用年限（天/年）
    data['car_age_days'] = (data['creatDate_dt'] - data['regDate_dt']).dt.days
    data['car_age'] = data['car_age_days'] / 365.25
    # 若有负值或缺失，填充为中位数
    # 注意：这里的median_car_age应该和训练集计算的一致，如果训练集有此统计量，建议加载
    # 简单处理，这里用测试集的中位数
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
    current_year = pd.Timestamp.now().year # 假设与训练时运行年份一致
    data['regYear_from_now'] = current_year - data['regYear']
    data['creatYear_from_now'] = current_year - data['creatYear']
    # 季节特征
    data['regSeason'] = data['regMonth'].apply(lambda x: (x%12 + 3)//3)
    data['creatSeason'] = data['creatMonth'].apply(lambda x: (x%12 + 3)//3)
    # 每年行驶的公里数
    data['km_per_year'] = data['kilometer'] / (data['car_age'] + 0.1)
    # 车龄分段
    data['age_segment'] = pd.cut(data['car_age'], bins=[-0.01, 1, 3, 5, 10, 100], labels=['0-1年', '1-3年', '3-5年', '5-10年', '10年以上'], right=True)
    # 注册年份分段
    data['regYear_bin'] = pd.cut(data['regYear'], bins=[1980,1995,2000,2005,2010,2015,2020], labels=False, right=True)
    # 公里数分段
    data['km_bin'] = pd.cut(data['kilometer'], bins=[0,5,10,12,14,15], labels=False, right=True)
    # 功率分段
    data['power_bin'] = pd.cut(data['power'], bins=[0,50,100,150,200,300,600], labels=False, right=True)
    # 品牌与公里数分段
    data['brand_km_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['kilometer'], bins=[0,5,10,12,14,15], labels=False, right=True).astype(str)
    # 品牌与功率分段
    data['brand_power_bin'] = data['brand'].astype(str) + '_' + pd.cut(data['power'], bins=[0,50,100,150,200,300,600], labels=False, right=True).astype(str)
    # 品牌与车龄分段
    data['brand_age_segment'] = data['brand'].astype(str) + '_' + data['age_segment'].astype(str)
    # 品牌与注册年份分段
    data['brand_regYear_bin'] = data['brand'].astype(str) + '_' + data['regYear_bin'].astype(str)

    # ========== 缺失值处理与缺失标记优化 (与训练时保持一致) ==========
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

    # 3. 异常值处理（测试集不需要像训练集那样剔除行，只需要标记和clip）
    for col in ['power', 'kilometer', 'v_0']:
        # 注意：这里的Q1和Q3应该和训练集计算的一致，如果训练集有此统计量，建议加载
        # 简单处理，这里用测试集的Q1和Q3
        Q1 = data[col].quantile(0.05)
        Q3 = data[col].quantile(0.95)
        IQR = Q3 - Q1
        data[f'{col}_outlier'] = ((data[col] < (Q1 - 1.5 * IQR)) | (data[col] > (Q3 + 1.5 * IQR))).astype(int)
        data[col] = data[col].clip(Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)

    # 4. 统计特征（品牌均值/中位数/计数/标准差等）
    # 注意：这里的统计量应该和训练集计算的一致，必须加载训练集计算的统计量
    try:
        train_brand_stats = joblib.load('train_brand_stats.joblib') # 尝试加载训练集的品牌统计信息
    except FileNotFoundError:
        print("错误：未找到 'train_brand_stats.joblib'，请确保模型已保存。")
        return # 终止程序，因为无法保证特征一致性

    data = data.merge(train_brand_stats, on='brand', how='left')
    # 填充NaN值，这些NaN值可能因为测试集中有训练集中没有的品牌导致
    # 这里的填充值也应该和训练集计算的一致，如果训练集有此统计量，建议加载
    # 或者确保训练时统计量填充后，这里对训练集中未出现的品牌进行合理的填充，例如使用全局均值
    for col in ['brand_price_mean', 'brand_price_median', 'brand_price_std', 'brand_price_count']:
        if col in data.columns: # 确保列存在
            # 使用训练集计算的均值/中位数来填充新品牌导致的NaN，这里需要一个默认值，或者加载训练集的全局均值
            # 为了简化，这里暂时使用测试集该列的中位数，但实际应加载训练集的全局中位数
            # 如果训练时这些列没有NaN，这里不应该有NaN，除非测试集有新品牌
            data[col] = data[col].fillna(data[col].median()) # 临时填充，应加载训练集的全局中位数或均值

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

    # ========== 高基数类别特征采用频数编码 (与训练时保持一致) ==========
    high_card_cols = ['model', 'brand_model', 'brand_power_bin', 'brand_age_segment']
    for col in high_card_cols:
        if col in data.columns:
            try:
                freq_encoding_map = joblib.load(f'{col}_freq_encoding_map.joblib')
                data[f'{col}_freq'] = data[col].map(freq_encoding_map).fillna(0) # 未知类别填充0
            except FileNotFoundError:
                print(f"错误：未找到 '{col}_freq_encoding_map.joblib'，请确保模型已保存。")
                return # 终止程序，因为无法保证特征一致性


    # 其余类别特征用LabelEncoder (与训练时保持一致)
    categorical_features = [
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin', 'notRepairedDamage',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'age_segment'
    ]
    for col in categorical_features:
        if col in data.columns:
            try:
                le = joblib.load(f'{col}_label_encoder.joblib')
                # 对于测试集中LabelEncoder未见过的类别，将其映射到一个特殊值（例如-1）
                data[col] = data[col].astype(str).apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
            except FileNotFoundError:
                print(f"错误：未找到 '{col}_label_encoder.joblib'，请确保模型已保存。")
                return # 终止程序，因为无法保证特征一致性

    # ========== 匿名特征及PCA降维 (与训练时保持一致) ==========
    v_cols = [f'v_{i}' for i in range(15)]
    # PCA模型需要加载训练时fit的实例
    try:
        pca = joblib.load('pca_model.joblib')
        v_pca = pca.transform(data[v_cols])
    except FileNotFoundError:
        print("错误：未找到 'pca_model.joblib'，请确保模型已保存。")
        return # 终止程序，因为无法保证特征一致性

    for i in range(v_pca.shape[1]):
        data[f'v_pca_{i}'] = v_pca[:, i]

    # ========== 数值归一化 (与训练时保持一致) ==========
    num_cols = ['power', 'kilometer', 'car_age', 'km_per_year', 'power_log', 'kilometer_log', 'car_age_log', 'km_age', 'power_age'] + [f'v_pca_{i}' for i in range(v_pca.shape[1])]
    # StandardScaler模型需要加载训练时fit的实例
    try:
        scaler = joblib.load('scaler_model.joblib')
        data[num_cols] = scaler.transform(data[num_cols])
    except FileNotFoundError:
        print("错误：未找到 'scaler_model.joblib'，请确保模型已保存。")
        return # 终止程序，因为无法保证特征一致性

    # ========== 最终特征列表 (与训练时保持一致) ==========
    features = [
        # 高基数特征频数编码
        'model_freq', 'brand_model_freq', 'brand_power_bin_freq', 'brand_age_segment_freq',
        # 其余类别特征
        'brand', 'bodyType', 'fuelType', 'gearbox', 'regionCode', 'seller', 'offerType',
        'regYear_bin', 'km_bin', 'power_bin',
        'brand_bodyType', 'brand_regYear_bin', 'brand_km_bin', 'notRepairedDamage',
        'age_segment', # 修正：age_segment应该放在这里，不是其他频数编码部分
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
        *[f'{col}_missing' for col in all_missing_cols if f'{col}_missing' in data.columns],
        *[f'{col}_outlier' for col in ['power', 'kilometer', 'v_0'] if f'{col}_outlier' in data.columns]
    ]
    # 去重，保证特征唯一且存在于数据中
    features = list(dict.fromkeys([f for f in features if f in data.columns]))

    # 提取测试集数据和SaleID
    X_test = data[features]
    test_saleid = data['SaleID'] if 'SaleID' in data.columns else None

    # 检查特征名唯一性，若有重复则去重并打印
    duplicated_cols = X_test.columns[X_test.columns.duplicated()].tolist()
    if len(duplicated_cols) > 0:
        print('存在重复特征名:', duplicated_cols)
        X_test = X_test.loc[:, ~X_test.columns.duplicated()]

    # 确保所有特征列的数据类型是XGBoost支持的数值类型 (LabelEncoder已经处理，此处可能冗余)
    # 如果前面的LabelEncoder和PCA等都正确加载并transform，这里应该不会再有object类型
    # 移除此段，依赖上游特征工程的正确性
    # for col in X_test.columns:
    #     if X_test[col].dtype == 'object':
    #         try:
    #             X_test[col] = X_test[col].astype(float)
    #         except ValueError:
    #             print(f"警告: 测试集列 '{col}' 无法转换为数值类型，请检查。")

    # 加载模型
    try:
        xgb = joblib.load('xgb_model_final_4000.joblib')
        print('模型xgb_model_final_4000.joblib加载成功！')
    except FileNotFoundError:
        print('错误：未找到模型文件 xgb_model_final_4000.joblib，请确保模型已保存。')
        return

    # 预测
    print('开始进行预测...')
    test_pred_log = xgb.predict(X_test)
    test_pred = np.expm1(test_pred_log)

    # 保存预测结果
    result = pd.DataFrame({'SaleID': test_saleid, 'price': test_pred}) if test_saleid is not None else pd.DataFrame({'price': test_pred})
    result.to_csv('xgb_prediction.csv', index=False)
    print('预测结果已保存到 xgb_prediction.csv')

if __name__ == "__main__":
    main() 