'''
程序说明：
## 1. 读取并展示训练集和测试集的基本信息，包括字段名、数据类型、缺失值统计、类别分布等。
## 2. 便于后续数据预处理和特征工程的理解。
'''
import pandas as pd

# 读取训练集和测试集
df_train = pd.read_csv('train.csv', encoding='utf-8')
df_test = pd.read_csv('test.csv', encoding='utf-8')

print('训练集样本数:', df_train.shape[0], '字段数:', df_train.shape[1])
print('测试集样本数:', df_test.shape[0], '字段数:', df_test.shape[1])

print('\n训练集字段名:')
print(df_train.columns.tolist())
print('\n测试集字段名:')
print(df_test.columns.tolist())

print('\n训练集前5行:')
print(df_train.head())

print('\n训练集各字段数据类型:')
print(df_train.dtypes)

print('\n训练集缺失值统计:')
print(df_train.isnull().sum())

print('\n测试集缺失值统计:')
print(df_test.isnull().sum())

# 展示部分类别型字段的取值分布
cat_cols = ['BusinessTravel', 'Department', 'EducationField', 'Gender', 'JobRole', 'MaritalStatus', 'OverTime']
for col in cat_cols:
    if col in df_train.columns:
        print(f'\n字段【{col}】在训练集中的取值分布:')
        print(df_train[col].value_counts())
    if col in df_test.columns:
        print(f'\n字段【{col}】在测试集中的取值分布:')
        print(df_test[col].value_counts())

print('\n目标字段Attrition分布:')
if 'Attrition' in df_train.columns:
    print(df_train['Attrition'].value_counts()) 