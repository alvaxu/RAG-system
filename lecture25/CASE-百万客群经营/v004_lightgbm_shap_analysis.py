"""
程序说明：

## 1. 基于v003版本的LightGBM预测模型
## 2. 增加SHAP值分析功能：
   - 全局解释：分析整体特征重要性
   - 局部解释：解释单个客户预测结果
## 3. 可视化SHAP分析结果：
   - 全局特征重要性图
   - 特征影响瀑布图
   - 特征依赖图
## 4. 输出详细的分析报告

"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score
import lightgbm as lgb
import matplotlib.pyplot as plt
import shap
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
    :return: 处理后的特征DataFrame和标签Series，以及特征名列表，原始特征名映射
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
    
    # 保存原始特征值映射
    feature_mappings = {}
    for col in category_cols:
        df[col + '_encoded'] = le.fit_transform(df[col])
        feature_mappings[col] = dict(zip(le.classes_, range(len(le.classes_))))
    
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
    
    # 保存客户ID
    customer_ids = df['customer_id'].values
    
    # 删除包含空值的行
    df = df.dropna()
    
    return df[feature_columns], df['target'], feature_columns, feature_mappings, customer_ids

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
    
    return model, X_train, X_test, y_train, y_test

def global_shap_analysis(model, X_train, feature_names):
    """
    全局SHAP值分析
    :function: 分析整体特征重要性
    :param model: 训练好的模型
    :param X_train: 训练数据
    :param feature_names: 特征名列表
    """
    print("\n开始全局SHAP值分析...")
    
    # 计算SHAP值
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_train)
    
    # 如果是二分类问题，取第二个类别的SHAP值
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    
    # 绘制全局特征重要性图
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X_train, feature_names=feature_names, show=False)
    plt.title("SHAP特征重要性分析", fontsize=12)
    plt.tight_layout()
    plt.savefig('v004_shap_global_importance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 计算并打印平均绝对SHAP值
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': mean_abs_shap
    })
    importance_df = importance_df.sort_values('importance', ascending=False)
    
    print("\n=== 特征重要性排名（基于SHAP值） ===")
    for idx, row in importance_df.iterrows():
        print(f"{row['feature']}: {row['importance']:.4f}")
    
    return explainer, shap_values

def local_shap_analysis(explainer, X_test, feature_names, customer_ids, n_samples=5):
    """
    局部SHAP值分析
    :function: 解释单个客户的预测结果
    :param explainer: SHAP解释器
    :param X_test: 测试数据
    :param feature_names: 特征名列表
    :param customer_ids: 客户ID列表
    :param n_samples: 要分析的样本数量
    """
    print(f"\n开始局部SHAP值分析（随机选择{n_samples}个客户）...")
    
    # 随机选择样本
    sample_indices = np.random.choice(len(X_test), n_samples, replace=False)
    
    for idx in sample_indices:
        # 获取单个样本的SHAP值
        sample = X_test.iloc[idx:idx+1]
        shap_values = explainer.shap_values(sample)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        # 绘制瀑布图
        plt.figure(figsize=(12, 6))
        shap.waterfall_plot(shap.Explanation(
            values=shap_values[0],
            base_values=explainer.expected_value if not isinstance(explainer.expected_value, list) 
            else explainer.expected_value[1],
            data=sample.values[0],
            feature_names=feature_names
        ), show=False)
        plt.title(f"客户 {customer_ids[idx]} 的SHAP值瀑布图", fontsize=12)
        plt.tight_layout()
        plt.savefig(f'v004_shap_local_waterfall_{idx}.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 打印特征贡献
        print(f"\n=== 客户 {customer_ids[idx]} 的预测解释 ===")
        feature_contributions = pd.DataFrame({
            'feature': feature_names,
            'value': sample.values[0],
            'shap_value': shap_values[0]
        })
        feature_contributions = feature_contributions.sort_values('shap_value', ascending=False)
        
        print("\n正向影响特征:")
        for _, row in feature_contributions[feature_contributions['shap_value'] > 0].iterrows():
            print(f"{row['feature']}: {row['shap_value']:.4f} (值: {row['value']:.2f})")
        
        print("\n负向影响特征:")
        for _, row in feature_contributions[feature_contributions['shap_value'] < 0].iterrows():
            print(f"{row['feature']}: {row['shap_value']:.4f} (值: {row['value']:.2f})")

def analyze_feature_dependencies(shap_values, X_train, feature_names):
    """
    分析特征依赖关系
    :function: 绘制特征依赖图
    :param shap_values: SHAP值
    :param X_train: 训练数据
    :param feature_names: 特征名列表
    """
    print("\n分析特征依赖关系...")
    
    # 选择最重要的特征进行依赖分析
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    top_features = pd.Series(mean_abs_shap, index=feature_names).nlargest(5).index
    
    for feature in top_features:
        plt.figure(figsize=(10, 6))
        shap.dependence_plot(
            feature, shap_values, X_train,
            feature_names=feature_names,
            show=False
        )
        plt.title(f"{feature}特征依赖图", fontsize=12)
        plt.tight_layout()
        plt.savefig(f'v004_shap_dependence_{feature}.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """
    主函数
    :function: 执行完整的建模和SHAP分析流程
    """
    print("开始加载和处理数据...")
    X, y, feature_names, feature_mappings, customer_ids = load_and_process_data()
    
    # 训练模型
    model, X_train, X_test, y_train, y_test = train_lightgbm(X, y, feature_names)
    
    # 全局SHAP分析
    explainer, shap_values = global_shap_analysis(model, X_train, feature_names)
    
    # 局部SHAP分析
    local_shap_analysis(explainer, X_test, feature_names, customer_ids)
    
    # 特征依赖分析
    analyze_feature_dependencies(shap_values, X_train, feature_names)
    
    print("\n分析完成！所有可视化结果已保存为PNG文件。")

if __name__ == "__main__":
    main() 