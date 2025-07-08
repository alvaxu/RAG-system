# -*- coding: utf-8 -*-
# 使用Tushare下载688692.SH股票的历史收盘价数据
import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# 设置Tushare的token
# 注意：需要先注册Tushare账号并获取token
# 请替换下面的YOUR_TOKEN为您的实际token
token = '91ff05c57927e99826a17d718b1f95180c82b36cf2435d50bfbbc942'
ts.set_token(token)
pro = ts.pro_api()

# 定义股票代码和时间范围
stock_code = '688692.SH'
# 获取当前日期作为结束日期
end_date = datetime.now().strftime('%Y%m%d')
# 设置起始日期为上市日期或更早的日期
start_date = '20200101'  # 可以根据实际需要调整

# 下载股票数据
try:
    # 使用pro_bar接口获取日线数据
    df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
    
    # 检查是否成功获取数据
    if df is not None and not df.empty:
        # 按照日期升序排列
        df = df.sort_values('trade_date')
        
        # 将trade_date转换为datetime格式
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        
        # 设置trade_date为索引
        df.set_index('trade_date', inplace=True)
        
        # 保存数据到CSV文件
        output_file = f'{stock_code.replace(".", "_")}_daily_data.csv'
        df.to_csv(output_file)
        print(f'数据已保存到 {output_file}')
        
        # 查看数据
        print("数据前5行:")
        print(df.head())
        
        # 显示收盘价走势图
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['close'], label='收盘价')
        plt.title(f'{stock_code} 历史收盘价走势图')
        plt.xlabel('日期')
        plt.ylabel('收盘价(元)')
        plt.grid(True)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{stock_code.replace(".", "_")}_close_price.png')
        plt.show()
        
        # 统计信息
        print("\n基本统计信息:")
        print(df['close'].describe())
        
    else:
        print("未获取到数据，请检查股票代码和日期范围")

except Exception as e:
    print(f"获取数据时出错: {e}")
    print("请确保您已正确设置Tushare的token，并且股票代码格式正确")
    print("如果您还没有Tushare账号，请访问 https://tushare.pro 注册并获取token") 