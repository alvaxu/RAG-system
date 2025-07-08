import pandas as pd
import numpy as np
import lightgbm as lgb

# 设置matplotlib中文字体，防止乱码
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# ========== 加载模型 ==========
model_path = 'lgbm_high_value_model.txt'
gbm = lgb.Booster(model_file=model_path)

# ========== 指定客户特征输入 ==========
# 请根据实际客户数据填写以下特征
customer_data = {
    'total_assets': 950000,  # 当前总资产
    'monthly_income': 50000, # 月收入
    'product_count': 3,      # 产品持有数
    'app_login_count': 10,   # 手机银行登录次数
    'financial_repurchase_count': 2, # 理财复购次数
    'investment_monthly_count': 1    # 月均投资次数
}

# 保证特征顺序与训练一致
features = [
    'total_assets', 'monthly_income', 'product_count', 'app_login_count',
    'financial_repurchase_count', 'investment_monthly_count'
]

X_pred = pd.DataFrame([customer_data], columns=features).fillna(0)

# ========== 预测 ==========
prob = gbm.predict(X_pred)[0]
label = int(prob >= 0.5)

# ========== 输出结果 ==========
print(f'预测概率：{prob:.4f}')
print(f'预测结果：{"未来3个月资产可达100万+" if label == 1 else "未来3个月资产难以达100万"}')

# ========== 中文注释 ==========
# 本脚本用于加载已训练的LightGBM模型，对指定客户特征进行百万资产预测。
# 请根据实际客户数据修改customer_data字典。 