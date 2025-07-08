import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import warnings

warnings.filterwarnings('ignore')  # 忽略所有警告

# 读取数据
try:
    df = pd.read_csv('二组模拟数据.csv', encoding='utf-8')
except Exception:
    df = pd.read_csv('二组模拟数据.csv', encoding='gbk')

# 创建产品持有标记
df['deposit_flag'] = (df['deposit_balance'] > 0).astype(int)
df['financial_flag'] = (df['wealth_management_balance'] > 0).astype(int)
df['fund_flag'] = (df['fund_balance'] > 0).astype(int)
df['insurance_flag'] = (df['insurance_balance'] > 0).astype(int)

# 选择产品持有相关字段
product_cols = ['deposit_flag', 'financial_flag', 'fund_flag', 'insurance_flag']

# 只保留产品持有标志（1/0），并去重
basket = df[product_cols].fillna(0).astype(int)
basket = basket.drop_duplicates()

# Apriori算法挖掘频繁项集
frequent_itemsets = apriori(basket, min_support=0.05, use_colnames=True)

# 生成关联规则
rules = association_rules(frequent_itemsets, metric='lift', min_threshold=1.0)

# 输出频繁项集
print('频繁产品组合（min_support=0.05）：')
print(frequent_itemsets.sort_values('support', ascending=False))

# 输出关联规则
print('\n产品组合关联规则：')
print(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']])

# 保存结果
frequent_itemsets.to_csv('frequent_product_itemsets.csv', index=False, encoding='utf-8-sig')
rules.to_csv('product_association_rules.csv', index=False, encoding='utf-8-sig')

# 中文注释：
# 本脚本用于Apriori算法挖掘客户产品持有的频繁组合模式，输出频繁项集和关联规则。 