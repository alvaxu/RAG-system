# 4.2.0_stock_predict_lstm_seq2seq.py
'''
程序说明：
## 1. 本程序为4.2.0版股票LSTM Seq2Seq多步预测系统，支持输入股票名称、窗口长度、预测天数，自动从Oracle数据库读取数据，完成特征工程并用LSTM Seq2Seq结构直接预测未来n天收盘价。
## 2. 采用滑动窗口构造样本，输入为window天特征，输出为未来pred_days天的close序列，避免递归误差放大。
## 3. 特征工程、可视化、表格输出与4.1.0版一致，支持调试/正式模式切换。
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

MODEL_DIR = '4.2.0_lstm_seq2seq_model'
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
    df['is_holiday'] = df['weekday'].isin([5,6]).astype(int)
    df['is_next_workday'] = 0
    for i in range(1, len(df)):
        if df.loc[i-1, 'is_holiday']==1 and df.loc[i, 'is_holiday']==0:
            df.loc[i, 'is_next_workday'] = 1
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
    df['is_holiday'] = df['trade_date'].apply(lambda d: int(chinese_calendar.is_holiday(d)))
    df['is_workday'] = df['trade_date'].apply(lambda d: int(chinese_calendar.is_workday(d)))
    return df

def preprocess_features(df, feature_cols):
    scaler = StandardScaler()
    X = scaler.fit_transform(df[feature_cols].fillna(0))
    return X, scaler

def make_seq2seq_samples(X, y, window, pred_days):
    X_seq, y_seq = [], []
    for i in range(len(X) - window - pred_days + 1):
        X_seq.append(X[i:i+window])
        y_seq.append(y[i+window:i+window+pred_days])
    return np.array(X_seq), np.array(y_seq)

def plot_prediction(df, pred_dates, y_true, y_pred, stock_name, save_dir):
    plt.figure(figsize=(12,6))
    plt.plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
    if y_true is not None and len(y_true) == len(pred_dates):
        plt.plot(pred_dates, y_true, 'o-', label='真实收盘价', color='green')
    plt.plot(pred_dates, y_pred, 'r--', label='预测收盘价')
    plt.xlabel('日期')
    plt.ylabel('收盘价')
    plt.title(f'{stock_name} LSTM Seq2Seq未来收盘价预测')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    filename = f'{safe_filename(stock_name)}_lstm_seq2seq_pred_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path)
    plt.close()
    return save_path

def get_model_paths(stock_name, window, pred_days, feature_cols):
    import hashlib
    feat_hash = hashlib.md5(str(feature_cols).encode('utf-8')).hexdigest()[:8]
    base = f"{safe_filename(stock_name)}_win{window}_pred{pred_days}_feat{feat_hash}"
    model_path = os.path.join(MODEL_DIR, base + '.h5')
    scaler_path = os.path.join(MODEL_DIR, base + '_scaler.pkl')
    meta_path = os.path.join(MODEL_DIR, base + '_meta.json')
    return model_path, scaler_path, meta_path

def main():
    print("请输入股票名称（如：贵州茅台）：")
    stock_name = input().strip()
    print("请输入窗口长度（如：20）：")
    window = int(input().strip())
    print("请输入预测天数（如：5）：")
    pred_days = int(input().strip())
    DEBUG = False  # 调试模式只取近120天，正式模式可全量
    ts_code = STOCKS.get(stock_name, stock_name)
    today = datetime.today().date()
    start_date = (today - timedelta(days=365 if not DEBUG else 120)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    df = get_stock_data(ts_code, start_date, end_date)
    print(f"实际历史数据量: {len(df)} 天，起止日期: {df['trade_date'].iloc[0]} ~ {df['trade_date'].iloc[-1]}")
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
        'weekday','month_period','is_month_end','is_holiday','is_next_workday',
        'is_workday' if 'is_workday' in df.columns else None
    ]
    feature_cols = [c for c in feature_cols if c is not None]
    df[feature_cols] = df[feature_cols].fillna(0)
    X, scaler = preprocess_features(df, feature_cols)
    y = df['close'].values
    X_seq, y_seq = make_seq2seq_samples(X, y, window, pred_days)
    print(f"滑动窗口样本数: {X_seq.shape[0]}，每个样本窗口长度: {window}，特征数: {X.shape[1]}，预测天数: {pred_days}")
    train_size = int(X_seq.shape[0] * 0.9)
    X_train, y_train = X_seq[:train_size], y_seq[:train_size]
    X_test, y_test = X_seq[train_size:], y_seq[train_size:]
    print(f"训练集样本数: {X_train.shape[0]}，测试集样本数: {X_test.shape[0]}")
    model_path, scaler_path, meta_path = get_model_paths(stock_name, window, pred_days, feature_cols)
    need_train = True
    import json
    if os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        if meta.get('window') == window and meta.get('feature_cols') == feature_cols and meta.get('stock_name') == stock_name and meta.get('pred_days') == pred_days:
            print(f"检测到已存在的模型和scaler，直接加载，无需重新训练。")
            from keras.models import load_model
            model = load_model(model_path)
            scaler = joblib.load(scaler_path)
            need_train = False
        else:
            print("参数变动，需重新训练模型。")
    if need_train:
        print("开始训练LSTM Seq2Seq模型...")
        model = Sequential([
            LSTM(64, input_shape=(window, X.shape[1]), return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(pred_days)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X_train, y_train, epochs=30 if not DEBUG else 5, batch_size=16, verbose=2)
        print("训练完成，保存模型和scaler...")
        model.save(model_path)
        joblib.dump(scaler, scaler_path)
        meta = {'window': window, 'feature_cols': feature_cols, 'stock_name': stock_name, 'pred_days': pred_days}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"模型和scaler已保存到{MODEL_DIR}目录。")
    print("开始预测...")
    # 用最后一个窗口做未来n天预测
    last_seq = X_seq[-1][np.newaxis, :, :]
    future_preds = model.predict(last_seq).flatten()
    pred_dates = pd.date_range(df['trade_date'].iloc[-pred_days], periods=pred_days)
    save_dir = '4.2.0_lstm_seq2seq_pred_image_show'
    img_path = plot_prediction(df, pred_dates, y_test[-1] if len(y_test)>0 else None, future_preds, stock_name, save_dir)
    pred_table = pd.DataFrame({
        '预测日期': pred_dates.strftime('%Y-%m-%d'),
        '预测收盘价': np.round(future_preds,2)
    })
    print("\n未来{}天预测结果：".format(pred_days))
    print(pred_table.to_markdown(index=False))
    print(f"\n预测趋势图已保存：{img_path}")
    print("\n主要特征工程说明：")
    print("- 原始特征：open、high、low、close、pre_close、change、pct_chg、vol、amount")
    print("- 衍生特征：5日/10日均线、涨跌幅滚动均值/方差、成交量变化率、价格与均线偏离度")
    print("- 周期性时间特征：weekday, month_period, is_holiday, is_next_workday, is_month_end")
    print("- 节假日特征：is_holiday, is_workday")
    print("\n如需正式全量预测，请将DEBUG=False。")

if __name__ == '__main__':
    main() 