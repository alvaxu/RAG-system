'''
程序说明：
## 1. 本程序使用tushare获取贵州茅台、五粮液、国泰君安、中芯国际的历史价格数据（2020-01-01至今），并将数据保存为xlsx文件。
## 2. 采用传统方式保存为xlsx，便于后续分析。代码包含详细中文注释，便于理解和维护。
'''

import tushare as ts
import pandas as pd
from datetime import datetime
from langchain_community.utilities import SQLDatabase

# 设置tushare的token（请替换为你自己的token）
TS_TOKEN = '1a67a1eee576746cb77b4b72078d4ccf72af7c9903c85547870b7067'
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

# 股票代码及名称映射（A股/港股）
stocks = {
    '贵州茅台': '600519.SH',
    '五粮液': '000858.SZ',
    '国泰君安': '601211.SH',
    '中芯国际': '688981.SH',  # 若需港股代码请改为'0981.HK'
}

# 设置起止日期
start_date = '20200101'
end_date = datetime.now().strftime('%Y%m%d')

# 保存数据的Excel文件名
output_file = '1.1.0_stock_history_20200101_to_now.xlsx'

# 用于存储所有股票数据
data_dict = {}

for name, code in stocks.items():
    print(f'正在获取{name}（{code}）的历史数据...')
    try:
        # 获取日线行情
        df = pro.daily(ts_code=code, start_date=start_date, end_date=end_date)
        if df.empty:
            print(f'警告：{name}（{code}）无数据！')
            continue
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date')
        data_dict[name] = df
        print(f'{name}数据获取成功，共{len(df)}条记录。')
    except Exception as e:
        print(f'获取{name}（{code}）数据时出错：{e}')

# 将所有数据写入Excel的不同sheet
if data_dict:
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for name, df in data_dict.items():
            df.to_excel(writer, sheet_name=name, index=False)
    print(f'所有数据已保存到 {output_file}')
else:
    print('未获取到任何数据，未生成Excel文件。')

# 说明：
# 1. 运行前请确保已安装 tushare、pandas、xlsxwriter。
# 2. 需在tushare官网注册并替换自己的token。
# 3. 若需调试，可将stocks字典缩减为1只股票以加快速度。

#oracle数据库连接配置:
#1.创建cx_Oracle连接
import cx_Oracle
dsn = cx_Oracle.makedsn('192.168.43.11', 1521, service_name='FREEPDB1')  # 替换实际主机名
conn = cx_Oracle.connect(user="dbtest", password="test", dsn=dsn)

# print(conn.version)  # 输出版本号表示成功
# conn.close()

#2.转换为SQLDatabase实例
db = SQLDatabase.from_uri(f"oracle+cx_oracle://", engine_args={"creator": lambda: conn})

#3. 执行测试查询
result = db.run("SELECT count （*） FROM stock_history_data")
print(result)
