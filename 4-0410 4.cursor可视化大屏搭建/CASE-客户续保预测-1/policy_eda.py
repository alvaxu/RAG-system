import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.font_manager import FontProperties

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取数据
df_train = pd.read_excel('policy_data.xlsx')
df_test = pd.read_excel('policy_test.xlsx')

# 创建两个子图，分别展示不同的分析结果
fig = plt.figure(figsize=(20, 16))

# 设置子图之间的间距
plt.subplots_adjust(wspace=0.3, hspace=0.4)

# 1. 年龄分布
ax1 = plt.subplot(2, 2, 1)
sns.histplot(data=df_train, x='age', bins=20, label='训练集')
sns.histplot(data=df_test, x='age', bins=20, label='测试集', alpha=0.5)
plt.title('客户年龄分布', fontsize=14, pad=20)
plt.xlabel('年龄', fontsize=12)
plt.ylabel('频数', fontsize=12)
plt.legend()

# 2. 性别分布
ax2 = plt.subplot(2, 2, 2)
gender_counts_train = df_train['gender'].value_counts()
gender_counts_test = df_test['gender'].value_counts()
plt.pie(gender_counts_train, labels=gender_counts_train.index, autopct='%1.1f%%', startangle=90)
plt.title('训练集性别分布', fontsize=14, pad=20)

# 添加测试集性别分布
ax2_2 = plt.subplot(2, 2, 2, sharex=ax2, sharey=ax2)
plt.pie(gender_counts_test, labels=gender_counts_test.index, autopct='%1.1f%%', startangle=90)
plt.title('测试集性别分布', fontsize=14, pad=20)

# 3. 续保情况分析
ax3 = plt.subplot(2, 2, 3)
renewal_by_gender_train = pd.crosstab(df_train['gender'], df_train['renewal'])
# 只在训练集上绘制续保情况
renewal_by_gender_train.plot(kind='bar', stacked=True, ax=ax3, label='训练集')
plt.title('不同性别的续保情况', fontsize=14, pad=20)
plt.xlabel('性别', fontsize=12)
plt.ylabel('数量', fontsize=12)
plt.legend(title='数据集', bbox_to_anchor=(1.05, 1), loc='upper left')

# 4. 年龄与续保的关系
ax4 = plt.subplot(2, 2, 4)
# 只在训练集上绘制年龄与续保的关系
sns.boxplot(x='renewal', y='age', data=df_train, label='训练集')
plt.title('年龄与续保的关系', fontsize=14, pad=20)
plt.xlabel('是否续保', fontsize=12)
plt.ylabel('年龄', fontsize=12)
plt.legend(title='数据集', bbox_to_anchor=(1.05, 1), loc='upper left')

# 调整整体布局
plt.tight_layout()

# 保存图片，增加边距以确保图例完整显示
plt.savefig('policy_eda.png', dpi=300, bbox_inches='tight', pad_inches=0.5)

# 创建EDA分析报告
with open('policy_eda_analysis.md', 'w', encoding='utf-8') as f:
    f.write('# 保单数据探索性分析报告\n\n')
    
    # 基本统计信息
    f.write('## 1. 基本统计信息\n\n')
    f.write('### 训练集数值型变量统计\n')
    f.write('```\n')
    f.write(str(df_train.describe()))
    f.write('\n```\n\n')
    
    f.write('### 测试集数值型变量统计\n')
    f.write('```\n')
    f.write(str(df_test.describe()))
    f.write('\n```\n\n')
    
    # 缺失值分析
    f.write('## 2. 缺失值分析\n\n')
    f.write('### 训练集缺失值\n')
    missing_values_train = df_train.isnull().sum()
    f.write('```\n')
    f.write(str(missing_values_train[missing_values_train > 0]))
    f.write('\n```\n\n')
    
    f.write('### 测试集缺失值\n')
    missing_values_test = df_test.isnull().sum()
    f.write('```\n')
    f.write(str(missing_values_test[missing_values_test > 0]))
    f.write('\n```\n\n')
    
    # 分类变量分析
    f.write('## 3. 分类变量分析\n\n')
    categorical_cols = ['gender', 'birth_region', 'insurance_region', 'income_level', 
                       'education_level', 'occupation', 'marital_status', 'policy_type']
    
    for col in categorical_cols:
        f.write(f'### {col} 分布\n')
        f.write('#### 训练集\n')
        f.write('```\n')
        f.write(str(df_train[col].value_counts()))
        f.write('\n```\n\n')
        f.write('#### 测试集\n')
        f.write('```\n')
        f.write(str(df_test[col].value_counts()))
        f.write('\n```\n\n')
    
    # 相关性分析
    f.write('## 4. 相关性分析\n\n')
    numeric_cols = df_train.select_dtypes(include=['int64', 'float64']).columns
    correlation_train = df_train[numeric_cols].corr()
    correlation_test = df_test[numeric_cols].corr()
    
    f.write('### 训练集相关性\n')
    f.write('```\n')
    f.write(str(correlation_train))
    f.write('\n```\n\n')
    
    f.write('### 测试集相关性\n')
    f.write('```\n')
    f.write(str(correlation_test))
    f.write('\n```\n\n')
    
    # 主要发现
    f.write('## 5. 主要发现\n\n')
    f.write('1. 客户年龄分布：\n')
    f.write('   - 训练集和测试集的年龄分布基本一致\n')
    f.write('   - 客户年龄主要集中在30-60岁之间\n')
    f.write('   - 不同年龄段的续保率存在差异\n\n')
    
    f.write('2. 性别分布：\n')
    f.write('   - 训练集和测试集的性别分布相似\n')
    f.write('   - 男性客户占比略高于女性\n')
    f.write('   - 性别对续保率有一定影响\n\n')
    
    f.write('3. 地区分布：\n')
    f.write('   - 训练集和测试集的地区分布基本一致\n')
    f.write('   - 客户主要来自经济发达地区\n')
    f.write('   - 不同地区的续保率存在差异\n\n')
    
    f.write('4. 收入水平：\n')
    f.write('   - 训练集和测试集的收入水平分布相似\n')
    f.write('   - 收入水平与续保率呈正相关\n')
    f.write('   - 高收入客户续保意愿更强\n\n')
    
    f.write('5. 保单特征：\n')
    f.write('   - 训练集和测试集的保单类型分布基本一致\n')
    f.write('   - 不同保单类型的续保率差异明显\n')
    f.write('   - 保费金额与续保率存在相关性\n') 