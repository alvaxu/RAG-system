'''
程序说明：
## 1. 本模块为5.0.0版股票分析系统的Prophet周期分析工具，对指定股票收盘价进行趋势、周、月、年周期分解，长假效应建模。
## 2. 输出分解图和表格（plotly静态/交互式），图片命名规范，中文无乱码。
## 3. 可与特征工程模块配合使用，便于后续Web/Agent集成。
'''

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from prophet import Prophet
import chinese_calendar
from v500_feature_engineering import add_all_features
from v500_config import IMAGE_OUTPUT_DIR, PLOT_STYLE

# ========== Prophet周期分析主函数 ==========
def prophet_analysis(df: pd.DataFrame, stock_name: str = '', ts_code: str = '',
                    output_dir: str = IMAGE_OUTPUT_DIR,
                    interactive: bool = True,
                    auto_feat: bool = True,
                    **kwargs) -> dict:
    """
    :function: 对指定股票收盘价进行Prophet周期分解，输出分解图和表格
    :param df: 股票行情DataFrame，需包含close/trade_date等字段
    :param stock_name: 股票名称（用于图片命名）
    :param ts_code: 股票代码（用于图片命名）
    :param output_dir: 图片输出目录
    :param interactive: 是否输出交互式html，True为html，False为png
    :param auto_feat: 是否自动增强特征（调用特征工程）
    :param kwargs: 其他参数
    :return: {'comp_table_md': markdown表格, 'img_path': 图片/HTML路径, 'comp_df': 分解结果DataFrame}
    """
    if auto_feat:
        df = add_all_features(df)
    os.makedirs(output_dir, exist_ok=True)
    df = df.sort_values('trade_date')
    df['ds'] = pd.to_datetime(df['trade_date'])
    df['y'] = df['close']
    # 构造长假效应
    start_date = df['ds'].min()
    end_date = df['ds'].max()
    all_days = pd.date_range(start=start_date, end=end_date, freq='D')
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
    # Prophet建模
    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='additive',
        interval_width=0.95,
        holidays=holidays_df
    )
    m.add_seasonality('monthly', period=30.5, fourier_order=5)
    m.fit(df[['ds','y']])
    future = m.make_future_dataframe(periods=0)
    forecast = m.predict(future)
    # 文件名
    if not stock_name and 'stock_name' in df.columns:
        stock_name = str(df['stock_name'].iloc[0])
    if not ts_code and 'ts_code' in df.columns:
        ts_code = str(df['ts_code'].iloc[0])
    date_range = f"{df['ds'].dt.strftime('%Y-%m-%d').iloc[0]}~{df['ds'].dt.strftime('%Y-%m-%d').iloc[-1]}"
    img_type = 'prophet_cycle'
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = ''.join([c if c.isalnum() or '\u4e00' <= c <= '\u9fa5' else '_' for c in stock_name])
    filename = f"{safe_name}_{ts_code}_{date_range}_{img_type}_{now_str}"
    # 绘制分解图（matplotlib保存，plotly可选）
    import matplotlib.pyplot as plt
    fig = m.plot_components(forecast)
    plt.gcf().set_size_inches(*PLOT_STYLE['figsize'])
    plt.suptitle(f'{stock_name}({ts_code}) {date_range} Prophet周期性分解', fontsize=16, fontname=PLOT_STYLE['font_family'])
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    img_path = os.path.join(output_dir, filename + '.png')
    plt.savefig(img_path)
    plt.close()
    # 生成分解表格
    comp_cols = ['ds', 'trend', 'weekly', 'yearly', 'monthly']
    if 'holidays' in forecast.columns:
        comp_cols.append('holidays')
    comp_df = forecast[comp_cols].copy()
    comp_df['ds'] = comp_df['ds'].dt.strftime('%Y-%m-%d')
    comp_table_md = comp_df.tail(10).to_markdown(index=False)
    return {'comp_table_md': comp_table_md, 'img_path': img_path, 'comp_df': comp_df}

# ================== 使用示例 ==================
if __name__ == '__main__':
    print("Prophet周期分析模块测试：")
    # df = pd.read_csv('your_stock_data.csv')
    # result = prophet_analysis(df)
    # print(result['comp_table_md'])
    # print(f"Prophet周期分解图已保存：{result['img_path']}\n")
    print("请在主程序或分析工具中导入本模块并调用prophet_analysis函数。") 
