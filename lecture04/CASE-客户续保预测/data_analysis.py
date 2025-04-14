import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def load_and_preprocess_data(file_path):
    """
    加载并预处理数据
    
    参数:
        file_path: Excel文件路径
    
    返回:
        DataFrame: 处理后的数据
    """
    # 读取数据
    df = pd.read_excel(file_path)
    
    # 显示基本信息
    print("数据基本信息：")
    print(f"数据形状: {df.shape}")
    print("\n数据类型：")
    print(df.dtypes)
    print("\n数据统计描述：")
    print(df.describe())
    
    # 检查缺失值
    print("\n缺失值统计：")
    print(df.isnull().sum())
    
    return df

def analyze_categorical_features(df):
    """
    分析分类特征
    
    参数:
        df: DataFrame
    """
    # 创建一个大图
    plt.figure(figsize=(20, 15))
    
    # 性别分布
    plt.subplot(2, 2, 1)
    gender_counts = df['gender'].value_counts()
    plt.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', 
            colors=['#ff9999','#66b3ff'], explode=[0.05, 0], shadow=True)
    plt.title('性别分布', fontsize=14, pad=20)
    
    # 续保情况分布
    plt.subplot(2, 2, 2)
    renewal_counts = df['renewal'].value_counts()
    plt.pie(renewal_counts, labels=renewal_counts.index, autopct='%1.1f%%', 
            colors=['#99ff99','#ffcc99'], explode=[0.05, 0], shadow=True)
    plt.title('续保情况分布', fontsize=14, pad=20)
    
    # 收入水平分布
    plt.subplot(2, 2, 3)
    income_counts = df['income_level'].value_counts()
    sns.barplot(x=income_counts.values, y=income_counts.index, 
                hue=income_counts.index, legend=False, palette='viridis')
    plt.title('收入水平分布', fontsize=14, pad=20)
    plt.xlabel('数量', fontsize=12)
    plt.ylabel('收入水平', fontsize=12)
    
    # 教育水平分布
    plt.subplot(2, 2, 4)
    education_counts = df['education_level'].value_counts()
    sns.barplot(x=education_counts.values, y=education_counts.index, 
                hue=education_counts.index, legend=False, palette='plasma')
    plt.title('教育水平分布', fontsize=14, pad=20)
    plt.xlabel('数量', fontsize=12)
    plt.ylabel('教育水平', fontsize=12)
    
    plt.tight_layout()
    plt.savefig('categorical_features.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 出生地区分布（取前10个地区）
    plt.figure(figsize=(12, 8))
    region_counts = df['birth_region'].value_counts().head(10)
    sns.barplot(x=region_counts.values, y=region_counts.index, 
                hue=region_counts.index, legend=False, palette='coolwarm')
    plt.title('出生地区分布（Top 10）', fontsize=14, pad=20)
    plt.xlabel('数量', fontsize=12)
    plt.ylabel('地区', fontsize=12)
    plt.tight_layout()
    plt.savefig('region_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def analyze_numerical_features(df):
    """
    分析数值特征
    
    参数:
        df: DataFrame
    """
    # 创建一个大图
    plt.figure(figsize=(20, 15))
    
    # 年龄分布
    plt.subplot(2, 2, 1)
    sns.histplot(df['age'], bins=30, kde=True, color='skyblue', 
                edgecolor='black', linewidth=1.2)
    plt.title('年龄分布', fontsize=14, pad=20)
    plt.xlabel('年龄', fontsize=12)
    plt.ylabel('频数', fontsize=12)
    
    # 保费金额分布
    plt.subplot(2, 2, 2)
    sns.histplot(df['premium_amount'], bins=30, kde=True, color='salmon', 
                edgecolor='black', linewidth=1.2)
    plt.title('保费金额分布', fontsize=14, pad=20)
    plt.xlabel('保费金额', fontsize=12)
    plt.ylabel('频数', fontsize=12)
    
    # 家庭成员数量分布
    plt.subplot(2, 2, 3)
    sns.histplot(df['family_members'], bins=10, kde=True, color='lightgreen', 
                edgecolor='black', linewidth=1.2)
    plt.title('家庭成员数量分布', fontsize=14, pad=20)
    plt.xlabel('家庭成员数量', fontsize=12)
    plt.ylabel('频数', fontsize=12)
    
    # 年龄与保费的关系
    plt.subplot(2, 2, 4)
    sns.scatterplot(x='age', y='premium_amount', data=df, alpha=0.6, 
                   color='purple', s=100, edgecolor='black', linewidth=0.5)
    plt.title('年龄与保费的关系', fontsize=14, pad=20)
    plt.xlabel('年龄', fontsize=12)
    plt.ylabel('保费金额', fontsize=12)
    
    plt.tight_layout()
    plt.savefig('numerical_features.png', dpi=300, bbox_inches='tight')
    plt.close()

def analyze_time_features(df):
    """
    分析时间特征
    
    参数:
        df: DataFrame
    """
    # 将日期列转换为datetime类型
    df['policy_start_date'] = pd.to_datetime(df['policy_start_date'])
    df['policy_end_date'] = pd.to_datetime(df['policy_end_date'])
    
    # 计算保单期限（年）
    df['policy_duration'] = (df['policy_end_date'] - df['policy_start_date']).dt.days / 365
    
    # 创建一个大图
    plt.figure(figsize=(20, 10))
    
    # 保单期限分布
    plt.subplot(1, 2, 1)
    sns.histplot(df['policy_duration'], bins=30, kde=True, color='orange', 
                edgecolor='black', linewidth=1.2)
    plt.title('保单期限分布', fontsize=14, pad=20)
    plt.xlabel('保单期限（年）', fontsize=12)
    plt.ylabel('频数', fontsize=12)
    
    # 保单开始日期分布
    plt.subplot(1, 2, 2)
    df['start_year'] = df['policy_start_date'].dt.year
    year_counts = df['start_year'].value_counts().sort_index()
    sns.lineplot(x=year_counts.index, y=year_counts.values, marker='o', 
                color='green', linewidth=2.5, markersize=10)
    plt.title('保单开始年份分布', fontsize=14, pad=20)
    plt.xlabel('年份', fontsize=12)
    plt.ylabel('保单数量', fontsize=12)
    
    plt.tight_layout()
    plt.savefig('time_features.png', dpi=300, bbox_inches='tight')
    plt.close()

def analyze_correlations(df):
    """
    分析特征相关性
    
    参数:
        df: DataFrame
    """
    # 数值特征相关性分析
    plt.figure(figsize=(12, 8))
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
    correlation_matrix = df[numeric_columns].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', 
               linewidths=0.5, square=True)
    plt.title('数值特征相关性分析', fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig('correlation_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 分类特征与续保的关系
    categorical_features = ['gender', 'income_level', 'education_level', 'marital_status']
    plt.figure(figsize=(20, 15))
    
    for i, feature in enumerate(categorical_features, 1):
        plt.subplot(2, 2, i)
        sns.countplot(x=feature, hue='renewal', data=df, palette='Set2', 
                     edgecolor='black', linewidth=0.5)
        plt.title(f'{feature}与续保的关系', fontsize=14, pad=20)
        plt.xlabel(feature, fontsize=12)
        plt.ylabel('数量', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(title='续保情况', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('categorical_renewal_relation.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # 加载数据
    df = load_and_preprocess_data('policy_data.xlsx')
    
    # 分析分类特征
    analyze_categorical_features(df)
    
    # 分析数值特征
    analyze_numerical_features(df)
    
    # 分析时间特征
    analyze_time_features(df)
    
    # 分析相关性
    analyze_correlations(df)

if __name__ == "__main__":
    main() 