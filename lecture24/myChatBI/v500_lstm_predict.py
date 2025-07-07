'''
程序说明：
## 1. 本模块为5.0.0版股票分析系统的LSTM深度学习多目标预测工具，支持单只股票的多目标预测（开盘、收盘、最高、最低、成交量）。
## 2. 复用特征工程，支持窗口长度、预测天数、特征选择等参数灵活配置。
## 3. 训练、预测、特征导出、可视化一体化，输出训练loss曲线、历史+未来预测三子图、局部K线图。
## 4. 图片命名规范，中文无乱码，详细中文注释，接口清晰。
'''

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from v500_feature_engineering import add_all_features, get_feature_columns
import json
import hashlib
import re
import warnings
import glob
from v500_config import IMAGE_OUTPUT_DIR, MODEL_OUTPUT_DIR, PLOT_STYLE, LSTM_DEFAULTS, PRED_DAYS
warnings.filterwarnings('ignore')
import plotly.graph_objects as go

# ========== 工具函数 ==========
def safe_filename(s):
    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '_', str(s))

def make_sequences(X, y, window):
    X_seq, y_seq = [], []
    for i in range(len(X) - window):
        X_seq.append(X[i:i+window])
        y_seq.append(y[i+window])
    return np.array(X_seq), np.array(y_seq)

# ===================== 归一化处理 =====================
def normalize_features(X, y, price_scaler=None, vol_scaler=None, fit=True):
    X_scaler = MinMaxScaler()
    if fit:
        X_scaled = X_scaler.fit_transform(X)
    else:
        X_scaled = X_scaler.transform(X)
    y_df = pd.DataFrame(y, columns=['open','close','high','low','vol'])
    price_y = y_df[['open','close','high','low']].values
    vol_y = np.log1p(y_df['vol'].clip(lower=0)).values.reshape(-1, 1)
    if price_scaler is None:
        price_scaler = MinMaxScaler()
        price_scaled = price_scaler.fit_transform(price_y)
    else:
        price_scaled = price_scaler.transform(price_y)
    if vol_scaler is None:
        vol_scaler = MinMaxScaler()
        vol_scaled = vol_scaler.fit_transform(vol_y)
    else:
        vol_scaled = vol_scaler.transform(vol_y)
    y_scaled = np.concatenate([price_scaled, vol_scaled], axis=1)
    return X_scaled, y_scaled, X_scaler, price_scaler, vol_scaler

# ===================== 特征工程（需与训练递推一致） =====================
def robust_feature_engineering(df, stat_dict=None):
    df = df.copy()
    price_cols = ['open','high','low','close','pre_close','ma5','ma10']
    for col in price_cols:
        df['log_' + col] = np.log1p(df[col].clip(lower=0))
    pct_cols = ['change','pct_chg','pct_chg_mean5','pct_chg_std5','abs_pct_chg']
    for col in pct_cols:
        df[col] = df[col].clip(-0.1, 0.1)
    vol_cols = ['vol','amount']
    for col in vol_cols:
        df['log_' + col] = np.log1p(df[col].clip(lower=0))
        key_q01 = 'log_' + col + '_q01'
        key_q99 = 'log_' + col + '_q99'
        if stat_dict is not None and key_q01 in stat_dict and key_q99 in stat_dict:
            lower = stat_dict[key_q01]
            upper = stat_dict[key_q99]
        else:
            lower = df['log_' + col].quantile(0.01)
            upper = df['log_' + col].quantile(0.99)
        df['log_' + col] = df['log_' + col].clip(lower, upper)
    diff_cols = ['close_ma5_diff','close_ma10_diff','close_open_diff','high_low_diff']
    for col in diff_cols:
        if stat_dict is None:
            mean = df[col].mean()
            std = df[col].std()
        else:
            mean = stat_dict[col + '_mean']
            std = stat_dict[col + '_std']
        df[col] = df[col].clip(mean-3*std, mean+3*std)
    ratio_cols = ['vol_ratio','turnover_rate','close_ma5_ratio','close_ma10_ratio','amount_mean5_ratio']
    for col in ratio_cols:
        if stat_dict is None:
            lower = df[col].quantile(0.01)
            upper = df[col].quantile(0.99)
        else:
            lower = stat_dict[col + '_q01']
            upper = stat_dict[col + '_q99']
        df[col] = df[col].clip(lower, upper)
    discrete_cols = ['weekday','month_period','is_month_end','is_holiday','is_trade_day','is_post_holiday_trade_day']
    df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
    df['weekday_cos'] = np.cos(2 * np.pi * df['weekday'] / 7)
    feature_cols = [
        'log_open','log_high','log_low','log_close','log_pre_close',
        'change','pct_chg','log_vol','log_amount',
        'weekday_sin','weekday_cos','month_period','is_month_end','is_holiday','is_trade_day','is_post_holiday_trade_day',
        'log_ma5','log_ma10','close_ma5_diff','close_ma10_diff','pct_chg_mean5','pct_chg_std5',
        'abs_pct_chg','amplitude','close_open_diff','high_low_diff','vol_ratio','turnover_rate','close_ma5_ratio','close_ma10_ratio','amount_mean5_ratio'
    ]
    if stat_dict is None:
        stat_dict = {}
        for col in vol_cols:
            stat_dict['log_' + col + '_q01'] = df['log_' + col].quantile(0.01)
            stat_dict['log_' + col + '_q99'] = df['log_' + col].quantile(0.99)
        for col in diff_cols:
            stat_dict[col + '_mean'] = df[col].mean()
            stat_dict[col + '_std'] = df[col].std()
        for col in ratio_cols:
            stat_dict[col + '_q01'] = df[col].quantile(0.01)
            stat_dict[col + '_q99'] = df[col].quantile(0.99)
    df[feature_cols] = df[feature_cols].fillna(0)
    return df, stat_dict, feature_cols

# 新增：获取未来N个A股交易日（非周末、非节假日）
def get_next_trade_days(start_date, n):
    import chinese_calendar
    days = []
    cur = pd.to_datetime(start_date)
    while len(days) < n:
        cur += pd.Timedelta(days=1)
        if cur.weekday() < 5 and not chinese_calendar.is_holiday(cur):
            days.append(cur.date())
    return pd.Series(days)

# ===================== 损失函数 =====================
def weighted_multi_mse(y_true, y_pred):
    """
    :function: 多目标加权MSE损失，价格权重1，vol权重0.01
    :param y_true: [batch, 5]
    :param y_pred: [batch, 5]
    :return: 加权损失
    """
    price_loss = tf.reduce_mean(tf.square(y_true[:, :4] - y_pred[:, :4]))
    vol_loss = tf.reduce_mean(tf.square(y_true[:, 4] - y_pred[:, 4]))
    return price_loss + 0.085 * vol_loss

# ===================== 递推预测 =====================
def rolling_predict_df(model, df_hist, window, n, feature_cols, stat_dict, method='future', y_true=None, dates=None, price_scaler=None, vol_scaler=None):
    preds = []
    features = []
    # 只用robust_feature_engineering和stat_dict，不再做add_all_features等其它处理
    df_hist, _, feature_cols = robust_feature_engineering(df_hist, stat_dict)
    window_df = df_hist.iloc[-window:].copy().reset_index(drop=True)
    prev_close = max(window_df.iloc[-1]['close'], 0.01)
    prev_vol = max(window_df.iloc[-1]['vol'], 1.0)
    for i in range(n):
        X_input = window_df[feature_cols].values
        pred_scaled = model.predict(X_input[np.newaxis, :, :]).flatten()
        price_pred = price_scaler.inverse_transform(pred_scaled[:4].reshape(1, -1)).flatten()
        vol_pred = np.expm1(vol_scaler.inverse_transform(pred_scaled[4].reshape(1, -1)).flatten())[0]
        pred_open, pred_close, pred_high, pred_low = float(price_pred[0]), float(price_pred[1]), float(price_pred[2]), float(price_pred[3])
        pred_vol = float(vol_pred)
        pred_high = max(pred_high, pred_open, pred_close)
        pred_low = min(pred_low, pred_open, pred_close)
        pred_vol = max(pred_vol, 1.0)
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
        avg_price = (pred_open + pred_close + pred_high + pred_low) / 4
        amount = pred_vol * avg_price * 100
        new_row['amount'] = max(amount, 1.0)
        window_df = pd.concat([window_df, pd.DataFrame([new_row])], ignore_index=True)
        # 只用robust_feature_engineering和stat_dict
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
    return np.array(preds), features

# ========== LSTM多目标预测主函数 ==========
def lstm_predict(df: pd.DataFrame, stock_name: str = '', ts_code: str = '',
                window: int = None, pred_days: int = None,
                output_dir: str = IMAGE_OUTPUT_DIR,
                model_dir: str = MODEL_OUTPUT_DIR,
                feature_cols: list = None,
                epochs: int = None, batch_size: int = None,
                dropout: float = None, lstm_units: int = None,
                patience: int = None, lstm_layers: int = None,
                auto_feat: bool = True,
                **kwargs) -> dict:
    img_paths = {}
    try:
        # 默认参数全部从LSTM_DEFAULTS读取
        if window is None:
            window = LSTM_DEFAULTS['window']
        if pred_days is None:
            pred_days = PRED_DAYS
        if epochs is None:
            epochs = LSTM_DEFAULTS['epochs']
        if batch_size is None:
            batch_size = LSTM_DEFAULTS['batch_size']
        if dropout is None:
            dropout = LSTM_DEFAULTS['dropout']
        if lstm_units is None:
            lstm_units = LSTM_DEFAULTS['lstm_units']
        if patience is None:
            patience = LSTM_DEFAULTS.get('patience', 20)
        if lstm_layers is None:
            lstm_layers = LSTM_DEFAULTS.get('lstm_layers', 2)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(model_dir, exist_ok=True)
        if auto_feat:
            df = add_all_features(df)
        df = df.sort_values('trade_date')
        if not stock_name and 'stock_name' in df.columns:
            stock_name = str(df['stock_name'].iloc[0])
        if not ts_code and 'ts_code' in df.columns:
            ts_code = str(df['ts_code'].iloc[0])
        # 特征工程
        df, stat_dict, feature_cols = robust_feature_engineering(df)
        X = df[feature_cols].values
        y = df[['open','close','high','low','vol']].values
        X_seq, y_seq = make_sequences(X, y, window)
        # 价格和vol分开归一化
        X_train, y_train, X_scaler, price_scaler, vol_scaler = normalize_features(X_seq[:len(X_seq)-2*pred_days].reshape(-1, X.shape[1]), y_seq[:len(X_seq)-2*pred_days].reshape(-1, 5), fit=True)
        X_train = X_train.reshape(-1, window, X.shape[1])
        y_train = y_train.reshape(-1, 5)
        # 验证和测试集归一化
        X_val = X_scaler.transform(X_seq[len(X_seq)-2*pred_days:len(X_seq)-pred_days].reshape(-1, X.shape[1])).reshape(-1, window, X.shape[1])
        y_val = np.concatenate([
            price_scaler.transform(pd.DataFrame(y_seq[len(X_seq)-2*pred_days:len(X_seq)-pred_days], columns=['open','close','high','low','vol'])[['open','close','high','low']].values),
            vol_scaler.transform(np.log1p(pd.DataFrame(y_seq[len(X_seq)-2*pred_days:len(X_seq)-pred_days], columns=['open','close','high','low','vol'])['vol'].clip(lower=0)).values.reshape(-1,1))
        ], axis=1)
        X_test = X_scaler.transform(X_seq[len(X_seq)-pred_days:].reshape(-1, X.shape[1])).reshape(-1, window, X.shape[1])
        y_test = np.concatenate([
            price_scaler.transform(pd.DataFrame(y_seq[len(X_seq)-pred_days:], columns=['open','close','high','low','vol'])[['open','close','high','low']].values),
            vol_scaler.transform(np.log1p(pd.DataFrame(y_seq[len(X_seq)-pred_days:], columns=['open','close','high','low','vol'])['vol'].clip(lower=0)).values.reshape(-1,1))
        ], axis=1)
        # ========== 模型唯一性hash ==========
        feat_hash = hashlib.md5(str(feature_cols).encode('utf-8')).hexdigest()[:8]
        model_path = os.path.join(model_dir, f'{safe_filename(stock_name)}_{ts_code}_win{window}_feat{feat_hash}_lstm.h5')
        meta_path = os.path.join(model_dir, f'{safe_filename(stock_name)}_{ts_code}_win{window}_feat{feat_hash}_meta.json')
        need_train = True
        if os.path.exists(model_path) and os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            if meta.get('window') == window and meta.get('feature_cols') == feature_cols and meta.get('stock_name') == stock_name and meta.get('ts_code') == ts_code:
                from tensorflow.keras.models import load_model
                model = load_model(model_path, compile=False)
                need_train = False
        if need_train:
            model = Sequential()
            for i in range(lstm_layers):
                return_sequences = (i < lstm_layers - 1)
                if i == 0:
                    model.add(LSTM(lstm_units, return_sequences=return_sequences, input_shape=(window, X_train.shape[-1])))
                else:
                    model.add(LSTM(lstm_units, return_sequences=return_sequences))
                model.add(BatchNormalization())
                model.add(Dropout(dropout))
            model.add(Dense(5))
            model.compile(optimizer='adam', loss=weighted_multi_mse)
            early_stop = EarlyStopping(monitor='loss', patience=patience, restore_best_weights=True)
            checkpoint = ModelCheckpoint(model_path, monitor='loss', save_best_only=True)
            history = model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, callbacks=[early_stop, checkpoint], verbose=2)
            # 训练loss曲线
            loss_img_path = os.path.join(output_dir, f"{safe_filename(stock_name)}_lstm_train_loss_win{window}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.figure()
            plt.plot(history.history['loss'])
            plt.title(f'{stock_name}({ts_code}) LSTM训练loss曲线')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.savefig(loss_img_path)
            plt.close()
            img_paths['loss'] = loss_img_path
            meta = {'window': window, 'feature_cols': feature_cols, 'stock_name': stock_name, 'ts_code': ts_code}
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        else:
            # 查找最新的loss曲线图片
            loss_imgs = sorted(glob.glob(os.path.join(output_dir, f"{safe_filename(stock_name)}_lstm_train_loss_win{window}_*.png")), reverse=True)
            if loss_imgs:
                img_paths['loss'] = loss_imgs[0]
            else:
                img_paths['loss'] = None
        # ========== 未来N天递推预测 ==========
        last_trade_date = df['trade_date'].iloc[-1]
        pred_dates = get_next_trade_days(last_trade_date, pred_days)
        future_preds, future_feats = rolling_predict_df(model, df, window, pred_days, feature_cols, stat_dict, method='future', dates=pred_dates, price_scaler=price_scaler, vol_scaler=vol_scaler)
        # ========== 验证集递推式与滑窗式预测 ==========
        val_dates = df['trade_date'].iloc[-pred_days:]
        df_val1 = df.iloc[-2*pred_days-window:-pred_days].copy().reset_index(drop=True)
        val1_preds, val1_feats = rolling_predict_df(model, df_val1, window, pred_days, feature_cols, stat_dict, method='val1', dates=val_dates, price_scaler=price_scaler, vol_scaler=vol_scaler)
        df_val2 = df.iloc[-2*pred_days-window:-pred_days].copy().reset_index(drop=True)
        y_true_val2 = y_seq[-pred_days:]
        val2_preds, val2_feats = rolling_predict_df(model, df_val2, window, pred_days, feature_cols, stat_dict, method='val2', y_true=y_true_val2, dates=val_dates, price_scaler=price_scaler, vol_scaler=vol_scaler)
        # ========== 可视化：三子图 ==========
        # --- 调试输出：未来预测和验证集递推/滑窗的low-close、high-close差异 ---
        debug_log = open('debug_predict_log.txt', 'a', encoding='utf-8')
        # 生成future_pred，务必补trade_date字段
        future_pred = pd.DataFrame(future_preds, columns=['open','close','high','low','vol'])
        future_pred['trade_date'] = pred_dates.values
        future_pred['low_close_diff'] = future_pred['low'] - future_pred['close']
        future_pred['high_close_diff'] = future_pred['high'] - future_pred['close']
        debug_log.write("未来预测 low-close 差值描述:\n" + str(future_pred['low_close_diff'].describe()) + '\n')
        debug_log.write("未来预测 high-close 差值描述:\n" + str(future_pred['high_close_diff'].describe()) + '\n')
        future_pred.to_csv('future_pred_low_high_close_diff.csv', index=False, encoding='utf-8-sig')
        # 验证集递推
        val1_pred = pd.DataFrame(val1_preds, columns=['open','close','high','low','vol'])
        val1_pred['low_close_diff'] = val1_pred['low'] - val1_pred['close']
        val1_pred['high_close_diff'] = val1_pred['high'] - val1_pred['close']
        debug_log.write("验证集递推 low-close 差值描述:\n" + str(val1_pred['low_close_diff'].describe()) + '\n')
        debug_log.write("验证集递推 high-close 差值描述:\n" + str(val1_pred['high_close_diff'].describe()) + '\n')
        val1_pred.to_csv('val1_pred_low_high_close_diff.csv', index=False, encoding='utf-8-sig')
        # 验证集滑窗
        val2_pred = pd.DataFrame(val2_preds, columns=['open','close','high','low','vol'])
        val2_pred['low_close_diff'] = val2_pred['low'] - val2_pred['close']
        val2_pred['high_close_diff'] = val2_pred['high'] - val2_pred['close']
        debug_log.write("验证集滑窗 low-close 差值描述:\n" + str(val2_pred['low_close_diff'].describe()) + '\n')
        debug_log.write("验证集滑窗 high-close 差值描述:\n" + str(val2_pred['high_close_diff'].describe()) + '\n')
        val2_pred.to_csv('val2_pred_low_high_close_diff.csv', index=False, encoding='utf-8-sig')
        debug_log.close()
        def plot_three_subplots(df, pred_dates, future_preds, val_dates, val1_preds, val2_preds, val_true, stock_name, ts_code, save_dir, zoom=False):
            plt.figure(figsize=PLOT_STYLE['figsize'])
            # 子图1：历史+未来预测
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
            plt.plot(pred_dates, future_preds[:,2], 'orange', linestyle='--', label='未来预测最高价')
            plt.plot(pred_dates, future_preds[:,3], 'g--', label='未来预测最低价')
            if zoom:
                plt.scatter(pred_dates, future_preds[:,1], color='red', marker='o', label='预测收盘价点')
                plt.scatter(pred_dates, future_preds[:,2], color='orange', marker='^', label='预测最高价点')
                plt.scatter(pred_dates, future_preds[:,3], color='green', marker='s', label='预测最低价点')
            plt.plot([hist_dates.iloc[-1], pred_dates[0]], [hist_close.iloc[-1], future_preds[0,1]], color='orange', linestyle='--', linewidth=2, label='T到T+1连接')
            plt.title(f'{stock_name}({ts_code}) 历史+未来预测' + ("（局部）" if zoom else ""))
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
            plt.plot(val_dates, val1_preds[:,1], 'g-', label='验证集方法一收盘价')
            plt.plot(val_dates, val1_preds[:,2], color='orange', linestyle='-', label='验证集方法一最高价')
            plt.plot(val_dates, val1_preds[:,3], color='b', linestyle='-', label='验证集方法一最低价')
            if zoom:
                plt.scatter(val_dates, val1_preds[:,1], color='green', marker='o', label='预测收盘价点')
                plt.scatter(val_dates, val1_preds[:,2], color='orange', marker='^', label='预测最高价点')
                plt.scatter(val_dates, val1_preds[:,3], color='blue', marker='s', label='预测最低价点')
            plt.plot(val_dates, val_true[:,1], 'r--', label='验证集真实收盘价')
            plt.title(f'{stock_name}({ts_code}) 验证集递推式（方法一）' + ("（局部）" if zoom else ""))
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
            plt.plot(val_dates, val2_preds[:,1], 'g-', label='验证集方法二收盘价')
            plt.plot(val_dates, val2_preds[:,2], color='orange', linestyle='-', label='验证集方法二最高价')
            plt.plot(val_dates, val2_preds[:,3], color='b', linestyle='-', label='验证集方法二最低价')
            if zoom:
                plt.scatter(val_dates, val2_preds[:,1], color='green', marker='o', label='预测收盘价点')
                plt.scatter(val_dates, val2_preds[:,2], color='orange', marker='^', label='预测最高价点')
                plt.scatter(val_dates, val2_preds[:,3], color='blue', marker='s', label='预测最低价点')
            plt.plot(val_dates, val_true[:,1], 'r--', label='验证集真实收盘价')
            plt.title(f'{stock_name}({ts_code}) 验证集滑窗式（方法二）' + ("（局部）" if zoom else ""))
            plt.legend()
            plt.xlabel('日期')
            plt.ylabel('收盘价')
            plt.xticks(rotation=45)
            plt.tight_layout()
            filename = f'{safe_filename(stock_name)}_{ts_code}_three_subplots_{"zoomed_" if zoom else ""}{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            save_path = os.path.join(save_dir, filename)
            plt.savefig(save_path)
            plt.close()
            return save_path
        # 生成全量三子图
        img_path_three = plot_three_subplots(df, pred_dates, future_preds, val_dates, val1_preds, val2_preds, y_seq[-pred_days:], stock_name, ts_code, output_dir, zoom=False)
        img_paths['three'] = img_path_three
        # 生成局部三子图
        img_path_three_zoom = plot_three_subplots(df, pred_dates, future_preds, val_dates, val1_preds, val2_preds, y_seq[-pred_days:], stock_name, ts_code, output_dir, zoom=True)
        img_paths['three_zoomed'] = img_path_three_zoom
        # 生成局部K线图（plotly）
        idx_start = max(0, len(df)-window-5)
        df_zoom = df.iloc[idx_start:]
        kline_dates = pd.to_datetime(df_zoom['trade_date']).dt.strftime('%Y-%m-%d') if hasattr(df_zoom['trade_date'], 'dt') else df_zoom['trade_date']
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=kline_dates,
            open=df_zoom['open'], high=df_zoom['high'], low=df_zoom['low'], close=df_zoom['close'],
            increasing_line_color='blue', decreasing_line_color='cyan', name='历史K线'))
        fig.add_trace(go.Candlestick(
            x=future_pred['trade_date'],
            open=future_pred['open'], high=future_pred['high'], low=future_pred['low'], close=future_pred['close'],
            increasing_line_color='red', decreasing_line_color='magenta', name='预测K线'))
        fig.update_layout(
            title=f'{stock_name}({ts_code}) 局部K线图（历史:蓝/未来:红）',
            xaxis_title='日期', yaxis_title='价格',
            font=dict(family='SimHei,Microsoft YaHei,Arial Unicode MS', size=16),
            xaxis_rangeslider_visible=False,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis=dict(type='category')
        )
        kline_img_path = os.path.join(output_dir, f'{safe_filename(stock_name)}_{ts_code}_kline_zoomed_plotly_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
        fig.write_html(kline_img_path)
        img_paths['kline'] = kline_img_path
        result = {'future_pred': future_pred, 'img_paths': img_paths}
        # 兜底：如果'loss' key仍不存在，补None
        if 'loss' not in img_paths:
            img_paths['loss'] = None
        return result
    except Exception as e:
        # 发生异常时也保证返回结构完整
        if 'loss' not in img_paths:
            img_paths['loss'] = None
        return {'future_pred': None, 'img_paths': img_paths, 'error': str(e)}

# ================== 使用示例 ==================
if __name__ == '__main__':
    print("LSTM多目标预测模块测试：")
    # df = pd.read_csv('your_stock_data.csv')
    # result = lstm_predict(df, window=20, pred_days=5)
    # print(result['future_pred'].head())
    # print(f"训练loss曲线：{result['img_paths']['loss']}")
    # print(f"三子图：{result['img_paths']['three']}")
    # print(f"局部K线图：{result['img_paths']['kline']}")
    print("请在主程序或分析工具中导入本模块并调用lstm_predict函数。") 
