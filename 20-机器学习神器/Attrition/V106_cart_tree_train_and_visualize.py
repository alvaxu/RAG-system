'''
程序说明：
## 1. 本程序使用原始特征训练CART决策树（深度4）进行员工离职预测。
## 2. 输出AUC分数，打印决策树规则，并生成决策树可视化图片（仅png）。
'''
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn import tree

# 读取原始特征数据
train = pd.read_csv('V102_train_feature.csv', encoding='utf-8')
test = pd.read_csv('V102_test_feature.csv', encoding='utf-8')

# 1. 特征与标签
y = train['Attrition']
X = train.drop(columns=['user_id', 'EmployeeNumber', 'Attrition'])
X_test = test.drop(columns=['user_id', 'EmployeeNumber'])

# 2. 划分训练集和验证集，评估AUC
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = DecisionTreeClassifier(max_depth=4, random_state=42)
model.fit(X_train, y_train)

val_pred = model.predict_proba(X_val)[:, 1]
auc = roc_auc_score(y_val, val_pred)
print(f'验证集AUC: {auc:.4f}')

# 3. 打印决策树规则
feature_names = X.columns.tolist()
rules = export_text(model, feature_names=feature_names, max_depth=4)
print('决策树规则如下：')
print(rules)

# 4. 决策树可视化（仅保存为png）
plt.figure(figsize=(20,10))
tree.plot_tree(model, feature_names=feature_names, class_names=['No', 'Yes'], filled=True, rounded=True, max_depth=4, fontsize=10)
plt.savefig('V106_cart_tree.png', dpi=200, bbox_inches='tight')
plt.close()

print('决策树可视化已保存为 V106_cart_tree.png。') 