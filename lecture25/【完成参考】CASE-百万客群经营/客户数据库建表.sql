-- 银行客户数据表建表语句
CREATE TABLE customer_data (
    customer_id VARCHAR(10) PRIMARY KEY COMMENT '客户编号',
    gender CHAR(1) COMMENT '性别: M-男, F-女',
    age INT COMMENT '年龄',
    occupation VARCHAR(20) COMMENT '职业',
    marital_status VARCHAR(10) COMMENT '婚姻状况: 已婚、未婚、离异',
    city_level VARCHAR(10) COMMENT '城市等级: 一线、二线、三线',
    account_open_date VARCHAR(10) COMMENT '开户日期',
    total_aum DECIMAL(18, 2) COMMENT '总资产管理规模',
    deposit_balance DECIMAL(18, 2) COMMENT '存款余额',
    wealth_management_balance DECIMAL(18, 2) COMMENT '理财余额',
    fund_balance DECIMAL(18, 2) COMMENT '基金余额',
    insurance_balance DECIMAL(18, 2) COMMENT '保险余额',
    deposit_balance_monthly_avg DECIMAL(18, 2) COMMENT '存款月均余额',
    wealth_management_balance_monthly_avg DECIMAL(18, 2) COMMENT '理财月均余额',
    fund_balance_monthly_avg DECIMAL(18, 2) COMMENT '基金月均余额',
    insurance_balance_monthly_avg DECIMAL(18, 2) COMMENT '保险月均余额',
    monthly_transaction_count DECIMAL(10, 2) COMMENT '月均交易次数',
    monthly_transaction_amount DECIMAL(18, 2) COMMENT '月均交易金额',
    last_transaction_date VARCHAR(10) COMMENT '最近交易日期',
    mobile_bank_login_count INT COMMENT '手机银行登录次数',
    branch_visit_count INT COMMENT '网点访问次数',
    last_mobile_login VARCHAR(10) COMMENT '最近手机银行登录日期',
    last_branch_visit VARCHAR(10) COMMENT '最近网点访问日期',
    customer_tier VARCHAR(10) COMMENT '客户等级: 普通、潜力、临界、高净值'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='银行客户数据表';

-- 创建索引
CREATE INDEX idx_customer_tier ON customer_data(customer_tier);
CREATE INDEX idx_age ON customer_data(age);
CREATE INDEX idx_total_aum ON customer_data(total_aum);
CREATE INDEX idx_occupation ON customer_data(occupation);
CREATE INDEX idx_city_level ON customer_data(city_level);
CREATE INDEX idx_account_open_date ON customer_data(account_open_date);
CREATE INDEX idx_last_transaction_date ON customer_data(last_transaction_date);

-- 用于数据导入的SQL语句示例
-- LOAD DATA INFILE '二组模拟数据.csv'
-- INTO TABLE customer_data
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 LINES
-- (customer_id, gender, age, occupation, marital_status, city_level, account_open_date,
-- total_aum, deposit_balance, wealth_management_balance, fund_balance, insurance_balance,
-- deposit_balance_monthly_avg, wealth_management_balance_monthly_avg, fund_balance_monthly_avg, 
-- insurance_balance_monthly_avg, monthly_transaction_count, monthly_transaction_amount, 
-- last_transaction_date, mobile_bank_login_count, branch_visit_count, last_mobile_login, last_branch_visit,
-- customer_tier); 