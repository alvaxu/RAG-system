# 4.1.2_stock_predict_lstm.py
'''
程序说明：
## 1. 本程序为4.1.2版股票LSTM预测系统，**完全去除归一化/标准化**，所有特征递推和模型输入输出均用真实数值，避免递归预测时归一化失真导致的崩溃。
## 2. 预测期open=pre_close=上一日close，high/low在close基础上加减1%~2%波动，vol/amount用历史均值±std正态采样，均线等衍生特征递推生成。
## 3. 输出为csv格式，便于中文兼容和后续分析。
## 4. 其它功能、可视化与4.1.1版一致。
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

MODEL_DIR = '4.1.2_lstm_model'
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
    if len(df) < window + pred_days + 10:
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
    # 不做归一化，直接用真实数值
    X = df[feature_cols].values
    y = df['close'].values
    X_seq, y_seq = make_sequences(X, y, window)
    train_size = len(X_seq) - pred_days
    X_train, y_train = X_seq[:train_size], y_seq[:train_size]
    X_test, y_test = X_seq[train_size:], y_seq[train_size:]
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
    y_pred = model.predict(X_test).flatten()
    last_seq = X_seq[-1]
    future_preds = []
    cur_seq = X_seq[-1].copy()
    last_date = df['trade_date'].iloc[-1]
    pred_dates = get_future_trade_days(last_date, pred_days)
    window_df = df.iloc[-window:].copy().reset_index(drop=True)
    vol_mean = df['vol'].mean()
    vol_std = df['vol'].std()
    amount_mean = df['amount'].mean()
    amount_std = df['amount'].std()
    rng = np.random.default_rng()
    prev_close = df['close'].iloc[-1]
    # 递推预测期特征
    future_features = []
    for i, pred_date in enumerate(pred_dates):
        weekday = pred_date.weekday()
        is_holiday = int(chinese_calendar.is_holiday(pred_date))
        is_trade_day = int((weekday<5) and (is_holiday==0))
        prev_date = pred_dates[i-1] if i>0 else df['trade_date'].iloc[-1]
        prev_is_trade_day = int((prev_date.weekday()<5) and (not chinese_calendar.is_holiday(prev_date)))
        is_post_holiday_trade_day = int((prev_is_trade_day==0) and (is_trade_day==1))
        # 递推close时加微小噪声，防止恒值
        pred_close = float(model.predict(cur_seq[np.newaxis, :, :]).flatten()[0])
        noise = rng.normal(0, max(1, abs(pred_close)*0.01))  # 1%噪声
        pred_close = max(0.01, pred_close + noise)  # 保证非负
        # 加涨跌幅保护，限制单步涨跌幅不超过±10%
        pred_close = min(max(pred_close, prev_close*0.9), prev_close*1.1)
        row = {
            'trade_date': pred_date,
            'open': prev_close,
            'pre_close': prev_close,
            'vol': float(rng.normal(vol_mean, vol_std)),
            'amount': float(rng.normal(amount_mean, amount_std)),
            'weekday': weekday,
            'month_period': pred_date.day//10 if pred_date.day<=20 else 2,
            'is_month_end': int(pd.Timestamp(pred_date).is_month_end),
            'is_holiday': is_holiday,
            'is_trade_day': is_trade_day,
            'is_post_holiday_trade_day': is_post_holiday_trade_day
        }
        row['close'] = pred_close
        high_ratio = 1 + rng.uniform(0.01, 0.02)
        low_ratio = 1 - rng.uniform(0.01, 0.02)
        row['high'] = row['close'] * high_ratio
        row['low'] = row['close'] * low_ratio
        row['change'] = row['close'] - row['pre_close']
        row['pct_chg'] = (row['change'] / row['pre_close'] * 100) if row['pre_close'] != 0 else 0
        tmp_df = pd.concat([window_df, pd.DataFrame([row])], ignore_index=True)
        tmp_df['ma5'] = tmp_df['close'].rolling(5).mean()
        tmp_df['ma10'] = tmp_df['close'].rolling(10).mean()
        tmp_df['pct_chg'] = tmp_df['close'].pct_change() * 100
        tmp_df['pct_chg_mean5'] = tmp_df['pct_chg'].rolling(5).mean()
        tmp_df['pct_chg_std5'] = tmp_df['pct_chg'].rolling(5).std()
        tmp_df['vol_chg'] = tmp_df['vol'].pct_change()
        tmp_df['close_ma5_diff'] = tmp_df['close'] - tmp_df['ma5']
        tmp_df['close_ma10_diff'] = tmp_df['close'] - tmp_df['ma10']
        for col in ['ma5','ma10','pct_chg_mean5','pct_chg_std5','vol_chg','close_ma5_diff','close_ma10_diff']:
            row[col] = tmp_df.iloc[-1][col]
        row['类型'] = '预测'
        future_features.append(row)
        if len(window_df) >= window:
            window_df = window_df.iloc[1:].copy()
        window_df = pd.concat([window_df, pd.DataFrame([row])], ignore_index=True)
        prev_close = row['close']
        next_feat = []
        for col in feature_cols:
            next_feat.append(row.get(col, 0))
        cur_seq = np.vstack([cur_seq[1:], np.array(next_feat)])
        future_preds.append(row['close'])
    save_dir = '4.1.2_lstm_pred_image_show'
    img_path_future = plot_future_prediction(df, pred_dates, future_preds, stock_name, save_dir)
    # ========== 回测/验证集效果评估 ==========
    val_X = X_seq[-pred_days:]
    val_dates = df['trade_date'].iloc[-pred_days:]
    val_true = y_seq[-pred_days:]
    val_pred = model.predict(val_X).flatten()
    img_path_backtest = plot_backtest(df, val_dates, val_true, val_pred, stock_name, save_dir)
    # ========== 新增复合可视化 ==========
    img_path_full_val = plot_full_and_val_subplots(df, pred_dates, future_preds, val_dates, val_true, val_pred, stock_name, save_dir)
    print(f"\n全量历史+预测/全量回测复合图已保存：{img_path_full_val}")
    img_path_zoom_val = plot_zoomed_val_and_pred_subplots(df, pred_dates, future_preds, val_dates, val_true, val_pred, stock_name, save_dir)
    print(f"局部历史+预测/局部回测复合图已保存：{img_path_zoom_val}")
    # ========== 输出表格 ==========
    pred_table = pd.DataFrame({
        '预测日期': pred_dates.strftime('%Y-%m-%d'),
        '预测收盘价': np.round(future_preds,2)
    })
    print("\n未来{}天预测结果：".format(pred_days))
    print(pred_table.to_markdown(index=False))
    print(f"\n未来走势预测图已保存：{img_path_future}")
    print(f"回测/验证集效果图已保存：{img_path_backtest}")
    print("\n主要特征工程说明：")
    print("- 原始特征：open、high、low、close、pre_close、change、pct_chg、vol、amount")
    print("- 衍生特征：5日/10日均线、涨跌幅滚动均值/方差、成交量变化率、价格与均线偏离度")
    print("- 周期性时间特征：weekday, month_period, is_month_end")
    print("- 交易日特征：is_holiday（法定节假日）、is_trade_day（A股交易日）、is_post_holiday_trade_day（节后首日）")
    print("\n如需正式全量预测，请将DEBUG=False。")
    # 输出特征到CSV
    feature_out_dir = save_dir
    os.makedirs(feature_out_dir, exist_ok=True)
    last5_idx = df.index[-5:]
    last5_features = df.loc[last5_idx, ['trade_date'] + feature_cols].copy()
    last5_features['类型'] = '历史'
    future_features_df = pd.DataFrame(future_features)
    features_out = pd.concat([last5_features, future_features_df], ignore_index=True)
    features_out['trade_date'] = pd.to_datetime(features_out['trade_date']).dt.strftime('%Y-%m-%d')
    csv_name = f"{safe_filename(stock_name)}_lstm_pred_features_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = os.path.join(feature_out_dir, csv_name)
    features_out.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n特征明细已导出：{csv_path}")

if __name__ == '__main__':
    main() 