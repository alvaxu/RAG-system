import pandas as pd
import numpy as np
import lightgbm as lgb
import shap

# ========== 1. 生成模拟客户数据并保存为xlsx ==========
np.random.seed(42)
n_customers = 20  # 可调整客户数量

data = {
    'total_assets': np.random.randint(500000, 1200000, n_customers),  # 当前总资产
    'monthly_income': np.random.randint(10000, 80000, n_customers),    # 月收入
    'product_count': np.random.randint(1, 5, n_customers),             # 产品持有数
    'app_login_count': np.random.randint(1, 30, n_customers),          # 手机银行登录次数
    'financial_repurchase_count': np.random.randint(0, 5, n_customers),# 理财复购次数
    'investment_monthly_count': np.random.randint(0, 4, n_customers)   # 月均投资次数
}
df = pd.DataFrame(data)
# 增加客户ID列，格式为CUST0001、CUST0002等
customer_ids = [f'CUST{i+1:04d}' for i in range(n_customers)]
df.insert(0, 'customer_id', customer_ids)
# 增加客户标签列（青年、中年、老年，随机分配）
tags = np.random.choice(['青年', '中年', '老年'], size=n_customers, p=[0.4, 0.4, 0.2])
df.insert(1, 'customer_tag', tags)

xlsx_path = 'simulated_customers.xlsx'
df.to_excel(xlsx_path, index=False)
print(f'已生成模拟客户数据并保存到: {xlsx_path}')

# ========== 2. 加载模型并批量预测 ==========
model_path = 'lgbm_high_value_model.txt'
gbm = lgb.Booster(model_file=model_path)
features = [
    'total_assets', 'monthly_income', 'product_count', 'app_login_count',
    'financial_repurchase_count', 'investment_monthly_count'
]
X_pred = df[features].fillna(0)
probs = gbm.predict(X_pred)
labels = (probs >= 0.5).astype(int)

# ========== 2.1 计算SHAP值并写入 ==========
explainer = shap.TreeExplainer(gbm)
shap_values = explainer.shap_values(X_pred)
# 计算每个客户的SHAP解释强度（如sum(abs(shap value))）
shap_strength = np.abs(shap_values).sum(axis=1)
df['SHAP解释强度'] = shap_strength
# 将每个特征的SHAP值单独写入一列
for i, feat in enumerate(features):
    df[f'SHAP_{feat}'] = shap_values[:, i]

# ========== 3. 写入预测结果到xlsx ==========
df['预测概率'] = probs
# 预测结果文本
result_text = np.where(labels == 1, '未来3个月资产可达100万+', '未来3个月资产难以达100万')
df['预测结果'] = result_text

df.to_excel(xlsx_path, index=False)
print(f'预测结果已写入: {xlsx_path}')

# ========== 中文注释 ==========
# 本脚本用于批量模拟客户数据，使用已训练LightGBM模型预测，并将结果写入Excel。 