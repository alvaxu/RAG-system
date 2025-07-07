'''
程序说明：
## 1. 本模块为5.0.0版股票分析系统的BOLL布林带异常点检测工具，支持20日+2σ布林带检测。
## 2. 自动检测超买/超卖点，输出Markdown表格和布林带图（plotly静态/交互式），图片命名规范，中文无乱码。
## 3. 可与特征工程模块配合使用，便于后续Web/Agent集成。
'''

import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from v500_feature_engineering import add_all_features
from v500_config import IMAGE_OUTPUT_DIR, PLOT_STYLE

# ========== BOLL布林带检测主函数 ==========
def boll_detection(df: pd.DataFrame, stock_name: str = '', ts_code: str = '',
                  output_dir: str = IMAGE_OUTPUT_DIR,
                  window: int = 20, n_sigma: float = 2.0,
                  interactive: bool = True,
                  auto_feat: bool = True,
                  **kwargs) -> dict:
    """
    :function: 对指定股票数据进行BOLL布林带异常点检测，输出表格和布林带图
    :param df: 股票行情DataFrame，需包含close/trade_date等字段
    :param stock_name: 股票名称（用于图片命名）
    :param ts_code: 股票代码（用于图片命名）
    :param output_dir: 图片输出目录
    :param window: 布林带周期，默认20
    :param n_sigma: 标准差倍数，默认2.0
    :param interactive: 是否输出交互式html，True为html，False为png
    :param auto_feat: 是否自动增强特征（调用特征工程）
    :return: {'table_md': markdown表格, 'img_path': 图片/HTML路径, 'outlier_df': 异常点DataFrame}
    """
    if auto_feat:
        df = add_all_features(df)
    os.makedirs(output_dir, exist_ok=True)
    df = df.sort_values('trade_date')
    df['trade_date_str'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
    # 计算BOLL指标
    df['MA'] = df['close'].rolling(window=window).mean()
    df['STD'] = df['close'].rolling(window=window).std()
    df['UPPER'] = df['MA'] + n_sigma * df['STD']
    df['LOWER'] = df['MA'] - n_sigma * df['STD']
    # 检测超买超卖点
    df['signal'] = ''
    df.loc[df['close'] > df['UPPER'], 'signal'] = '超买'
    df.loc[df['close'] < df['LOWER'], 'signal'] = '超卖'
    outlier_df = df[df['signal'] != '']
    # 生成结果表格
    result_md = outlier_df[['trade_date_str', 'close', 'MA', 'UPPER', 'LOWER', 'signal']].copy()
    result_md = result_md.rename(columns={'trade_date_str':'日期','close':'收盘价','MA':'MA20','UPPER':'上轨','LOWER':'下轨','signal':'信号'})
    table_md = result_md.to_markdown(index=False)
    # 文件名
    if not stock_name and 'stock_name' in df.columns:
        stock_name = str(df['stock_name'].iloc[0])
    if not ts_code and 'ts_code' in df.columns:
        ts_code = str(df['ts_code'].iloc[0])
    date_range = f"{df['trade_date_str'].iloc[0]}~{df['trade_date_str'].iloc[-1]}"
    img_type = 'boll'
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = ''.join([c if c.isalnum() or '\u4e00' <= c <= '\u9fa5' else '_' for c in stock_name])
    filename = f"{safe_name}_{ts_code}_{date_range}_{img_type}_{now_str}"
    # 绘制plotly布林带图
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['trade_date_str'], y=df['close'], mode='lines', name='收盘价', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['trade_date_str'], y=df['MA'], mode='lines', name=f'MA{window}', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df['trade_date_str'], y=df['UPPER'], mode='lines', name='上轨', line=dict(color='red', dash='dash')))
    fig.add_trace(go.Scatter(x=df['trade_date_str'], y=df['LOWER'], mode='lines', name='下轨', line=dict(color='green', dash='dash')))
    # 标记异常点
    if not outlier_df.empty:
        fig.add_trace(go.Scatter(x=outlier_df['trade_date_str'], y=outlier_df['close'],
                                 mode='markers', name='异常点',
                                 marker=dict(size=10, color=outlier_df['signal'].map({'超买':'red','超卖':'green'}),
                                             line=dict(width=2, color='black'))))
    fig.update_layout(
        title=f'{stock_name}({ts_code}) {date_range} BOLL布林带异常点检测',
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
    return {'table_md': table_md, 'img_path': img_path, 'outlier_df': outlier_df}

# ================== 使用示例 ==================
if __name__ == '__main__':
    print("BOLL布林带异常点检测模块测试：")
    # df = pd.read_csv('your_stock_data.csv')
    # result = boll_detection(df)
    # print(result['table_md'])
    # print(f"布林带图已保存：{result['img_path']}")
    print("请在主程序或分析工具中导入本模块并调用boll_detection函数。") 
