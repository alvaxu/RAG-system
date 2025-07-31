# 4.0_deep_tuning_groupmean_best_combine_2(125).py 与 V328_prophet_monthperiod_regressor_full(124).py 预测实现对比

## 1. 核心思想与方法对比

- **4.0_deep_tuning_groupmean_best_combine_2(125).py**
  - 采用分组均值法（Group Mean），即根据多个特征分组后，计算每组的历史均值作为预测。
  - 预测时优先用全分组匹配，若无则降级匹配更少特征，最后用全局均值兜底。
  - 完全是统计型、无参数的传统方法。

- **V328_prophet_monthperiod_regressor_full(124).py**
  - 采用Prophet时间序列建模，属于机器学习/统计建模方法。
  - 在Prophet基础上，加入了month_period（月内分段）one-hot特征作为回归器（regressor），提升对周期性/结构性特征的拟合能力。
  - 具备趋势、季节性、节假日等多种建模能力。

## 2. 特征工程与输入数据对比

- **4.0_deep_tuning_groupmean_best_combine_2(125).py**
  - 特征工程较为丰富，包含：weekday、month_period、is_holiday、is_next_workday、is_month_end、is_quarter_end、is_festival_eve、holiday_len、is_long_holiday等。
  - 预测时分组用到：weekday、month_period、is_holiday、is_next_workday、is_month_end。
  - 输入数据为全量日期（2014-03-01~2014-10-10），特征表与聚合数据合并。

- **V328_prophet_monthperiod_regressor_full(124).py**
  - 特征工程主要关注month_period（月内分段），并对其做one-hot编码。
  - 只用month_period作为回归特征，节假日通过Prophet的holidays参数建模。
  - 输入数据为全量日期（2014-03-01~2014-09-30），并为每一天补齐month_period one-hot特征。

## 3. 模型训练与预测流程对比

- **4.0_deep_tuning_groupmean_best_combine_2(125).py**
  - 训练集：2014-03-01~2014-08-31
  - 预测集：2014-09-01~2014-09-30（输出），但特征表覆盖到2014-10-10
  - 预测流程：对每一天，按分组特征查找历史均值，降级匹配，最后用全局均值。
  - 无需拟合参数，直接统计。

- **V328_prophet_monthperiod_regressor_full(124).py**
  - 训练集：2014-03-01~2014-08-31
  - 预测集：2014-09-01~2014-09-30
  - 预测流程：Prophet模型先用训练集拟合（含month_period回归特征），再对全量日期（含9月）做预测。
  - 需模型训练、参数拟合，预测时需补齐所有回归特征。

## 4. 输出与可视化对比

- **4.0_deep_tuning_groupmean_best_combine_2(125).py**
  - 输出：9月预测结果csv、训练区间RMSE、申购/赎回真实值与预测对比图。
  - 可视化：训练区间的真实值与预测值对比（分组均值法）。

- **V328_prophet_monthperiod_regressor_full(124).py**
  - 输出：9月预测结果csv、申购/赎回真实值与in-sample预测、9月预测对比图、分解图、残差分析图。
  - 可视化：训练区间和9月的真实值、in-sample预测、9月预测，残差分析，Prophet分解图。

## 5. 优缺点分析

| 方法 | 优点 | 缺点 |
|------|------|------|
| 分组均值法 | 简单直观，易于解释，速度快，对数据异常不敏感，特征可灵活组合 | 不能建模趋势、复杂季节性，泛化能力有限，无法外推新周期 |
| Prophet+回归特征 | 能建模趋势、季节性、节假日，支持外生特征，泛化能力强，能外推未来 | 需模型训练，参数敏感，特征工程需谨慎，部分极端情况不如分组均值稳健 |

---

**总结：**
- 分组均值法适合特征分组规律明显、数据量较小、对趋势/季节性要求不高的场景。
- Prophet+回归特征适合趋势、季节性、节假日等多因素影响明显、需外推预测的场景。
- 实际应用中可结合两者优点，或用分组均值法做基线、Prophet做提升。 