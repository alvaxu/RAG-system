# -*- coding: utf-8 -*-
# 使用Tushare旧版API下载688692.SH股票的历史收盘价数据
import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# 定义股票代码和时间范围
# 注意：旧版API需要将股票代码格式转换为6位数字+sh/sz格式
stock_code_pro = '688692.SH'
stock_code = '688692.SH'.split('.')[0] + '.SH'  # 保持原格式以便兼容

# 获取当前日期作为结束日期
end_date = datetime.now().strftime('%Y-%m-%d')
# 设置起始日期为上市日期或更早的日期
start_date = '2020-01-01'  # 可以根据实际需要调整

try:
    # 使用get_hist_data获取历史行情数据
    # 注意：此API不需要token，但可能有数据限制
    print(f"正在获取 {stock_code} 的历史数据...")
    df = ts.get_hist_data(code=stock_code.replace('.SH', '').replace('.SZ', ''), 
                          start=start_date, 
                          end=end_date)
    
    # 检查是否成功获取数据
    if df is not None and not df.empty:
        # 按照日期升序排列
        df = df.sort_index()
        
        # 保存数据到CSV文件
        output_file = f'{stock_code.replace(".", "_")}_daily_data_alt.csv'
        df.to_csv(output_file)
        print(f'数据已保存到 {output_file}')
        
        # 查看数据
        print("数据前5行:")
        print(df.head())
        
        # 显示收盘价走势图
        plt.figure(figsize=(12, 6))
        plt.rcParams['font.sans-serif']=['SimHei'] # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus']=False   # 用来正常显示负号
        plt.plot(df.index, df['close'], label='收盘价')
        plt.title(f'{stock_code} 历史收盘价走势图')
        plt.xlabel('日期')
        plt.ylabel('收盘价(元)')
        plt.grid(True)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{stock_code.replace(".", "_")}_close_price_alt.png')
        plt.show()
        
        # 统计信息
        print("\n基本统计信息:")
        print(df['close'].describe())
        
    else:
        print("未获取到数据，请检查股票代码和日期范围")
        # 尝试获取股票基本信息
        stock_basics = ts.get_stock_basics()
        if stock_basics is not None and not stock_basics.empty:
            # 检查股票代码是否存在
            code = stock_code.replace('.SH', '').replace('.SZ', '')
            if code in stock_basics.index:
                print(f"股票 {code} 存在于数据库中，但未能获取历史数据")
            else:
                print(f"股票代码 {code} 不存在于数据库中，请检查股票代码是否正确")
        else:
            print("无法获取股票基本信息，请检查网络连接")

except Exception as e:
    print(f"获取数据时出错: {e}")
    print("如果您需要更完整的数据，请使用Tushare的专业版API(需要token)")
    print("访问 https://tushare.pro 注册并获取token，然后使用download_688692SH.py文件")

# 备注：如果上述方法无法获取数据，您还可以尝试以下方法：
print("\n备选方法:")
print("1. 使用akshare库:")
print("   pip install akshare")
print("   import akshare as ak")
print("   df = ak.stock_zh_a_hist(symbol='688692', period='daily', start_date='20200101', end_date='20230101')")
print("2. 使用baostock库:")
print("   pip install baostock")
print("   import baostock as bs")
print("   bs.login()")
print("   df = bs.query_history_k_data_plus('sh.688692', 'date,close', start_date='2020-01-01', end_date='2023-01-01')")
print("   bs.logout()") 