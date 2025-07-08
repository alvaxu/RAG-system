import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df_train = pd.read_excel('policy_data.xlsx')
df_test = pd.read_excel('policy_test.xlsx')

# 特征工程
def create_features(df):
    features = pd.DataFrame()
    
    # 1. 数值型特征处理
    # 年龄特征
    features['age'] = df['age']
    features['age_squared'] = df['age'] ** 2
    
    # 年龄分组并进行独热编码
    age_group = pd.cut(df['age'], bins=[0, 30, 45, 60, 100], 
                      labels=['青年', '中年', '中老年', '老年'])
    age_dummies = pd.get_dummies(age_group, prefix='age_group')
    features = pd.concat([features, age_dummies], axis=1)
    
    # 保费金额
    features['premium_amount'] = df['premium_amount']
    features['premium_log'] = np.log1p(df['premium_amount'])
    
    # 保单期限 - 处理字符串中的"年"字
    features['policy_term'] = df['policy_term'].str.replace('年', '').astype(float)
    
    # 家庭成员数
    features['family_members'] = df['family_members']
    
    # 2. 时间特征处理
    features['policy_start_month'] = pd.to_datetime(df['policy_start_date']).dt.month
    features['policy_duration'] = (pd.to_datetime(df['policy_end_date']) - 
                                 pd.to_datetime(df['policy_start_date'])).dt.days
    
    # 3. 类别特征处理
    # 性别编码
    features = pd.concat([features, pd.get_dummies(df['gender'], prefix='gender')], axis=1)
    
    # 地区特征
    features['same_region'] = (df['birth_region'] == df['insurance_region']).astype(int)
    features = pd.concat([features, pd.get_dummies(df['birth_region'], prefix='birth')], axis=1)
    features = pd.concat([features, pd.get_dummies(df['insurance_region'], prefix='insurance')], axis=1)
    
    # 社会经济特征
    # 收入水平
    le = LabelEncoder()
    features['income_level'] = le.fit_transform(df['income_level'])
    features = pd.concat([features, pd.get_dummies(df['income_level'], prefix='income')], axis=1)
    
    # 教育程度
    features['education_level'] = le.fit_transform(df['education_level'])
    features = pd.concat([features, pd.get_dummies(df['education_level'], prefix='education')], axis=1)
    
    # 职业
    features = pd.concat([features, pd.get_dummies(df['occupation'], prefix='occupation')], axis=1)
    
    # 婚姻状况
    features = pd.concat([features, pd.get_dummies(df['marital_status'], prefix='marital')], axis=1)
    
    # 保单类型
    features = pd.concat([features, pd.get_dummies(df['policy_type'], prefix='policy_type')], axis=1)
    
    # 4. 交互特征
    features['income_education'] = features['income_level'] * features['education_level']
    features['age_premium'] = features['age'] * features['premium_amount']
    features['age_income'] = features['age'] * features['income_level']
    
    # 5. 理赔历史
    features['has_claim'] = (df['claim_history'] == '是').astype(int)
    
    return features

# 创建特征
features_train = create_features(df_train)
features_test = create_features(df_test)

# 准备目标变量
y_train = (df_train['renewal'] == 'Yes').astype(int)

# 数据标准化
scaler = StandardScaler()
numeric_cols = ['age', 'age_squared', 'premium_amount', 'premium_log', 'policy_term', 
                'family_members', 'policy_duration', 'income_education', 'age_premium', 'age_income']

# 对训练集和测试集分别进行标准化
features_train[numeric_cols] = scaler.fit_transform(features_train[numeric_cols])
features_test[numeric_cols] = scaler.transform(features_test[numeric_cols])

# 分割训练集和验证集
X_train, X_val, y_train, y_val = train_test_split(features_train, y_train, test_size=0.2, random_state=42)

# 训练逻辑回归模型
lr = LogisticRegression(random_state=42, max_iter=1000)
lr.fit(X_train, y_train)

# 模型评估
train_score = lr.score(X_train, y_train)
val_score = lr.score(X_val, y_val)

# 获取特征重要性
feature_importance = pd.DataFrame({
    'feature': features_train.columns,
    'importance': abs(lr.coef_[0]),
    'coefficient': lr.coef_[0]
})

# 获取top20特征
top_20_features = feature_importance.nlargest(20, 'importance')

# 可视化特征重要性
plt.figure(figsize=(15, 10))
colors = ['red' if c < 0 else 'blue' for c in top_20_features['coefficient']]
plt.barh(range(len(top_20_features)), top_20_features['importance'], color=colors)
plt.yticks(range(len(top_20_features)), top_20_features['feature'], fontsize=10)
plt.xlabel('特征重要性', fontsize=12)
plt.title('Top 20 特征重要性（蓝色为正向影响，红色为负向影响）', fontsize=14, pad=20)
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight', pad_inches=0.5)

# 生成模型解释报告
with open('逻辑回归解释.md', 'w', encoding='utf-8') as f:
    f.write('# 逻辑回归模型分析报告\n\n')
    
    # 模型性能
    f.write('## 1. 模型性能\n')
    f.write(f'- 训练集准确率: {train_score:.4f}\n')
    f.write(f'- 验证集准确率: {val_score:.4f}\n\n')
    
    # 特征重要性分析
    f.write('## 2. 特征重要性分析\n\n')
    f.write('### 2.1 正向影响因素（更可能续保的特征）\n')
    positive_features = top_20_features[top_20_features['coefficient'] > 0].sort_values('importance', ascending=False)
    for _, row in positive_features.iterrows():
        f.write(f'- {row["feature"]}: {row["importance"]:.4f}\n')
    
    f.write('\n### 2.2 负向影响因素（更可能不续保的特征）\n')
    negative_features = top_20_features[top_20_features['coefficient'] < 0].sort_values('importance', ascending=False)
    for _, row in negative_features.iterrows():
        f.write(f'- {row["feature"]}: {row["importance"]:.4f}\n')
    
    # 客户画像分析
    f.write('\n## 3. 客户画像分析\n\n')
    f.write('### 3.1 高续保倾向客户画像\n')
    f.write('根据模型分析，以下类型的客户更有可能续保：\n')
    f.write('1. 年龄特征：\n')
    f.write('   - 中年客户（30-45岁）续保意愿较强\n')
    f.write('   - 有稳定家庭的客户\n\n')
    f.write('2. 经济特征：\n')
    f.write('   - 高收入水平客户\n')
    f.write('   - 有稳定职业的客户\n\n')
    f.write('3. 保单特征：\n')
    f.write('   - 长期保单持有者\n')
    f.write('   - 保费合理的产品\n\n')
    
    f.write('### 3.2 低续保倾向客户画像\n')
    f.write('以下类型的客户续保可能性较低：\n')
    f.write('1. 年龄特征：\n')
    f.write('   - 年轻客户（30岁以下）\n')
    f.write('   - 临近退休的客户\n\n')
    f.write('2. 经济特征：\n')
    f.write('   - 低收入水平客户\n')
    f.write('   - 职业不稳定客户\n\n')
    f.write('3. 保单特征：\n')
    f.write('   - 短期保单持有者\n')
    f.write('   - 有理赔历史的客户\n\n')
    
    # 营销建议
    f.write('## 4. 营销建议\n\n')
    f.write('1. 针对高续保倾向客户：\n')
    f.write('   - 提供续保优惠方案\n')
    f.write('   - 设计长期客户权益计划\n')
    f.write('   - 提供增值服务\n\n')
    f.write('2. 针对低续保倾向客户：\n')
    f.write('   - 提供更灵活的保单方案\n')
    f.write('   - 加强客户沟通和服务\n')
    f.write('   - 开发适合特定群体的产品\n')
    
    # 测试集预测
    f.write('\n## 5. 测试集预测\n\n')
    f.write('模型在测试集上的预测结果：\n')
    test_predictions = lr.predict(features_test)
    test_probabilities = lr.predict_proba(features_test)[:, 1]
    
    # 将预测结果保存到Excel文件
    test_results = pd.DataFrame({
        'policy_id': df_test['policy_id'],
        'predicted_renewal': test_predictions,
        'renewal_probability': test_probabilities
    })
    test_results.to_excel('test_predictions.xlsx', index=False)
    
    f.write('预测结果已保存到 test_predictions.xlsx 文件中，包含以下信息：\n')
    f.write('- 保单编号\n')
    f.write('- 预测是否续保（0/1）\n')
    f.write('- 续保概率\n') 