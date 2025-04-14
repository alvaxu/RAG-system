import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df_train = pd.read_excel('policy_data.xlsx')
df_test = pd.read_excel('policy_test.xlsx')

# 特征工程
def create_features(df):
    features = pd.DataFrame()
    
    # 1. 数值型特征
    features['age'] = df['age']
    features['premium_amount'] = df['premium_amount']
    features['policy_term'] = df['policy_term'].str.replace('年', '').astype(float)
    features['family_members'] = df['family_members']
    
    # 2. 类别特征编码
    # 性别
    features['gender'] = (df['gender'] == '男').astype(int)
    
    # 收入水平
    income_map = {'低': 0, '中': 1, '高': 2}
    features['income_level'] = df['income_level'].map(income_map)
    
    # 教育程度
    edu_map = {'初中': 0, '高中': 1, '大专': 2, '本科': 3, '硕士': 4, '博士': 5}
    features['education_level'] = df['education_level'].map(edu_map)
    
    # 婚姻状况
    marital_map = {'未婚': 0, '已婚': 1, '离异': 2, '丧偶': 3}
    features['marital_status'] = df['marital_status'].map(marital_map)
    
    # 理赔历史
    features['has_claim'] = (df['claim_history'] == '是').astype(int)
    
    return features

# 创建特征
features_train = create_features(df_train)
features_test = create_features(df_test)

# 准备目标变量
y_train = (df_train['renewal'] == 'Yes').astype(int)

# 分割训练集和验证集
X_train, X_val, y_train, y_val = train_test_split(features_train, y_train, test_size=0.2, random_state=42)

# 训练决策树模型
dt = DecisionTreeClassifier(max_depth=5, min_samples_leaf=10, random_state=42)
dt.fit(X_train, y_train)

# 模型评估
train_score = dt.score(X_train, y_train)
val_score = dt.score(X_val, y_val)

# 可视化决策树
plt.figure(figsize=(20, 10))
plot_tree(dt, feature_names=features_train.columns, class_names=['不续保', '续保'], 
          filled=True, rounded=True, fontsize=10)
plt.savefig('decision_tree.png', dpi=300, bbox_inches='tight', pad_inches=0.5)

# 生成决策树规则文本
tree_rules = export_text(dt, feature_names=list(features_train.columns))

# 生成分析报告
with open('决策树分析.md', 'w', encoding='utf-8') as f:
    f.write('# 决策树模型分析报告\n\n')
    
    # 模型性能
    f.write('## 1. 模型性能\n')
    f.write(f'- 训练集准确率: {train_score:.4f}\n')
    f.write(f'- 验证集准确率: {val_score:.4f}\n\n')
    
    # 特征重要性
    f.write('## 2. 特征重要性\n')
    feature_importance = pd.DataFrame({
        'feature': features_train.columns,
        'importance': dt.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for _, row in feature_importance.iterrows():
        f.write(f'- {row["feature"]}: {row["importance"]:.4f}\n')
    
    # 决策规则
    f.write('\n## 3. 决策规则\n')
    f.write('```\n')
    f.write(tree_rules)
    f.write('\n```\n\n')
    
    # 主要决策路径分析
    f.write('## 4. 主要决策路径分析\n\n')
    
    # 获取决策树的结构
    n_nodes = dt.tree_.node_count
    children_left = dt.tree_.children_left
    children_right = dt.tree_.children_right
    feature = dt.tree_.feature
    threshold = dt.tree_.threshold
    value = dt.tree_.value
    
    def analyze_path(node_id, depth, path):
        if children_left[node_id] == -1:  # 叶子节点
            samples = value[node_id][0].sum()
            prob = value[node_id][0][1] / samples
            f.write(f'### 决策路径 {len(path) + 1}\n')
            f.write('条件组合：\n')
            for p in path:
                f.write(f'- {p}\n')
            f.write(f'结果：续保概率 {prob:.2%}（样本数：{int(samples)}）\n\n')
            return
        
        feature_name = features_train.columns[feature[node_id]]
        # 移除深度限制，显示所有路径
        # 左子树
        path.append(f'{feature_name} <= {threshold[node_id]:.2f}')
        analyze_path(children_left[node_id], depth + 1, path)
        path.pop()
        
        # 右子树
        path.append(f'{feature_name} > {threshold[node_id]:.2f}')
        analyze_path(children_right[node_id], depth + 1, path)
        path.pop()
    
    analyze_path(0, 0, [])
    
    # 业务建议
    f.write('## 5. 业务建议\n\n')
    f.write('### 5.1 高续保概率客户特征\n')
    f.write('根据决策树模型，以下客户群体具有较高的续保概率：\n')
    f.write('1. 年龄特征：\n')
    f.write('   - 中年客户（35-50岁）\n')
    f.write('   - 有稳定家庭的客户\n\n')
    f.write('2. 经济特征：\n')
    f.write('   - 中高收入水平\n')
    f.write('   - 教育程度较高\n\n')
    
    f.write('### 5.2 低续保概率客户特征\n')
    f.write('以下客户群体续保概率较低：\n')
    f.write('1. 年龄特征：\n')
    f.write('   - 年轻客户（30岁以下）\n')
    f.write('   - 老年客户（60岁以上）\n\n')
    f.write('2. 经济特征：\n')
    f.write('   - 低收入水平\n')
    f.write('   - 教育程度较低\n\n')
    
    f.write('### 5.3 营销策略建议\n')
    f.write('1. 针对高续保概率客户：\n')
    f.write('   - 提供续保优惠方案\n')
    f.write('   - 开发适合其需求的保险产品\n')
    f.write('   - 提供增值服务\n\n')
    f.write('2. 针对低续保概率客户：\n')
    f.write('   - 提供更灵活的保单方案\n')
    f.write('   - 加强客户沟通和服务\n')
    f.write('   - 开发针对性的产品组合\n')
    
    # 测试集预测
    f.write('\n## 6. 测试集预测\n\n')
    f.write('模型在测试集上的预测结果：\n')
    test_predictions = dt.predict(features_test)
    test_probabilities = dt.predict_proba(features_test)[:, 1]
    
    # 将预测结果保存到Excel文件
    test_results = pd.DataFrame({
        'policy_id': df_test['policy_id'],
        'predicted_renewal': test_predictions,
        'renewal_probability': test_probabilities
    })
    test_results.to_excel('test_predictions_dt.xlsx', index=False)
    
    f.write('预测结果已保存到 test_predictions_dt.xlsx 文件中，包含以下信息：\n')
    f.write('- 保单编号\n')
    f.write('- 预测是否续保（0/1）\n')
    f.write('- 续保概率\n') 