"""
程序说明：

## 1. 使用逻辑回归预测客户未来3个月资产提升至100万+的概率
## 2. 可视化模型特征系数，分析各个因素的影响程度
## 3. 输出预测结果及模型评估指标

"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

def load_and_process_data():
    """
    加载和处理数据
    :function: 读取CSV文件，处理特征，构建标签
    :return: 处理后的特征DataFrame和标签Series
    """
    # 读取数据
    df_base = pd.read_csv('customer_base.csv')
    df_behavior = pd.read_csv('customer_behavior_assets.csv')
    
    # 合并数据
    df = pd.merge(df_base, df_behavior, on='customer_id', how='inner')
    
    # 处理时间特征
    df['open_account_date'] = pd.to_datetime(df['open_account_date'])
    df['stat_month'] = pd.to_datetime(df['stat_month'])
    df['account_age'] = (df['stat_month'] - df['open_account_date']).dt.days / 365
    
    # 处理类别特征
    le = LabelEncoder()
    category_cols = ['gender', 'occupation', 'occupation_type', 'lifecycle_stage', 
                    'marriage_status', 'city_level', 'asset_level']
    
    for col in category_cols:
        df[col + '_encoded'] = le.fit_transform(df[col])
    
    # 构建特征
    feature_columns = [
        'age', 'monthly_income', 'account_age',
        'total_assets', 'deposit_balance', 'financial_balance',
        'fund_balance', 'insurance_balance', 'product_count',
        'financial_repurchase_count', 'credit_card_monthly_expense',
        'investment_monthly_count', 'app_login_count',
        'app_financial_view_time', 'app_product_compare_count'
    ] + [col + '_encoded' for col in category_cols]
    
    # 构建标签（是否在未来达到100万资产）
    df = df.sort_values(['customer_id', 'stat_month'])
    df['future_assets'] = df.groupby('customer_id')['total_assets'].shift(-3)  # 预测3个月后
    df['target'] = (df['future_assets'] >= 1000000).astype(int)
    
    # 删除包含空值的行
    df = df.dropna()
    
    return df[feature_columns], df['target']

def train_model(X, y):
    """
    训练逻辑回归模型
    :function: 划分数据集，训练模型，输出评估指标
    :param X: 特征DataFrame
    :param y: 标签Series
    :return: 训练好的模型和标准化器
    """
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 标准化特征
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 训练模型
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train_scaled, y_train)
    
    # 模型评估
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    auc_score = roc_auc_score(y_test, y_pred_proba)
    
    print("\n=== 模型评估 ===")
    print(f"AUC得分: {auc_score:.4f}")
    print("\n分类报告:")
    print(classification_report(y_test, model.predict(X_test_scaled)))
    
    return model, scaler

def visualize_coefficients(model, feature_names):
    """
    可视化模型系数
    :function: 绘制特征重要性条形图，并在控制台输出系数
    :param model: 训练好的模型
    :param feature_names: 特征名称列表
    """
    # 获取系数
    coefficients = pd.DataFrame({
        'Feature': feature_names,
        'Coefficient': model.coef_[0]
    })
    
    # 按系数绝对值排序
    coefficients = coefficients.sort_values('Coefficient', ascending=True)
    
    # 在控制台输出系数
    print("\n=== 模型系数（按影响程度排序）===")
    print("\n特征系数表:")
    pd.set_option('display.max_rows', None)  # 显示所有行
    pd.set_option('display.float_format', lambda x: '{:.4f}'.format(x))  # 设置小数点位数
    print(coefficients.sort_values('Coefficient', ascending=False))
    
    # 创建图形
    plt.figure(figsize=(15, 10))
    
    # 绘制条形图
    bars = plt.barh(range(len(coefficients)), coefficients['Coefficient'])
    plt.yticks(range(len(coefficients)), coefficients['Feature'])
    
    # 添加颜色
    colors = ['red' if x < 0 else 'green' for x in coefficients['Coefficient']]
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    # 设置标题和标签
    plt.title('特征重要性分析', fontsize=14, pad=20)
    plt.xlabel('系数值', fontsize=12)
    
    # 添加垂直线
    plt.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    
    # 在条形上添加数值标签
    for i, v in enumerate(coefficients['Coefficient']):
        plt.text(v + (0.01 if v >= 0 else -0.01), 
                i,
                f'{v:.4f}',
                va='center',
                ha='left' if v >= 0 else 'right',
                fontsize=9)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图片
    plt.savefig('v001_feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 输出特征影响力总结
    print("\n=== 特征影响力总结 ===")
    positive_features = coefficients[coefficients['Coefficient'] > 0].sort_values('Coefficient', ascending=False)
    negative_features = coefficients[coefficients['Coefficient'] < 0].sort_values('Coefficient')
    
    print("\n正向影响最强的前5个特征:")
    for idx, row in positive_features.head().iterrows():
        print(f"{row['Feature']}: +{row['Coefficient']:.4f}")
    
    print("\n负向影响最强的前5个特征:")
    for idx, row in negative_features.head().iterrows():
        print(f"{row['Feature']}: {row['Coefficient']:.4f}")

def predict_probability(model, scaler, X):
    """
    预测概率
    :function: 使用模型预测客户资产提升的概率
    :param model: 训练好的模型
    :param scaler: 标准化器
    :param X: 特征DataFrame
    :return: 预测概率Series
    """
    X_scaled = scaler.transform(X)
    probabilities = model.predict_proba(X_scaled)[:, 1]
    return probabilities

def main():
    """
    主函数
    :function: 执行完整的建模和预测流程
    """
    print("开始加载和处理数据...")
    X, y = load_and_process_data()
    
    print("\n开始训练模型...")
    model, scaler = train_model(X, y)
    
    print("\n生成特征重要性可视化...")
    visualize_coefficients(model, X.columns)
    
    print("\n计算预测概率...")
    probabilities = predict_probability(model, scaler, X)
    
    # 将预测结果添加到原始数据中
    results = pd.DataFrame({
        'probability': probabilities,
        'actual': y
    })
    
    print("\n预测结果统计:")
    print(f"平均提升概率: {results['probability'].mean():.2%}")
    print(f"高概率客户占比 (>50%): {(results['probability'] > 0.5).mean():.2%}")
    
    # 保存预测结果
    results.to_csv('v001_prediction_results.csv', index=False)
    print("\n预测结果已保存到 v001_prediction_results.csv")

if __name__ == "__main__":
    main() 