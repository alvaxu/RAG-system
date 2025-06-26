import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import shap
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')  # 忽略所有警告

# 设置matplotlib中文字体，防止乱码
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# 读取数据
try:
    df_base = pd.read_csv('customer_base.csv', encoding='utf-8')
except Exception:
    df_base = pd.read_csv('customer_base.csv', encoding='gbk')
try:
    df_assets = pd.read_csv('customer_behavior_assets.csv', encoding='utf-8')
except Exception:
    df_assets = pd.read_csv('customer_behavior_assets.csv', encoding='gbk')

# 合并数据（以customer_id为主键）
df = pd.merge(df_base, df_assets, on='customer_id', how='inner')

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

# ========== SHAP 全局解释 ==========
explainer = shap.TreeExplainer(gbm)
shap_values = explainer.shap_values(X_test)

# summary_plot 展示全局特征重要性
plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values, X_test, feature_names=X_test.columns, show=False)
plt.title('SHAP全局特征重要性（summary_plot）')
plt.tight_layout()
plt.savefig('shap_summary_plot.png', dpi=150)
plt.show()

# 打印全局特征重要性均值（按绝对值排序）
shap_abs_mean = np.abs(shap_values).mean(axis=0)
print('全局SHAP特征重要性均值（按绝对值排序）：')
for f, v in sorted(zip(X_test.columns, shap_abs_mean), key=lambda x: -x[1]):
    print(f'{f}: {v:.4f}')

# ========== SHAP 局部解释 ==========
# 选择一个客户（如测试集第0个）
idx = 0
plt.figure(figsize=(10, 3))
shap.force_plot(explainer.expected_value, shap_values[idx], X_test.iloc[idx], feature_names=X_test.columns, matplotlib=True, show=False)
plt.title('SHAP局部解释（force_plot）- 单客户')
plt.savefig('shap_force_plot.png', dpi=150, bbox_inches='tight')
plt.show()

# 打印单个客户的SHAP值及特征贡献
print('\n单客户（测试集第0个）SHAP值及特征贡献：')
for f, shap_v, val in zip(X_test.columns, shap_values[idx], X_test.iloc[idx]):
    print(f'{f}: SHAP值={shap_v:.4f}, 特征值={val}')

# 中文注释：
# 本脚本用于基于LightGBM模型的SHAP全局和局部解释，输出summary_plot和force_plot图片。 