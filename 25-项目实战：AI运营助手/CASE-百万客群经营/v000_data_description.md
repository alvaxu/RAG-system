# 数据表结构说明

本文档详细说明了客户经营分析项目中使用的两个核心数据表的结构。这些数据用于客户分层分析、预测模型构建和精准营销策略制定。

## 1. 客户基础信息表 (customer_base.csv)

该表包含了客户的基本信息，用于构建客户画像和分层分析。

| 字段名 | 字段说明 | 示例值 | 备注 |
|--------|----------|--------|------|
| customer_id | 客户唯一标识 | 316d72c0795f4fa9a61aeb8804c21b8f | 系统生成的唯一ID |
| name | 客户姓名 | 王丹 | 客户基本信息 |
| age | 客户年龄 | 49 | 用于年龄分布分析 |
| gender | 性别 | 男/女 | 人口统计特征 |
| occupation | 职业 | - | 具体职业名称 |
| occupation_type | 职业类型 | - | 职业的分类类型 |
| monthly_income | 月收入 | - | 收入水平分析 |
| open_account_date | 开户日期 | - | 客户生命周期分析 |
| lifecycle_stage | 生命周期阶段 | 新客户/成长客户/成熟客户/忠诚客户 | 客户价值阶段划分 |
| marriage_status | 婚姻状况 | 已婚/未婚 | 家庭特征分析 |
| city_level | 城市等级 | 一线城市 | 地域分布分析 |
| branch_name | 开户网点 | 招商银行上海分行外滩支行 | 网点分布分析 |

## 2. 客户行为与资产表 (customer_behavior_assets.csv)

该表记录了客户的资产情况和行为特征，用于预测模型构建和营销策略制定。

| 字段名 | 字段说明 | 示例值 | 备注 |
|--------|----------|--------|------|
| id | 记录唯一标识 | 57effb3e08b6423c86aba6fd6db09bbf | 系统生成的唯一ID |
| customer_id | 客户唯一标识 | 316d72c0795f4fa9a61aeb8804c21b8f | 关联客户基础信息表 |
| total_assets | 总资产 | 72080.23 | 客户资产规模 |
| deposit_balance | 存款余额 | - | 存款类资产 |
| financial_balance | 理财余额 | - | 理财类资产 |
| fund_balance | 基金余额 | - | 基金类资产 |
| insurance_balance | 保险余额 | - | 保险类资产 |
| asset_level | 资产等级 | - | 资产分层标识 |
| deposit_flag | 存款标志 | - | 是否有存款产品 |
| financial_flag | 理财标志 | - | 是否有理财产品 |
| fund_flag | 基金标志 | - | 是否有基金产品 |
| insurance_flag | 保险标志 | - | 是否有保险产品 |
| product_count | 产品持有数 | - | 客户产品覆盖度 |
| financial_repurchase_count | 理财复购次数 | - | 理财产品复购行为 |
| credit_card_monthly_expense | 信用卡月消费 | - | 消费能力指标 |
| investment_monthly_count | 月投资次数 | - | 投资活跃度 |
| app_login_count | APP登录次数 | - | 线上活跃度 |
| app_financial_view_time | APP理财页面浏览时长 | - | 理财兴趣度 |
| app_product_compare_count | APP产品对比次数 | - | 产品研究深度 |
| last_app_login_time | 最近APP登录时间 | - | 活跃时间 |
| last_contact_time | 最近联系时间 | - | 营销触达时间 |
| contact_result | 联系结果 | 未接通/成功/NaN | 营销效果 |
| marketing_cool_period | 营销冷却期 | 2024-07-14 | 下次可营销时间 |
| stat_month | 统计月份 | 2024-07 | 数据统计期间 |

## 数据应用说明

基于项目说明，这些数据将用于：

1. **客户分层分析**
   - 利用资产数据（total_assets及各类资产余额）进行资产分层
   - 结合年龄（age）和职业（occupation）进行人群分布分析
   - 通过lifecycle_stage进行生命周期管理

2. **预测模型构建**
   - 利用客户行为数据（app相关指标、投资行为）
   - 结合资产变动情况预测客户价值
   - 通过contact_result分析营销效果

3. **精准营销策略**
   - 基于客户画像（年龄、职业、婚姻状况等）定制营销方案
   - 结合APP使用行为选择最佳触达时机
   - 通过marketing_cool_period控制营销频率
   - 利用contact_result优化营销策略 

## 字段值说明

### 1. 布尔类型字段（0/1标志）

| 表名 | 字段名 | 值含义 |
|------|--------|--------|
| customer_behavior_assets | deposit_flag | 0: 无存款产品, 1: 有存款产品 |
| customer_behavior_assets | financial_flag | 0: 无理财产品, 1: 有理财产品 |
| customer_behavior_assets | fund_flag | 0: 无基金产品, 1: 有基金产品 |
| customer_behavior_assets | insurance_flag | 0: 无保险产品, 1: 有保险产品 |

### 2. 类别型字段

| 表名 | 字段名 | 可能的值 | 含义说明 |
|------|--------|----------|----------|
| customer_base | gender | 男/女 | 客户性别 |
| customer_base | lifecycle_stage | 新客户/成长客户/成熟客户/忠诚客户 | 客户生命周期阶段 |
| customer_base | marriage_status | 已婚/未婚 | 婚姻状况 |
| customer_base | city_level | 一线城市/二线城市/三线城市/其他 | 城市等级分类 |
| customer_behavior_assets | asset_level | 普通客户/中端客户/高端客户/私人银行 | 资产等级分类 |
| customer_behavior_assets | contact_result | 成功/未接通/NaN | 营销联系结果，NaN表示未联系 |

## 数据类型对应关系

### 1. customer_base表字段类型映射

| 字段名 | CSV数据类型 | Oracle数据类型 | 说明 |
|--------|------------|----------------|------|
| customer_id | object(str) | VARCHAR2(32) | 客户唯一标识 |
| name | object(str) | VARCHAR2(32) | 客户姓名 |
| age | int64 | NUMBER(3) | 客户年龄 |
| gender | object(str) | VARCHAR2(4) | 性别 |
| occupation | object(str) | VARCHAR2(32) | 职业 |
| occupation_type | object(str) | VARCHAR2(32) | 职业类型 |
| monthly_income | float64 | NUMBER(12,2) | 月收入 |
| open_account_date | object(str) | DATE | 开户日期 |
| lifecycle_stage | object(str) | VARCHAR2(16) | 生命周期阶段 |
| marriage_status | object(str) | VARCHAR2(8) | 婚姻状况 |
| city_level | object(str) | VARCHAR2(16) | 城市等级 |
| branch_name | object(str) | VARCHAR2(64) | 开户网点 |

### 2. customer_behavior_assets表字段类型映射

| 字段名 | CSV数据类型 | Oracle数据类型 | 说明 |
|--------|------------|----------------|------|
| id | object(str) | VARCHAR2(32) | 记录唯一标识 |
| customer_id | object(str) | VARCHAR2(32) | 客户唯一标识 |
| total_assets | float64 | NUMBER(20,2) | 总资产 |
| deposit_balance | float64 | NUMBER(20,2) | 存款余额 |
| financial_balance | float64 | NUMBER(20,2) | 理财余额 |
| fund_balance | float64 | NUMBER(20,2) | 基金余额 |
| insurance_balance | float64 | NUMBER(20,2) | 保险余额 |
| asset_level | object(str) | VARCHAR2(16) | 资产等级 |
| deposit_flag | int64 | NUMBER(1) | 存款标志 |
| financial_flag | int64 | NUMBER(1) | 理财标志 |
| fund_flag | int64 | NUMBER(1) | 基金标志 |
| insurance_flag | int64 | NUMBER(1) | 保险标志 |
| product_count | int64 | NUMBER(4) | 产品持有数 |
| financial_repurchase_count | int64 | NUMBER(6) | 理财复购次数 |
| credit_card_monthly_expense | float64 | NUMBER(12,2) | 信用卡月消费 |
| investment_monthly_count | int64 | NUMBER(6) | 月投资次数 |
| app_login_count | int64 | NUMBER(6) | APP登录次数 |
| app_financial_view_time | int64 | NUMBER(10,2) | APP理财页面浏览时长 |
| app_product_compare_count | int64 | NUMBER(6) | APP产品对比次数 |
| last_app_login_time | object(str) | TIMESTAMP | 最近APP登录时间 |
| last_contact_time | object(str) | TIMESTAMP | 最近联系时间 |
| contact_result | object(str) | VARCHAR2(16) | 联系结果 |
| marketing_cool_period | object(str) | DATE | 营销冷却期 |
| stat_month | object(str) | VARCHAR2(7) | 统计月份 |

### 数据类型转换说明

1. 字符串类型(object)：转换为VARCHAR2，长度根据实际数据长度设置
2. 整数类型(int64)：根据数值范围转换为相应精度的NUMBER
3. 浮点数类型(float64)：转换为带小数位的NUMBER
4. 日期时间类型：
   - 日期转换为DATE
   - 时间戳转换为TIMESTAMP
5. 布尔标志：使用NUMBER(1)存储，值为0或1 