-- 程序说明：
-- 1. 本SQL用于创建customer_base和customer_behavior_assets表
-- 2. 适配Oracle数据库，注释通过COMMENT语句实现
-- 3. 包含主键和外键约束的创建

-- 删除已存在的表（如果存在）
DROP TABLE customer_behavior_assets CASCADE CONSTRAINTS;
DROP TABLE customer_base CASCADE CONSTRAINTS;

-- 1. 创建客户基础信息表
CREATE TABLE customer_base (
    customer_id VARCHAR2(32) PRIMARY KEY,
    name VARCHAR2(32) NOT NULL,
    age NUMBER(3),
    gender VARCHAR2(4),
    occupation VARCHAR2(32),
    occupation_type VARCHAR2(32),
    monthly_income NUMBER(12,2),
    open_account_date DATE,
    lifecycle_stage VARCHAR2(16),
    marriage_status VARCHAR2(8),
    city_level VARCHAR2(16),
    branch_name VARCHAR2(64)
);

-- 2. 创建客户行为与资产表
CREATE TABLE customer_behavior_assets (
    id VARCHAR2(32) PRIMARY KEY,
    customer_id VARCHAR2(32) NOT NULL,
    total_assets NUMBER(20,2),
    deposit_balance NUMBER(20,2),
    financial_balance NUMBER(20,2),
    fund_balance NUMBER(20,2),
    insurance_balance NUMBER(20,2),
    asset_level VARCHAR2(16),
    deposit_flag NUMBER(1),
    financial_flag NUMBER(1),
    fund_flag NUMBER(1),
    insurance_flag NUMBER(1),
    product_count NUMBER(4),
    financial_repurchase_count NUMBER(6),
    credit_card_monthly_expense NUMBER(12,2),
    investment_monthly_count NUMBER(6),
    app_login_count NUMBER(6),
    app_financial_view_time NUMBER(10,2),
    app_product_compare_count NUMBER(6),
    last_app_login_time TIMESTAMP,
    last_contact_time TIMESTAMP,
    contact_result VARCHAR2(16),
    marketing_cool_period DATE,
    stat_month VARCHAR2(7),
    CONSTRAINT fk_customer_id FOREIGN KEY (customer_id) REFERENCES customer_base(customer_id)
);

-- 3. 创建索引
CREATE INDEX idx_customer_base_lifecycle ON customer_base(lifecycle_stage);
CREATE INDEX idx_customer_base_city ON customer_base(city_level);
CREATE INDEX idx_behavior_assets_month ON customer_behavior_assets(stat_month);
CREATE INDEX idx_behavior_assets_asset_level ON customer_behavior_assets(asset_level);

-- 4. 添加表注释
COMMENT ON TABLE customer_base IS '客户基础信息表';
COMMENT ON TABLE customer_behavior_assets IS '客户行为与资产表';

-- 5. 添加字段注释
-- 客户基础信息表字段注释
COMMENT ON COLUMN customer_base.customer_id IS '客户唯一标识';
COMMENT ON COLUMN customer_base.name IS '客户姓名';
COMMENT ON COLUMN customer_base.age IS '客户年龄';
COMMENT ON COLUMN customer_base.gender IS '性别 (男/女)';
COMMENT ON COLUMN customer_base.occupation IS '职业';
COMMENT ON COLUMN customer_base.occupation_type IS '职业类型';
COMMENT ON COLUMN customer_base.monthly_income IS '月收入';
COMMENT ON COLUMN customer_base.open_account_date IS '开户日期';
COMMENT ON COLUMN customer_base.lifecycle_stage IS '生命周期阶段 (新客户/成长客户/成熟客户/忠诚客户)';
COMMENT ON COLUMN customer_base.marriage_status IS '婚姻状况 (已婚/未婚)';
COMMENT ON COLUMN customer_base.city_level IS '城市等级 (一线城市/二线城市/三线城市/其他)';
COMMENT ON COLUMN customer_base.branch_name IS '开户网点';

-- 客户行为与资产表字段注释
COMMENT ON COLUMN customer_behavior_assets.id IS '记录唯一标识';
COMMENT ON COLUMN customer_behavior_assets.customer_id IS '客户唯一标识';
COMMENT ON COLUMN customer_behavior_assets.total_assets IS '总资产';
COMMENT ON COLUMN customer_behavior_assets.deposit_balance IS '存款余额';
COMMENT ON COLUMN customer_behavior_assets.financial_balance IS '理财余额';
COMMENT ON COLUMN customer_behavior_assets.fund_balance IS '基金余额';
COMMENT ON COLUMN customer_behavior_assets.insurance_balance IS '保险余额';
COMMENT ON COLUMN customer_behavior_assets.asset_level IS '资产等级 (普通客户/中端客户/高端客户/私人银行)';
COMMENT ON COLUMN customer_behavior_assets.deposit_flag IS '存款标志 (0: 无存款产品, 1: 有存款产品)';
COMMENT ON COLUMN customer_behavior_assets.financial_flag IS '理财标志 (0: 无理财产品, 1: 有理财产品)';
COMMENT ON COLUMN customer_behavior_assets.fund_flag IS '基金标志 (0: 无基金产品, 1: 有基金产品)';
COMMENT ON COLUMN customer_behavior_assets.insurance_flag IS '保险标志 (0: 无保险产品, 1: 有保险产品)';
COMMENT ON COLUMN customer_behavior_assets.product_count IS '产品持有数';
COMMENT ON COLUMN customer_behavior_assets.financial_repurchase_count IS '理财复购次数';
COMMENT ON COLUMN customer_behavior_assets.credit_card_monthly_expense IS '信用卡月消费';
COMMENT ON COLUMN customer_behavior_assets.investment_monthly_count IS '月投资次数';
COMMENT ON COLUMN customer_behavior_assets.app_login_count IS 'APP登录次数';
COMMENT ON COLUMN customer_behavior_assets.app_financial_view_time IS 'APP理财页面浏览时长';
COMMENT ON COLUMN customer_behavior_assets.app_product_compare_count IS 'APP产品对比次数';
COMMENT ON COLUMN customer_behavior_assets.last_app_login_time IS '最近APP登录时间';
COMMENT ON COLUMN customer_behavior_assets.last_contact_time IS '最近联系时间';
COMMENT ON COLUMN customer_behavior_assets.contact_result IS '联系结果 (成功/未接通/NaN，NaN表示未联系)'; 
COMMENT ON COLUMN customer_behavior_assets.marketing_cool_period IS '营销冷却期';
COMMENT ON COLUMN customer_behavior_assets.stat_month IS '统计月份'; 