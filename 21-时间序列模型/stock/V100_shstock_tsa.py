# -*- coding: utf-8 -*-
'''
程序说明：
## 1. 本程序基于上海股市历史数据，利用statsmodels的季节性分解(seasonal_decompose)方法，对收盘价进行趋势、季节性和残差分解，并进行可视化和图片保存。
## 2. 代码包含数据预处理（如缺失值插补）、分解及可视化全过程，适合初步时间序列分析。
'''

import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import matplotlib

def set_chinese_font():
    """
    :function: 设置matplotlib的中文字体，防止中文乱码
    :return: None
    """
    try:
        matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 黑体
        matplotlib.rcParams['axes.unicode_minus'] = False    # 负号正常显示
    except Exception as e:
        print("字体设置失败，可能导致中文乱码：", e)

def tsa_analysis_and_plot(csv_path, period=250, show_plot=True, save_path=None):
    """
    :function: 对股票价格数据进行季节性分解（趋势、季节性、残差）并可视化和保存图片
    :param csv_path: 股票数据CSV文件路径，需包含'Timestamp'和'Price'两列
    :param period: 分解周期，默认为250（约等于一年交易日数）
    :param show_plot: 是否显示分解结果图
    :param save_path: 图片保存路径（如'V100_shstock_tsa_result.png'），为None时不保存
    :return: 分解结果对象
    """
    set_chinese_font()
    # 读取数据
    data = pd.read_csv(csv_path, usecols=['Timestamp', 'Price'])
    data['Timestamp'] = pd.to_datetime(data['Timestamp'])
    data = data.set_index('Timestamp')
    data['Price'] = pd.to_numeric(data['Price'], errors='coerce')
    # 线性插值填补缺失值
    data['Price'].interpolate(inplace=True)
    # 时间序列分解
    result = sm.tsa.seasonal_decompose(data['Price'], period=period)
    fig = result.plot()
    plt.suptitle('上海股市指数TSA分解', fontsize=16)
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
        print(f"分解结果图片已保存到：{save_path}")
    if show_plot:
        plt.show()
    plt.close()
    return result

if __name__ == "__main__":
    # 调试模式：只取部分数据，加快运行速度
    DEBUG = False
    if DEBUG:
        df = pd.read_csv('shanghai_index_1990_12_19_to_2020_03_12.csv', usecols=['Timestamp', 'Price'])
        df = df.head(1000)
        df.to_csv('debug_shanghai_index.csv', index=False)
        tsa_analysis_and_plot('debug_shanghai_index.csv', period=250, save_path='V100_shstock_tsa_result.png')
    else:
        # 正式运行
        tsa_analysis_and_plot('shanghai_index_1990_12_19_to_2020_03_12.csv', period=250, save_path='V100_shstock_tsa_result.png')
