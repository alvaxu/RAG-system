-- 程序说明：
-- 1. 本SQL用于创建stock_history_data表，字段与tushare日线行情（daily）接口返回字段一致，增加stock_name字段用于存储股票名称。
-- 2. 可直接用于MySQL等主流数据库，字段类型已做合理推断，如需适配其他数据库请根据实际情况调整。

CREATE TABLE stock_history_data (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    stock_name VARCHAR(32) NOT NULL COMMENT '股票名称',
    ts_code VARCHAR(16) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open DECIMAL(10, 3) COMMENT '开盘价',
    high DECIMAL(10, 3) COMMENT '最高价',
    low DECIMAL(10, 3) COMMENT '最低价',
    close DECIMAL(10, 3) COMMENT '收盘价',
    pre_close DECIMAL(10, 3) COMMENT '昨收价',
    change DECIMAL(10, 3) COMMENT '涨跌额',
    pct_chg DECIMAL(6, 3) COMMENT '涨跌幅(%)',
    vol BIGINT COMMENT '成交量(手)',
    amount DECIMAL(20, 3) COMMENT '成交额(千元)'
) COMMENT='股票历史日线行情数据（含股票名称）'; 