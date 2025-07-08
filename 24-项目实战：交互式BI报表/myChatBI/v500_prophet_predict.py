'''
程序说明：
## 1. 本模块为5.0.0版股票分析系统的Prophet未来预测工具，支持自定义训练/验证区间，先评估验证集误差，再用全量数据预测未来N天。
## 2. 输出趋势图和表格（plotly静态/交互式），图片命名规范，中文无乱码。
## 3. 可与特征工程模块配合使用，便于后续Web/Agent集成。
'''

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from prophet import Prophet
import chinese_calendar
from sklearn.metrics import mean_absolute_error, mean_squared_error
from v500_feature_engineering import add_all_features
from v500_config import IMAGE_OUTPUT_DIR, PLOT_STYLE

# ========== Prophet未来预测主函数 ==========
def prophet_predict(df: pd.DataFrame, n: int = None, stock_name: str = '', ts_code: str = '',
                   train_start: str = '', train_end: str = '',
                   val_start: str = '', val_end: str = '',
                   output_dir: str = IMAGE_OUTPUT_DIR,
                   interactive: bool = True,
                   auto_feat: bool = True,
                   **kwargs) -> dict:
    """
    :function: 对指定股票收盘价用Prophet预测未来n天，支持自定义训练/验证区间，输出趋势图和表格
    :param df: 股票行情DataFrame，需包含close/trade_date等字段
    :param n: 预测天数
    :param stock_name: 股票名称（用于图片命名）
    :param ts_code: 股票代码（用于图片命名）
    :param train_start: 训练集起始日期（YYYY-MM-DD），可选
    :param train_end: 训练集结束日期（YYYY-MM-DD），可选
    :param val_start: 验证集起始日期（YYYY-MM-DD），可选
    :param val_end: 验证集结束日期（YYYY-MM-DD），可选
    :param output_dir: 图片输出目录
    :param interactive: 是否输出交互式html，True为html，False为png
    :param auto_feat: 是否自动增强特征（调用特征工程）
    :param kwargs: 其他参数
    :return: {'val_table_md': 验证集表格, 'future_table_md': 未来预测表格, 'img_path': 图片/HTML路径, 'val_pred': 验证集预测DataFrame, 'future_pred': 未来预测DataFrame}
    """
    if auto_feat:
        df = add_all_features(df)
    os.makedirs(output_dir, exist_ok=True)
    df = df.sort_values('trade_date')
    df['ds'] = pd.to_datetime(df['trade_date'])
    df['y'] = df['close']
    today = df['ds'].max()
    # 默认近一年数据
    default_start = today - timedelta(days=365)
    default_end = today
    # 自动分割训练/验证集
    if not train_start:
        train_start = default_start
    else:
        train_start = pd.to_datetime(train_start)
    if not train_end:
        train_end = default_end - timedelta(days=30)
    else:
        train_end = pd.to_datetime(train_end)
    if not val_start:
        val_start = default_end - timedelta(days=30)
    else:
        val_start = pd.to_datetime(val_start)
    if not val_end:
        val_end = default_end
    else:
        val_end = pd.to_datetime(val_end)
    prophet_df = df[['ds','y']].copy()
    train_df = prophet_df[(prophet_df['ds'] >= train_start) & (prophet_df['ds'] <= train_end)]
    val_df = prophet_df[(prophet_df['ds'] >= val_start) & (prophet_df['ds'] <= val_end)]
    # 构造长假效应
    all_days = pd.date_range(start=prophet_df['ds'].min(), end=prophet_df['ds'].max() + timedelta(days=n), freq='D')
    is_holiday = [chinese_calendar.is_holiday(d) for d in all_days]
    long_holiday_dates = []
    i = 0
    while i < len(all_days):
        if is_holiday[i]:
            j = i
            while j < len(all_days) and is_holiday[j]:
                j += 1
            if j - i >= 3:
                long_holiday_dates.extend(all_days[i:j])
            i = j
        else:
            i += 1
    holidays_df = pd.DataFrame({
        'holiday': 'long_chinese_holiday',
        'ds': pd.to_datetime(long_holiday_dates),
        'lower_window': 0,
        'upper_window': 1
    })
    # 训练集建模，验证集评估
    m_val = Prophet(
        holidays=holidays_df,
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.10,
        seasonality_prior_scale=10.0,
        holidays_prior_scale=5.0,
        seasonality_mode='additive',
        changepoint_range=0.8,
        n_changepoints=25
    )
    m_val.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    m_val.fit(train_df)
    val_future = pd.DataFrame({'ds': val_df['ds']})
    val_forecast = m_val.predict(val_future)
    val_pred = val_forecast[['ds','yhat']].copy()
    val_pred = val_pred.set_index('ds').reindex(val_df['ds']).reset_index()
    val_pred['y_true'] = val_df['y'].values
    val_pred['abs_err'] = (val_pred['yhat'] - val_pred['y_true']).abs()
    mae = mean_absolute_error(val_pred['y_true'], val_pred['yhat'])
    rmse = mean_squared_error(val_pred['y_true'], val_pred['yhat']) ** 0.5
    val_pred['ds'] = val_pred['ds'].dt.strftime('%Y-%m-%d')
    val_table_md = val_pred[['ds','y_true','yhat','abs_err']].to_markdown(index=False)
    val_summary = f"验证集MAE={mae:.2f}，RMSE={rmse:.2f}"
    # 全量数据建模，未来n天预测
    m = Prophet(
        holidays=holidays_df,
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.10,
        seasonality_prior_scale=10.0,
        holidays_prior_scale=5.0,
        seasonality_mode='additive',
        changepoint_range=0.8,
        n_changepoints=25
    )
    m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    m.fit(prophet_df)
    last_date = prophet_df['ds'].max()
    future = m.make_future_dataframe(periods=n)
    forecast = m.predict(future)
    pred_df = forecast[forecast['ds'] > last_date][['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    # 绘图
    import matplotlib.pyplot as plt
    plt.figure(figsize=PLOT_STYLE['figsize'])
    plt.plot(prophet_df['ds'], prophet_df['y'], color='blue', label='历史收盘价')
    plt.scatter(val_df['ds'], val_df['y'], color='blue', marker='o', s=40, label='验证集真实值')
    plt.scatter(pd.to_datetime(val_pred['ds']), val_pred['yhat'], color='orange', marker='x', s=50, label='验证集预测值')
    plt.plot(pred_df['ds'], pred_df['yhat'], 'r--', label='未来预测收盘价')
    plt.fill_between(pred_df['ds'], pred_df['yhat_lower'], pred_df['yhat_upper'], color='pink', alpha=0.3, label='置信区间')
    plt.xlabel('日期')
    plt.ylabel('收盘价')
    plt.title(f'{stock_name}({ts_code}) Prophet未来{n}天收盘价预测', fontname=PLOT_STYLE['font_family'])
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    if not stock_name and 'stock_name' in df.columns:
        stock_name = str(df['stock_name'].iloc[0])
    if not ts_code and 'ts_code' in df.columns:
        ts_code = str(df['ts_code'].iloc[0])
    date_range = f"{prophet_df['ds'].dt.strftime('%Y-%m-%d').iloc[0]}~{prophet_df['ds'].dt.strftime('%Y-%m-%d').iloc[-1]}"
    img_type = 'prophet_pred'
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = ''.join([c if c.isalnum() or '\u4e00' <= c <= '\u9fa5' else '_' for c in stock_name])
    filename = f"{safe_name}_{ts_code}_{date_range}_{img_type}_{now_str}.png"
    img_path = os.path.join(output_dir, filename)
    plt.savefig(img_path)
    plt.close()
    pred_df['ds'] = pred_df['ds'].dt.strftime('%Y-%m-%d')
    future_table_md = pred_df.to_markdown(index=False)
    return {'val_table_md': val_table_md + '\n' + val_summary, 'future_table_md': future_table_md, 'img_path': img_path, 'val_pred': val_pred, 'future_pred': pred_df}

# ================== 使用示例 ==================
if __name__ == '__main__':
    print("Prophet未来预测模块测试：")
    # df = pd.read_csv('your_stock_data.csv')
    # result = prophet_predict(df, n=10)
    # print(result['val_table_md'])
    # print(result['future_table_md'])
    # print(f"Prophet预测图已保存：{result['img_path']}")
    print("请在主程序或分析工具中导入本模块并调用prophet_predict函数。") 
