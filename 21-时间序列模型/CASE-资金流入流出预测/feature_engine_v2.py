import pandas as pd
from datetime import date, timedelta, datetime
import warnings
import numpy as np

warnings.filterwarnings("ignore")

# 将法定节假日定义为pandas.Timestamp对象集合，以便与DataFrame的index（Timestamp类型）直接比较
_holidays_2014_timestamps = {
    pd.Timestamp(2014, 1, 1), # 元旦
    pd.Timestamp(2014, 1, 31), pd.Timestamp(2014, 2, 1), pd.Timestamp(2014, 2, 2), pd.Timestamp(2014, 2, 3), pd.Timestamp(2014, 2, 4), pd.Timestamp(2014, 2, 5), pd.Timestamp(2014, 2, 6), # 春节
    pd.Timestamp(2014, 4, 5), pd.Timestamp(2014, 4, 6), pd.Timestamp(2014, 4, 7), # 清明节
    pd.Timestamp(2014, 5, 1), pd.Timestamp(2014, 5, 2), pd.Timestamp(2014, 5, 3), # 劳动节
    pd.Timestamp(2014, 5, 31), pd.Timestamp(2014, 6, 1), pd.Timestamp(2014, 6, 2), # 六一儿童节 / 端午节 (2014年为同一假期范围)
    pd.Timestamp(2014, 9, 6), pd.Timestamp(2014, 9, 7), pd.Timestamp(2014, 9, 8), # 中秋节
    pd.Timestamp(2014, 10, 1), pd.Timestamp(2014, 10, 2), pd.Timestamp(2014, 10, 3), pd.Timestamp(2014, 10, 4), pd.Timestamp(2014, 10, 5), pd.Timestamp(2014, 10, 6), pd.Timestamp(2014, 10, 7) # 国庆节
}

"""
:function: 判断日期是否为法定节假日（2014年中国大陆主要节假日）或周末
:param date_obj: pandas.Timestamp 对象
:return: True 如果是节假日或周末，否则 False
"""
def is_special_day(date_obj):
    # date_obj 将是 pandas.Timestamp 类型
    
    # 检查是否为周末
    if date_obj.weekday() in [5, 6]: # 5是周六，6是周日
        return True
    # 检查是否为法定节假日
    if date_obj in _holidays_2014_timestamps: # 直接与Timestamp集合比较
        return True
    return False

"""
:function: 加载数据并进行特征工程
:param balance_csv_path: 用户余额表CSV文件路径
:param profile_csv_path: 用户画像表CSV文件路径
:param shibor_csv_path: Shibor利率表CSV文件路径
:param interest_csv_path: 收益率表CSV文件路径
:return: pd.DataFrame 包含处理后的所有数据和所有特征
"""
def load_and_engineer_features(
    balance_csv_path='user_balance_table.csv',
    profile_csv_path='user_profile_table.csv',
    shibor_csv_path='mfd_bank_shibor.csv',
    interest_csv_path='mfd_day_share_interest.csv'
):
    print("开始加载数据并进行特征工程...")

    # --- 1. 加载和预处理 user_balance_table.csv ---
    try:
        df_balance = pd.read_csv(balance_csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df_balance = pd.read_csv(balance_csv_path, encoding='gbk')
    
    df_balance['report_date'] = pd.to_datetime(df_balance['report_date'], format='%Y%m%d')
    # 按日期汇总申购和赎回金额
    df_agg = df_balance.groupby('report_date').agg(
        total_purchase_amt=('total_purchase_amt', 'sum'),
        total_redeem_amt=('total_redeem_amt', 'sum')
    ).reset_index()
    df_agg = df_agg.set_index('report_date').sort_index()

    print(f"原始申购赎回数据加载完成，共 {len(df_agg)} 天数据。")

    # --- 2. 加载和预处理 mfd_day_share_interest.csv ---
    df_interest = pd.read_csv(interest_csv_path, encoding='utf-8')
    df_interest.columns = df_interest.columns.str.strip() # 清理列名，去除空格
    df_interest['mfd_date'] = pd.to_datetime(df_interest['mfd_date'], format='%Y%m%d')
    df_interest = df_interest.set_index('mfd_date')
    print(f"收益率数据加载完成，共 {len(df_interest)} 天数据。")

    # --- 3. 加载和预处理 mfd_bank_shibor.csv ---
    df_shibor = pd.read_csv(shibor_csv_path, encoding='utf-8')
    df_shibor.columns = df_shibor.columns.str.strip() # 清理列名，去除空格
    # 重命名列以匹配之前的修复
    df_shibor.rename(columns={'Interest_O_N': 'Interest_0_N'}, inplace=True)
    df_shibor['mfd_date'] = pd.to_datetime(df_shibor['mfd_date'], format='%Y%m%d')
    df_shibor = df_shibor.set_index('mfd_date')
    print(f"Shibor数据加载完成，共 {len(df_shibor)} 天数据。")

    # --- 4. 合并数据到完整日期范围 ---
    # 创建包含历史和预测期（额外30天）的完整日期范围
    start_full_date = df_agg.index.min()
    end_full_date = df_agg.index.max() + timedelta(days=30) # 包含预测期
    full_date_range = pd.date_range(start=start_full_date, end=end_full_date, freq='D')
    
    df_full = pd.DataFrame(index=full_date_range) # 以完整日期范围为索引

    # 将申购赎回数据合并
    df_full = df_full.merge(df_agg[['total_purchase_amt', 'total_redeem_amt']],
                            left_index=True, right_index=True, how='left')
    
    # 将收益率和Shibor数据合并
    df_full = df_full.merge(df_interest, left_index=True, right_index=True, how='left')
    df_full = df_full.merge(df_shibor, left_index=True, right_index=True, how='left')

    # 对合并后的数据进行前向填充，处理缺失值
    # 注意：这里只对外部变量进行前向填充，申购赎回的NaN代表没有数据，应保持或用0填充
    for col in df_full.columns:
        if col not in ['total_purchase_amt', 'total_redeem_amt']:
            df_full[col] = df_full[col].fillna(method='ffill')
    
    # 申购赎回金额的NaN（例如未来日期和原始数据中不存在的日期）用0填充
    df_full[['total_purchase_amt', 'total_redeem_amt']] = df_full[['total_purchase_amt', 'total_redeem_amt']].fillna(0)
    
    # 对于所有列，如果ffill后仍然有NaN（如序列最前端），则用0填充
    df_full = df_full.fillna(0) 

    print("外部数据合并完成。")

    # --- 5. 生成时间序列特征 (基于完整的 df_full) ---
    df_full['year'] = df_full.index.year
    df_full['month'] = df_full.index.month
    df_full['day'] = df_full.index.day
    df_full['dayofweek'] = df_full.index.weekday # 0=周一, 6=周日
    df_full['dayofyear'] = df_full.index.dayofyear
    df_full['weekofyear'] = df_full.index.isocalendar().week.astype(int) # 周数
    df_full['quarter'] = df_full.index.quarter
    df_full['is_month_start'] = df_full.index.is_month_start.astype(int)
    df_full['is_month_end'] = df_full.index.is_month_end.astype(int)
    df_full['is_quarter_start'] = df_full.index.is_quarter_start.astype(int)
    df_full['is_quarter_end'] = df_full.index.is_quarter_end.astype(int)
    df_full['is_year_start'] = df_full.index.is_year_start.astype(int)
    df_full['is_year_end'] = df_full.index.is_year_end.astype(int)
    df_full['is_weekend'] = ((df_full['dayofweek'] == 5) | (df_full['dayofweek'] == 6)).astype(int)

    # 趋势特征：从数据起始日开始的天数
    df_full['days_since_start'] = (df_full.index - df_full.index.min()).days

    # 添加傅里叶级数特征以捕捉周期性（季节性）
    # 年周期（基于 dayofyear）
    df_full['dayofyear_sin'] = np.sin(2 * np.pi * df_full['dayofyear'] / 365)
    df_full['dayofyear_cos'] = np.cos(2 * np.pi * df_full['dayofyear'] / 365)
    # 周周期（基于 dayofweek）
    df_full['dayofweek_sin'] = np.sin(2 * np.pi * df_full['dayofweek'] / 7)
    df_full['dayofweek_cos'] = np.cos(2 * np.pi * df_full['dayofweek'] / 7)

    # 独热编码星期几
    # 确保生成所有7个weekday的列，即使某些在训练集中可能不出现
    weekday_dummies = pd.get_dummies(df_full['dayofweek'], prefix='weekday').astype(int)
    df_full = pd.concat([df_full, weekday_dummies], axis=1)
    
    # 生成节假日特征
    df_full['is_holiday'] = df_full.index.map(is_special_day).astype(float) # 确保为float

    # 独热编码节假日类型 - 之前 feature_engine 没有这个，现在添加，但需要 holidays_2014 到字符串映射
    # 考虑到 is_special_day 函数只返回 True/False，或者 None，这里不能直接使用它来做独热编码。
    # 需要一个函数来返回节假日名称，类似于 6.lightgbm_forecast.py 中的 is_special_day
    # 为了避免重复逻辑，暂时不在 feature_engine 中直接生成具体节假日独热编码，
    # 而是依赖 is_holiday 和 weekday_dummies。

    # --- 6. 生成滞后特征 (可根据需要调整滞后天数) ---
    # 滞后申购金额和赎回金额
    for i in [1, 2, 3, 7, 14, 28, 30]: # 增加更深层次的滞后，考虑周、月周期
        df_full[f'total_purchase_amt_lag_{i}d'] = df_full['total_purchase_amt'].shift(i)
        df_full[f'total_redeem_amt_lag_{i}d'] = df_full['total_redeem_amt'].shift(i)
    
    # 滞后收益率和Shibor
    # 确保所有Shibor利率都包含在滞后特征的生成中
    for col in ['mfd_daily_yield', 'mfd_7_daily_yield',
                'Interest_0_N', 'Interest_1_W', 'Interest_2_W', 
                'Interest_1_M', 'Interest_3_M', 'Interest_6_M', 
                'Interest_9_M', 'Interest_1_Y']:
        if col in df_full.columns: # 检查列是否存在
            for i in [1, 2, 3, 7]: # 收益率和Shibor也考虑更长的滞后
                df_full[f'{col}_lag_{i}d'] = df_full[col].shift(i)

    # 新增滚动统计特征（更多窗口）
    for col in ['total_purchase_amt', 'total_redeem_amt', 'mfd_daily_yield', 'mfd_7_daily_yield',
                'Interest_0_N', 'Interest_1_W', 'Interest_1_M']:
        if col in df_full.columns: # 检查列是否存在，避免KeyError
            for window in [7, 14, 28]: # 增加7天、14天、28天滚动窗口
                df_full[f'{col}_rolling_mean_{window}'] = df_full[col].rolling(window=window).mean().shift(1)
                df_full[f'{col}_rolling_std_{window}'] = df_full[col].rolling(window=window).std().shift(1)
                df_full[f'{col}_rolling_min_{window}'] = df_full[col].rolling(window=window).min().shift(1)
                df_full[f'{col}_rolling_max_{window}'] = df_full[col].rolling(window=window).max().shift(1)


    # 填充滞后特征产生的NaN (使用前一个有效值填充，或根据实际情况选择其他填充策略)
    # 再次填充是为了处理滞后特征本身产生的NaN，这些NaN只会在序列的起始部分出现
    df_full = df_full.fillna(method='ffill')
    df_full = df_full.fillna(0) # 对于仍然存在的NaN，可能出现在序列最前端，用0填充

    print("时间序列特征和滞后特征生成完成。")

    # --- 7. 返回完整的特征数据框 ---
    print("特征工程完成，返回所有日期的数据。")
    return df_full

if __name__ == "__main__":
    # 示例调用
    features_df = load_and_engineer_features()
    print("\n生成的特征数据框前5行：")
    print(features_df.head())
    print("\n生成的特征数据框信息：")
    features_df.info()
    print("\n申购金额和赎回金额的描述性统计：")
    print(features_df[['total_purchase_amt', 'total_redeem_amt']].describe()) 