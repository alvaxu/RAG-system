'''
程序说明：
## 1. 本程序为5.0.0版股票历史数据智能分析与预测系统的TUI（命令行菜单式交互）主入口。
## 2. 支持特征工程、K线图、BOLL、ARIMA、Prophet周期、Prophet预测、LSTM预测等功能，参数输入灵活，输出表格/图片路径/智能建议。
'''

import pandas as pd
import traceback
from v500_config import STOCKS, ORACLE_CONN_STR, IMAGE_OUTPUT_DIR, LSTM_DEFAULTS, PRED_DAYS
from v500_feature_engineering import add_all_features, get_feature_columns
from v500_kline_plot import plot_kline, plot_line
from v500_boll_detection import boll_detection
from v500_arima_stock import arima_stock
from v500_prophet_analysis import prophet_analysis
from v500_prophet_predict import prophet_predict
from v500_lstm_predict import lstm_predict
from sqlalchemy import create_engine

# ========== 数据读取 ==========
def get_stock_data(ts_code, start_date, end_date):
    engine = create_engine(ORACLE_CONN_STR)
    sql = f"""
    SELECT stock_name, ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount
    FROM stock_history_data
    WHERE ts_code = '{ts_code}'
      AND trade_date >= TO_DATE('{start_date}', 'YYYY-MM-DD')
      AND trade_date <= TO_DATE('{end_date}', 'YYYY-MM-DD')
    ORDER BY trade_date
    """
    df = pd.read_sql(sql, engine)
    return df

# ========== TUI主流程 ==========
def main():
    print("欢迎使用5.0.0版股票历史数据智能分析与预测系统！\n")
    while True:
        print("""
请选择功能：
1. 特征工程
2. K线图
3. BOLL布林带
4. ARIMA预测
5. Prophet周期分析
6. Prophet未来预测
7. LSTM多目标预测
0. 退出
""")
        choice = input("请输入功能编号：").strip()
        if choice == '0':
            print("感谢使用，再见！")
            break
        # ====== 通用参数输入 ======
        print("可选股票：", ', '.join([f"{k}({v})" for k,v in STOCKS.items()]))
        stock_name = input("请输入股票名称（默认:贵州茅台）：").strip() or '贵州茅台'
        ts_code = STOCKS.get(stock_name, stock_name)
        start_date = input("请输入开始日期（YYYY-MM-DD，默认:2024-01-01）：").strip() or '2024-01-01'
        end_date = input("请输入结束日期（YYYY-MM-DD，默认:2024-06-30）：").strip() or '2024-06-30'
        try:
            df = get_stock_data(ts_code, start_date, end_date)
            print(f"【数据读取】成功，样本数：{len(df)}，字段：{list(df.columns)}")
        except Exception as e:
            print("【数据读取】失败：", e)
            continue
        # ====== 功能分支 ======
        try:
            if choice == '1':
                df_feat = add_all_features(df)
                print("【特征工程】成功，特征列：", get_feature_columns(df_feat))
                print(df_feat.head())
            elif choice == '2':
                kline_path = plot_kline(df)
                print(f"【K线图】已保存：{kline_path}")
                line_path = plot_line(df, y_cols=['close','ma5'] if 'ma5' in df.columns else None)
                print(f"【折线图】已保存：{line_path}")
            elif choice == '3':
                boll_result = boll_detection(df)
                print("【BOLL检测】表格：\n", boll_result['table_md'])
                print(f"【BOLL检测】图已保存：{boll_result['img_path']}")
            elif choice == '4':
                arima_result = arima_stock(df, n=PRED_DAYS)
                print("【ARIMA预测】表格：\n", arima_result['pred_table_md'])
                print(f"【ARIMA预测】图已保存：{arima_result['img_path']}")
            elif choice == '5':
                prophet_cycle = prophet_analysis(df)
                print("【Prophet周期】表格：\n", prophet_cycle['comp_table_md'])
                print(f"【Prophet周期】图已保存：{prophet_cycle['img_path']}")
            elif choice == '6':
                prophet_pred = prophet_predict(df, n=PRED_DAYS)
                print("【Prophet预测】验证集：\n", prophet_pred['val_table_md'])
                print("【Prophet预测】未来预测：\n", prophet_pred['future_table_md'])
                print(f"【Prophet预测】图已保存：{prophet_pred['img_path']}")
            elif choice == '7':
                window = input(f"请输入LSTM窗口长度（默认:{LSTM_DEFAULTS['window']}）：").strip() or LSTM_DEFAULTS['window']
                pred_days = input(f"请输入预测天数（默认:{PRED_DAYS}）：").strip() or PRED_DAYS
                epochs = input(f"请输入训练轮数（默认:{LSTM_DEFAULTS['epochs']}）：").strip() or LSTM_DEFAULTS['epochs']
                batch_size = input(f"请输入batch_size（默认:{LSTM_DEFAULTS['batch_size']}）：").strip() or LSTM_DEFAULTS['batch_size']
                lstm_result = lstm_predict(df, window=int(window), pred_days=int(pred_days), epochs=int(epochs), batch_size=int(batch_size))
                print("【LSTM预测】未来预测：\n", lstm_result['future_pred'].head())
                print("【LSTM预测】loss曲线：", lstm_result['img_paths']['loss'])
                print("【LSTM预测】三子图：", lstm_result['img_paths'].get('three'))
                print("【LSTM预测】局部K线图：", lstm_result['img_paths'].get('kline'))
                if lstm_result['img_paths']['loss'] is None:
                    print("【智能建议】：本次未生成loss曲线，建议检查模型训练或历史loss曲线文件。")
            else:
                print("无效选择，请重新输入。")
        except Exception as e:
            print("【功能执行失败】：\n", traceback.format_exc())

if __name__ == '__main__':
    main() 