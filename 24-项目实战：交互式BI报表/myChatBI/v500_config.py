'''
程序说明：
## 1. 本配置文件统一管理5.0.0版股票分析系统的输出目录、模型目录、数据库连接、股票池、模型参数、画图风格等全局参数。
## 2. 所有分析与预测模块均应import本文件，避免路径硬编码，便于维护和环境切换。
'''

# 路径相关
IMAGE_OUTPUT_DIR = '5.0.0_image_show'
MODEL_OUTPUT_DIR = '5.0.0_lstm_model'

# 数据库连接
DB_USER = 'dbtest'
DB_PASSWORD = 'test'
DB_HOST = '192.168.43.11:1521'
SERVICE_NAME = 'FREEPDB1'
ORACLE_CONN_STR = f"oracle+cx_oracle://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/?service_name={SERVICE_NAME}"

# 股票池
STOCKS = {
    '贵州茅台': '600519.SH',
    '五粮液': '000858.SZ',
    '国泰君安': '601211.SH',
    '中芯国际': '688981.SH',
    '全志科技': '300458.SZ',
}

# LSTM默认参数
LSTM_DEFAULTS = {
    'epochs': 2000,
    'batch_size': 32,
    'window': 20,
    'dropout': 0.2,
    'lstm_units': 128,
    'lstm_layers': 2,
    'patience': 50,
}

# 画图风格
PLOT_STYLE = {
    'font_family': 'SimHei,Microsoft YaHei,Arial Unicode MS',
    'figsize': (16, 12)
}

# 预测天数、验证集长度
PRED_DAYS = 5
VAL_DAYS = 30

# 调试模式
DEBUG = False

# TUI默认参数
import datetime
TODAY = datetime.date.today()
DEFAULT_END_DATE = TODAY.strftime('%Y-%m-%d')
DEFAULT_START_DATE = (TODAY - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
DEFAULT_STOCK_NAME = '中芯国际'

# ARIMA默认参数（参考3.1.8实际建模参数）
ARIMA_DEFAULTS = {
    'order': (5, 1, 5),  # (p, d, q)
    'seasonal_order': (0, 0, 0, 0),  # (P, D, Q, s)，如无季节性可不填
    'trend': 'c',  # 常数项
}

# Prophet默认参数（参考3.1.8实际建模参数）
PROPHET_DEFAULTS = {
    'seasonality_mode': 'additive',  # 可选 'additive' 或 'multiplicative'
    'changepoint_prior_scale': 0.10,  # 趋势变化点灵敏度
    'seasonality_prior_scale': 10.0,  # 季节性先验
    'holidays_prior_scale': 5.0,      # 节假日先验
    'yearly_seasonality': True,
    'weekly_seasonality': True,
    'daily_seasonality': False,
    'interval_width': 0.95,
    'changepoint_range': 0.8,
    'n_changepoints': 25,
    'add_monthly': True,  # 是否添加月度季节性
    'monthly_fourier_order': 5,  # 月度季节性Fourier阶数
}

# BOLL带默认参数（参考3.1.8实际参数）
BOLL_DEFAULTS = {
    'window': 20,  # 均线窗口
    'num_std': 2,  # 标准差倍数
}

# TUI主菜单内容（如需多语言/自定义可在此扩展）
TUI_MENU = [
    '特征工程',
    'K线图',
    'BOLL布林带',
    'ARIMA预测',
    'Prophet周期分析',
    'Prophet未来预测',
    'LSTM多目标预测',
    '退出'
]

# 其它全局参数可在此扩展 