"""
程序说明：
## 1. 分析customer_behavior_assets.csv文件的数据特征
## 2. 检查时间序列的完整性和分布
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

def analyze_data(file_path='customer_behavior_assets.csv'):
    """
    分析数据文件的基本特征
    :param file_path: 数据文件路径
    """
    try:
        print("\n=== 数据文件分析 ===")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误：文件 {file_path} 不存在！")
            print(f"当前工作目录: {os.getcwd()}")
            print("目录中的文件:")
            for f in os.listdir('.'):
                print(f"- {f}")
            return None
        
        # 读取数据
        print(f"正在读取数据文件: {file_path}")
        print(f"文件大小: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
        
        df = pd.read_csv(file_path)
        
        # 基本信息
        print(f"\n1. 数据基本信息:")
        print(f"总记录数: {len(df)}")
        print(f"字段列表: {', '.join(df.columns)}")
        print("\n字段数据类型:")
        for col in df.columns:
            print(f"- {col}: {df[col].dtype}")
        
        # 时间范围分析
        print(f"\n2. 时间范围分析:")
        df['stat_month'] = pd.to_datetime(df['stat_month'])
        time_range = df['stat_month'].agg(['min', 'max'])
        print(f"最早时间: {time_range['min'].strftime('%Y-%m-%d')}")
        print(f"最晚时间: {time_range['max'].strftime('%Y-%m-%d')}")
        print(f"时间跨度: {(time_range['max'] - time_range['min']).days} 天")
        
        # 按月份统计
        monthly_stats = df.groupby('stat_month').agg({
            'customer_id': 'count',
            'total_assets': ['sum', 'mean', 'std']
        }).round(2)
        
        # 重命名列以便更好地显示
        monthly_stats.columns = ['客户数', '总资产和', '平均资产', '资产标准差']
        
        print(f"\n3. 月度统计:")
        print(f"月份数量: {len(monthly_stats)}")
        print("\n月度数据概览:")
        print(monthly_stats)
        
        # 计算月度增长率
        monthly_stats['资产环比增长率'] = monthly_stats['总资产和'].pct_change() * 100
        print("\n4. 月度资产增长率:")
        print(monthly_stats['资产环比增长率'].round(2))
        
        return df
        
    except Exception as e:
        print(f"错误：{str(e)}")
        print(f"错误类型：{type(e).__name__}")
        import traceback
        print("详细错误信息：")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    print(f"Python版本: {sys.version}")
    print(f"Pandas版本: {pd.__version__}")
    print(f"当前工作目录: {os.getcwd()}")
    df = analyze_data() 