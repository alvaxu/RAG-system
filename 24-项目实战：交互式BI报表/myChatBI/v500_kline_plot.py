'''
程序说明：
## 1. 本模块为5.0.0版股票分析系统的K线图/折线图自动绘制工具，支持plotly静态/交互式K线图和折线图。
## 2. 自动识别数据字段，支持多股票对比、区间自定义，图片命名规范，中文无乱码。
## 3. 可与特征工程模块配合使用，便于后续Web/Agent集成。
'''

import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from v500_feature_engineering import add_all_features
from v500_config import IMAGE_OUTPUT_DIR, PLOT_STYLE

# ========== 主要绘图函数 ==========
def plot_kline(df: pd.DataFrame, stock_name: str = '', ts_code: str = '',
               output_dir: str = IMAGE_OUTPUT_DIR,
               interactive: bool = True,
               auto_feat: bool = True) -> str:
    """
    :function: 自动绘制plotly K线图，支持静态/交互式，自动识别字段，中文无乱码
    :param df: 股票行情DataFrame，需包含open/high/low/close/vol/trade_date等字段
    :param stock_name: 股票名称（用于图片命名）
    :param ts_code: 股票代码（用于图片命名）
    :param output_dir: 图片输出目录
    :param interactive: 是否输出交互式html，True为html，False为png
    :param auto_feat: 是否自动增强特征（调用特征工程）
    :return: 图片/HTML文件路径
    """
    if auto_feat:
        df = add_all_features(df)
    os.makedirs(output_dir, exist_ok=True)
    df = df.sort_values('trade_date')
    df['trade_date_str'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
    # 自动识别股票名/代码
    if not stock_name and 'stock_name' in df.columns:
        stock_name = str(df['stock_name'].iloc[0])
    if not ts_code and 'ts_code' in df.columns:
        ts_code = str(df['ts_code'].iloc[0])
    # 文件名
    date_range = f"{df['trade_date_str'].iloc[0]}~{df['trade_date_str'].iloc[-1]}"
    img_type = 'kline'
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = ''.join([c if c.isalnum() or '\u4e00' <= c <= '\u9fa5' else '_' for c in stock_name])
    filename = f"{safe_name}_{ts_code}_{date_range}_{img_type}_{now_str}"
    # plotly K线
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['trade_date_str'],
        open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        increasing_line_color='red', decreasing_line_color='green',
        name='K线'))
    # 成交量
    if 'vol' in df.columns:
        fig.add_trace(go.Bar(
            x=df['trade_date_str'],
            y=df['vol'],
            name='成交量',
            yaxis='y2',
            marker_color='rgba(100,100,200,0.3)'))
        fig.update_layout(
            yaxis=dict(title='价格'),
            yaxis2=dict(title='成交量', overlaying='y', side='right', showgrid=False, position=1.0)
        )
    fig.update_layout(
        title=f'{stock_name}({ts_code}) {date_range} K线图',
        xaxis_title='日期',
        yaxis_title='价格',
        font=dict(family=PLOT_STYLE['font_family'], size=16),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(type='category')
    )
    # 输出
    if interactive:
        html_path = os.path.join(output_dir, filename + '.html')
        fig.write_html(html_path)
        return html_path
    else:
        png_path = os.path.join(output_dir, filename + '.png')
        fig.write_image(png_path, width=960, height=690, scale=1)
        return png_path


def plot_line(df: pd.DataFrame, y_cols=None, stock_name: str = '', ts_code: str = '',
              output_dir: str = IMAGE_OUTPUT_DIR,
              auto_feat: bool = True) -> str:
    """
    :function: 自动绘制plotly折线图，支持多指标/多股票对比，中文无乱码
    :param df: 股票行情DataFrame，需包含trade_date及数值型字段
    :param y_cols: 需要绘制的y轴字段列表，默认只显示核心特征['close','ma5','ma10','vol']
    :param stock_name: 股票名称（用于图片命名）
    :param ts_code: 股票代码（用于图片命名）
    :param output_dir: 图片输出目录
    :param auto_feat: 是否自动增强特征（调用特征工程）
    :return: 图片文件路径
    """
    if auto_feat:
        df = add_all_features(df)
    os.makedirs(output_dir, exist_ok=True)
    df = df.sort_values('trade_date')
    df['trade_date_str'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
    # 默认只显示核心特征
    if not y_cols:
        y_cols = [col for col in ['close','ma5','ma10','vol'] if col in df.columns]
    if not stock_name and 'stock_name' in df.columns:
        stock_name = str(df['stock_name'].iloc[0])
    if not ts_code and 'ts_code' in df.columns:
        ts_code = str(df['ts_code'].iloc[0])
    date_range = f"{df['trade_date_str'].iloc[0]}~{df['trade_date_str'].iloc[-1]}"
    img_type = 'line'
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = ''.join([c if c.isalnum() or '\u4e00' <= c <= '\u9fa5' else '_' for c in stock_name])
    filename = f"{safe_name}_{ts_code}_{date_range}_{img_type}_{now_str}.png"
    fig = go.Figure()
    for col in y_cols:
        fig.add_trace(go.Scatter(x=df['trade_date_str'], y=df[col], mode='lines+markers', name=col))
    fig.update_layout(
        title=f'{stock_name}({ts_code}) {date_range} 折线图',
        xaxis_title='日期',
        yaxis_title='数值',
        font=dict(family=PLOT_STYLE['font_family'], size=16),
        xaxis=dict(type='category'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    img_path = os.path.join(output_dir, filename)
    fig.write_image(img_path, width=960, height=690, scale=1)
    return img_path

# ================== 使用示例 ==================
if __name__ == '__main__':
    print("K线图/折线图自动绘制模块测试：")
    # df = pd.read_csv('your_stock_data.csv')
    # kline_path = plot_kline(df)
    # print(f"K线图已保存：{kline_path}")
    # line_path = plot_line(df, y_cols=['close','ma5'])
    # print(f"折线图已保存：{line_path}")
    print("请在主程序或分析工具中导入本模块并调用plot_kline/plot_line函数。") 
