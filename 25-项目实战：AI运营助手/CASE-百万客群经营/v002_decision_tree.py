"""
程序说明：

## 1. 使用决策树(depth=4)预测客户未来3个月资产是否能提升至100万+
## 2. 可视化决策树结构（文本形式和图形形式）
## 3. 输出预测结果及模型评估指标

"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

def load_and_process_data():
    """
    加载和处理数据
    :function: 读取CSV文件，处理特征，构建标签
    :return: 处理后的特征DataFrame和标签Series，以及特征名列表
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
    
    return df[feature_columns], df['target'], feature_columns

def train_decision_tree(X, y, feature_names):
    """
    训练决策树模型
    :function: 训练模型，输出评估指标和决策树结构
    :param X: 特征DataFrame
    :param y: 标签Series
    :param feature_names: 特征名列表
    :return: 训练好的模型
    """
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 训练模型
    model = DecisionTreeClassifier(max_depth=4, random_state=42)
    model.fit(X_train, y_train)
    
    # 模型评估
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc_score = roc_auc_score(y_test, y_pred_proba)
    
    print("\n=== 模型评估 ===")
    print(f"AUC得分: {auc_score:.4f}")
    print("\n分类报告:")
    print(classification_report(y_test, model.predict(X_test)))
    
    # 输出决策树文本表示
    print("\n=== 决策树结构（文本形式）===")
    tree_text = export_text(model, feature_names=feature_names)
    print(tree_text)
    
    # 保存决策树文本到文件
    with open('v002_decision_tree_structure.txt', 'w', encoding='utf-8') as f:
        f.write(tree_text)
    
    return model, X_test, y_test

def visualize_tree(model, feature_names):
    """
    可视化决策树
    :function: 生成决策树的图形可视化
    :param model: 训练好的决策树模型
    :param feature_names: 特征名列表
    """
    plt.figure(figsize=(20, 10))
    plot_tree(model, 
             feature_names=feature_names,
             class_names=['不会提升', '会提升'],
             filled=True,
             rounded=True,
             fontsize=10)
    
    plt.title("客户资产提升预测决策树", fontsize=16, pad=20)
    plt.savefig('v002_decision_tree_visualization.png', dpi=300, bbox_inches='tight')
    plt.close()

def analyze_feature_importance(model, feature_names):
    """
    分析特征重要性
    :function: 计算并可视化特征重要性
    :param model: 训练好的决策树模型
    :param feature_names: 特征名列表
    """
    # 获取特征重要性
    importance = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    })
    importance = importance.sort_values('importance', ascending=True)
    
    # 创建水平条形图
    plt.figure(figsize=(12, 8))
    plt.barh(range(len(importance)), importance['importance'])
    plt.yticks(range(len(importance)), importance['feature'])
    
    plt.title('特征重要性分析', fontsize=14)
    plt.xlabel('重要性得分')
    
    plt.tight_layout()
    plt.savefig('v002_feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 打印特征重要性
    print("\n=== 特征重要性排名 ===")
    for idx, row in importance.sort_values('importance', ascending=False).iterrows():
        print(f"{row['feature']}: {row['importance']:.4f}")

def predict_and_save(model, X, y):
    """
    预测并保存结果
    :function: 生成预测结果并保存到文件
    :param model: 训练好的模型
    :param X: 特征数据
    :param y: 实际标签
    """
    # 预测概率
    probabilities = model.predict_proba(X)[:, 1]
    
    # 创建结果DataFrame
    results = pd.DataFrame({
        'probability': probabilities,
        'actual': y
    })
    
    # 输出统计信息
    print("\n=== 预测结果统计 ===")
    print(f"平均提升概率: {results['probability'].mean():.2%}")
    print(f"高概率客户占比 (>50%): {(results['probability'] > 0.5).mean():.2%}")
    
    # 保存预测结果
    results.to_csv('v002_prediction_results.csv', index=False)
    print("\n预测结果已保存到 v002_prediction_results.csv")

def main():
    """
    主函数
    :function: 执行完整的建模和预测流程
    """
    print("开始加载和处理数据...")
    X, y, feature_names = load_and_process_data()
    
    print("\n开始训练决策树模型...")
    model, X_test, y_test = train_decision_tree(X, y, feature_names)
    
    print("\n生成决策树可视化...")
    visualize_tree(model, feature_names)
    
    print("\n分析特征重要性...")
    analyze_feature_importance(model, feature_names)
    
    print("\n生成预测结果...")
    predict_and_save(model, X_test, y_test)

if __name__ == "__main__":
    main() 