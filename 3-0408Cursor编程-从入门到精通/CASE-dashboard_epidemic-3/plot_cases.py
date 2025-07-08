import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.dates import DateFormatter, WeekdayLocator
from matplotlib.font_manager import FontProperties

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取Excel文件
file_path = '香港各区疫情数据_20250322.xlsx'
try:
    # 读取Excel文件
    df = pd.read_excel(file_path)
    
    # 确保日期列格式正确
    df['报告日期'] = pd.to_datetime(df['报告日期'])
    
    # 按日期分组，计算每日新增确诊和累计确诊
    daily_data = df.groupby('报告日期').agg({
        '新增确诊': 'sum',
        '累计确诊': 'sum'
    }).reset_index()
    
    # 创建图表和双Y轴
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()
    
    # 设置颜色
    color1 = 'tab:blue'
    color2 = 'tab:red'
    
    # 绘制柱状图（每日新增确诊）
    ax1.bar(daily_data['报告日期'], daily_data['新增确诊'], 
            color=color1, alpha=0.7, label='每日新增确诊')
    ax1.set_xlabel('日期', fontsize=12)
    ax1.set_ylabel('每日新增确诊数', color=color1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # 绘制折线图（累计确诊）
    ax2.plot(daily_data['报告日期'], daily_data['累计确诊'], 
             color=color2, linewidth=2, label='累计确诊')
    ax2.set_ylabel('累计确诊数', color=color2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 设置标题
    plt.title('香港每日新增确诊与累计确诊趋势', fontsize=14, pad=20)
    
    # 设置网格
    ax1.grid(True, linestyle='--', alpha=0.3)
    
    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    # 设置日期格式和间隔
    ax1.xaxis.set_major_locator(WeekdayLocator(interval=1))
    ax1.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    
    # 自动调整日期显示
    plt.gcf().autofmt_xdate()
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('香港疫情趋势图.png', dpi=300, bbox_inches='tight')
    print("图表已保存为'香港疫情趋势图.png'")
    
    # 显示图表
    plt.show()
    
except FileNotFoundError:
    print(f"错误：找不到文件 {file_path}")
except Exception as e:
    print(f"处理数据时发生错误：{str(e)}") 