# XGBoost模型特征工程详解（4.1.1model_xgb_more_feature.py）

本文件详细介绍了用于XGBoost模型训练的特征工程步骤。目标是利用原始数据构建出更具表达能力和预测能力的特征，以提升模型性能。

## 1. 数据读取与基础处理

- **数据读取**: 读取 `used_car_train_20200313.csv` 作为训练集，`used_car_testB_20200421.csv` 作为测试集。
- **合并数据集**: 为了保持特征工程的一致性，将训练集和测试集通过 `pd.concat` 合并。测试集的 `price` 列被初始化为 `-1` 以区分训练集。

## 2. 时间特征处理

时间特征的提取和转化对于理解车辆使用情况至关重要。

- **日期转换**: `regDate` (注册日期) 和 `creatDate` (创建日期) 从整数格式转换为 `datetime` 对象 (`regDate_dt`, `creatDate_dt`)。
- **车辆使用年限 (`car_age_days`, `car_age`)**:
    - `car_age_days`: `creatDate_dt` 减去 `regDate_dt` 得到车辆已使用天数。
    - `car_age`: `car_age_days` 除以 365.25 得到车辆使用年限（年）。
    - **缺失值/负值处理**: 对 `car_age` 列，如果出现缺失值（`pd.isnull(x)`）或负值（`x < 0`），则填充为该列的中位数。
- **年份、月份、日期提取**: 从 `regDate_dt` 和 `creatDate_dt` 中分别提取 `regYear`, `regMonth`, `regDay`, `creatYear`, `creatMonth`, `creatDay`。
- **是否为新车 (`is_new_car`)**: 基于 `car_age` 是否小于 1 年创建二元特征。
- **相对年份特征**: 计算 `regYear_from_now` (当前年份 - 注册年份) 和 `creatYear_from_now` (当前年份 - 创建年份)。
- **季节特征**: 根据月份 (`regMonth`, `creatMonth`) 计算 `regSeason` 和 `creatSeason`。
- **每年行驶公里数 (`km_per_year`)**: `kilometer` 除以 `car_age`（加上一个小的平滑项 0.1 避免除以零）。
- **分段特征**:
    - `age_segment`: 车辆年龄 `car_age` 分为 `['0-1年', '1-3年', '3-5年', '5-10年', '10年以上']` 几个段。
    - `regYear_bin`: 注册年份 `regYear` 进行分段。
    - `km_bin`: 公里数 `kilometer` 进行分段。
    - `power_bin`: 功率 `power` 进行分段。
- **品牌与分段特征交互**:
    - `brand_km_bin`: `brand` 和 `km_bin` 的组合。
    - `brand_power_bin`: `brand` 和 `power_bin` 的组合。
    - `brand_age_segment`: `brand` 和 `age_segment` 的组合。
    - `brand_regYear_bin`: `brand` 和 `regYear_bin` 的组合。

## 3. 缺失值处理与缺失标记优化

对于包含缺失值的特征，程序采用中位数或众数填充，并为每个缺失特征创建了对应的缺失标记列。

- **缺失特征列表**: `all_missing_cols` 包含了可能存在缺失值的特征。
- **缺失标记**: 对 `all_missing_cols` 中的每个特征 `col`，创建一个新的二元特征 `f'{col}_missing'`，如果 `col` 缺失则为 1，否则为 0。
- **缺失值填充**:
    - **数值型特征**: 使用该特征的中位数 (`median()`) 进行填充。
    - **类别型特征**: 使用该特征的众数 (`mode()[0]`) 进行填充。

## 4. 异常值处理与标记

此部分主要针对训练集进行异常值处理，并为异常值创建标记。

- **价格异常值剔除**: 移除训练集中 `price` 不在 [100, 100000] 范围内的记录。
- **功率异常值剔除**: 移除训练集中 `power` 不在 (0, 600) 范围内的记录。
- **公里数异常值剔除**: 移除训练集中 `kilometer` 不在 (0, 15] 范围内的记录。
- **异常值标记与裁剪**: 对于 `power`, `kilometer`, `v_0` 这三个特征：
    - 计算其 5% 和 95% 分位数 (`Q1`, `Q3`) 及四分位距 (`IQR`)。
    - 创建二元特征 `f'{col}_outlier'`，标记是否为异常值（超出 \(Q1 - 1.5 \times IQR\) 或 \(Q3 + 1.5 \times IQR\) 的范围）。
    - 将特征值裁剪 (`clip`) 到 \(Q1 - 1.5 \times IQR\) 和 \(Q3 + 1.5 \times IQR\) 之间。

## 5. 统计特征

利用 `brand` 特征，计算其在训练集上对应 `price` 的统计量，并合并回 `data`。

- **品牌价格统计**:
    - 计算每个 `brand` 的 `price` 均值 (`brand_price_mean`)、中位数 (`brand_price_median`)、标准差 (`brand_price_std`) 和计数 (`brand_price_count`)。这些统计量仅基于训练集数据计算。
    - 将这些统计特征通过 `brand` 合并到主 `data` DataFrame。
- **品牌价格比率**: `brand_price_ratio` (`brand_price_mean` 除以所有品牌 `brand_price_mean` 的均值)。
- **统计特征保存**: `train_brand_stats.joblib` 保存了训练集的品牌统计信息，以便在预测时使用。

## 6. 特征交互（交叉特征）

创建额外的交互特征以捕捉变量之间的非线性关系。

- `brand_model`: `brand` 和 `model` 的组合。
- `brand_bodyType`: `brand` 和 `bodyType` 的组合。
- `brand_regYear_bin`: `brand` 和 `regYear_bin` 的组合。
- **数值交互特征**:
    - `km_age`: `kilometer` 和 `car_age` 的乘积。
    - `power_age`: `power` 和 `car_age` 的乘积。
- **对数转换**: 对 `power`, `kilometer`, `car_age` 进行 `np.log1p` 对数转换，生成 `power_log`, `kilometer_log`, `car_age_log`，以处理偏斜分布的数值特征。

## 7. 类别特征编码

采用不同的策略处理高基数和低基数的类别特征。

### 高基数类别特征频数编码

- **高基数特征列表**: `high_card_cols` 包含 `model`, `brand_model`, `brand_power_bin`, `brand_age_segment`。
- **频数编码**: 对每个高基数特征，计算其每个类别的出现频率，并将原始特征替换为该频率值。
- **频数编码映射保存**: 每个频数编码映射都保存为 `f'{col}_freq_encoding_map.joblib'`，以确保预测时的一致性。

### 其余类别特征用LabelEncoder

- **类别特征列表**: `categorical_features` 包含除高基数特征外的其他类别特征。
- **LabelEncoder编码**: 对这些特征使用 `LabelEncoder` 将其转换为数值型。
- **LabelEncoder实例保存**: 每个 `LabelEncoder` 实例都保存为 `f'{col}_label_encoder.joblib'`，以确保预测时的一致性。

## 8. 匿名特征及PCA降维

对匿名特征 `v_0` 到 `v_14` 进行PCA降维。

- **匿名特征列表**: `v_cols` 包含了 `v_0` 到 `v_14`。
- **PCA降维**: 使用 `PCA(n_components=10)` 将这15个匿名特征降维到10个主成分。
- **新特征**: 降维后的特征命名为 `v_pca_0` 到 `v_pca_9`。
- **PCA模型保存**: `pca_model.joblib` 保存了训练好的PCA模型，以确保预测时的一致性。

## 9. 数值归一化（StandardScaler）

对所有数值特征进行标准化处理。

- **数值特征列表**: `num_cols` 包含了原始数值特征、对数转换特征、交互特征和PCA降维特征。
- **标准化**: 使用 `StandardScaler` 对这些数值特征进行Z-score标准化（均值为0，方差为1）。
- **StandardScaler模型保存**: `scaler_model.joblib` 保存了训练好的StandardScaler模型，以确保预测时的一致性。

## 10. 最终特征列表与数据准备

- **特征汇总**: `features` 列表汇总了所有经过特征工程处理后的特征，包括频数编码特征、LabelEncoder编码特征、数值特征、匿名特征、PCA降维特征、缺失标记特征和异常值标记特征。
- **特征去重**: 使用 `list(dict.fromkeys(...))` 对 `features` 列表进行去重，并确保所有特征列都存在于 `data` DataFrame 中。
- **训练集/测试集划分**: 将 `data` 重新划分为 `train` 和 `test`。
    - `X` 为训练集的特征，`y` 为训练集的 `price`。
    - `X_test` 为测试集的特征。
- **数据类型检查与转换**: 再次检查 `X` 和 `X_test` 中的特征数据类型，确保所有 `object` 类型（如果存在）都被正确转换为数值类型（例如 `float`），尽管前面的LabelEncoder应该已经处理了大部分类别特征。

通过以上全面而细致的特征工程步骤，数据集被转化为更适合XGBoost模型训练的格式，旨在提升模型的预测准确性和鲁棒性。 