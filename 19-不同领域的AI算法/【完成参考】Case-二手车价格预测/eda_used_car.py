# -*- coding: utf-8 -*-
"""
对 used_car_train_20200313.csv 进行基础EDA分析。
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 设置pandas显示所有列
pd.set_option('display.max_columns', None)

# 读取数据，分隔符为空格（支持多个空格）
df = pd.read_csv('used_car_train_20200313.csv', sep='\s+', engine='python')

# 1. 数据基本信息
print('数据行数和列数:', df.shape)
print('字段类型信息:')
print(df.dtypes)

# 2. 缺失值统计
print('\n每列缺失值数量:')
print(df.isnull().sum())

# # 3. 数值型字段描述性统计
# print('\n数值型字段描述性统计:')
# print(df.describe())

# 查看主要类别型变量的分布
cat_cols = ['model', 'brand', 'bodyType', 'fuelType', 'gearbox', 'notRepairedDamage']
for col in cat_cols:
    if col in df.columns:
        print(f'\n{col} 字段的分布:')
        print(df[col].value_counts())

# # 5. 价格分布直方图
# plt.figure(figsize=(8, 5))
# sns.histplot(df['price'], bins=50, kde=True)
# plt.title('二手车价格分布')
# plt.xlabel('价格（元）')
# plt.ylabel('样本数')
# plt.tight_layout()
# plt.savefig('price_hist.png')
# plt.close()

# # 6. 品牌分布条形图
# if 'brand' in df.columns:
#     plt.figure(figsize=(10, 6))
#     brand_counts = df['brand'].value_counts().head(20)
#     sns.barplot(x=brand_counts.index, y=brand_counts.values)
#     plt.title('品牌分布（Top 20）')
#     plt.xlabel('品牌编码')
#     plt.ylabel('样本数')
#     plt.tight_layout()
#     plt.savefig('brand_bar.png')
#     plt.close()

# # 可视化kilometer字段分布
# import matplotlib.pyplot as plt
# import seaborn as sns

# # 强制转换为数值型，无法转换的变为NaN
# km = pd.to_numeric(df['kilometer'], errors='coerce')

# # 直方图
# plt.figure(figsize=(8, 5))
# sns.histplot(km.dropna(), bins=30, kde=True)
# plt.title('kilometer字段分布直方图')
# plt.xlabel('kilometer（万公里）')
# plt.ylabel('样本数')
# plt.tight_layout()
# plt.savefig('kilometer_hist.png')
# plt.close()

# # 箱线图
# plt.figure(figsize=(8, 3))
# sns.boxplot(x=km.dropna())
# plt.title('kilometer字段箱线图')
# plt.xlabel('kilometer（万公里）')
# plt.tight_layout()
# plt.savefig('kilometer_box.png')
# plt.close()

# print('kilometer字段分布图已保存为 kilometer_hist.png 和 kilometer_box.png')

# print('\nEDA分析完成，部分统计图已保存为 price_hist.png 和 brand_bar.png') 