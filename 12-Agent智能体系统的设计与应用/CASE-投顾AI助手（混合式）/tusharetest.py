import tushare as ts
from datetime import datetime, timedelta

# tushare配置
TS_TOKEN = 'bef9363ee81f40ec250748ae9d8150773c92672fa3f010adf39cec28'
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

# 获取今天日期
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')

# 获取最近两个交易日（包括今天，防止今天是交易日）
cal = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)
trade_days = cal[cal['is_open'] == 1]['cal_date'].tolist()

if len(trade_days) < 2:
    print("无法获取最近两个交易日，请检查数据源。")
else:
    last_trade_day = trade_days[-2]  # 倒数第二个是上一交易日
    # 查询上一交易日上证指数行情
    df = pro.index_daily(ts_code='000001.SH', trade_date=last_trade_day)
    if df.empty:
        print(f"上一交易日({last_trade_day})没有上证指数数据。")
    else:
        print(f"上一交易日({last_trade_day})上证指数行情：")
        print(df)

