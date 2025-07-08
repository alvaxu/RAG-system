import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')  # 忽略所有警告

# 设置matplotlib中文字体，防止乱码
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

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

# 训练LightGBM模型
lgb_train = lgb.Dataset(X_train, y_train)
lgb_eval = lgb.Dataset(X_test, y_test, reference=lgb_train)
params = {
    'objective': 'binary',
    'metric': 'auc',
    'verbosity': -1,
    'boosting_type': 'gbdt',
    'seed': 42
}
gbm = lgb.train(params, lgb_train, num_boost_round=100, valid_sets=[lgb_train, lgb_eval])

# 输出特征重要性（文本）
print('特征重要性排序：')
importance = gbm.feature_importance()
for f, imp in sorted(zip(X.columns, importance), key=lambda x: -x[1]):
    print(f'{f}: {imp}')

# 可视化特征重要性
plt.figure(figsize=(8, 5))
lgb.plot_importance(gbm, max_num_features=10, importance_type='split', title='特征重要性排序', xlabel='重要性', ylabel='特征')
plt.tight_layout()
plt.savefig('lgbm_feature_importance.png', dpi=150)
plt.show()

# 保存模型到文件
model_path = 'lgbm_high_value_model.txt'
gbm.save_model(model_path)
print(f'模型已保存到: {model_path}')

# 中文注释：
# 本脚本用于LightGBM预测客户未来3个月资产是否能提升至100万+，输出特征重要性排序（文本和图片）。 
# 模型保存路径: lgbm_high_value_model.txt 