'''
程序说明：
## 1. 本程序用于辅助数据预处理建议书的细化，检查部分需确认的数据项。
## 2. 包含user_id与EmployeeNumber一致性、常数字段唯一值、数值型字段极端值、类别型字段一致性等检查。
'''
import pandas as pd

# 读取数据
df_train = pd.read_csv('train.csv', encoding='utf-8')
df_test = pd.read_csv('test.csv', encoding='utf-8')

print('【1】user_id 与 EmployeeNumber 是否完全一致')
print('训练集:', (df_train['user_id'] == df_train['EmployeeNumber']).all())
print('测试集:', (df_test['user_id'] == df_test['EmployeeNumber']).all())

print('\n【2】EmployeeCount、Over18、StandardHours 字段唯一值检查')
for col in ['EmployeeCount', 'Over18', 'StandardHours']:
    print(f'{col} 训练集唯一值:', df_train[col].unique())
    print(f'{col} 测试集唯一值:', df_test[col].unique())

print('\n【3】数值型字段极端值检查')
for col in ['MonthlyIncome', 'DistanceFromHome']:
    print(f'字段 {col} 的描述性统计:')
    print(df_train[col].describe())

print('\n【4】类别型字段在训练集和测试集的取值是否完全一致')
cat_cols = ['BusinessTravel', 'Department', 'EducationField', 'Gender', 'JobRole', 'MaritalStatus', 'OverTime']
for col in cat_cols:
    train_set = set(df_train[col].unique())
    test_set = set(df_test[col].unique())
    print(f'字段 {col} 训练集类别: {train_set}')
    print(f'字段 {col} 测试集类别: {test_set}')
    print(f'字段 {col} 取值是否完全一致: {train_set == test_set}\n') 