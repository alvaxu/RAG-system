-- 程序说明：
-- 1. 本SQL用于创建stock_history_data表，字段与tushare日线行情（daily）接口返回字段一致，增加stock_name字段用于存储股票名称。
-- 2. 适配Oracle数据库，注释通过COMMENT语句实现。

-- 1. 创建表
CREATE TABLE stock_history_data (
    stock_name VARCHAR2(32) NOT NULL,
    ts_code VARCHAR2(16) NOT NULL,
    trade_date DATE NOT NULL,
    open NUMBER(10, 3),
    high NUMBER(10, 3),
    low NUMBER(10, 3),
    close NUMBER(10, 3),
    pre_close NUMBER(10, 3),
    change NUMBER(10, 3),
    pct_chg NUMBER(6, 3),
    vol NUMBER(20),
    amount NUMBER(20, 3)
);

-- 2. 字段注释
COMMENT ON COLUMN stock_history_data.stock_name IS '股票名称';
COMMENT ON COLUMN stock_history_data.ts_code IS '股票代码';
COMMENT ON COLUMN stock_history_data.trade_date IS '交易日期';
COMMENT ON COLUMN stock_history_data.open IS '开盘价';
COMMENT ON COLUMN stock_history_data.high IS '最高价';
COMMENT ON COLUMN stock_history_data.low IS '最低价';
COMMENT ON COLUMN stock_history_data.close IS '收盘价';
COMMENT ON COLUMN stock_history_data.pre_close IS '昨收价';
COMMENT ON COLUMN stock_history_data.change IS '涨跌额';
COMMENT ON COLUMN stock_history_data.pct_chg IS '涨跌幅(%)';
COMMENT ON COLUMN stock_history_data.vol IS '成交量(手)';
COMMENT ON COLUMN stock_history_data.amount IS '成交额(千元)';

-- 3. 表注释
COMMENT ON TABLE stock_history_data IS '股票历史日线行情数据（含股票名称）';