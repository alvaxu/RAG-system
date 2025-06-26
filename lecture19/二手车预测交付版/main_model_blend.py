"""
main_model_blend.py

融合XGBoost、CatBoost、LightGBM三种模型的预测结果，自动调优权重以获得最优融合效果。
最优融合权重: XGB=0.55, CatBoost=0.30, LGB=0.15
融合验证集MAE: 490.9687
融合预测结果已保存为 main_model_blend_predict.csv

成绩：478.1295
"""
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error
import itertools

# 读取各模型的预测结果
xgb_pred = pd.read_csv('main_model_predict.csv')
cat_pred = pd.read_csv('main_model_catboost_predict.csv')
lgb_pred = pd.read_csv('main_model_lgb_predict.csv')

# 读取验证集真实值（从XGBoost模型的验证集分割方式）
# 由于各模型的验证集划分一致，直接用main_model.py的分割方式
from sklearn.model_selection import train_test_split
train_df = pd.read_csv('train_features.csv', dtype={'model': str})
X = train_df.drop(columns=['price'])
y = train_df['price']
_, X_val, _, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
val_saleid = X_val['SaleID'] if 'SaleID' in X_val.columns else None

# 读取各模型在验证集上的预测（需各模型保存验证集预测，或用相同分割重算）
# 这里假设各模型的验证集预测已保存为：
#   main_model_7000_val_pred.csv, main_model_catboost_val_pred.csv, main_model_lgb_val_pred.csv
# 若没有，可在各模型脚本中加保存验证集预测的代码
try:
    xgb_val_pred = pd.read_csv('main_model_7000_val_pred.csv')
    cat_val_pred = pd.read_csv('main_model_catboost_val_pred.csv')
    lgb_val_pred = pd.read_csv('main_model_lgb_val_pred.csv')
except FileNotFoundError:
    raise RuntimeError('请先在各模型脚本中保存验证集预测为 main_model_7000_val_pred.csv、main_model_catboost_val_pred.csv、main_model_lgb_val_pred.csv')

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
blend_submission.to_csv('main_model_blend_predict.csv', index=False)
print('融合预测结果已保存为 main_model_blend_predict.csv') 