# 4.1.3_stock_predict_lstm.py
'''
程序说明：
## 1. 本程序为4.1.3版股票LSTM预测系统，集成了更稳健的特征工程与归一化方案，提升递推多步预测的稳定性。
## 2. 新增未来预测递推与两种验证集递推方案：
##    - 未来预测：用T-（N-1)到T+0真实值递推预测T+1，后续每步用前面预测值+真实历史递推到T+N。
##    - 验证集方法一（递推式）：用T-(2N-1)~T-N真实值递推预测T-(N-1)~T，每步用前面预测值+真实历史。
##    - 验证集方法二（滑窗式）：用T-(2N-1)~T-N真实值，滑窗预测T-(N-1)~T，每步只用当前窗口真实值。
## 3. 输出表格包含真实值、方法一预测、方法二预测，类型字段区分。
## 4. 可视化大图含三个子图：真实+未来预测、真实+验证集方法一、真实+验证集方法二。
## 5. 其它功能、可视化与4.1.2版一致。
'''

import os
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
import re
import chinese_calendar
from keras.callbacks import EarlyStopping

# ========== 配置区 ==========
DB_USER = 'dbtest'
DB_PASSWORD = 'test'
DB_HOST = '192.168.43.11:1521'
SERVICE_NAME = 'FREEPDB1'
oracle_connection_string = f"oracle+cx_oracle://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/?service_name={SERVICE_NAME}"

STOCKS = {
    '贵州茅台': '600519.SH',
    '五粮液': '000858.SZ',
    '国泰君安': '601211.SH',
    '中芯国际': '688981.SH',
    '全志科技': '300458.SZ',
}

MODEL_DIR = '4.1.3_lstm_model'
os.makedirs(MODEL_DIR, exist_ok=True)

def safe_filename(s):
    """
    :function: 将字符串转为安全的文件名，只保留中英文、数字，其他替换为下划线
    :param s: 原始字符串
    :return: 安全文件名字符串
    """
    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '_', str(s))

def get_stock_data(ts_code, start_date, end_date):
    engine = create_engine(oracle_connection_string)
    sql = f"""
    SELECT trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount
    FROM stock_history_data
    WHERE ts_code = '{ts_code}'
      AND trade_date >= TO_DATE('{start_date}', 'YYYY-MM-DD')
      AND trade_date <= TO_DATE('{end_date}', 'YYYY-MM-DD')
    ORDER BY trade_date
    """
    df = pd.read_sql(sql, engine)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date').reset_index(drop=True)
    return df

def add_time_features(df):
    df['weekday'] = df['trade_date'].dt.weekday
    df['month_period'] = df['trade_date'].dt.day.apply(lambda d: 0 if d<=10 else (1 if d<=20 else 2))
    df['is_month_end'] = df['trade_date'].dt.is_month_end.astype(int)
    df['is_holiday'] = df['trade_date'].apply(lambda d: int(chinese_calendar.is_holiday(d)))
    df['is_trade_day'] = df.apply(lambda row: int((row['weekday']<5) and (row['is_holiday']==0)), axis=1)
    df['is_post_holiday_trade_day'] = 0
    for i in range(1, len(df)):
        if df.loc[i-1, 'is_trade_day']==0 and df.loc[i, 'is_trade_day']==1:
            df.loc[i, 'is_post_holiday_trade_day'] = 1
    return df

def add_derived_features(df):
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['pct_chg_mean5'] = df['pct_chg'].rolling(5).mean()
    df['pct_chg_std5'] = df['pct_chg'].rolling(5).std()
    df['vol_chg'] = df['vol'].pct_change()
    df['close_ma5_diff'] = df['close'] - df['ma5']
    df['close_ma10_diff'] = df['close'] - df['ma10']
    return df

def robust_feature_engineering(df, stat_dict=None):
    """
    :function: 稳健特征工程与归一化，递推期用stat_dict参数，自动集成时间类周期性编码
    :param df: DataFrame
    :param stat_dict: 训练集统计量dict，递推期用
    :return: df_new, stat_dict, feature_cols
    """
    df = df.copy()
    # 1. 价格类对数变换
    price_cols = ['open','high','low','close','pre_close','ma5','ma10']
    for col in price_cols:
        df['log_' + col] = np.log1p(df[col].clip(lower=0))
    # 2. 涨跌幅类clip到±10%
    pct_cols = ['change','pct_chg','pct_chg_mean5','pct_chg_std5']
    for col in pct_cols:
        df[col] = df[col].clip(-0.1, 0.1)
    # 3. 成交量/额/vol_chg对数变换+clip
    vol_cols = ['vol','amount','vol_chg']
    for col in vol_cols:
        df['log_' + col] = np.log1p(df[col].clip(lower=0))
        if stat_dict is None:
            lower = df['log_' + col].quantile(0.01)
            upper = df['log_' + col].quantile(0.99)
        else:
            lower = stat_dict['log_' + col + '_q01']
            upper = stat_dict['log_' + col + '_q99']
        df['log_' + col] = df['log_' + col].clip(lower, upper)
    # 4. 价差类clip到均值±3std
    diff_cols = ['close_ma5_diff','close_ma10_diff']
    for col in diff_cols:
        if stat_dict is None:
            mean = df[col].mean()
            std = df[col].std()
        else:
            mean = stat_dict[col + '_mean']
            std = stat_dict[col + '_std']
        df[col] = df[col].clip(mean-3*std, mean+3*std)
    # 5. 离散特征直接用+周期性编码
    discrete_cols = ['weekday','month_period','is_month_end','is_holiday','is_trade_day','is_post_holiday_trade_day']
    # 新增周期性编码
    df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
    df['weekday_cos'] = np.cos(2 * np.pi * df['weekday'] / 7)
    # 6. 统计量保存
    if stat_dict is None:
        stat_dict = {}
        for col in vol_cols:
            stat_dict['log_' + col + '_q01'] = df['log_' + col].quantile(0.01)
            stat_dict['log_' + col + '_q99'] = df['log_' + col].quantile(0.99)
        for col in diff_cols:
            stat_dict[col + '_mean'] = df[col].mean()
            stat_dict[col + '_std'] = df[col].std()
    # 7. 返回新特征列顺序
    feature_cols = ['log_open','log_high','log_low','log_close','log_pre_close',
                    'change','pct_chg','log_vol','log_amount','ma5','ma10',
                    'pct_chg_mean5','pct_chg_std5','log_vol_chg','close_ma5_diff','close_ma10_diff'] \
                   + discrete_cols + ['weekday_sin','weekday_cos']
    return df, stat_dict, feature_cols

def make_sequences(X, y, window):
    X_seq, y_seq = [], []
    for i in range(len(X) - window):
        X_seq.append(X[i:i+window])
        y_seq.append(y[i+window])
    return np.array(X_seq), np.array(y_seq)

def plot_future_prediction(df, pred_dates, y_pred, stock_name, save_dir):
    plt.figure(figsize=(12,6))
    plt.plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
    plt.plot(pred_dates, y_pred, 'r--', label='未来预测收盘价')
    plt.xlabel('日期')
    plt.ylabel('收盘价')
    plt.title(f'{stock_name} LSTM未来收盘价预测（仅历史+预测）')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    filename = f'{safe_filename(stock_name)}_lstm_pred_future_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path)
    plt.close()
    return save_path

def plot_backtest(df, val_dates, y_true, y_pred, stock_name, save_dir):
    plt.figure(figsize=(12,6))
    plt.plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
    plt.plot(val_dates, y_true, 'o-', label='验证集真实收盘价', color='green')
    plt.plot(val_dates, y_pred, 'r--', label='验证集预测收盘价')
    plt.xlabel('日期')
    plt.ylabel('收盘价')
    plt.title(f'{stock_name} LSTM回测/验证集效果对比')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    filename = f'{safe_filename(stock_name)}_lstm_pred_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path)
    plt.close()
    return save_path

def get_model_paths(stock_name, window, feature_cols):
    import hashlib
    feat_hash = hashlib.md5(str(feature_cols).encode('utf-8')).hexdigest()[:8]
    base = f"{safe_filename(stock_name)}_win{window}_feat{feat_hash}"
    model_path = os.path.join(MODEL_DIR, base + '.h5')
    meta_path = os.path.join(MODEL_DIR, base + '_meta.json')
    return model_path, meta_path

def get_future_trade_days(last_date, n):
    days = []
    cur = last_date + pd.Timedelta(days=1)
    while len(days) < n:
        if (cur.weekday() < 5) and (not chinese_calendar.is_holiday(cur)):
            days.append(cur)
        cur += pd.Timedelta(days=1)
    return pd.DatetimeIndex(days)

def plot_full_and_val_subplots(df, pred_dates, future_preds, val_dates, val_true, val_pred, stock_name, save_dir):
    """
    :function: 画全量历史+预测、全量回测/验证集效果对比 两个子图
    :param df: 历史DataFrame
    :param pred_dates: 预测日期序列
    :param future_preds: 预测收盘价序列
    :param val_dates: 验证集日期序列
    :param val_true: 验证集真实收盘价
    :param val_pred: 验证集预测收盘价
    :param stock_name: 股票名
    :param save_dir: 保存目录
    :return: 图片路径
    """
    fig, axs = plt.subplots(2, 1, figsize=(14, 10))
    # 子图1：全量历史+预测
    axs[0].plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
    axs[0].plot(pred_dates, future_preds, 'r--', label='未来预测收盘价')
    axs[0].set_title(f'{stock_name} 全量历史+预测')
    axs[0].legend()
    axs[0].set_xlabel('日期')
    axs[0].set_ylabel('收盘价')
    axs[0].tick_params(axis='x', rotation=45)
    # 子图2：全量回测/验证集效果对比
    axs[1].plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
    axs[1].plot(val_dates, val_true, 'o-', label='验证集真实收盘价', color='green')
    axs[1].plot(val_dates, val_pred, 'r--', label='验证集预测收盘价')
    axs[1].set_title(f'{stock_name} 全量回测/验证集效果对比')
    axs[1].legend()
    axs[1].set_xlabel('日期')
    axs[1].set_ylabel('收盘价')
    axs[1].tick_params(axis='x', rotation=45)
    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    filename = f'{safe_filename(stock_name)}_full_and_val_subplots_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path)
    plt.close()
    return save_path

def plot_zoomed_val_and_pred_subplots(df, pred_dates, future_preds, val_dates, val_true, val_pred, stock_name, save_dir):
    """
    :function: 画只包含验证集及前一周及预测期的"历史+预测"与回测/验证集效果对比 两个子图
    :param df: 历史DataFrame
    :param pred_dates: 预测日期序列
    :param future_preds: 预测收盘价序列
    :param val_dates: 验证集日期序列
    :param val_true: 验证集真实收盘价
    :param val_pred: 验证集预测收盘价
    :param stock_name: 股票名
    :param save_dir: 保存目录
    :return: 图片路径
    """
    # 取验证集前一周（5个交易日）+验证集+预测期
    n_val = len(val_dates)
    idx_start = max(0, df.index[-n_val-5])
    idx_end = len(df)
    df_zoom = df.iloc[idx_start:idx_end]
    fig, axs = plt.subplots(2, 1, figsize=(14, 10))
    # 子图1：局部历史+预测
    axs[0].plot(df_zoom['trade_date'], df_zoom['close'], label='历史收盘价', color='blue')
    axs[0].plot(pred_dates, future_preds, 'r--', label='未来预测收盘价')
    axs[0].set_title(f'{stock_name} 局部历史+预测（验证集前一周+预测期）')
    axs[0].legend()
    axs[0].set_xlabel('日期')
    axs[0].set_ylabel('收盘价')
    axs[0].tick_params(axis='x', rotation=45)
    # 子图2：局部回测/验证集效果对比
    axs[1].plot(df_zoom['trade_date'], df_zoom['close'], label='历史收盘价', color='blue')
    axs[1].plot(val_dates, val_true, 'o-', label='验证集真实收盘价', color='green')
    axs[1].plot(val_dates, val_pred, 'r--', label='验证集预测收盘价')
    axs[1].set_title(f'{stock_name} 局部回测/验证集效果对比（验证集前一周+预测期）')
    axs[1].legend()
    axs[1].set_xlabel('日期')
    axs[1].set_ylabel('收盘价')
    axs[1].tick_params(axis='x', rotation=45)
    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    filename = f'{safe_filename(stock_name)}_zoomed_val_and_pred_subplots_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path)
    plt.close()
    return save_path

# ========== 新递推式与滑窗式预测/验证，窗口递推重算特征 ==========
def rolling_predict_df(model, df_hist, window, n, feature_cols, method='future', y_true=None, dates=None):
    """
    :function: 递推式预测/验证，窗口为DataFrame，每步append新行并重算所有特征，递推链条不断，涨跌幅保护
    :param model: 已训练模型
    :param df_hist: 历史DataFrame（含所有特征）
    :param window: 窗口长度
    :param n: 预测步数
    :param feature_cols: 特征列名
    :param method: 'future'为未来预测，'val1'为验证集方法一，'val2'为验证集方法二
    :param y_true: 方法二时用到真实y
    :param dates: 预测/验证日期序列
    :return: 预测值序列、特征明细
    """
    preds = []
    features = []
    window_df = df_hist.iloc[-window:].copy().reset_index(drop=True)
    prev_close = window_df.iloc[-1]['close']
    for i in range(n):
        # 1. 用当前窗口特征输入模型
        X_input = window_df[feature_cols].values
        pred = float(model.predict(X_input[np.newaxis, :, :]).flatten()[0])
        # 涨跌幅保护，防止递推塌陷
        pred = min(max(pred, prev_close*0.9), prev_close*1.1)
        # 2. 构造新行（递推链条不断，open=pre_close，high/low为close上下浮动，vol/amount扰动）
        new_row = window_df.iloc[-1].copy()
        if method == 'future' or method == 'val1':
            new_row['pre_close'] = prev_close
            new_row['open'] = prev_close
            new_row['close'] = pred
            high_ratio = 1 + np.random.uniform(0.01, 0.02)
            low_ratio = 1 - np.random.uniform(0.01, 0.02)
            new_row['high'] = pred * high_ratio
            new_row['low'] = pred * low_ratio
            prev_close = pred
        elif method == 'val2':
            if y_true is not None and i < len(y_true):
                new_row['pre_close'] = prev_close
                new_row['open'] = prev_close
                new_row['close'] = y_true[i]
                high_ratio = 1 + np.random.uniform(0.01, 0.02)
                low_ratio = 1 - np.random.uniform(0.01, 0.02)
                new_row['high'] = y_true[i] * high_ratio
                new_row['low'] = y_true[i] * low_ratio
                prev_close = y_true[i]
        # 日期
        if dates is not None:
            date_val = dates.iloc[i] if hasattr(dates, 'iloc') else dates[i]
            new_row['trade_date'] = date_val
        # vol/amount等用历史均值+扰动，clip到正数
        for col in ['vol','amount']:
            mean = df_hist[col].mean()
            std = df_hist[col].std()
            val = float(np.random.normal(mean, std))
            new_row[col] = max(val, 1.0)
        # 其它时间特征
        if dates is not None:
            d = pd.to_datetime(new_row['trade_date'])
            new_row['weekday'] = d.weekday()
            new_row['month_period'] = 0 if d.day<=10 else (1 if d.day<=20 else 2)
            new_row['is_month_end'] = int(pd.Timestamp(d).is_month_end)
            import chinese_calendar
            new_row['is_holiday'] = int(chinese_calendar.is_holiday(d))
            new_row['is_trade_day'] = int((d.weekday()<5) and (new_row['is_holiday']==0))
            if i==0:
                prev_d = df_hist['trade_date'].iloc[-1]
            else:
                prev_d = pd.to_datetime(dates.iloc[i-1] if hasattr(dates, 'iloc') else dates[i-1])
            prev_is_trade_day = int((prev_d.weekday()<5) and (not chinese_calendar.is_holiday(prev_d)))
            new_row['is_post_holiday_trade_day'] = int((prev_is_trade_day==0) and (new_row['is_trade_day']==1))
        # 3. append到窗口
        window_df = pd.concat([window_df, pd.DataFrame([new_row])], ignore_index=True)
        # 4. 重算所有衍生特征
        window_df = add_derived_features(window_df)
        # 5. 记录特征明细
        feat_row = window_df.iloc[-1][feature_cols].to_dict()
        # nan/inf保护
        for k, v in feat_row.items():
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                feat_row[k] = 0.0
        if dates is not None:
            feat_row['日期'] = pd.to_datetime(new_row['trade_date']).strftime('%Y-%m-%d')
        feat_row['预测收盘价'] = pred
        feat_row['类型'] = '未来预测' if method=='future' else ('验证方法一' if method=='val1' else '验证方法二')
        features.append(feat_row)
        preds.append(pred)
        # 6. 滚动窗口
        window_df = window_df.iloc[1:].reset_index(drop=True)
    return np.array(preds), features

# ========== 修改主流程 ==========
def main():
    print("请输入股票名称（如：贵州茅台，回车默认）：")
    stock_name = input().strip()
    if not stock_name:
        stock_name = '贵州茅台'
    print("请输入窗口长度（如：20，回车默认）：")
    window_in = input().strip()
    window = int(window_in) if window_in else 20
    print("请输入预测天数（如：5，回车默认）：")
    pred_days_in = input().strip()
    pred_days = int(pred_days_in) if pred_days_in else 5
    DEBUG = False
    ts_code = STOCKS.get(stock_name, stock_name)
    today = datetime.today().date()
    start_date = (today - timedelta(days=365 if not DEBUG else 120)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    df = get_stock_data(ts_code, start_date, end_date)
    if len(df) < 2*pred_days + window:
        print("数据量不足，无法建模。")
        return
    df = add_time_features(df)
    df = add_derived_features(df)
    feature_cols = [
        'open','high','low','close','pre_close','change','pct_chg','vol','amount',
        'ma5','ma10','pct_chg_mean5','pct_chg_std5','vol_chg','close_ma5_diff','close_ma10_diff',
        'weekday','month_period','is_month_end','is_holiday','is_trade_day','is_post_holiday_trade_day'
    ]
    df[feature_cols] = df[feature_cols].fillna(0)
    X = df[feature_cols].values
    y = df['close'].values
    X_seq, y_seq = make_sequences(X, y, window)
    train_size = len(X_seq) - 2*pred_days
    X_train, y_train = X_seq[:train_size], y_seq[:train_size]
    X_val, y_val = X_seq[train_size:train_size+pred_days], y_seq[train_size:train_size+pred_days]
    X_test, y_test = X_seq[train_size+pred_days:], y_seq[train_size+pred_days:]
    model_path, meta_path = get_model_paths(stock_name, window, feature_cols)
    need_train = True
    import json
    if os.path.exists(model_path) and os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        if meta.get('window') == window and meta.get('feature_cols') == feature_cols and meta.get('stock_name') == stock_name:
            print(f"检测到已存在的模型，直接加载，无需重新训练。")
            from keras.models import load_model
            model = load_model(model_path, compile=False)
            need_train = False
        else:
            print("参数变动，需重新训练模型。")
    if need_train:
        print("开始训练LSTM模型...")
        model = Sequential([
            LSTM(64, input_shape=(window, X.shape[1]), return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1)
        model.fit(X_train, y_train, epochs=500 if not DEBUG else 5, batch_size=16, verbose=2, validation_split=0.1, callbacks=[early_stop])
        print("训练完成，保存模型...")
        model.save(model_path)
        meta = {'window': window, 'feature_cols': feature_cols, 'stock_name': stock_name}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"模型已保存到{MODEL_DIR}目录。")
    print("开始预测...")
    # ========== 未来递推预测 ==========
    pred_dates = df['trade_date'].iloc[-1] + pd.to_timedelta(np.arange(1, pred_days+1), unit='D')
    future_preds, future_feats = rolling_predict_df(model, df, window, pred_days, feature_cols, method='future', dates=pred_dates)
    # ========== 验证集递推预测 ==========
    val_dates = df['trade_date'].iloc[-pred_days:]
    # 方法一：递推式
    df_val1 = df.iloc[-pred_days-window:-pred_days].copy().reset_index(drop=True)
    val1_preds, val1_feats = rolling_predict_df(model, df_val1, window, pred_days, feature_cols, method='val1', dates=val_dates)
    # 方法二：滑窗式
    df_val2 = df.iloc[-pred_days-window:-pred_days].copy().reset_index(drop=True)
    y_true_val2 = y_seq[-pred_days:]
    val2_preds, val2_feats = rolling_predict_df(model, df_val2, window, pred_days, feature_cols, method='val2', y_true=y_true_val2, dates=val_dates)
    # ========== 输出表格 ==========
    table_rows = []
    for i in range(pred_days):
        # 真实值
        row_real = {'日期': val_dates.iloc[i].strftime('%Y-%m-%d'), '收盘价': y_seq[-pred_days:][i], '类型': '真实'}
        # 方法一
        row_val1 = {'日期': val_dates.iloc[i].strftime('%Y-%m-%d'), '收盘价': val1_preds[i], '类型': '验证方法一'}
        # 方法二
        row_val2 = {'日期': val_dates.iloc[i].strftime('%Y-%m-%d'), '收盘价': val2_preds[i], '类型': '验证方法二'}
        table_rows.extend([row_real, row_val1, row_val2])
    pred_table = pd.DataFrame(table_rows)
    print("\n验证集预测结果：")
    print(pred_table.to_markdown(index=False))
    # 未来预测表格
    future_table = pd.DataFrame({
        '预测日期': pred_dates.strftime('%Y-%m-%d'),
        '预测收盘价': np.round(future_preds,2)
    })
    print("\n未来{}天预测结果：".format(pred_days))
    print(future_table.to_markdown(index=False))
    # ========== CSV输出 ==========
    save_dir = '4.1.3_lstm_pred_image_show'
    os.makedirs(save_dir, exist_ok=True)
    # 验证集明细
    val_feats_all = pd.DataFrame(val1_feats + val2_feats)
    val_feats_all.to_csv(os.path.join(save_dir, f"{safe_filename(stock_name)}_val_pred_features_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"), index=False, encoding='utf-8-sig')
    print(f"验证集特征明细已导出：{save_dir}")
    # 未来预测明细
    future_feats_df = pd.DataFrame(future_feats)
    future_feats_df.to_csv(os.path.join(save_dir, f"{safe_filename(stock_name)}_future_pred_features_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"), index=False, encoding='utf-8-sig')
    print(f"未来预测特征明细已导出：{save_dir}")
    # ========== 可视化 ==========
    def plot_three_subplots(df, pred_dates, future_preds, val_dates, val1_preds, val2_preds, val_true, stock_name, save_dir, zoom=False):
        plt.figure(figsize=(16, 14))
        # 子图1：真实+未来预测
        plt.subplot(3,1,1)
        if zoom:
            idx_start = max(0, df.index[-pred_days-5])
            idx_end = len(df)
            df_zoom = df.iloc[idx_start:idx_end]
            plt.plot(df_zoom['trade_date'], df_zoom['close'], label='历史收盘价', color='blue')
        else:
            plt.plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
        plt.plot(pred_dates, future_preds, 'r--', label='未来预测收盘价')
        plt.title(f'{stock_name} 历史+未来预测' + ("（局部）" if zoom else ""))
        plt.legend()
        plt.xlabel('日期')
        plt.ylabel('收盘价')
        plt.xticks(rotation=45)
        # 子图2：真实+验证集方法一
        plt.subplot(3,1,2)
        if zoom:
            plt.plot(df_zoom['trade_date'], df_zoom['close'], label='历史收盘价', color='blue')
        else:
            plt.plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
        plt.plot(val_dates, val1_preds, 'r--', label='验证集方法一预测')
        plt.plot(val_dates, val_true, 'g-', label='验证集真实收盘价')
        plt.title(f'{stock_name} 验证集递推式（方法一）' + ("（局部）" if zoom else ""))
        plt.legend()
        plt.xlabel('日期')
        plt.ylabel('收盘价')
        plt.xticks(rotation=45)
        # 子图3：真实+验证集方法二
        plt.subplot(3,1,3)
        if zoom:
            plt.plot(df_zoom['trade_date'], df_zoom['close'], label='历史收盘价', color='blue')
        else:
            plt.plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
        plt.plot(val_dates, val2_preds, 'r--', label='验证集方法二预测')
        plt.plot(val_dates, val_true, 'g-', label='验证集真实收盘价')
        plt.title(f'{stock_name} 验证集滑窗式（方法二）' + ("（局部）" if zoom else ""))
        plt.legend()
        plt.xlabel('日期')
        plt.ylabel('收盘价')
        plt.xticks(rotation=45)
        plt.tight_layout()
        filename = f'{safe_filename(stock_name)}_three_subplots_{"zoomed_" if zoom else ""}{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        save_path = os.path.join(save_dir, filename)
        plt.savefig(save_path)
        plt.close()
        return save_path
    img_path_three = plot_three_subplots(df, pred_dates, future_preds, val_dates, val1_preds, val2_preds, y_seq[-pred_days:], stock_name, save_dir, zoom=False)
    print(f"\n全量三子图大图已保存：{img_path_three}")
    img_path_three_zoom = plot_three_subplots(df, pred_dates, future_preds, val_dates, val1_preds, val2_preds, y_seq[-pred_days:], stock_name, save_dir, zoom=True)
    print(f"局部三子图大图已保存：{img_path_three_zoom}")
    # 其它说明
    print("\n主要特征工程说明：")
    print("- 原始特征：open、high、low、close、pre_close、change、pct_chg、vol、amount")
    print("- 衍生特征：5日/10日均线、涨跌幅滚动均值/方差、成交量变化率、价格与均线偏离度")
    print("- 周期性时间特征：weekday, month_period, is_month_end")
    print("- 交易日特征：is_holiday（法定节假日）、is_trade_day（A股交易日）、is_post_holiday_trade_day（节后首日）")
    print("\n如需正式全量预测，请将DEBUG=False。")

if __name__ == '__main__':
    main() 