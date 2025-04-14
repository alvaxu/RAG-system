# 保单数据分析报告

## policy_data.xlsx前5行数据
```
   policy_id  age gender birth_region  ... policy_start_date policy_end_date claim_history renewal
0      10001   56      男          湖北省  ...        2015-01-17      2035-01-17             否     Yes
1      10002   69      男      香港特别行政区  ...        2015-05-20      2035-05-20             是     Yes
2      10003   46      男          青海省  ...        2021-06-10      2031-06-10             是     Yes
3      10004   32      女          河北省  ...        2017-01-29      2027-01-29             否     Yes
4      10005   60      男          陕西省  ...        2013-06-04      2033-06-04             否     Yes

[5 rows x 17 columns]
```

## 数据基本信息

### policy_data.xlsx
- 数据维度: (1000, 17)
- 列名:
  - policy_id
  - age
  - gender
  - birth_region
  - insurance_region
  - income_level
  - education_level
  - occupation
  - marital_status
  - family_members
  - policy_type
  - policy_term
  - premium_amount
  - policy_start_date
  - policy_end_date
  - claim_history
  - renewal

### policy_test.xlsx
- 数据维度: (200, 16)
- 列名:
  - policy_id
  - age
  - gender
  - birth_region
  - insurance_region
  - income_level
  - education_level
  - occupation
  - marital_status
  - family_members
  - policy_type
  - policy_term
  - premium_amount
  - policy_start_date
  - policy_end_date
  - claim_history

## 数据分析建议

根据数据的基本信息，这些数据可以用于：
1. 保单数据分析：分析保单的基本特征和分布情况
2. 客户行为分析：研究客户的保单购买行为和偏好
3. 风险预测：基于历史数据预测保单风险
4. 客户分群：对客户进行分群，制定差异化营销策略
5. 续保预测：预测客户续保的可能性
