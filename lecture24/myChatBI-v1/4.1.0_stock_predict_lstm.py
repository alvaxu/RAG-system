# 4.1.0_stock_predict_lstm.py
'''
程序说明：
## 1. 本程序为4.1.0版股票LSTM预测系统，支持输入股票名称、窗口长度、预测天数，自动从Oracle数据库读取数据，完成特征工程并用LSTM预测未来n天收盘价。
## 2. 特征工程包含原始特征、衍生特征（均线、涨跌幅滚动统计、成交量变化率、价格与均线偏离度）、周期性时间特征（weekday, month_period, is_holiday, is_next_workday, is_month_end等）。
## 3. 可视化输出风格与3.1.8版一致，支持调试/正式模式切换，便于快速调试和全量预测。
## 4. 输出包括预测表格、趋势图和主要特征工程说明。
'''

import os
import warnings
warnings.filterwarnings('ignore')
# 屏蔽TensorFlow等库的冗余日志
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

MODEL_DIR = '4.1.0_lstm_model'
os.makedirs(MODEL_DIR, exist_ok=True)

def safe_filename(s):
    """将字符串转为安全的文件名"""
    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '_', str(s))

def get_stock_data(ts_code, start_date, end_date):
    """
    :function: 从Oracle数据库读取指定股票的历史行情数据
    :param ts_code: 股票代码
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: DataFrame
    """
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
    :function: 增加周期性时间特征
    :param df: DataFrame，需包含trade_date
    :return: DataFrame
    """
    df['weekday'] = df['trade_date'].dt.weekday
    df['month_period'] = df['trade_date'].dt.day.apply(lambda d: 0 if d<=10 else (1 if d<=20 else 2))
    df['is_month_end'] = df['trade_date'].dt.is_month_end.astype(int)
    # 节假日、调休、下一个工作日等可根据实际情况补充
    df['is_holiday'] = df['weekday'].isin([5,6]).astype(int)  # 简化：周末为假日
    df['is_next_workday'] = 0
    for i in range(1, len(df)):
        if df.loc[i-1, 'is_holiday']==1 and df.loc[i, 'is_holiday']==0:
            df.loc[i, 'is_next_workday'] = 1
    return df

def add_derived_features(df):
    """
    :function: 增加衍生特征
    :param df: DataFrame
    :return: DataFrame
    """
    # 均线
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    # 涨跌幅滚动均值/方差
    df['pct_chg_mean5'] = df['pct_chg'].rolling(5).mean()
    df['pct_chg_std5'] = df['pct_chg'].rolling(5).std()
    # 成交量变化率
    df['vol_chg'] = df['vol'].pct_change()
    # 价格与均线偏离度
    df['close_ma5_diff'] = df['close'] - df['ma5']
    df['close_ma10_diff'] = df['close'] - df['ma10']
    return df

def add_holiday_features(df):
    df['is_holiday'] = df['trade_date'].apply(lambda d: int(chinese_calendar.is_holiday(d)))
    df['is_workday'] = df['trade_date'].apply(lambda d: int(chinese_calendar.is_workday(d)))
    # 你还可以自定义"调休补班日"等特征
    return df

def preprocess_features(df, feature_cols):
    """
    :function: 特征归一化
    :param df: DataFrame
    :param feature_cols: 特征列名
    :return: 归一化后的特征、scaler对象
    """
    scaler = StandardScaler()
    X = scaler.fit_transform(df[feature_cols].fillna(0))
    return X, scaler

def make_sequences(X, y, window):
    """
    :function: 构造滑动窗口序列
    :param X: 特征数组
    :param y: 目标数组
    :param window: 窗口长度
    :return: X_seq, y_seq
    """
    X_seq, y_seq = [], []
    for i in range(len(X) - window):
        X_seq.append(X[i:i+window])
        y_seq.append(y[i+window])
    return np.array(X_seq), np.array(y_seq)

def plot_prediction(df, pred_dates, y_true, y_pred, stock_name, save_dir):
    """
    :function: 绘制历史与预测趋势图
    :param df: 历史数据DataFrame
    :param pred_dates: 预测日期序列
    :param y_true: 真实值
    :param y_pred: 预测值
    :param stock_name: 股票名称
    :param save_dir: 图片保存目录
    :return: 图片路径
    """
    plt.figure(figsize=(12,6))
    plt.plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
    if y_true is not None and len(y_true) == len(pred_dates):
        plt.plot(pred_dates, y_true, 'o-', label='真实收盘价', color='green')
    plt.plot(pred_dates, y_pred, 'r--', label='预测收盘价')
    plt.xlabel('日期')
    plt.ylabel('收盘价')
    plt.title(f'{stock_name} LSTM未来收盘价预测')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    filename = f'{safe_filename(stock_name)}_lstm_pred_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path)
    plt.close()
    return save_path

def get_model_paths(stock_name, window, feature_cols):
    """
    :function: 生成模型和scaler的保存路径，包含股票、窗口长度、特征hash
    :return: (model_path, scaler_path, meta_path)
    """
    import hashlib
    feat_hash = hashlib.md5(str(feature_cols).encode('utf-8')).hexdigest()[:8]
    base = f"{safe_filename(stock_name)}_win{window}_feat{feat_hash}"
    model_path = os.path.join(MODEL_DIR, base + '.h5')
    scaler_path = os.path.join(MODEL_DIR, base + '_scaler.pkl')
    meta_path = os.path.join(MODEL_DIR, base + '_meta.json')
    return model_path, scaler_path, meta_path

def main():
    """
    :function: 主程序入口
    :return: None
    """
    print("请输入股票名称（如：贵州茅台）：")
    stock_name = input().strip()
    print("请输入窗口长度（如：20）：")
    window = int(input().strip())
    print("请输入预测天数（如：5）：")
    pred_days = int(input().strip())
    DEBUG = False  # 调试模式只取近120天，正式模式可全量
    ts_code = STOCKS.get(stock_name, stock_name)
    today = datetime.today().date()
    # start_date = (today - timedelta(days=365 if not DEBUG else 120)).strftime('%Y-%m-%d')
    start_date = '2020-01-01'  # 或你的数据起始日
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
        'weekday','month_period','is_month_end','is_holiday','is_next_workday',
        'is_workday' if 'is_workday' in df.columns else None
    ]
    feature_cols = [c for c in feature_cols if c is not None]
    df[feature_cols] = df[feature_cols].fillna(0)
    X, scaler = preprocess_features(df, feature_cols)
    y = df['close'].values
    X_seq, y_seq = make_sequences(X, y, window)
    train_size = len(X_seq) - pred_days
    X_train, y_train = X_seq[:train_size], y_seq[:train_size]
    X_test, y_test = X_seq[train_size:], y_seq[train_size:]
    # ====== 模型文件路径 ======
    model_path, scaler_path, meta_path = get_model_paths(stock_name, window, feature_cols)
    need_train = True
    import json
    # 检查模型和scaler文件是否存在且参数一致
    if os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        if meta.get('window') == window and meta.get('feature_cols') == feature_cols and meta.get('stock_name') == stock_name:
            print(f"检测到已存在的模型和scaler，直接加载，无需重新训练。")
            from keras.models import load_model
            model = load_model(model_path)
            scaler = joblib.load(scaler_path)
            need_train = False
        else:
            print("参数变动，需重新训练模型。")
    if need_train:
        print("开始训练LSTM模型...")
        from keras.models import Sequential
        from keras.layers import LSTM, Dense, Dropout
        model = Sequential([
            LSTM(64, input_shape=(window, X.shape[1]), return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X_train, y_train, epochs=30 if not DEBUG else 5, batch_size=16, verbose=2)
        print("训练完成，保存模型和scaler...")
        model.save(model_path)
        joblib.dump(scaler, scaler_path)
        meta = {'window': window, 'feature_cols': feature_cols, 'stock_name': stock_name}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"模型和scaler已保存到{MODEL_DIR}目录。")
    print("开始预测...")
    y_pred = model.predict(X_test).flatten()
    # 预测未来n天
    last_seq = X_seq[-1]
    future_preds = []
    cur_seq = last_seq.copy()
    for i in range(pred_days):
        pred = model.predict(cur_seq[np.newaxis, :, :]).flatten()[0]
        future_preds.append(pred)
        next_feat = np.zeros_like(cur_seq[0])
        next_feat[:-5] = cur_seq[-1][:-5]
        next_feat[3] = pred
        cur_seq = np.vstack([cur_seq[1:], next_feat])
    pred_dates = pd.date_range(df['trade_date'].iloc[-pred_days], periods=pred_days)
    save_dir = '4.1.0_lstm_pred_image_show'
    img_path = plot_prediction(df, pred_dates, y_test if len(y_test)==pred_days else None, future_preds, stock_name, save_dir)
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