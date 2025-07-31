'''
程序说明：
## 1. 本程序使用AKShare库，查询当天（今日）上证指数（000001.SH）的行情数据。
## 2. 若无数据（如休市日或接口异常），会自动回溯到最近一个有数据的交易日。
'''

import akshare as ak
from datetime import datetime, timedelta

# 获取今天日期，格式为YYYYMMDD
today = datetime.now()
max_lookback = 10  # 最多回溯10天，防止死循环

for i in range(max_lookback):
    query_date = (today - timedelta(days=i)).strftime('%Y%m%d')
    try:
        df = ak.index_zh_a_hist(symbol="sh000001", period="daily", start_date=query_date, end_date=query_date)
        if df is not None and not df.empty:
            print(f"最近有数据的交易日为：{query_date}，上证指数行情如下：")
            print(df)
            break
        else:
            if i == 0:
                print(f"今日({query_date})没有上证指数数据，尝试回溯...")
    except Exception as e:
        if i == 0:
            print(f"查询今日({query_date})时发生错误，尝试回溯... 错误信息：{e}")
    if i == max_lookback - 1:
        print(f"连续{max_lookback}天都未查到上证指数数据，可能接口异常或长时间休市。") 