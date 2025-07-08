# 4.1.1_stock_predict_lstm.py
'''
程序说明：
## 1. 本程序为4.1.1版股票LSTM预测系统，重点优化了交易日特征工程，适配中国A股"非周末且非法定节假日为交易日"的规则。
## 2. 新增is_trade_day（交易日）、is_post_holiday_trade_day（节后首日）等特征，递归预测时仅对未来真实交易日递推。
## 3. 修正预测期特征生成方式，确保所有特征为真实递推值，杜绝归一化-1等无效值。
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
from sklearn.preprocessing import StandardScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
import re
import chinese_calendar
import joblib
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

MODEL_DIR = '4.1.1_lstm_model'
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
    """
    :function: 增加周期性时间特征，包括is_holiday（法定节假日）、is_trade_day（A股交易日）、is_post_holiday_trade_day（节后首日）
    :param df: DataFrame，需包含trade_date
    :return: DataFrame
    """
    df['weekday'] = df['trade_date'].dt.weekday
    df['month_period'] = df['trade_date'].dt.day.apply(lambda d: 0 if d<=10 else (1 if d<=20 else 2))
    df['is_month_end'] = df['trade_date'].dt.is_month_end.astype(int)
    # 法定节假日
    df['is_holiday'] = df['trade_date'].apply(lambda d: int(chinese_calendar.is_holiday(d)))
    # 交易日（非周末且非法定节假日）
    df['is_trade_day'] = df.apply(lambda row: int((row['weekday']<5) and (row['is_holiday']==0)), axis=1)
    # 节后首个交易日
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

def add_holiday_features(df):
    """
    :function: 保留接口，已在add_time_features中处理法定节假日和交易日
    :param df: DataFrame
    :return: DataFrame
    """
    return df

def preprocess_features(df, feature_cols):
    scaler = StandardScaler()
    X = scaler.fit_transform(df[feature_cols].fillna(0))
    return X, scaler

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
    scaler_path = os.path.join(MODEL_DIR, base + '_scaler.pkl')
    meta_path = os.path.join(MODEL_DIR, base + '_meta.json')
    return model_path, scaler_path, meta_path

def get_future_trade_days(last_date, n):
    """
    :function: 获取未来n个A股交易日（非周末且非法定节假日）
    :param last_date: pd.Timestamp，历史最后一个交易日
    :param n: 需要的未来交易日数量
    :return: pd.DatetimeIndex
    """
    days = []
    cur = last_date + pd.Timedelta(days=1)
    while len(days) < n:
        if (cur.weekday() < 5) and (not chinese_calendar.is_holiday(cur)):
            days.append(cur)
        cur += pd.Timedelta(days=1)
    return pd.DatetimeIndex(days)

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
    try:
        df = add_holiday_features(df)
    except Exception:
        pass
    feature_cols = [
        'open','high','low','close','pre_close','change','pct_chg','vol','amount',
        'ma5','ma10','pct_chg_mean5','pct_chg_std5','vol_chg','close_ma5_diff','close_ma10_diff',
        'weekday','month_period','is_month_end','is_holiday','is_trade_day','is_post_holiday_trade_day'
    ]
    feature_cols = [c for c in feature_cols if c is not None]
    df[feature_cols] = df[feature_cols].fillna(0)
    X, scaler = preprocess_features(df, feature_cols)
    y = df['close'].values
    X_seq, y_seq = make_sequences(X, y, window)
    train_size = len(X_seq) - pred_days
    X_train, y_train = X_seq[:train_size], y_seq[:train_size]
    X_test, y_test = X_seq[train_size:], y_seq[train_size:]
    model_path, scaler_path, meta_path = get_model_paths(stock_name, window, feature_cols)
    need_train = True
    import json
    if os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        if meta.get('window') == window and meta.get('feature_cols') == feature_cols and meta.get('stock_name') == stock_name:
            print(f"检测到已存在的模型和scaler，直接加载，无需重新训练。")
            from keras.models import load_model
            model = load_model(model_path, compile=False)
            scaler = joblib.load(scaler_path)
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
        print("训练完成，保存模型和scaler...")
        model.save(model_path)
        joblib.dump(scaler, scaler_path)
        meta = {'window': window, 'feature_cols': feature_cols, 'stock_name': stock_name}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"模型和scaler已保存到{MODEL_DIR}目录。")
    print("开始预测...")
    y_pred = model.predict(X_test).flatten()
    last_seq = X_seq[-1]
    future_preds = []
    cur_seq = X_seq[-1].copy()
    # 未来预测日期
    last_date = df['trade_date'].iloc[-1]
    pred_dates = get_future_trade_days(last_date, pred_days)
    # 用于动态递推未来特征的窗口DataFrame，初始为历史最后window天
    window_df = df.iloc[-window:].copy().reset_index(drop=True)
    # 历史均值，用于未来不可知特征
    vol_mean = df['vol'].mean()
    amount_mean = df['amount'].mean()
    for i, pred_date in enumerate(pred_dates):
        # 1. 先用上一日预测close（或历史最后一日close）
        prev_close = window_df['close'].iloc[-1] if i > 0 else df['close'].iloc[-1]
        # 2. 预测close
        feat = cur_seq[-1].copy()
        weekday = pred_date.weekday()
        is_holiday = int(chinese_calendar.is_holiday(pred_date))
        is_trade_day = int((weekday<5) and (is_holiday==0))
        prev_date = pred_dates[i-1] if i>0 else df['trade_date'].iloc[-1]
        prev_is_trade_day = int((prev_date.weekday()<5) and (not chinese_calendar.is_holiday(prev_date)))
        is_post_holiday_trade_day = int((prev_is_trade_day==0) and (is_trade_day==1))
        # 3. 构造未来一行DataFrame
        row = {
            'trade_date': pred_date,
            'open': prev_close,
            'high': prev_close,
            'low': prev_close,
            'close': prev_close,  # 先用prev_close，预测后再更新
            'pre_close': prev_close,
            'change': 0,
            'pct_chg': 0,
            'vol': vol_mean,
            'amount': amount_mean,
            'ma5': 0, 'ma10': 0, 'pct_chg_mean5': 0, 'pct_chg_std5': 0, 'vol_chg': 0, 'close_ma5_diff': 0, 'close_ma10_diff': 0,
            'weekday': weekday,
            'month_period': pred_date.day//10 if pred_date.day<=20 else 2,
            'is_month_end': int(pd.Timestamp(pred_date).is_month_end),
            'is_holiday': is_holiday,
            'is_trade_day': is_trade_day,
            'is_post_holiday_trade_day': is_post_holiday_trade_day
        }
        # 4. 用window_df递推均线、涨跌幅等衍生特征
        tmp_df = pd.concat([window_df, pd.DataFrame([row])], ignore_index=True)
        tmp_df['ma5'] = tmp_df['close'].rolling(5).mean()
        tmp_df['ma10'] = tmp_df['close'].rolling(10).mean()
        tmp_df['pct_chg'] = tmp_df['close'].pct_change() * 100
        tmp_df['pct_chg_mean5'] = tmp_df['pct_chg'].rolling(5).mean()
        tmp_df['pct_chg_std5'] = tmp_df['pct_chg'].rolling(5).std()
        tmp_df['vol_chg'] = tmp_df['vol'].pct_change()
        tmp_df['close_ma5_diff'] = tmp_df['close'] - tmp_df['ma5']
        tmp_df['close_ma10_diff'] = tmp_df['close'] - tmp_df['ma10']
        # 5. 用最新一行的特征填充feat
        for j, col in enumerate(feature_cols):
            if col in tmp_df.columns:
                feat[j] = tmp_df.iloc[-1][col]
        # 6. 预测close
        pred = model.predict(cur_seq[np.newaxis, :, :]).flatten()[0]
        future_preds.append(pred)
        # 7. 更新row和window_df
        row['close'] = pred
        row['pre_close'] = prev_close
        if len(window_df) >= window:
            window_df = window_df.iloc[1:].copy()
        window_df = pd.concat([window_df, pd.DataFrame([row])], ignore_index=True)
        # 8. 构造下一个窗口
        next_feat = feat.copy()
        next_feat[3] = pred  # close
        cur_seq = np.vstack([cur_seq[1:], next_feat])
    save_dir = '4.1.1_lstm_pred_image_show'
    img_path_future = plot_future_prediction(df, get_future_trade_days(df['trade_date'].iloc[-1], pred_days), future_preds, stock_name, save_dir)
    # ========== 回测/验证集效果评估 ===========
    # 用训练集最后pred_days个窗口，预测历史最后pred_days天
    val_X = X_seq[-pred_days:]
    val_dates = df['trade_date'].iloc[-pred_days:]
    val_true = y_seq[-pred_days:]
    val_pred = model.predict(val_X).flatten()
    img_path_backtest = plot_backtest(df, val_dates, val_true, val_pred, stock_name, save_dir)
    # ========== 输出表格 ==========
    pred_table = pd.DataFrame({
        '预测日期': get_future_trade_days(df['trade_date'].iloc[-1], pred_days).strftime('%Y-%m-%d'),
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
    # 历史最后5个交易日特征
    last5_idx = df.index[-5:]
    last5_features = df.loc[last5_idx, ['trade_date'] + feature_cols].copy()
    last5_features['类型'] = '历史'
    # 未来预测期特征（递推生成真实值+合理波动）
    future_features = []
    window_df = df.iloc[-window:].copy().reset_index(drop=True)
    pred_dates = get_future_trade_days(df['trade_date'].iloc[-1], pred_days)
    prev_close = df['close'].iloc[-1]
    vol_mean = df['vol'].mean()
    vol_std = df['vol'].std()
    amount_mean = df['amount'].mean()
    amount_std = df['amount'].std()
    rng = np.random.default_rng()
    for i, pred_date in enumerate(pred_dates):
        weekday = pred_date.weekday()
        is_holiday = int(chinese_calendar.is_holiday(pred_date))
        is_trade_day = int((weekday<5) and (is_holiday==0))
        prev_date = pred_dates[i-1] if i>0 else df['trade_date'].iloc[-1]
        prev_is_trade_day = int((prev_date.weekday()<5) and (not chinese_calendar.is_holiday(prev_date)))
        is_post_holiday_trade_day = int((prev_is_trade_day==0) and (is_trade_day==1))
        # open/pre_close=上一日close，high/low在close基础上加减1%~2%波动
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
        # close用模型预测
        row['close'] = future_preds[i] if i < len(future_preds) else prev_close
        # high/low加波动
        high_ratio = 1 + rng.uniform(0.01, 0.02)
        low_ratio = 1 - rng.uniform(0.01, 0.02)
        row['high'] = row['close'] * high_ratio
        row['low'] = row['close'] * low_ratio
        # change/pct_chg
        row['change'] = row['close'] - row['pre_close']
        row['pct_chg'] = (row['change'] / row['pre_close'] * 100) if row['pre_close'] != 0 else 0
        # 递推均线等衍生特征
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
        # 递推窗口
        if len(window_df) >= window:
            window_df = window_df.iloc[1:].copy()
        window_df = pd.concat([window_df, pd.DataFrame([row])], ignore_index=True)
        prev_close = row['close']
    future_features_df = pd.DataFrame(future_features)
    # 合并输出
    features_out = pd.concat([last5_features, future_features_df], ignore_index=True)
    features_out['trade_date'] = pd.to_datetime(features_out['trade_date']).dt.strftime('%Y-%m-%d')
    csv_name = f"{safe_filename(stock_name)}_lstm_pred_features_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = os.path.join(feature_out_dir, csv_name)
    features_out.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n特征明细已导出：{csv_path}")

if __name__ == '__main__':
    main() 