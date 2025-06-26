"""
:function: 使用LightGBM模型预测申购和赎回金额
:param balance_csv_path: 用户余额表CSV文件路径
调用feature_engine_v2.py中的load_and_engineer_features()函数生成特征
成绩：95.7593

"""

import pandas as pd
import numpy as np
import lightgbm as lgbm
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
from feature_engine_v2 import load_and_engineer_features # 导入特征工程函数

# 忽略所有警告
warnings.filterwarnings('ignore')

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def train_and_predict_lightgbm(df_features, forecast_start_date, forecast_end_date):
    """
    :function: 训练LightGBM模型并进行预测。
    :param df_features: 包含特征和目标变量的DataFrame
    :param forecast_start_date: 预测开始日期
    :param forecast_end_date: 预测结束日期
    :return: 包含预测结果的DataFrame
    """
    df_features = df_features.sort_index() # 确保索引已排序

    # 定义所有可能的特征列，排除目标变量和 report_date 索引本身
    # 明确列出所有可能的独热编码列
    all_possible_features = [col for col in df_features.columns if col not in ['total_purchase_amt', 'total_redeem_amt']]
    
    # 确保所有 weekday_X 列都在 feature_cols 中，即使它们在某些子集中可能为空
    for i in range(7): # weekday_0 to weekday_6
        if f'weekday_{i}' not in all_possible_features:
            all_possible_features.append(f'weekday_{i}')
            
    # 确保所有 holiday_X 列都在 feature_cols 中
    # 这里需要一个更动态的方式来获取所有可能的 holiday_X 列，因为 feature_engine 没有直接提供
    # 目前仅排除 'holiday_' 开头的，这个逻辑是正确的

    feature_cols = [col for col in all_possible_features if not col.startswith('holiday_')]

    # 划分训练集和预测集
    train_start_date = pd.Timestamp(2014, 3, 1) # 新增：训练数据开始日期
    train_df = df_features[(df_features.index >= train_start_date) & (df_features.index < forecast_start_date)].copy() # 使用 .copy() 避免 SettingWithCopyWarning
    predict_df = df_features[(df_features.index >= forecast_start_date) & (df_features.index <= forecast_end_date)].copy() # 使用 .copy()

    print(f"predict_df shape: {predict_df.shape}") # Debug print
    if not predict_df.empty:
        print(f"predict_df index min: {predict_df.index.min()}, max: {predict_df.index.max()}") # Debug print
    else:
        print("predict_df is empty!") # Debug print

    # 确保 X_train 和 X_predict 具有相同的列，并填充可能缺失的值（例如，某个星期几或节假日类型在子集中不存在）
    X_train = train_df.reindex(columns=feature_cols, fill_value=0) # 使用 reindex 确保所有列存在并填充0
    y_purchase_train = train_df['total_purchase_amt']
    y_redeem_train = train_df['total_redeem_amt']

    X_predict = predict_df.reindex(columns=feature_cols, fill_value=0) # 使用 reindex 确保所有列存在并填充0

    # 初始化LightGBM模型参数
    lgb_params = {
        'objective': 'regression', # 更改为MSE，以期捕捉更多波动
        'metric': 'rmse',
        'n_estimators': 1000,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 1,
        'lambda_l1': 0.1,
        'lambda_l2': 0.1,
        'num_leaves': 63, # 增加模型复杂度，允许学习更复杂的模式
        'verbose': -1, # 关闭详细输出，早停时会自动输出
        'n_jobs': -1,
        'seed': 42
    }

    # 定义早停回调函数
    callbacks = [
        lgbm.early_stopping(stopping_rounds=100, verbose=False), # 当验证集性能连续100轮没有提升时停止，不打印每次评估结果
        lgbm.log_evaluation(period=100) # 每100轮打印一次评估结果
    ]

    # 训练申购金额模型
    print("开始训练申购金额LightGBM模型...")
    model_purchase = lgbm.LGBMRegressor(**lgb_params)
    model_purchase.fit(X_train, y_purchase_train,
                        eval_set=[(X_train, y_purchase_train)], # 训练集作为评估集
                        eval_metric='rmse',
                        callbacks=callbacks)
    print("申购金额LightGBM模型训练完成。")

    # 预测申购金额
    predicted_purchase = model_purchase.predict(X_predict)
    # 确保预测结果非负
    predicted_purchase[predicted_purchase < 0] = 0
    # 转换为整数
    predicted_purchase = [int(round(x)) for x in predicted_purchase]

    # 训练赎回金额模型
    print("开始训练赎回金额LightGBM模型...")
    model_redeem = lgbm.LGBMRegressor(**lgb_params)
    model_redeem.fit(X_train, y_redeem_train,
                       eval_set=[(X_train, y_redeem_train)], # 训练集作为评估集
                       eval_metric='rmse',
                       callbacks=callbacks)
    print("赎回金额LightGBM模型训练完成。")

    # 预测赎回金额
    predicted_redeem = model_redeem.predict(X_predict)
    # 确保预测结果非负
    predicted_redeem[predicted_redeem < 0] = 0
    # 转换为整数
    predicted_redeem = [int(round(x)) for x in predicted_redeem]

    # 构建预测结果DataFrame
    forecast_dates = pd.date_range(start=forecast_start_date, end=forecast_end_date, freq='D')
    df_forecast_results = pd.DataFrame(index=forecast_dates, columns=['purchase', 'redeem'])

    # 准备用于递归预测的当前特征行
    # 从 df_features 中获取预测期的数据，但只保留非目标滞后特征和未来已知特征
    # 我们需要一个基础的预测期特征框架，其中申购/赎回的滞后特征最初是NaN
    # 这样，在递归预测时，我们可以明确地填充它们
    
    # 获取预测期内的所有特征列，但排除掉我们即将动态填充的滞后特征
    # 1. 识别出所有滞后申购和赎回的特征列
    lag_purchase_cols = [col for col in feature_cols if col.startswith('total_purchase_amt_lag_')]
    lag_redeem_cols = [col for col in feature_cols if col.startswith('total_redeem_amt_lag_')]
    
    # 2. 移除这些滞后列，得到基础的未来已知特征
    base_feature_cols = [col for col in feature_cols if col not in lag_purchase_cols and col not in lag_redeem_cols]

    # 初始化预测期的特征DataFrame，只包含未来已知的特征（如日期特征、外部变量、傅里叶特征）
    X_predict_base = df_features[base_feature_cols].loc[forecast_start_date:forecast_end_date].copy()

    # 创建一个完整的 X_predict 框架，包含所有特征列，用于填充递归预测的滞后特征
    # 初始时，所有滞后特征都将从 df_features 中继承，对于预测期开始，这些是历史的滞后值
    # 但是我们需要在每次迭代中更新它们
    X_current_predict_features = df_features[feature_cols].loc[forecast_start_date:forecast_end_date].copy()


    # 迭代预测每一天
    print("开始进行LightGBM递归预测...")
    for current_date in forecast_dates:
        # 获取当前日期的特征行
        # 使用 .loc 确保获取到的是一个 Series，而不是 DataFrame
        current_features_series = X_current_predict_features.loc[current_date].copy()

        # 对当前日期进行预测
        # LightGBM 模型期望二维数组输入，所以需要 reshape(-1, 1) 或者 .to_frame().T
        predicted_purchase_current = model_purchase.predict(current_features_series.to_frame().T)[0]
        predicted_redeem_current = model_redeem.predict(current_features_series.to_frame().T)[0]

        # 确保预测结果非负并转换为整数
        predicted_purchase_current = int(round(max(0, predicted_purchase_current)))
        predicted_redeem_current = int(round(max(0, predicted_redeem_current)))

        # 存储当前日的预测结果
        df_forecast_results.loc[current_date, 'purchase'] = predicted_purchase_current
        df_forecast_results.loc[current_date, 'redeem'] = predicted_redeem_current

        # 如果不是预测期的最后一天，更新下一天的滞后特征
        next_date = current_date + pd.Timedelta(days=1)
        if next_date <= forecast_end_date:
            # 遍历所有滞后天数，更新下一天的滞后特征
            for lag_days in [1, 2, 3, 7, 14, 28, 30]:
                if current_date + pd.Timedelta(days=lag_days) <= forecast_end_date:
                    # 更新申购金额滞后特征
                    if f'total_purchase_amt_lag_{lag_days}d' in feature_cols:
                        # 找到当前预测值应该作为哪个滞后特征（lag_days天前的特征）
                        # 例如，如果今天是 current_date，我们预测了 purchase_current
                        # 那么对于 next_date + (lag_days - 1) 天的预测，purchase_current 将是其 lag_days 天前的 purchase_amt
                        # 简单来说，当前日的预测值将成为未来的某个滞后特征
                        # 对于 next_date，它的 lag_1d 将是 current_date 的实际值 (如果 current_date 是训练集) 或预测值
                        # 我们需要将 current_date 的预测值，作为 next_date 的 lag_1d，
                        # next_date - 1 的 lag_2d，等等。
                        # 更准确的做法是，对于 next_date，其 lag_1d 就是 current_date 的预测值。
                        # 对于 next_date，其 lag_2d 就是 current_date - 1 的预测值。
                        # 这是一个滑动窗口的概念，需要对 X_current_predict_features 进行更新

                        # 将当前预测值填充到下一天对应的滞后特征位置
                        # 例如：对于 next_date，其 `lag_1d` 应该是 `current_date` 的预测值
                        # 对于 `next_date + 1`，其 `lag_2d` 应该是 `current_date` 的预测值
                        # 这需要更复杂的特征更新逻辑，这里我们简化处理，
                        # 直接将当前预测值作为下一天的 1-day 滞后特征。

                        # 更准确的递归更新方式：
                        # 在 X_current_predict_features 中，找到所有 *_lag_1d 的列，用当前预测值填充
                        # 然后 shift 这些列，将 lag_1d 变为 lag_2d，等等
                        # 这个操作需要作用于整个预测期部分的 X_current_predict_features
                        pass # 复杂，暂时不在这里实现，考虑用pd.Series.shift()

    # 简化递归更新逻辑：
    # 填充 df_features 中预测期内的申购赎回滞后特征
    # 我们可以用预测值来"回填" df_features 中的这些 NaN/0 值
    # 然后再用这个更新后的 df_features 来构建 X_predict
    # 或者，在循环中，直接更新 X_current_predict_features 的相关列

    # 递归预测的核心在于：
    # 对于每个要预测的日期 `t`，其特征向量 `X_t` 中包含 `target_lag_1d`, `target_lag_2d`, ...
    # 其中 `target_lag_1d` 是 `t-1` 的目标值
    # `target_lag_2d` 是 `t-2` 的目标值
    # ...
    # 当 `t-k` 位于训练集内时，使用真实值
    # 当 `t-k` 位于预测集内时，使用已经预测出的值

    # 重新构建预测循环，更清晰地处理滞后特征
    predicted_purchase_list = []
    predicted_redeem_list = []

    # 为了递归预测，我们需要一个临时的 DataFrame 来存储预测期间的真实值和预测值，
    # 以便为后续日期提供滞后特征
    temp_df = df_features.copy() # 复制一份完整的特征数据，用于在预测期填充预测值

    print("开始进行LightGBM递归预测 (修订版)...")
    for current_date in forecast_dates:
        # 获取当前日期的特征行
        # 注意：这里的 current_date 可能是预测期的第一天，也可能是中间某一天
        # 对于当前日期的特征，它的滞后特征应该包含：
        #   - 训练集内的真实历史值
        #   - 预测集内，但已完成预测的日期的预测值
        
        # 构建当前日期的特征向量
        current_features_row = temp_df.loc[current_date:current_date][feature_cols].copy()
        
        # 预测申购金额
        purchase_pred = model_purchase.predict(current_features_row)[0]
        purchase_pred = int(round(max(0, purchase_pred)))
        predicted_purchase_list.append(purchase_pred)

        # 预测赎回金额
        redeem_pred = model_redeem.predict(current_features_row)[0]
        redeem_pred = int(round(max(0, redeem_pred)))
        predicted_redeem_list.append(redeem_pred)

        # 将当前预测值"回填"到 temp_df 中，以便作为后续日期的滞后特征
        if current_date < forecast_end_date: # 如果不是预测期的最后一天
            # 更新 temp_df 中当前日期的 total_purchase_amt 和 total_redeem_amt
            # 这样在计算下一天的滞后特征时，可以利用到这些预测值
            temp_df.loc[current_date, 'total_purchase_amt'] = purchase_pred
            temp_df.loc[current_date, 'total_redeem_amt'] = redeem_pred

            # 重新计算下一天（或其后的几天）的滞后特征
            # 这里需要针对下一天的特征行，重新计算其依赖于 `current_date` 预测值的滞后特征
            # 这是一个复杂的过程，简单的方法是重新运行 feature_engine 的滞后部分
            # 但这效率低下。更优的方法是，每次预测后，仅更新 `temp_df` 中未来日期的对应滞后特征。

            # 另一种更简单的递归实现方式：
            # 每次循环，根据 temp_df 现有数据（包含历史真实值和已预测值），
            # 重新计算整个预测期内所有相关滞后特征。
            # 这是为了避免在 feature_engine 中进行 ffill/fillna(0) 对预测期内滞后特征的静态填充。

            # 再次调用特征工程的一部分，仅用于更新预测期的滞后特征
            # 这种方式会更准确地反映递归逻辑
            # 但是，由于 load_and_engineer_features 处理整个 DataFrame，我们不能简单地在这里调用它
            # 我们需要手动更新 future_date 的滞后特征
            # 考虑在循环外预先计算所有除滞后目标变量外的特征，然后在循环内手动更新滞后目标变量。

            # 鉴于 LightGBM 接受 `np.ndarray`，我们可以直接操作 numpy 数组来构建特征
            # 但为了可读性和与 pandas 的兼容性，我们还是用 DataFrame
            pass # 这个递归更新滞后特征的逻辑需要更细致的实现

    # 重新思考递归预测的实现：
    # 我们可以预先创建好所有未来已知特征 (日期特征，外部变量，傅里叶特征) 的 predict_df
    # 然后，在循环中，只更新 `total_purchase_amt_lag_Xd` 和 `total_redeem_amt_lag_Xd`。

    # 初始化用于预测的特征DataFrame，包含所有列，但预测期内的目标滞后特征需要动态填充
    X_predict_recursive = df_features[feature_cols].loc[forecast_start_date:forecast_end_date].copy()

    # 将预测期内的申购和赎回目标滞后特征清零或设为NaN，以便我们进行递归填充
    for col in lag_purchase_cols + lag_redeem_cols:
        X_predict_recursive[col] = np.nan # 用 NaN 标记需要动态填充的滞后特征

    predicted_purchase_list = []
    predicted_redeem_list = []

    print("开始进行LightGBM递归预测 (最终修订版)...")
    for i, current_date in enumerate(forecast_dates):
        # 构建当前日期的特征向量
        current_features_row = X_predict_recursive.loc[current_date].copy()

        # 对于当前日期的滞后特征，如果它们是NaN，则需要从历史数据或已预测数据中获取
        for lag_days in [1, 2, 3, 7, 14, 28, 30]:
            past_date = current_date - pd.Timedelta(days=lag_days)
            
            # 更新申购金额滞后特征
            lag_purchase_col = f'total_purchase_amt_lag_{lag_days}d'
            if lag_purchase_col in feature_cols and pd.isna(current_features_row[lag_purchase_col]):
                if past_date in train_df.index: # 如果滞后日期在训练集内，使用真实值
                    current_features_row[lag_purchase_col] = train_df.loc[past_date, 'total_purchase_amt']
                elif past_date in df_forecast_results.index: # 如果滞后日期在预测集内且已预测，使用预测值
                    current_features_row[lag_purchase_col] = df_forecast_results.loc[past_date, 'purchase']
                else: # 否则，如果滞后日期在所有数据之前，或者未预测，则为0
                    current_features_row[lag_purchase_col] = 0
            
            # 更新赎回金额滞后特征
            lag_redeem_col = f'total_redeem_amt_lag_{lag_days}d'
            if lag_redeem_col in feature_cols and pd.isna(current_features_row[lag_redeem_col]):
                if past_date in train_df.index:
                    current_features_row[lag_redeem_col] = train_df.loc[past_date, 'total_redeem_amt']
                elif past_date in df_forecast_results.index:
                    current_features_row[lag_redeem_col] = df_forecast_results.loc[past_date, 'redeem']
                else:
                    current_features_row[lag_redeem_col] = 0
        
        # 预测申购金额
        purchase_pred = model_purchase.predict(current_features_row.to_frame().T)[0]
        purchase_pred = int(round(max(0, purchase_pred)))
        predicted_purchase_list.append(purchase_pred)

        # 预测赎回金额
        redeem_pred = model_redeem.predict(current_features_row.to_frame().T)[0]
        redeem_pred = int(round(max(0, redeem_pred)))
        predicted_redeem_list.append(redeem_pred)

        # 将当前预测值填充到 df_forecast_results 中，以便在后续迭代中作为滞后特征使用
        df_forecast_results.loc[current_date, 'purchase'] = purchase_pred
        df_forecast_results.loc[current_date, 'redeem'] = redeem_pred

    df_forecast = pd.DataFrame({
        'report_date': forecast_dates.strftime('%Y%m%d'),
        'purchase': predicted_purchase_list,
        'redeem': predicted_redeem_list
    })

    # 为绘图准备数据：确保 history_data_for_plot 和 predict_data_for_plot 包含 'report_date' 列
    # train_df 和 predict_df 的索引已经是 report_date，我们将其转为列
    history_data_for_plot = train_df.copy()
    history_data_for_plot['report_date'] = history_data_for_plot.index # 将索引转为列
    history_data_for_plot = history_data_for_plot.reset_index(drop=True) # 重置旧索引

    predict_data_for_plot = predict_df.copy()
    predict_data_for_plot['report_date'] = predict_data_for_plot.index # 将索引转为列
    predict_data_for_plot = predict_data_for_plot.reset_index(drop=True) # 重置旧索引

    print("LightGBM预测完成。")
    return df_forecast, history_data_for_plot, predict_data_for_plot


def plot_results(history_df, predict_df, forecast_df, plot_title, save_path):
    """
    :function: 绘制历史数据与预测结果的趋势图。
    :param history_df: 历史数据DataFrame
    :param predict_df: 预测期实际数据DataFrame
    :param forecast_df: 预测结果DataFrame
    :param plot_title: 图表标题
    :param save_path: 图表保存路径
    :return: None
    """
    plt.figure(figsize=(20, 8))

    # 绘制申购金额
    plt.plot(history_df['report_date'], history_df['total_purchase_amt'], label='申购金额-历史', color='tab:blue')
    # 不再绘制预测期内的"实际"数据，因为这些数据在原始文件中缺失并被填充为0
    # plt.plot(predict_df['report_date'], predict_df['total_purchase_amt'], label='申购金额-实际', color='tab:blue', linestyle='-')
    plt.plot(pd.to_datetime(forecast_df['report_date']), forecast_df['purchase'], label='申购金额-预测', color='tab:blue', linestyle='--')

    # 绘制赎回金额
    plt.plot(history_df['report_date'], history_df['total_redeem_amt'], label='赎回金额-历史', color='tab:orange')
    # 不再绘制预测期内的"实际"数据
    # plt.plot(predict_df['report_date'], predict_df['total_redeem_amt'], label='赎回金额-实际', color='tab:orange', linestyle='-')
    plt.plot(pd.to_datetime(forecast_df['report_date']), forecast_df['redeem'], label='赎回金额-预测', color='tab:orange', linestyle='--')

    plt.title(plot_title)
    plt.xlabel('日期')
    plt.ylabel('金额')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.show()

if __name__ == '__main__':
    user_balance_path = 'user_balance_table.csv'
    mfd_day_share_interest_path = 'mfd_day_share_interest.csv'
    mfd_bank_shibor_path = 'mfd_bank_shibor.csv'

    # 定义预测的日期范围，确保为 pandas.Timestamp 对象以匹配 DataFrame 索引类型
    forecast_start_date = pd.Timestamp(2014, 9, 1)
    forecast_end_date = pd.Timestamp(2014, 9, 30)

    # 1. 加载数据并进行特征工程 (直接调用 feature_engine.py)
    df_features = load_and_engineer_features(
        balance_csv_path=user_balance_path,
        interest_csv_path=mfd_day_share_interest_path,
        shibor_csv_path=mfd_bank_shibor_path
    )
    print(f"特征工程完成，返回所有日期的数据。总列数: {df_features.shape[1]}")
    print(f"df_features index min: {df_features.index.min()}, max: {df_features.index.max()}") # Debug print

    # 2. 训练LightGBM模型并进行预测
    df_forecast_results, history_data_for_plot, predict_data_for_plot = train_and_predict_lightgbm(
        df_features.copy(), forecast_start_date, forecast_end_date
    )

    # 3. 保存预测结果到CSV
    output_csv_path = '6.lightgbm_forecast_201409.csv'
    df_forecast_results.to_csv(output_csv_path, index=False, header=False)
    print(f"LightGBM预测结果已保存到 {output_csv_path}")

    # 4. 绘制并保存趋势图
    plot_title = f"【LightGBM多特征预测】 2014-03~2014-08及未来30天每日申购与赎回金额趋势"
    plot_save_path = '6.lightgbm_forecast_trend_201409.png'
    plot_results(history_data_for_plot, predict_data_for_plot, df_forecast_results, plot_title, plot_save_path)
    print(f"趋势图已保存到 {plot_save_path}") 