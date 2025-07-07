'''
程序说明：
## 1. 本程序在4.1.5_stock_predict_lstm_advanced_multi_y.py基础上，升级为多目标预测（open、close、high、low、vol），递推链条每步预测5个特征。
## 2. 主要改进：LSTM输出层为Dense(5)，损失函数为MSE，递推时窗口open/close/high/low/vol均用模型预测值，pre_close用上一步的close。
## 3. 输出目录为4.1.6_lstm_pred_image_show，所有输出、可视化、特征导出等与4.1.5一致。
## 4. vol特征归一化采用log变换+clip+MinMaxScaler，训练和递推阶段保持一致。
## 5. 其它功能、注释、输出、可视化等全部保留并兼容。
'''


import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import re
import chinese_calendar
from sklearn.preprocessing import MinMaxScaler
import json
import hashlib
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint


import os
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 只显示FATAL级别TF日志
import logging
logging.getLogger('absl').setLevel(logging.ERROR)
logging.getLogger('tensorflow').setLevel(logging.ERROR)
try:
    import absl.logging
    absl.logging.set_verbosity(absl.logging.ERROR)
except ImportError:
    pass

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

MODEL_DIR = '4.1.6_lstm_model'
os.makedirs(MODEL_DIR, exist_ok=True)

# ===================== 参数设置 =====================
LSTM_UNITS = 128  # LSTM单元数
LSTM_LAYERS = 2   # LSTM层数
DROPOUT_RATE = 0.2
EPOCHS = 500
BATCH_SIZE = 32
PATIENCE = 20  # EarlyStopping耐心轮数

# MODEL_PATH = 'best_lstm_model.h5'

# ========== 工具函数 ==========
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

# ===================== 衍生特征处理 =====================
def add_derived_features(df):
    """
    :function: 计算部分重要衍生特征（ma5、ma10、close_ma5_diff、close_ma10_diff、pct_chg_mean5、pct_chg_std5）
    :param df: 原始DataFrame
    :return: 增加衍生特征后的DataFrame
    """
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['close_ma5_diff'] = df['close'] - df['ma5']
    df['close_ma10_diff'] = df['close'] - df['ma10']
    df['pct_chg_mean5'] = df['pct_chg'].rolling(5).mean()
    df['pct_chg_std5'] = df['pct_chg'].rolling(5).std()
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    return df

def make_sequences(X, y, window):
    X_seq, y_seq = [], []
    for i in range(len(X) - window):
        X_seq.append(X[i:i+window])
        y_seq.append(y[i+window])
    return np.array(X_seq), np.array(y_seq)

def get_model_paths(stock_name, window, feature_cols):
    feat_hash = hashlib.md5(str(feature_cols).encode('utf-8')).hexdigest()[:8]
    base = f"{safe_filename(stock_name)}_win{window}_feat{feat_hash}"
    model_path = os.path.join(MODEL_DIR, base + '.h5')
    meta_path = os.path.join(MODEL_DIR, base + '_meta.json')
    return model_path, meta_path

# ===================== 归一化处理 =====================
def normalize_features(X, y, y_scaler=None, fit=True):
    """
    :function: 特征归一化，y为多目标（open、close、high、low、vol），vol采用log变换+clip+MinMaxScaler
    :param X: 特征
    :param y: 标签（open、close、high、low、vol）
    :param y_scaler: 可选，递推时用训练集scaler
    :param fit: 是否fit scaler
    :return: X_scaled, y_scaled, X_scaler, y_scaler
    """
    X_scaler = MinMaxScaler()
    if fit:
        X_scaled = X_scaler.fit_transform(X)
    else:
        X_scaled = X_scaler.transform(X)
    # y: open, close, high, low, vol
    y_df = pd.DataFrame(y, columns=['open','close','high','low','vol'])
    y_df['log_vol'] = np.log1p(y_df['vol'].clip(lower=0))
    y_for_scaler = y_df[['open','close','high','low','log_vol']].values
    if y_scaler is None:
        y_scaler = MinMaxScaler()
        y_scaled = y_scaler.fit_transform(y_for_scaler)
    else:
        y_scaled = y_scaler.transform(y_for_scaler)
    return X_scaled, y_scaled, X_scaler, y_scaler

# ===================== 构建LSTM模型 =====================
def build_lstm_model(input_shape):
    model = Sequential()
    for i in range(LSTM_LAYERS):
        return_sequences = (i < LSTM_LAYERS - 1)
        if i == 0:
            model.add(LSTM(LSTM_UNITS, return_sequences=return_sequences, input_shape=input_shape))
        else:
            model.add(LSTM(LSTM_UNITS, return_sequences=return_sequences))
        model.add(BatchNormalization())
        model.add(Dropout(DROPOUT_RATE))
    model.add(Dense(5))  # 多目标输出open、close、high、low、vol
    model.compile(optimizer='adam', loss='mse')
    return model

# ===================== 训练模型 =====================
def train_model(model, X_train, y_train, model_path, save_dir, stock_name, window):
    """
    :function: 训练LSTM多目标模型，并保存最佳模型和loss曲线
    :param model: LSTM模型
    :param X_train: 训练特征
    :param y_train: 训练标签（多目标）
    :param model_path: 模型保存路径
    :param save_dir: loss曲线图片保存目录
    :param stock_name: 股票名称
    :param window: 窗口长度
    :return: 训练历史
    """
    early_stop = EarlyStopping(monitor='loss', patience=PATIENCE, restore_best_weights=True)
    checkpoint = ModelCheckpoint(model_path, monitor='loss', save_best_only=True)
    history = model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stop, checkpoint],
        verbose=2
    )
    plt.figure()
    plt.plot(history.history['loss'])
    plt.title('训练loss曲线')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    loss_img_path = os.path.join(save_dir, f"{safe_filename(stock_name)}_lstm_train_loss_win{window}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(loss_img_path)
    plt.close()
    print(f"训练loss曲线已保存：{loss_img_path}")
    y_pred = model.predict(X_train)
    print('训练集预测分布:')
    print('open均值:', np.mean(y_pred[:,0]), 'close均值:', np.mean(y_pred[:,1]), 'high均值:', np.mean(y_pred[:,2]), 'low均值:', np.mean(y_pred[:,3]), 'vol均值:', np.mean(y_pred[:,4]))
    print('open方差:', np.var(y_pred[:,0]), 'close方差:', np.var(y_pred[:,1]), 'high方差:', np.var(y_pred[:,2]), 'low方差:', np.var(y_pred[:,3]), 'vol方差:', np.var(y_pred[:,4]))
    return history

# ===================== 混合归一化与特征工程 =====================
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
    # 3. 成交量/额对数变换+clip
    vol_cols = ['vol','amount']
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
    df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
    df['weekday_cos'] = np.cos(2 * np.pi * df['weekday'] / 7)
    feature_cols = [
        'log_open','log_high','log_low','log_close','log_pre_close',
        'change','pct_chg','log_vol','log_amount',
        'weekday_sin','weekday_cos','month_period','is_month_end','is_holiday','is_trade_day','is_post_holiday_trade_day',
        'log_ma5','log_ma10','close_ma5_diff','close_ma10_diff','pct_chg_mean5','pct_chg_std5'
    ]
    # 统计量保存
    if stat_dict is None:
        stat_dict = {}
        for col in vol_cols:
            stat_dict['log_' + col + '_q01'] = df['log_' + col].quantile(0.01)
            stat_dict['log_' + col + '_q99'] = df['log_' + col].quantile(0.99)
        for col in diff_cols:
            stat_dict[col + '_mean'] = df[col].mean()
            stat_dict[col + '_std'] = df[col].std()
    df[feature_cols] = df[feature_cols].fillna(0)
    return df, stat_dict, feature_cols

# prepare_rolling_df
def prepare_rolling_df(df_hist, stat_dict):
    df_hist = add_time_features(df_hist)
    df_hist = add_derived_features(df_hist)
    df_hist, _, feature_cols = robust_feature_engineering(df_hist, stat_dict)
    return df_hist, feature_cols

# ===================== 主流程 =====================
def rolling_predict_df(model, df_hist, window, n, feature_cols, stat_dict, method='future', y_true=None, dates=None, debug_log=None, debug_predict_log=None, y_scaler=None):
    preds = []
    features = []
    df_hist, feature_cols = prepare_rolling_df(df_hist, stat_dict)
    window_df = df_hist.iloc[-window:].copy().reset_index(drop=True)
    prev_close = max(window_df.iloc[-1]['close'], 0.01)
    prev_vol = max(window_df.iloc[-1]['vol'], 1.0)
    for i in range(n):
        try:
            X_input = window_df[feature_cols].values
        except Exception as e:
            if debug_log is not None:
                debug_log.write(f"递推步{i+1} 特征列异常: {e}\n当前窗口列: {window_df.columns.tolist()}\n")
            if debug_predict_log is not None:
                debug_predict_log.write(f"递推步{i+1} 特征列异常: {e}\n当前窗口列: {window_df.columns.tolist()}\n")
            raise
        # --- 调试日志 ---
        if debug_predict_log is not None:
            debug_predict_log.write(f"\n==== 递推步 {i+1} ====\n")
            try:
                debug_predict_log.write('输入窗口特征（open/close/high/low/vol）：\n')
                debug_predict_log.write(str(window_df[['open','close','high','low','vol']].values) + '\n')
            except Exception as e:
                debug_predict_log.write(f'窗口特征打印异常: {e}\n')
            try:
                debug_predict_log.write('窗口全部特征统计：\n')
                debug_predict_log.write(str(window_df.describe()) + '\n')
            except Exception as e:
                debug_predict_log.write(f'窗口统计异常: {e}\n')
            try:
                debug_predict_log.write('模型输入x（flatten）：\n')
                debug_predict_log.write(str(X_input.flatten()) + '\n')
            except Exception as e:
                debug_predict_log.write(f'模型输入x打印异常: {e}\n')
        # --- 原有debug_log ---
        if debug_log is not None:
            debug_log.write(f"\n递推步{i+1} 输入窗口特征:\n{window_df[feature_cols]}\n")
            stats = window_df[feature_cols].agg(['mean','std','max','min'])
            debug_log.write(f"递推步{i+1} 窗口特征统计:\n{stats}\n")
        pred_scaled = model.predict(X_input[np.newaxis, :, :]).flatten()
        # 反归一化y
        y_pred_arr = y_scaler.inverse_transform(pred_scaled.reshape(1, -1)).flatten()
        pred_open, pred_close, pred_high, pred_low, pred_log_vol = float(y_pred_arr[0]), float(y_pred_arr[1]), float(y_pred_arr[2]), float(y_pred_arr[3]), float(y_pred_arr[4])
        pred_vol = np.expm1(pred_log_vol)
        if debug_predict_log is not None:
            debug_predict_log.write(f"模型输出y_pred: {[pred_open, pred_close, pred_high, pred_low, pred_vol]}\n")
        if debug_log is not None:
            debug_log.write(f"递推步{i+1} 模型输出: open={pred_open}, close={pred_close}, high={pred_high}, low={pred_low}, vol={pred_vol}\n")
        pred_high = max(pred_high, pred_open, pred_close)
        pred_low = min(pred_low, pred_open, pred_close)
        pred_vol = max(pred_vol, 1.0)
        if debug_predict_log is not None:
            try:
                debug_predict_log.write('滑动前窗口open/close/high/low/vol：\n')
                debug_predict_log.write(str(window_df[['open','close','high','low','vol']].values) + '\n')
            except Exception as e:
                debug_predict_log.write(f'滑动前窗口打印异常: {e}\n')
        new_row = window_df.iloc[-1].copy()
        if method == 'future' or method == 'val1':
            new_row['pre_close'] = prev_close
            new_row['open'] = pred_open
            new_row['close'] = pred_close
            new_row['high'] = pred_high
            new_row['low'] = pred_low
            new_row['vol'] = pred_vol
            prev_close = pred_close
            prev_vol = pred_vol
        elif method == 'val2':
            if y_true is not None and i < len(y_true):
                new_row['pre_close'] = prev_close
                new_row['open'] = y_true[i,0]
                new_row['close'] = y_true[i,1]
                new_row['high'] = y_true[i,2]
                new_row['low'] = y_true[i,3]
                new_row['vol'] = y_true[i,4]
                prev_close = y_true[i,1]
                prev_vol = y_true[i,4]
        if dates is not None:
            date_val = dates.iloc[i] if hasattr(dates, 'iloc') else dates[i]
            new_row['trade_date'] = date_val
        # 用vol和价格预测生成amount
        avg_price = (pred_open + pred_close + pred_high + pred_low) / 4
        amount = pred_vol * avg_price * 100  # 若数据库单位为元且vol为手
        new_row['amount'] = max(amount, 1.0)
        if dates is not None:
            d = pd.to_datetime(new_row['trade_date'])
            new_row['weekday'] = d.weekday()
            new_row['month_period'] = 0 if d.day<=10 else (1 if d.day<=20 else 2)
            new_row['is_month_end'] = int(pd.Timestamp(d).is_month_end)
            new_row['is_holiday'] = int(chinese_calendar.is_holiday(d))
            new_row['is_trade_day'] = int((d.weekday()<5) and (new_row['is_holiday']==0))
            if i==0:
                prev_d = df_hist['trade_date'].iloc[-1]
            else:
                prev_d = pd.to_datetime(dates.iloc[i-1] if hasattr(dates, 'iloc') else dates[i-1])
            prev_is_trade_day = int((prev_d.weekday()<5) and (not chinese_calendar.is_holiday(prev_d)))
            new_row['is_post_holiday_trade_day'] = int((prev_is_trade_day==0) and (new_row['is_trade_day']==1))
        window_df = pd.concat([window_df, pd.DataFrame([new_row])], ignore_index=True)
        window_df = add_derived_features(window_df)
        window_df, _, feature_cols = robust_feature_engineering(window_df, stat_dict)
        feat_row = window_df.iloc[-1][feature_cols].to_dict()
        if dates is not None:
            feat_row['日期'] = pd.to_datetime(new_row['trade_date']).strftime('%Y-%m-%d')
        feat_row['预测开盘价'] = pred_open
        feat_row['预测收盘价'] = pred_close
        feat_row['预测最高价'] = pred_high
        feat_row['预测最低价'] = pred_low
        feat_row['预测成交量'] = pred_vol
        feat_row['类型'] = '未来预测' if method=='future' else ('验证方法一' if method=='val1' else '验证方法二')
        features.append(feat_row)
        preds.append([pred_open, pred_close, pred_high, pred_low, pred_vol])
        window_df = window_df.iloc[1:].reset_index(drop=True)
        if debug_predict_log is not None:
            try:
                debug_predict_log.write('滑动后窗口open/close/high/low/vol：\n')
                debug_predict_log.write(str(window_df[['open','close','high','low','vol']].values) + '\n')
            except Exception as e:
                debug_predict_log.write(f'滑动后窗口打印异常: {e}\n')
    return np.array(preds), features

# 新增：获取未来N个A股交易日（非周末、非节假日）
def get_next_trade_days(start_date, n):
    """
    :function: 获取从start_date（不含）起未来n个A股交易日（非周末、非法定节假日）
    :param start_date: datetime.date或pd.Timestamp
    :param n: 需要的交易日数量
    :return: pd.Series of datetime.date
    """
    days = []
    cur = pd.to_datetime(start_date)
    while len(days) < n:
        cur += pd.Timedelta(days=1)
        if cur.weekday() < 5 and not chinese_calendar.is_holiday(cur):
            days.append(cur.date())
    return pd.Series(days)

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
    # --- 特征工程与归一化 ---
    df = add_time_features(df)
    df = add_derived_features(df)
    df, stat_dict, feature_cols = robust_feature_engineering(df)
    X = df[feature_cols].values
    y = df[['open','close','high','low','vol']].values
    X_seq, y_seq = make_sequences(X, y, window)
    # 归一化y（vol为log变换+clip+MinMaxScaler）
    X_train, y_train, X_scaler, y_scaler = normalize_features(X_seq[:len(X_seq)-2*pred_days].reshape(-1, X.shape[1]), y_seq[:len(X_seq)-2*pred_days].reshape(-1, 5), fit=True)
    X_train = X_train.reshape(-1, window, X.shape[1])
    y_train = y_train.reshape(-1, 5)
    # 验证和测试集归一化
    X_val = X_scaler.transform(X_seq[len(X_seq)-2*pred_days:len(X_seq)-pred_days].reshape(-1, X.shape[1])).reshape(-1, window, X.shape[1])
    y_val = y_scaler.transform(pd.DataFrame(y_seq[len(X_seq)-2*pred_days:len(X_seq)-pred_days], columns=['open','close','high','low','vol']).assign(log_vol=lambda d: np.log1p(d['vol'].clip(lower=0)))[['open','close','high','low','log_vol']].values)
    X_test = X_scaler.transform(X_seq[len(X_seq)-pred_days:].reshape(-1, X.shape[1])).reshape(-1, window, X.shape[1])
    y_test = y_scaler.transform(pd.DataFrame(y_seq[len(X_seq)-pred_days:], columns=['open','close','high','low','vol']).assign(log_vol=lambda d: np.log1p(d['vol'].clip(lower=0)))[['open','close','high','low','log_vol']].values)
    # --- 递推/验证时特征工程 ---
    model_path, meta_path = get_model_paths(stock_name, window, feature_cols)
    save_dir = '4.1.6_lstm_pred_image_show'
    os.makedirs(save_dir, exist_ok=True)
    need_train = True
    if os.path.exists(model_path) and os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        if meta.get('window') == window and meta.get('feature_cols') == feature_cols and meta.get('stock_name') == stock_name:
            print(f"检测到已存在的模型，直接加载，无需重新训练。")
            from tensorflow.keras.models import load_model
            model = load_model(model_path, compile=False)
            need_train = False
        else:
            print("参数变动，需重新训练模型。")
    if need_train:
        print("开始训练LSTM模型...")
        model = build_lstm_model((window, X.shape[1]))
        train_model(model, X_train, y_train, model_path, save_dir, stock_name, window)
        print("训练完成，保存模型...")
        model.save(model_path)
        meta = {'window': window, 'feature_cols': feature_cols, 'stock_name': stock_name}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"模型已保存到{MODEL_DIR}目录。")
    print("开始预测...")
    debug_log = open('debug_log.txt', 'w', encoding='utf-8')
    debug_log.write('训练集y分布：\n')
    debug_log.write(f'均值: {np.mean(y_train)}\n')
    debug_log.write(f'方差: {np.var(y_train)}\n')
    debug_log.write(f'最大: {np.max(y_train)}\n')
    debug_log.write(f'最小: {np.min(y_train)}\n')
    train_pred = model.predict(X_train).flatten()
    debug_log.write('训练集预测分布：\n')
    debug_log.write(f'均值: {np.mean(train_pred)}\n')
    debug_log.write(f'方差: {np.var(train_pred)}\n')
    debug_log.write(f'最大: {np.max(train_pred)}\n')
    debug_log.write(f'最小: {np.min(train_pred)}\n')
    # 修正：未来预测日期严格为A股交易日
    last_trade_date = df['trade_date'].iloc[-1]
    pred_dates = get_next_trade_days(last_trade_date, pred_days)
    # ========== 新增：递推调试日志 ==========
    debug_predict_log = open('debug_predict_log.txt', 'w', encoding='utf-8')
    debug_predict_log.write('递推调试日志\n')
    # 打印模型权重均值，确认权重已加载
    debug_predict_log.write('模型各层权重均值：\n')
    for layer in model.layers:
        try:
            w = layer.get_weights()
            if w:
                debug_predict_log.write(f'层 {layer.name} 权重均值: {np.mean(w[0])}\n')
            else:
                debug_predict_log.write(f'层 {layer.name} 无权重\n')
        except Exception as e:
            debug_predict_log.write(f'层 {layer.name} 权重读取异常: {e}\n')
    future_preds, future_feats = rolling_predict_df(model, df, window, pred_days, feature_cols, stat_dict, method='future', dates=pred_dates, debug_log=debug_log, debug_predict_log=debug_predict_log, y_scaler=y_scaler)
    val_dates = df['trade_date'].iloc[-pred_days:]
    df_val1 = df.iloc[-2*pred_days-window:-pred_days].copy().reset_index(drop=True)
    val1_preds, val1_feats = rolling_predict_df(model, df_val1, window, pred_days, feature_cols, stat_dict, method='val1', dates=val_dates, debug_log=debug_log, debug_predict_log=debug_predict_log, y_scaler=y_scaler)
    df_val2 = df.iloc[-2*pred_days-window:-pred_days].copy().reset_index(drop=True)
    y_true_val2 = y_seq[-pred_days:]
    val2_preds, val2_feats = rolling_predict_df(model, df_val2, window, pred_days, feature_cols, stat_dict, method='val2', y_true=y_true_val2, dates=val_dates, debug_log=debug_log, debug_predict_log=debug_predict_log, y_scaler=y_scaler)
    debug_predict_log.close()
    print('详细调试信息见debug_log.txt')
    table_rows = []
    for i in range(pred_days):
        row_real = {'日期': val_dates.iloc[i].strftime('%Y-%m-%d'), '开盘价': y_seq[-pred_days:][i,0], '收盘价': y_seq[-pred_days:][i,1], '最高价': y_seq[-pred_days:][i,2], '最低价': y_seq[-pred_days:][i,3], '成交量': y_seq[-pred_days:][i,4], '类型': '真实'}
        row_val1 = {'日期': val_dates.iloc[i].strftime('%Y-%m-%d'), '开盘价': val1_preds[i,0], '收盘价': val1_preds[i,1], '最高价': val1_preds[i,2], '最低价': val1_preds[i,3], '成交量': val1_preds[i,4], '类型': '验证方法一'}
        row_val2 = {'日期': val_dates.iloc[i].strftime('%Y-%m-%d'), '开盘价': val2_preds[i,0], '收盘价': val2_preds[i,1], '最高价': val2_preds[i,2], '最低价': val2_preds[i,3], '成交量': val2_preds[i,4], '类型': '验证方法二'}
        table_rows.extend([row_real, row_val1, row_val2])
    pred_table = pd.DataFrame(table_rows)
    print("\n验证集预测结果：")
    print(pred_table.to_markdown(index=False))
    future_table = pd.DataFrame({
        '预测日期': pred_dates.apply(lambda x: pd.to_datetime(x).strftime('%Y-%m-%d')),
        '预测开盘价': np.round(future_preds[:,0],2),
        '预测收盘价': np.round(future_preds[:,1],2),
        '预测最高价': np.round(future_preds[:,2],2),
        '预测最低价': np.round(future_preds[:,3],2),
        '预测成交量': np.round(future_preds[:,4],2)
    })
    print("\n未来{}天预测结果：".format(pred_days))
    print(future_table.to_markdown(index=False))
    val_feats_all = pd.DataFrame(val1_feats + val2_feats)
    val_feats_all.to_csv(os.path.join(save_dir, f"{safe_filename(stock_name)}_val_pred_features_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"), index=False, encoding='utf-8-sig')
    print(f"验证集特征明细已导出：{save_dir}")
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
            hist_dates = df_zoom['trade_date']
            hist_close = df_zoom['close']
        else:
            plt.plot(df['trade_date'], df['close'], label='历史收盘价', color='blue')
            hist_dates = df['trade_date']
            hist_close = df['close']
        plt.plot(pred_dates, future_preds[:,1], 'r--', label='未来预测收盘价')
        # 新增：连接T和T+1
        plt.plot([hist_dates.iloc[-1], pred_dates[0]], [hist_close.iloc[-1], future_preds[0,1]], color='orange', linestyle='--', linewidth=2, label='T到T+1连接')
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
        plt.plot(val_dates, val1_preds[:,1], 'r--', label='验证集方法一预测')
        plt.plot(val_dates, val_true[:,1], 'g-', label='验证集真实收盘价')
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
        plt.plot(val_dates, val2_preds[:,1], 'r--', label='验证集方法二预测')
        plt.plot(val_dates, val_true[:,1], 'g-', label='验证集真实收盘价')
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
    print("\n主要特征工程说明：")
    print("- 原始特征：open、high、low、close、pre_close、change、pct_chg、vol、amount")
    print("- 衍生特征：5日/10日均线、涨跌幅滚动均值/方差、成交量变化率、价格与均线偏离度")
    print("- 周期性时间特征：weekday, month_period, is_month_end")
    print("- 交易日特征：is_holiday（法定节假日）、is_trade_day（A股交易日）、is_post_holiday_trade_day（节后首日）")
    print("\n如需正式全量预测，请将DEBUG=False。")

if __name__ == '__main__':
    main()

# ===================== 说明 =====================
# 1. 本文件集成全部功能，优化模型结构和训练策略，特征工程和递推链条与4.1.3一致。
# 2. 训练和递推时务必用同一scaler进行归一化和反归一化。
# 3. 训练过程会自动保存最佳模型和loss曲线，便于分析。
# 4. 如需进一步优化，可调整LSTM层数、单元数、Dropout比例等参数。 