"""
程序说明：

## 1. 使用LightGBM预测客户未来3个月资产是否能提升至100万+
## 2. 可视化特征重要性（多种重要性指标）
## 3. 输出预测结果及模型评估指标

"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score
import lightgbm as lgb
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

def train_lightgbm(X, y, feature_names):
    """
    训练LightGBM模型
    :function: 训练模型，输出评估指标
    :param X: 特征DataFrame
    :param y: 标签Series
    :param feature_names: 特征名列表
    :return: 训练好的模型和测试数据
    """
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 创建数据集
    train_data = lgb.Dataset(X_train, label=y_train, feature_name=feature_names)
    test_data = lgb.Dataset(X_test, label=y_test, feature_name=feature_names)
    
    # 设置参数
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'early_stopping_round': 50
    }
    
    # 训练模型
    print("开始训练LightGBM模型...")
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[test_data],
        callbacks=[lgb.log_evaluation(10)]
    )
    
    # 模型评估
    y_pred_proba = model.predict(X_test)
    auc_score = roc_auc_score(y_test, y_pred_proba)
    
    print("\n=== 模型评估 ===")
    print(f"AUC得分: {auc_score:.4f}")
    print("\n分类报告:")
    y_pred = (y_pred_proba > 0.5).astype(int)
    print(classification_report(y_test, y_pred))
    
    return model, X_test, y_test

def analyze_feature_importance(model, feature_names):
    """
    分析特征重要性
    :function: 计算并可视化多种特征重要性指标
    :param model: 训练好的LightGBM模型
    :param feature_names: 特征名列表
    """
    # 获取多种特征重要性指标
    importance_types = ['split', 'gain']
    importance_dfs = []
    
    for imp_type in importance_types:
        importance = pd.DataFrame({
            'feature': feature_names,
            f'importance_{imp_type}': model.feature_importance(importance_type=imp_type)
        })
        importance = importance.sort_values(f'importance_{imp_type}', ascending=True)
        importance_dfs.append(importance)
    
    # 创建子图
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    
    # 绘制特征重要性条形图
    for idx, (imp_type, importance) in enumerate(zip(importance_types, importance_dfs)):
        axes[idx].barh(range(len(importance)), importance[f'importance_{imp_type}'])
        axes[idx].set_yticks(range(len(importance)))
        axes[idx].set_yticklabels(importance['feature'])
        axes[idx].set_title(f'特征重要性 ({imp_type})', fontsize=12)
        axes[idx].set_xlabel('重要性得分')
    
    plt.tight_layout()
    plt.savefig('v003_feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 打印特征重要性排名
    print("\n=== 特征重要性排名 ===")
    print("\n1. Split重要性（特征被用作分割点的次数）:")
    for idx, row in importance_dfs[0].sort_values('importance_split', ascending=False).iterrows():
        print(f"{row['feature']}: {row['importance_split']}")
    
    print("\n2. Gain重要性（特征带来的性能提升）:")
    for idx, row in importance_dfs[1].sort_values('importance_gain', ascending=False).iterrows():
        print(f"{row['feature']}: {row['importance_gain']}")

def predict_and_save(model, X, y):
    """
    预测并保存结果
    :function: 生成预测结果并保存到文件
    :param model: 训练好的模型
    :param X: 特征数据
    :param y: 实际标签
    """
    # 预测概率
    probabilities = model.predict(X)
    
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
    results.to_csv('v003_prediction_results.csv', index=False)
    print("\n预测结果已保存到 v003_prediction_results.csv")

def main():
    """
    主函数
    :function: 执行完整的建模和预测流程
    """
    print("开始加载和处理数据...")
    X, y, feature_names = load_and_process_data()
    
    # 训练模型
    model, X_test, y_test = train_lightgbm(X, y, feature_names)
    
    # 分析特征重要性
    print("\n分析特征重要性...")
    analyze_feature_importance(model, feature_names)
    
    # 生成预测结果
    print("\n生成预测结果...")
    predict_and_save(model, X_test, y_test)

if __name__ == "__main__":
    main() 