'''
程序说明：
## 1. 本程序融合V100_XGBoost、V100_CatBoost、V100_LightGBM三种模型的预测结果，自动调优权重以获得最优融合效果。
## 2. 所有输入输出文件名均以V100_开头，适配新版特征工程和模型输出，结构更清晰，便于调试和复现。

日期:2025-07-17 15:53:30

分数:473.3405 (blending)

日期:2025-07-17 15:45:42

分数:514.5145(catboost)

日期:2025-07-17 15:44:32

分数:495.0750(lgb)

日期:2025-07-17 15:43:07

分数:493.0538（xgboost）
'''
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error
import itertools

# 读取各模型的预测结果
xgb_pred = pd.read_csv('V100_main_model_predict.csv')
cat_pred = pd.read_csv('V100_main_model_catboost_predict.csv')
lgb_pred = pd.read_csv('V100_main_model_lgb_predict.csv')

# 读取验证集真实值（与XGBoost模型的验证集分割方式一致）
from sklearn.model_selection import train_test_split
train_df = pd.read_csv('V100_train_features.csv')
X = train_df.drop(columns=['price'])
y = train_df['price']
_, X_val, _, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
val_saleid = X_val['SaleID'] if 'SaleID' in X_val.columns else None

# 读取各模型在验证集上的预测
try:
    xgb_val_pred = pd.read_csv('V100_main_model_val_pred.csv')
    cat_val_pred = pd.read_csv('V100_main_model_catboost_val_pred.csv')
    lgb_val_pred = pd.read_csv('V100_main_model_lgb_val_pred.csv')
except FileNotFoundError:
    raise RuntimeError('请先在各模型脚本中保存验证集预测为 V100_main_model_val_pred.csv、V100_main_model_catboost_val_pred.csv、V100_main_model_lgb_val_pred.csv')

# 融合权重自动调优（暴力网格搜索）
best_mae = float('inf')
best_weights = (1/3, 1/3, 1/3)
for w1, w2, w3 in itertools.product(np.arange(0, 1.01, 0.05), repeat=3):
    if abs(w1 + w2 + w3 - 1) > 1e-6:
        continue
    blend_val_pred = w1 * xgb_val_pred['price'] + w2 * cat_val_pred['price'] + w3 * lgb_val_pred['price']
    mae = mean_absolute_error(y_val, blend_val_pred)
    if mae < best_mae:
        best_mae = mae
        best_weights = (w1, w2, w3)

print(f'最优融合权重: XGB={best_weights[0]:.2f}, CatBoost={best_weights[1]:.2f}, LGB={best_weights[2]:.2f}')
print(f'融合验证集MAE: {best_mae:.4f}')

# 用最优权重融合测试集预测
blend_test_pred = best_weights[0] * xgb_pred['price'] + best_weights[1] * cat_pred['price'] + best_weights[2] * lgb_pred['price']
blend_submission = pd.DataFrame({'SaleID': xgb_pred['SaleID'], 'price': blend_test_pred})
blend_submission.to_csv('V100_main_model_blend_predict.csv', index=False)
print('融合预测结果已保存为 V100_main_model_blend_predict.csv') 