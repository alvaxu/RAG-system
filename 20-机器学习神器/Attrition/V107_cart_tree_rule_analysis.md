'''
程序说明：
## 1. 本文档对CART决策树（深度4）进行规则解读，帮助理解员工离职的主要决策路径。
## 2. 结合可视化图和规则，分层描述每个分支的业务含义。
'''
决策树规则如下：
|--- MonthlyIncome <= 2487.50
|   |--- OverTime <= 0.50
|   |   |--- YearsSinceLastPromotion <= 1.50
|   |   |   |--- StockOptionLevel <= 1.50
|   |   |   |   |--- class: 0
|   |   |   |--- StockOptionLevel >  1.50
|   |   |   |   |--- class: 0
|   |   |--- YearsSinceLastPromotion >  1.50
|   |   |   |--- class: 0
|   |--- OverTime >  0.50
|   |   |--- DailyRate <= 1067.50
|   |   |   |--- NumCompaniesWorked <= 0.50
|   |   |   |   |--- class: 0
|   |   |   |--- NumCompaniesWorked >  0.50
|   |   |   |   |--- class: 1
|   |   |--- DailyRate >  1067.50
|   |   |   |--- MonthlyRate <= 11219.00
|   |   |   |   |--- class: 1
|   |   |   |--- MonthlyRate >  11219.00
|   |   |   |   |--- class: 0
|--- MonthlyIncome >  2487.50
|   |--- OverTime <= 0.50
|   |   |--- EnvironmentSatisfaction <= 1.50
|   |   |   |--- YearsWithCurrManager <= 0.50
|   |   |   |   |--- class: 1
|   |   |   |--- YearsWithCurrManager >  0.50
|   |   |   |   |--- class: 0
|   |   |--- EnvironmentSatisfaction >  1.50
|   |   |   |--- Age <= 32.50
|   |   |   |   |--- class: 0
|   |   |   |--- Age >  32.50
|   |   |   |   |--- class: 0
|   |--- OverTime >  0.50
|   |   |--- MaritalStatus_Single <= 0.50
|   |   |   |--- JobLevel <= 1.50
|   |   |   |   |--- class: 0
|   |   |   |--- JobLevel >  1.50
|   |   |   |   |--- class: 0
|   |   |--- MaritalStatus_Single >  0.50
|   |   |   |--- YearsSinceLastPromotion <= 5.00
|   |   |   |   |--- class: 0
|   |   |   |--- YearsSinceLastPromotion >  5.00
|   |   |   |   |--- class: 1

# 决策树规则文字解释

本决策树以员工的月收入（MonthlyIncome）、加班情况（OverTime）、环境满意度（EnvironmentSatisfaction）、单身状态（MaritalStatus_Single）、最近晋升年限（YearsSinceLastPromotion）等为主要分裂节点，分层判断员工离职风险。

## 第一层分裂
- **MonthlyIncome（月收入）<= 2487.5**：低收入员工更容易被进一步细分为高风险群体。
- **MonthlyIncome > 2487.5**：中高收入员工整体离职风险较低，但仍需结合其他特征判断。

## 第二层分裂
- 对于低收入员工：
  - **OverTime（加班）<= 0.5**（不加班）：离职风险较低。
  - **OverTime > 0.5**（加班）：离职风险显著升高。
- 对于中高收入员工：
  - **OverTime <= 0.5**（不加班）：大部分员工稳定，进一步细分环境满意度、与管理者共事年限、年龄等。
  - **OverTime > 0.5**（加班）：结合单身状态、岗位级别、晋升年限等进一步判断。

## 典型高风险路径举例
1. **低收入 & 加班 & 日工资较高 & 多次换工作**：
   - MonthlyIncome <= 2487.5 且 OverTime > 0.5 且 DailyRate <= 1067.5 且 NumCompaniesWorked > 0.5
   - 这类员工离职概率高。
2. **中高收入 & 加班 & 单身 & 最近5年未晋升**：
   - MonthlyIncome > 2487.5 且 OverTime > 0.5 且 MaritalStatus_Single > 0.5 且 YearsSinceLastPromotion > 5.0
   - 这类员工离职概率高。

## 典型低风险路径举例
1. **中高收入 & 不加班 & 环境满意度高 & 年龄大**：
   - MonthlyIncome > 2487.5 且 OverTime <= 0.5 且 EnvironmentSatisfaction > 1.5 且 Age > 32.5
   - 这类员工离职概率极低。
2. **低收入 & 不加班 & 最近晋升 & 期权较高**：
   - MonthlyIncome <= 2487.5 且 OverTime <= 0.5 且 YearsSinceLastPromotion <= 1.5 且 StockOptionLevel > 1.5
   - 这类员工也较为稳定。

## 主要业务洞察
- **加班**和**低收入**是离职风险的核心驱动因素。
- **频繁换工作**、**单身**、**晋升缓慢**、**环境满意度低**等也会显著提升离职概率。
- **高收入**、**不加班**、**满意度高**、**与管理者共事时间长**、**年龄大**等特征有助于员工留任。

---
如需进一步分析某一分支或结合实际业务场景解读，请随时告知。 