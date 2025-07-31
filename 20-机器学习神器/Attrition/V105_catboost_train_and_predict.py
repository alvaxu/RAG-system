'''
程序说明：
## 1. 本程序使用原始特征训练CatBoost模型进行员工离职预测。
## 2. 输出本地AUC分数，并生成可提交的测试集预测结果csv。
'''
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

# 读取原始特征数据
train = pd.read_csv('V102_train_feature.csv', encoding='utf-8')
test = pd.read_csv('V102_test_feature.csv', encoding='utf-8')

# 1. 特征与标签
y = train['Attrition']
X = train.drop(columns=['user_id', 'EmployeeNumber', 'Attrition'])
X_test = test.drop(columns=['user_id', 'EmployeeNumber'])

# 自动识别类别型特征（CatBoost支持）
cat_features = [col for col in X.columns if ('_' not in col and X[col].dtype == 'int64' and len(X[col].unique()) < 10) or X[col].dtype == 'object']

# 2. 划分训练集和验证集，评估AUC
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = CatBoostClassifier(iterations=500, learning_rate=0.05, depth=6, cat_features=cat_features, verbose=100, random_state=42)
model.fit(X_train, y_train, eval_set=(X_val, y_val), use_best_model=True)

val_pred = model.predict_proba(X_val)[:, 1]
auc = roc_auc_score(y_val, val_pred)
print(f'验证集AUC: {auc:.4f}')

# 3. 用全量训练集训练并预测测试集
model.fit(X, y, cat_features=cat_features, verbose=100)
test_pred = model.predict_proba(X_test)[:, 1]

# 4. 生成提交文件
submit = pd.DataFrame({'user_id': test['user_id'], 'Attrition': test_pred})
submit.to_csv('V105_submit_catboost.csv', index=False, encoding='utf-8')
print('测试集预测结果已保存为 V105_submit_catboost.csv，格式符合提交要求。') 