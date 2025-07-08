import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties

try:
    # 读取Excel文件
    df = pd.read_excel('香港各区疫情数据_20250322.xlsx')
    
    # 打印字段名称
    print('字段名称：')
    for col in df.columns:
        print(f'- {col}')
    
    # 打印前20行数据
    print('\n前20行数据：')
    print(df.head(20).to_string())
    
    # 计算每日新增确诊和累计确诊
    daily_stats = df.groupby('报告日期').agg({
        '新增确诊': 'sum',
        '累计确诊': 'sum'
    }).reset_index()
    
    # 打印每日统计数据
    print('\n每日新增确诊和累计确诊数据：')
    print(daily_stats.to_string())
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    
    # 创建图形
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # 绘制每日新增确诊
    ax1.plot(daily_stats['报告日期'], daily_stats['新增确诊'], 'r-', label='每日新增确诊')
    ax1.set_title('香港每日新增确诊病例趋势')
    ax1.set_xlabel('日期')
    ax1.set_ylabel('新增确诊数')
    ax1.grid(True)
    ax1.legend()
    
    # 绘制累计确诊
    ax2.plot(daily_stats['报告日期'], daily_stats['累计确诊'], 'b-', label='累计确诊')
    ax2.set_title('香港累计确诊病例趋势')
    ax2.set_xlabel('日期')
    ax2.set_ylabel('累计确诊数')
    ax2.grid(True)
    ax2.legend()
    
    # 设置x轴日期格式
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图片
    plt.savefig('香港疫情趋势图.png', dpi=300, bbox_inches='tight')
    print('图表已保存为：香港疫情趋势图.png')
    
    # 显示图表
    plt.show()
    
except Exception as e:
    print(f'发生错误：{str(e)}') 