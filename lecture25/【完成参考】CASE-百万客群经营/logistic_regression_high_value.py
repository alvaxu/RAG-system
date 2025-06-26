import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
import warnings
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

warnings.filterwarnings('ignore')  # 忽略所有警告

# 读取数据
try:
    df = pd.read_csv('二组模拟数据.csv', encoding='utf-8')
except Exception:
    df = pd.read_csv('二组模拟数据.csv', encoding='gbk')

# 数据准备
# 将AUM（资产管理规模）作为主要特征
df['total_assets'] = df['total_aum']  # 使用total_aum作为总资产
# 从月均交易金额、月均登录次数等生成衍生特征
df['monthly_income'] = df['monthly_transaction_amount'] * 0.3  # 模拟月收入
df['product_count'] = (df['deposit_balance'] > 0).astype(int) + \
                      (df['wealth_management_balance'] > 0).astype(int) + \
                      (df['fund_balance'] > 0).astype(int) + \
                      (df['insurance_balance'] > 0).astype(int)
df['app_login_count'] = df['mobile_bank_login_count']
df['financial_repurchase_count'] = df['monthly_transaction_count'] * (df['wealth_management_balance'] > 0).astype(int)
df['investment_monthly_count'] = df['monthly_transaction_count'] * ((df['fund_balance'] > 0) | (df['wealth_management_balance'] > 0)).astype(int)

# 构造标签：未来3个月资产是否提升至100万+（模拟，假设total_assets字段为当前资产，随机生成未来资产）
np.random.seed(42)
df['future_total_assets'] = df['total_assets'] * np.random.uniform(0.95, 1.2, size=len(df))
df['label'] = (df['future_total_assets'] >= 1000000).astype(int)

# 选择特征
features = [
    'total_assets', 'monthly_income', 'product_count', 'app_login_count',
    'financial_repurchase_count', 'investment_monthly_count'
]
# 部分特征可能缺失，做容错
features = [f for f in features if f in df.columns]
X = df[features].fillna(0)
y = df['label']

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 训练逻辑回归模型
model = LogisticRegression(max_iter=200, solver='lbfgs')
model.fit(X_train, y_train)

# 输出逻辑回归系数
coef = model.coef_[0]
feature_coef = pd.DataFrame({'特征': features, '系数': coef})
print('逻辑回归系数：')
print(feature_coef)

# 可视化逻辑回归系数（显示正负）
plt.figure(figsize=(8, 5))
# 按系数值排序并重置索引，确保显示顺序从大到小
feature_coef = feature_coef.sort_values('系数').reset_index(drop=True)
# 使用红蓝配色方案，突出正负效应
sns.barplot(x='系数', y='特征', data=feature_coef, palette='coolwarm', orient='h')
plt.axvline(0, color='gray', linestyle='--')
plt.title('逻辑回归特征系数（正负影响）')
plt.xlabel('系数')
plt.ylabel('特征')
plt.tight_layout()
plt.savefig('coefficient_bar.png', dpi=150)  # 保存图片
plt.show()

# 中文注释：
# 本脚本用于预测客户未来3个月资产提升至100万+的概率，输出逻辑回归系数并可视化，便于业务理解特征正负影响。

# 模型评估
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]
acc = accuracy_score(y_test, y_pred)
try:
    auc = roc_auc_score(y_test, y_prob)
except Exception:
    auc = None
print('\n模型评估结果：')
print(f'准确率：{acc:.4f}')
if auc is not None:
    print(f'AUC：{auc:.4f}')
print('分类报告：')
print(classification_report(y_test, y_pred, digits=4)) 