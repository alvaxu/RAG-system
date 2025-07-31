'''
程序说明：
## 1. 本程序实现员工离职预测数据的特征工程，包括字段筛选、编码、归一化等。
## 2. 支持调试模式（仅输出部分特征/样本）和正式模式（全量输出）。
'''
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, LabelEncoder, MinMaxScaler
import numpy as np

# 是否调试模式（True只输出前100行和部分特征，False输出全部）
DEBUG = False

# 读取数据
df_train = pd.read_csv('train.csv', encoding='utf-8')
df_test = pd.read_csv('test.csv', encoding='utf-8')

# 1. 删除常数字段
const_cols = ['EmployeeCount', 'Over18', 'StandardHours']
df_train = df_train.drop(columns=const_cols)
df_test = df_test.drop(columns=const_cols)

# 2. 保留user_id，EmployeeNumber作为普通特征
id_col = 'user_id'
emp_col = 'EmployeeNumber'

# 3. 目标字段编码（训练集）
if 'Attrition' in df_train.columns:
    df_train['Attrition'] = df_train['Attrition'].map({'No': 0, 'Yes': 1})

# 4. 类别型变量编码
cat_cols = ['BusinessTravel', 'Department', 'EducationField', 'Gender', 'JobRole', 'MaritalStatus', 'OverTime']
# Gender, OverTime二值编码
for col in ['Gender', 'OverTime']:
    for df in [df_train, df_test]:
        if col in df.columns:
            df[col] = df[col].map({'Male': 1, 'Female': 0, 'Yes': 1, 'No': 0})
# 其余类别型变量OneHot编码
onehot_cols = [c for c in cat_cols if c not in ['Gender', 'OverTime']]
all_data = pd.concat([df_train, df_test], axis=0, ignore_index=True)
onehot = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
onehot.fit(all_data[onehot_cols])
train_onehot = onehot.transform(df_train[onehot_cols])
test_onehot = onehot.transform(df_test[onehot_cols])
onehot_feature_names = onehot.get_feature_names_out(onehot_cols)
# 拼接回原数据
df_train_onehot = pd.DataFrame(train_onehot, columns=onehot_feature_names, index=df_train.index)
df_test_onehot = pd.DataFrame(test_onehot, columns=onehot_feature_names, index=df_test.index)
df_train = pd.concat([df_train.drop(columns=onehot_cols), df_train_onehot], axis=1)
df_test = pd.concat([df_test.drop(columns=onehot_cols), df_test_onehot], axis=1)

# 5. 有序型字段直接保留为数值型
# 6. 数值型字段归一化（可选）
num_cols = [c for c in df_train.columns if c not in [id_col, emp_col, 'Attrition'] and df_train[c].dtype in [np.int64, np.float64]]
scaler = MinMaxScaler()
scaler.fit(pd.concat([df_train[num_cols], df_test[num_cols]], axis=0))
df_train_norm = df_train.copy()
df_test_norm = df_test.copy()
df_train_norm[num_cols] = scaler.transform(df_train[num_cols])
df_test_norm[num_cols] = scaler.transform(df_test[num_cols])

# 7. 输出结果
if DEBUG:
    print('【调试模式】仅输出前100行和部分特征')
    print(df_train.head(3))
    print(df_train_norm.head(3))
    df_train.iloc[:100].to_csv('V102_train_feature_debug.csv', index=False, encoding='utf-8')
    df_test.iloc[:100].to_csv('V102_test_feature_debug.csv', index=False, encoding='utf-8')
    df_train_norm.iloc[:100].to_csv('V102_train_feature_norm_debug.csv', index=False, encoding='utf-8')
    df_test_norm.iloc[:100].to_csv('V102_test_feature_norm_debug.csv', index=False, encoding='utf-8')
else:
    df_train.to_csv('V102_train_feature.csv', index=False, encoding='utf-8')
    df_test.to_csv('V102_test_feature.csv', index=False, encoding='utf-8')
    df_train_norm.to_csv('V102_train_feature_norm.csv', index=False, encoding='utf-8')
    df_test_norm.to_csv('V102_test_feature_norm.csv', index=False, encoding='utf-8')

print('特征工程处理完成，输出文件见当前目录。') 