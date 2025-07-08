import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 指定中文字体为黑体
matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

"""
:function: 对二手车数据集进行探索性数据分析（EDA），并将主要分析结果可视化到一张图片上
:param 无
:return: 无
"""
def eda_used_car():
    # 读取数据，分隔符为空格
    df = pd.read_csv('used_car_train_20200313.csv', sep=' ')

    # 设置画布，2行3列布局
    plt.figure(figsize=(18, 10))

    # 1. 价格分布
    plt.subplot(2, 3, 1)
    sns.histplot(df['price'], bins=50, kde=True, color='skyblue')
    plt.title('价格分布')
    plt.xlabel('price')

    # 2. 注册年份分布
    plt.subplot(2, 3, 2)
    reg_year = df['regDate'].astype(str).str[:4].astype(int)
    sns.histplot(reg_year, bins=30, kde=False, color='orange')
    plt.title('注册年份分布')
    plt.xlabel('注册年份')

    # 3. 行驶公里数分布
    plt.subplot(2, 3, 3)
    sns.histplot(df['kilometer'], bins=30, kde=True, color='green')
    plt.title('行驶公里数分布')
    plt.xlabel('kilometer (万公里)')

    # 4. 品牌分布（展示前10品牌）
    plt.subplot(2, 3, 4)
    top_brands = df['brand'].value_counts().head(10)
    sns.barplot(x=top_brands.index, y=top_brands.values, palette='Blues_d')
    plt.title('品牌分布（Top10）')
    plt.xlabel('brand')
    plt.ylabel('数量')

    # 5. 缺失值统计
    plt.subplot(2, 3, 5)
    na_counts = df.isnull().sum()
    na_counts = na_counts[na_counts > 0]
    if not na_counts.empty:
        sns.barplot(x=na_counts.index, y=na_counts.values, palette='Reds')
        plt.title('缺失值统计')
        plt.ylabel('缺失数量')
        plt.xticks(rotation=45)
    else:
        plt.text(0.5, 0.5, '无缺失值', ha='center', va='center', fontsize=16)
        plt.axis('off')

    # 6. 车身类型分布
    plt.subplot(2, 3, 6)
    if 'bodyType' in df.columns:
        bodytype_counts = df['bodyType'].value_counts().sort_index()
        sns.barplot(x=bodytype_counts.index.astype(str), y=bodytype_counts.values, palette='Purples')
        plt.title('车身类型分布')
        plt.xlabel('bodyType')
        plt.ylabel('数量')
    else:
        plt.text(0.5, 0.5, '无bodyType字段', ha='center', va='center', fontsize=16)
        plt.axis('off')

    plt.tight_layout()
    plt.savefig('eda_summary.png', dpi=150)
    plt.show()

if __name__ == "__main__":
    eda_used_car() 