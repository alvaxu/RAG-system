'''
程序说明：
## 1. 本文件基于8.0.5_lgbm_recursive.py，仅使用申购/赎回各自Top20特征进行递归训练和预测。
## 2. 其他流程（特征工程、调试/正式切换、结构化输出等）与8.0.5版保持一致。
## 3. 便于调试和正式切换，控制台输出特征名、特征数等关键信息。
'''
# ... existing code ...
# ========== 特征列 ==========
NON_FEATURES = [USER_ID, DATE, TARGET_PURCHASE, TARGET_REDEEM, 'month']
# 申购Top20特征
PURCHASE_TOP20 = [
    'Interest_1_W_lag1', 'Interest_6_M_lag1', 'Interest_1_Y_lag1', 'Interest_2_W_lag1', 'mfd_daily_yield_lag1',
    'Interest_1_M_lag1', 'Interest_9_M_lag1', 'total_purchase_amt_lag1', 'Interest_O_N_lag1', 'Interest_3_M_lag1',
    'total_redeem_amt_lag1', 'mfd_7daily_yield_lag1', 'total_purchase_amt_lag3', 'total_purchase_amt_lag7',
    'total_purchase_amt_lag30', 'purchase_amt_bin', 'total_purchase_amt_lag14', 'total_redeem_amt_lag3',
    'constellation', 'day'
]
# 赎回Top20特征
REDEEM_TOP20 = [
    'mfd_daily_yield_lag1', 'Interest_3_M_lag1', 'total_redeem_amt_lag1', 'Interest_1_Y_lag1', 'total_purchase_amt_lag1',
    'Interest_1_W_lag1', 'Interest_9_M_lag1', 'mfd_7daily_yield_lag1', 'Interest_1_M_lag1', 'Interest_2_W_lag1',
    'Interest_O_N_lag1', 'Interest_6_M_lag1', 'sex_weekday', 'total_redeem_amt_lag3', 'total_purchase_amt_lag3',
    'constellation', 'total_purchase_amt_lag7', 'total_redeem_amt_lag7', 'total_purchase_amt_lag30', 'total_purchase_amt_lag14'
]
# 只保留Top20特征
PURCHASE_FEATURES = [f for f in PURCHASE_TOP20 if f in train_df.columns]
REDEEM_FEATURES = [f for f in REDEEM_TOP20 if f in train_df.columns]
PURCHASE_LAG_FEATURES = [f for f in PURCHASE_FEATURES if 'lag' in f]
REDEEM_LAG_FEATURES = [f for f in REDEEM_FEATURES if 'lag' in f]

print("==========================")
print("【特征工程阶段】")
print("--------------------------")
print(f"申购Top20特征数: {len(PURCHASE_FEATURES)}")
print("申购Top20特征名:")
print(PURCHASE_FEATURES)
print(f"赎回Top20特征数: {len(REDEEM_FEATURES)}")
print("赎回Top20特征名:")
print(REDEEM_FEATURES)
print("--------------------------")

# ========== 递归训练/混合训练主流程 ==========
# ... existing code ...
print('训练申购模型...')
purchase_model = scheduled_sampling_train(train_df, TARGET_PURCHASE, PURCHASE_FEATURES, PURCHASE_LAG_FEATURES, prob=0.8, n_rounds=PURCHASE_N_ROUNDS)
print('训练赎回模型...')
redeem_model = scheduled_sampling_train(train_df, TARGET_REDEEM, REDEEM_FEATURES, REDEEM_LAG_FEATURES, prob=0.8, n_rounds=REDEEM_N_ROUNDS)
# ... existing code ...
print('递归预测申购...')
purchase_pred = recursive_predict(purchase_model, df, PURCHASE_FEATURES, PURCHASE_LAG_FEATURES, predict_dates, USER_ID, DATE, TARGET_PURCHASE)
print('递归预测赎回...')
redeem_pred = recursive_predict(redeem_model, df, REDEEM_FEATURES, REDEEM_LAG_FEATURES, predict_dates, USER_ID, DATE, TARGET_REDEEM)
# ... existing code ... 