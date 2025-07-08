# 二手车数据集详细EDA分析报告

本次EDA分析基于如下数据与信息：
- 训练集：`used_car_train_20200313.csv`
- 测试集：`used_car_testB_20200421.csv`
- 字段说明：`Field Description.txt`
- 特征工程统计：`6.3_blending_100_features.txt`
- XGBoost特征重要性Top50图：`6.3_blending_100_importance_top50.png`

---

## 1. 字段与数据结构总览

| 字段名                | 含义说明                     | 类型/范围         |
|----------------------|-----------------------------|-------------------|
| SaleID               | 交易ID，唯一编码             | int              |
| name                 | 汽车交易名称，已脱敏         | str              |
| regDate              | 汽车注册日期（YYYYMMDD）     | int/str          |
| model                | 车型编码，已脱敏             | int/float        |
| brand                | 汽车品牌，已脱敏             | int              |
| bodyType             | 车身类型（0-7）              | int, 8类         |
| fuelType             | 燃油类型（0-6）              | int, 7类         |
| gearbox              | 变速箱（0手动/1自动）         | int, 2类         |
| power                | 发动机功率 [0,600]           | int/float        |
| kilometer            | 行驶公里（单位万km）          | float            |
| notRepairedDamage    | 是否有未修复损坏（0/1）       | int/str          |
| regionCode           | 地区编码，已脱敏              | int              |
| seller               | 销售方（0/1）                | int              |
| offerType            | 报价类型（0/1）              | int              |
| creatDate            | 上线时间（YYYYMMDD）          | int/str          |
| price                | 交易价格（预测目标）          | int              |
| v0-v14               | 匿名特征，15个float          | float            |

---

## 2. 缺失值与异常值分析

- **缺失值情况**  
  - `notRepairedDamage` 有"-"等缺失标记，需统一填充。
  - `bodyType`、`fuelType`、`gearbox`、`model` 等部分样本有缺失，已在特征工程中用missing特征标记。
  - `kilometer`、`power`、`v0-v14`等无缺失（见统计文件）。

- **异常值情况**  
  - `power` 存在极端大值（最大600），部分样本功率为0或异常高，已在特征工程中用outlier特征标记。
  - `kilometer` 理论范围0-15（万km），实际有部分极小/极大值，需clip或分箱。
  - `price` 目标变量，分布偏态，需log变换。

---

## 3. 数值型特征分布

- **power**  
  - 均值约0.05，std约0.96，min/max为-1.94/6.08（已归一化/变换）。
  - 存在长尾，建议clip或log变换。

- **kilometer**  
  - 13个唯一值，分布较为离散，常见值有5、10、12、15等（万km）。
  - 建议分箱处理。

- **car_age**  
  - 均值约0，std约1，min/max为-2.27/2.54（已归一化）。
  - 车龄分布合理，部分新车/老车需关注。

- **匿名特征v0-v14**  
  - 均为float，分布各异，部分有明显偏态或离群点。
  - 建议PCA降维、归一化、异常值处理。

---

## 4. 类别型特征分布

- **bodyType**  
  - 8类，分布较均匀，部分类别样本较少。

- **fuelType**  
  - 7类，汽油/柴油为主，混合动力/电动较少。

- **gearbox**  
  - 0/1两类，手动/自动比例约1:1。

- **regionCode/brand/model**  
  - 高基数类别，需频数编码/目标编码。

---

## 5. 统计衍生与交互特征

- **品牌均价/中位数/标准差**  
  - `brand_price_mean`、`brand_price_median`、`brand_price_std`，均有较大方差，反映品牌溢价能力。
- **区域品牌均价/标准差**  
  - `region_brand_price_mean`、`region_brand_price_std`，反映地区与品牌的价格分布。
- **交互特征**  
  - `km_age`（公里数×车龄）、`power_age`（功率×车龄）、`power_log`、`kilometer_log`等，提升模型表达力。

---

## 6. 特征重要性分析（结合XGBoost Top50）

- 匿名特征`v_3`、`v_12`、`v_0`、`v_pca_0`等在模型中极为重要。
- 统计衍生特征如`region_brand_price_mean`、`brand_price_std`等也有较高权重。
- 传统特征如`power`、`kilometer`、`regYear`、`car_age`等依然重要。
- 交互特征如`km_age`、`power_log`等有一定贡献。

---

## 7. 可视化建议（图片文件名以eda_开头）

1. **数值型特征分布直方图**  
   - `eda_power_hist.png`、`eda_kilometer_hist.png`、`eda_price_hist.png`、`eda_car_age_hist.png`
2. **类别型特征条形图**  
   - `eda_bodyType_bar.png`、`eda_fuelType_bar.png`、`eda_gearbox_bar.png`
3. **目标变量分布（原始+log）**  
   - `eda_price_dist.png`、`eda_price_log_dist.png`
4. **相关性热力图**  
   - `eda_corr_heatmap.png`
5. **重要特征箱线图/小提琴图**  
   - `eda_v3_box.png`、`eda_region_brand_price_mean_box.png`
6. **品牌/地区均价分布**  
   - `eda_brand_price_mean_bar.png`、`eda_region_brand_price_mean_bar.png`
7. **交互特征与目标的关系**  
   - `eda_km_age_vs_price.png`、`eda_power_log_vs_price.png`

---

## 8. EDA分析结论与特征工程建议

- **缺失与异常需重点处理**：如`notRepairedDamage`、`power`、`kilometer`等。
- **类别高基数需编码**：如`model`、`brand`、`regionCode`等。
- **匿名特征极为重要**，建议保留全部并做降维/归一化。
- **统计衍生与交互特征有效提升模型表现**，应充分挖掘。
- **目标变量强偏态，建议log变换**。
- **可视化有助于发现分布异常、类别不均、特征间关系等问题，指导后续特征工程。**

---

如需自动生成上述可视化图片或进一步分析，请随时告知！ 