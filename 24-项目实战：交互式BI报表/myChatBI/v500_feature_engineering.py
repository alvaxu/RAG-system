'''
程序说明：
## 1. 本模块为5.0.0版股票分析系统的统一特征工程模块，所有分析与预测工具（LSTM、ARIMA、Prophet等）均通过本模块进行特征处理。
## 2. 支持时间特征、价格/成交量衍生特征、滚动统计特征等，接口统一，便于扩展和维护。
'''

import pandas as pd
import numpy as np
import chinese_calendar
from typing import List, Optional

# ================== 特征工程主接口 ==================
def add_all_features(df: pd.DataFrame, 
                    price_cols: Optional[List[str]] = None, 
                    vol_col: str = 'vol', 
                    date_col: str = 'trade_date') -> pd.DataFrame:
    """
    :function: 对股票历史数据DataFrame添加全部常用特征（时间、衍生、滚动统计等）
    :param df: 原始DataFrame，需包含open/high/low/close/vol/trade_date等字段
    :param price_cols: 价格相关字段名列表，默认['open','high','low','close','pre_close']
    :param vol_col: 成交量字段名，默认'vol'
    :param date_col: 日期字段名，默认'trade_date'
    :return: 增加特征后的DataFrame
    """
    df = df.copy()
    if price_cols is None:
        price_cols = ['open','high','low','close','pre_close']
    # ========== 时间特征 ==========
    df[date_col] = pd.to_datetime(df[date_col])
    df['weekday'] = df[date_col].dt.weekday
    df['month_period'] = df[date_col].dt.day.apply(lambda d: 0 if d<=10 else (1 if d<=20 else 2))
    df['is_month_end'] = df[date_col].dt.is_month_end.astype(int)
    df['is_holiday'] = df[date_col].apply(lambda d: int(chinese_calendar.is_holiday(d)))
    df['is_trade_day'] = df.apply(lambda row: int((row['weekday']<5) and (row['is_holiday']==0)), axis=1)
    df['is_post_holiday_trade_day'] = 0
    for i in range(1, len(df)):
        if df.loc[i-1, 'is_trade_day']==0 and df.loc[i, 'is_trade_day']==1:
            df.loc[i, 'is_post_holiday_trade_day'] = 1
    df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
    df['weekday_cos'] = np.cos(2 * np.pi * df['weekday'] / 7)
    # ========== 价格/成交量衍生特征 ==========
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['close_ma5_diff'] = df['close'] - df['ma5']
    df['close_ma10_diff'] = df['close'] - df['ma10']
    df['pct_chg_mean5'] = df['pct_chg'].rolling(5).mean() if 'pct_chg' in df.columns else 0
    df['pct_chg_std5'] = df['pct_chg'].rolling(5).std() if 'pct_chg' in df.columns else 0
    df['abs_pct_chg'] = df['pct_chg'].abs() if 'pct_chg' in df.columns else 0
    df['amplitude'] = (df['high'] - df['low']) / df['pre_close'].replace(0, np.nan)
    df['close_open_diff'] = df['close'] - df['open']
    df['high_low_diff'] = df['high'] - df['low']
    df['vol_ratio'] = df[vol_col] / (df[vol_col].rolling(5).mean().replace(0, np.nan))
    df['turnover_rate'] = df[vol_col] / (df[vol_col].sum() + 1e-6)
    df['close_ma5_ratio'] = df['close'] / (df['ma5'].replace(0, np.nan))
    df['close_ma10_ratio'] = df['close'] / (df['ma10'].replace(0, np.nan))
    if 'amount' in df.columns:
        df['amount_mean5_ratio'] = df['amount'] / (df['amount'].rolling(5).mean().replace(0, np.nan))
    else:
        df['amount_mean5_ratio'] = 0
    # ========== 滚动统计特征 ==========
    for col in price_cols + [vol_col]:
        df[f'{col}_mean5'] = df[col].rolling(5).mean()
        df[f'{col}_std5'] = df[col].rolling(5).std()
        df[f'{col}_max5'] = df[col].rolling(5).max()
        df[f'{col}_min5'] = df[col].rolling(5).min()
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    return df

# ================== 特征选择工具 ==================
def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    :function: 自动筛选可用于建模的特征列
    :param df: DataFrame
    :return: 特征列名列表
    """
    exclude = ['stock_name','ts_code','trade_date','open','high','low','close','pre_close','vol','amount','pct_chg','change']
    return [col for col in df.columns if col not in exclude and df[col].dtype in [np.float64, np.int64, float, int]]

# ================== 使用示例 ==================
if __name__ == '__main__':
    print("特征工程模块测试：")
    # 假设有一个DataFrame df_stock，包含基本行情字段
    # df_stock = pd.read_csv('your_stock_data.csv')
    # df_feat = add_all_features(df_stock)
    # print(df_feat.head())
    print("请在实际分析工具中导入本模块并调用add_all_features(df)即可。") 
