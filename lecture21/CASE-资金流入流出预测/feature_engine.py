import pandas as pd
from datetime import date, timedelta
import warnings

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
    df_interest['mfd_date'] = pd.to_datetime(df_interest['mfd_date'], format='%Y%m%d')
    df_interest = df_interest.set_index('mfd_date')
    print(f"收益率数据加载完成，共 {len(df_interest)} 天数据。")

    # --- 3. 加载和预处理 mfd_bank_shibor.csv ---
    df_shibor = pd.read_csv(shibor_csv_path, encoding='utf-8')
    df_shibor['mfd_date'] = pd.to_datetime(df_shibor['mfd_date'], format='%Y%m%d')
    df_shibor = df_shibor.set_index('mfd_date')
    print(f"Shibor数据加载完成，共 {len(df_shibor)} 天数据。")

    # --- 4. 加载 user_profile_table.csv (目前不直接合并到日级别数据，留作后续分群或用户特征使用) ---
    # df_profile = pd.read_csv(profile_csv_path, encoding='utf-8')
    # print(f"用户画像数据加载完成，共 {len(df_profile)} 条用户数据。")

    # --- 5. 合并数据 ---
    # 将收益率和Shibor数据合并到主聚合数据框
    df_merged = df_agg.merge(df_interest, left_index=True, right_index=True, how='left')
    df_merged = df_merged.merge(df_shibor, left_index=True, right_index=True, how='left')

    # 对合并后的外部时间序列数据进行前向填充，处理缺失值
    df_merged['mfd_daily_yield'] = df_merged['mfd_daily_yield'].fillna(method='ffill')
    df_merged['mfd_7daily_yield'] = df_merged['mfd_7daily_yield'].fillna(method='ffill')
    # 修正 Shibor 列名以匹配实际数据，并确保填充
    if 'Interest_O_N' in df_shibor.columns: # 检查实际列名
        df_merged['Interest_O_N'] = df_merged['Interest_O_N'].fillna(method='ffill')
    if 'Interest_1_W' in df_shibor.columns:
        df_merged['Interest_1_W'] = df_merged['Interest_1_W'].fillna(method='ffill')
    if 'Interest_2_W' in df_shibor.columns:
        df_merged['Interest_2_W'] = df_merged['Interest_2_W'].fillna(method='ffill')
    if 'Interest_1_M' in df_shibor.columns:
        df_merged['Interest_1_M'] = df_merged['Interest_1_M'].fillna(method='ffill')
    if 'Interest_3_M' in df_shibor.columns:
        df_merged['Interest_3_M'] = df_merged['Interest_3_M'].fillna(method='ffill')
    if 'Interest_6_M' in df_shibor.columns:
        df_merged['Interest_6_M'] = df_merged['Interest_6_M'].fillna(method='ffill')
    if 'Interest_9_M' in df_shibor.columns:
        df_merged['Interest_9_M'] = df_merged['Interest_9_M'].fillna(method='ffill')
    if 'Interest_1_Y' in df_shibor.columns:
        df_merged['Interest_1_Y'] = df_merged['Interest_1_Y'].fillna(method='ffill')

    # 确保填充后没有NaN，对于初始行的NaN，可以再进行一次回填或用0填充
    # 考虑到Shibor和收益率在最早日期也可能有NaN，这里回填一次。
    # 如果数据一开始就有缺失，ffill无法填充，bfill可以填充前面没有的。
    df_merged = df_merged.fillna(0) # 最终确保没有NaN，对于初始的NaN，用0填充，或者可以考虑更复杂的填充策略

    print("外部数据合并完成。")

    # --- 6. 生成时间序列特征 ---
    df_merged['weekday'] = df_merged.index.weekday # 0=周一, 6=周日
    df_merged['dayofmonth'] = df_merged.index.day
    df_merged['month'] = df_merged.index.month
    df_merged['year'] = df_merged.index.year
    df_merged['dayofyear'] = df_merged.index.dayofyear
    df_merged['weekofyear'] = df_merged.index.isocalendar().week.astype(int) # 周数

    # 独热编码星期几
    df_merged = pd.get_dummies(df_merged, columns=['weekday'], prefix='weekday')
    
    # 生成节假日特征
    df_merged['is_holiday'] = df_merged.index.map(is_special_day).astype(float) # 确保为float

    # 确保独热编码特征为浮点类型
    for col in [col for col in df_merged.columns if col.startswith('weekday_')]:
        df_merged[col] = df_merged[col].astype(float)

    # --- 7. 生成滞后特征 (可根据需要调整滞后天数) ---
    # 滞后申购金额和赎回金额
    for i in range(1, 8): # 考虑过去7天的滞后
        df_merged[f'purchase_lag_{i}d'] = df_merged['total_purchase_amt'].shift(i)
        df_merged[f'redeem_lag_{i}d'] = df_merged['total_redeem_amt'].shift(i)
    
    # 滞后收益率和Shibor
    # 确保所有Shibor利率都包含在滞后特征的生成中
    for col in ['mfd_daily_yield', 'mfd_7daily_yield', 
                'Interest_O_N', 'Interest_1_W', 'Interest_2_W', 
                'Interest_1_M', 'Interest_3_M', 'Interest_6_M', 
                'Interest_9_M', 'Interest_1_Y']:
        if col in df_merged.columns:
            for i in range(1, 4): # 考虑过去3天的滞后
                df_merged[f'{col}_lag_{i}d'] = df_merged[col].shift(i)

    # 填充滞后特征产生的NaN (使用前一个有效值填充，或根据实际情况选择其他填充策略)
    df_merged = df_merged.fillna(method='ffill')
    df_merged = df_merged.fillna(0) # 对于仍然存在的NaN，可能出现在序列最前端，用0填充

    print("时间序列特征和滞后特征生成完成。")

    # --- 8. 返回完整的特征数据框，不再进行日期筛选 ---
    print("特征工程完成，返回所有日期的数据。")
    return df_merged

if __name__ == "__main__":
    # 示例调用
    features_df = load_and_engineer_features()
    print("\n生成的特征数据框前5行：")
    print(features_df.head())
    print("\n生成的特征数据框信息：")
    features_df.info()
    print("\n申购金额和赎回金额的描述性统计：")
    print(features_df[['total_purchase_amt', 'total_redeem_amt']].describe()) 