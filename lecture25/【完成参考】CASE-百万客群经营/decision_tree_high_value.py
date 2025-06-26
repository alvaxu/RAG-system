import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import warnings
import matplotlib

warnings.filterwarnings('ignore')  # 忽略所有警告

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
matplotlib.rcParams['axes.unicode_minus'] = False    # 正常显示负号

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

# 构造标签：未来3个月资产是否提升至100万+（模拟）
np.random.seed(42)
df['future_total_assets'] = df['total_assets'] * np.random.uniform(0.95, 1.2, size=len(df))
df['label'] = (df['future_total_assets'] >= 1000000).astype(int)

# 选择特征
features = [
    'total_assets', 'monthly_income', 'product_count', 'app_login_count',
    'financial_repurchase_count', 'investment_monthly_count'
]
features = [f for f in features if f in df.columns]
X = df[features].fillna(0)
y = df['label']

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 训练决策树模型（depth=4）
tree = DecisionTreeClassifier(max_depth=4, random_state=42)
tree.fit(X_train, y_train)

# 文本打印决策树结构
print('决策树结构（文本表示）：')
print(export_text(tree, feature_names=list(X.columns), show_weights=True))

# 可视化决策树并保存图片
plt.figure(figsize=(18, 8))
plot_tree(tree, feature_names=list(X.columns), class_names=['未达标', '达标'], filled=True, rounded=True, fontsize=12)
plt.title('决策树（depth=4）预测客户未来3个月资产是否提升至100万+')
plt.tight_layout()
plt.savefig('tree_depth4.png', dpi=150)
plt.show()

# 中文注释：
# 本脚本用于决策树（depth=4）预测客户未来3个月资产是否能提升至100万+，输出文本树结构和可视化图片。 