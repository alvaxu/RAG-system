'''
程序说明：
## 1. 本模块为5.0.0版股票分析系统的ARIMA预测工具，自动查询近一年数据，ARIMA(5,1,5)预测未来N天收盘价。
## 2. 输出预测表格和走势图（plotly静态/交互式），图片命名规范，中文无乱码。
## 3. 可与特征工程模块配合使用，便于后续Web/Agent集成。
'''

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
from v500_feature_engineering import add_all_features
from v500_config import IMAGE_OUTPUT_DIR, PLOT_STYLE, LSTM_DEFAULTS, PRED_DAYS

# ========== ARIMA预测主函数 ==========
def arima_stock(df: pd.DataFrame, n: int = None, stock_name: str = '', ts_code: str = '',
               output_dir: str = IMAGE_OUTPUT_DIR,
               interactive: bool = True,
               auto_feat: bool = True,
               **kwargs) -> dict:
    """
    :function: 对指定股票近一年数据用ARIMA(5,1,5)预测未来n天收盘价，输出表格和走势图
    :param df: 股票行情DataFrame，需包含close/trade_date等字段
    :param n: 预测天数
    :param stock_name: 股票名称（用于图片命名）
    :param ts_code: 股票代码（用于图片命名）
    :param output_dir: 图片输出目录
    :param interactive: 是否输出交互式html，True为html，False为png
    :param auto_feat: 是否自动增强特征（调用特征工程）
    :param kwargs: 其他参数
    :return: {'pred_table_md': markdown表格, 'img_path': 图片/HTML路径, 'pred_df': 预测结果DataFrame}
    """
    if auto_feat:
        df = add_all_features(df)
    os.makedirs(output_dir, exist_ok=True)
    df = df.sort_values('trade_date')
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    # 取近一年数据
    last_date = df['trade_date'].max()
    one_year_ago = last_date - timedelta(days=365)
    df = df[df['trade_date'] >= one_year_ago]
    close_series = df['close']
    # ARIMA建模与预测
    model = ARIMA(close_series, order=(5,1,5))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=n)
    # 生成预测日期
    pred_dates = pd.date_range(df['trade_date'].iloc[-1] + pd.Timedelta(days=1), periods=n, freq='B')
    pred_df = pd.DataFrame({'预测日期': pred_dates.strftime('%Y-%m-%d'), '预测收盘价': forecast})
    # 合并历史与预测，画图
    df['trade_date_str'] = df['trade_date'].dt.strftime('%Y-%m-%d')
    # 文件名
    if not stock_name and 'stock_name' in df.columns:
        stock_name = str(df['stock_name'].iloc[0])
    if not ts_code and 'ts_code' in df.columns:
        ts_code = str(df['ts_code'].iloc[0])
    date_range = f"{df['trade_date_str'].iloc[0]}~{df['trade_date_str'].iloc[-1]}"
    img_type = 'arima'
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = ''.join([c if c.isalnum() or '\u4e00' <= c <= '\u9fa5' else '_' for c in stock_name])
    filename = f"{safe_name}_{ts_code}_{date_range}_{img_type}_{now_str}"
    # 绘制plotly走势图
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['trade_date_str'], y=df['close'], mode='lines', name='历史收盘价', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=pred_df['预测日期'], y=pred_df['预测收盘价'], mode='lines+markers', name='预测收盘价', line=dict(color='red', dash='dash')))
    fig.update_layout(
        title=f'{stock_name}({ts_code}) ARIMA未来{n}天收盘价预测',
        xaxis_title='日期',
        yaxis_title='收盘价',
        font=dict(family=PLOT_STYLE['font_family'], size=16),
        xaxis=dict(type='category'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    # 输出
    if interactive:
        html_path = os.path.join(output_dir, filename + '.html')
        fig.write_html(html_path)
        img_path = html_path
    else:
        png_path = os.path.join(output_dir, filename + '.png')
        fig.write_image(png_path, width=960, height=690, scale=1)
        img_path = png_path
    pred_table_md = pred_df.to_markdown(index=False)
    return {'pred_table_md': pred_table_md, 'img_path': img_path, 'pred_df': pred_df}

# ================== 使用示例 ==================
if __name__ == '__main__':
    print("ARIMA预测模块测试：")
    # df = pd.read_csv('your_stock_data.csv')
    # result = arima_stock(df, n=7)
    # print(result['pred_table_md'])
    # print(f"ARIMA预测图已保存：{result['img_path']}")
    print("请在主程序或分析工具中导入本模块并调用arima_stock函数。") 
