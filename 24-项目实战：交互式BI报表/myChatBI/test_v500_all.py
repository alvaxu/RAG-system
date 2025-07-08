'''
程序说明：
## 1. 本脚本批量测试v500_系列分析模块，数据直接从Oracle数据库读取，涵盖特征工程、K线、BOLL、ARIMA、Prophet周期、Prophet预测、LSTM预测等功能。
## 2. 每步均有输出和异常捕获，便于快速定位问题。适合调试和环境验证。
'''

import pandas as pd
import traceback
from sqlalchemy import create_engine

# 导入分析模块
from v500_feature_engineering import add_all_features, get_feature_columns
from v500_kline_plot import plot_kline, plot_line
from v500_boll_detection import boll_detection
from v500_arima_stock import arima_stock
from v500_prophet_analysis import prophet_analysis
from v500_prophet_predict import prophet_predict
from v500_lstm_predict import lstm_predict
from v500_config import IMAGE_OUTPUT_DIR, ORACLE_CONN_STR, STOCKS, LSTM_DEFAULTS, PRED_DAYS

# ========== Oracle数据库连接配置 ==========
oracle_connection_string = ORACLE_CONN_STR

def get_stock_data(ts_code, start_date, end_date):
    """
    :function: 从Oracle数据库读取指定股票指定区间的历史行情数据
    :param ts_code: 股票代码，如'600519.SH'
    :param start_date: 开始日期，格式'YYYY-MM-DD'
    :param end_date: 结束日期，格式'YYYY-MM-DD'
    :return: DataFrame
    """
    engine = create_engine(oracle_connection_string)
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

if __name__ == '__main__':
    # 测试参数
    ts_code = STOCKS['贵州茅台']
    start_date = '2024-01-01'
    end_date = '2024-06-30'
    print(f"【数据读取】从Oracle读取{ts_code} {start_date}~{end_date} 的历史数据...")
    try:
        df = get_stock_data(ts_code, start_date, end_date)
        print(f"【数据读取】成功，样本数：{len(df)}，字段：{list(df.columns)}")
    except Exception as e:
        print("【数据读取】失败：", e)
        exit(1)

    # # 特征工程
    # try:
    #     df_feat = add_all_features(df)
    #     print("【特征工程】成功，特征列：", get_feature_columns(df_feat))
    #     print(df_feat.head())
    # except Exception as e:
    #     print("【特征工程】失败：\n", traceback.format_exc())

    # # K线图/折线图
    # try:
    #     kline_path = plot_kline(df)
    #     print("【K线图】已保存：", kline_path)
    #     line_path = plot_line(df, y_cols=['close','ma5'] if 'ma5' in df_feat.columns else None)
    #     print("【折线图】已保存：", line_path)
    # except Exception as e:
    #     print("【K线/折线图】失败：\n", traceback.format_exc())

    # # BOLL布林带
    # try:
    #     boll_result = boll_detection(df)
    #     print("【BOLL检测】表格：\n", boll_result['table_md'])
    #     print("【BOLL检测】图已保存：", boll_result['img_path'])
    # except Exception as e:
    #     print("【BOLL检测】失败：\n", traceback.format_exc())

    # # ARIMA预测
    # try:
    #     arima_result = arima_stock(df, n=5)
    #     print("【ARIMA预测】表格：\n", arima_result['pred_table_md'])
    #     print("【ARIMA预测】图已保存：", arima_result['img_path'])
    # except Exception as e:
    #     print("【ARIMA预测】失败：\n", traceback.format_exc())

    # # Prophet周期分析
    # try:
    #     prophet_cycle = prophet_analysis(df)
    #     print("【Prophet周期】表格：\n", prophet_cycle['comp_table_md'])
    #     print("【Prophet周期】图已保存：", prophet_cycle['img_path'])
    # except Exception as e:
    #     print("【Prophet周期】失败：\n", traceback.format_exc())

    # # Prophet未来预测
    # try:
    #     prophet_pred = prophet_predict(df, n=5)
    #     print("【Prophet预测】验证集：\n", prophet_pred['val_table_md'])
    #     print("【Prophet预测】未来预测：\n", prophet_pred['future_table_md'])
    #     print("【Prophet预测】图已保存：", prophet_pred['img_path'])
    # except Exception as e:
    #     print("【Prophet预测】失败：\n", traceback.format_exc())

    # LSTM预测（调试建议epochs=5, batch_size=8，加快测试）
    try:
        lstm_result = lstm_predict(df, window=LSTM_DEFAULTS['window'], pred_days=PRED_DAYS, epochs=LSTM_DEFAULTS['epochs'], batch_size=LSTM_DEFAULTS['batch_size'])
        print("【LSTM预测】未来预测：\n", lstm_result['future_pred'].head())
        print("【LSTM预测】loss曲线：", lstm_result['img_paths']['loss'])
        print("【LSTM预测】三子图：", lstm_result['img_paths']['three'])
        print("【LSTM预测】局部K线图：", lstm_result['img_paths']['kline'])
    except Exception as e:
        print("【LSTM预测】失败：\n", traceback.format_exc())

    print("【批量测试完成】如有报错请根据traceback定位模块和数据问题。")