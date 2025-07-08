import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取数据
def load_data():
    try:
        df = pd.read_excel('香港各区疫情数据_20250322.xlsx')
        # 确保报告日期列为datetime类型
        df['报告日期'] = pd.to_datetime(df['报告日期'])
        print("数据加载成功！")
        return df
    except Exception as e:
        print(f"数据加载失败：{e}")
        return None

# 基本数据统计
def basic_statistics(df):
    print("\n=== 基本统计信息 ===")
    print(f"数据时间范围：{df['报告日期'].min().strftime('%Y-%m-%d')} 至 {df['报告日期'].max().strftime('%Y-%m-%d')}")
    print(f"总记录数：{len(df)}")
    print(f"地区数量：{df['地区名称'].nunique()}")
    
    # 计算总体疫情指标
    total_stats = {
        '总新增确诊': df['新增确诊'].sum(),
        '总累计确诊': df['累计确诊'].max(),
        '总现存确诊': df['现存确诊'].max(),
        '总新增死亡': df['新增死亡'].sum(),
        '总累计死亡': df['累计死亡'].max()
    }
    print("\n总体疫情指标：")
    for key, value in total_stats.items():
        print(f"{key}: {value}")

# 地区分析
def district_analysis(df):
    print("\n=== 地区疫情分析 ===")
    # 按地区统计累计确诊
    district_stats = df.groupby('地区名称').agg({
        '累计确诊': 'max',
        '人口': 'max',
        '发病率(每10万人)': 'max'
    }).sort_values('累计确诊', ascending=False)
    
    print("\n各地区累计确诊情况：")
    print(district_stats)
    
    return district_stats

# 时间趋势分析
def time_analysis(df):
    print("\n=== 时间趋势分析 ===")
    # 按日期统计新增确诊和累计确诊
    daily_stats = df.groupby('报告日期').agg({
        '新增确诊': 'sum',
        '累计确诊': 'max'
    })
    
    print("\n最近10天的数据：")
    print(daily_stats.tail(10))
    
    return daily_stats

# 可视化函数
def visualize_data(df, daily_stats):
    # 创建图表和双纵轴
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()
    
    # 设置背景色
    fig.patch.set_facecolor('#F5F5F5')
    ax1.set_facecolor('#F5F5F5')
    
    # 绘制新增确诊折线（左轴）
    line1 = ax1.plot(daily_stats.index, daily_stats['新增确诊'], 
                    color='#FF6B6B', linewidth=2, label='每日新增确诊')
    ax1.set_ylabel('每日新增确诊数', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#FF6B6B')
    
    # 绘制累计确诊折线（右轴）
    line2 = ax2.plot(daily_stats.index, daily_stats['累计确诊'], 
                    color='#4ECDC4', linewidth=2, label='累计确诊')
    ax2.set_ylabel('累计确诊数', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#4ECDC4')
    
    # 设置标题和网格
    plt.title('香港每日新增确诊与累计确诊趋势', fontsize=14, pad=20)
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # 设置x轴为按周显示
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())  # 自动选择合适的主刻度间隔
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))  # 月-日格式
    ax1.xaxis.set_minor_locator(mdates.DayLocator())  # 次刻度为天
    
    # 设置x轴标签旋转
    plt.xticks(rotation=45, ha='right')
    
    # 添加图例
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('hk_covid_trend_daily.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # 加载数据
    df = load_data()
    if df is None:
        return
    
    # 执行分析
    basic_statistics(df)
    daily_stats = time_analysis(df)
    
    # 生成可视化
    visualize_data(df, daily_stats)
    print("\n分析完成！图表已保存为 'hk_covid_trend_daily.png'")

if __name__ == "__main__":
    main() 