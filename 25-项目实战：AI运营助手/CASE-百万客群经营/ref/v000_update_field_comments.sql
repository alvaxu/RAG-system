-- 程序说明：
-- 1. 本SQL用于更新customer_base和customer_behavior_assets表中布尔字段和类别字段的注释
-- 2. 为字段添加具体的值含义说明

-- 更新customer_base表的类别字段注释
COMMENT ON COLUMN customer_base.gender IS '性别 (男/女)';
COMMENT ON COLUMN customer_base.lifecycle_stage IS '生命周期阶段 (新客户/成长客户/成熟客户/忠诚客户)';
COMMENT ON COLUMN customer_base.marriage_status IS '婚姻状况 (已婚/未婚)';
COMMENT ON COLUMN customer_base.city_level IS '城市等级 (一线城市/二线城市/三线城市/其他)';

-- 更新customer_behavior_assets表的布尔字段注释
COMMENT ON COLUMN customer_behavior_assets.deposit_flag IS '存款标志 (0: 无存款产品, 1: 有存款产品)';
COMMENT ON COLUMN customer_behavior_assets.financial_flag IS '理财标志 (0: 无理财产品, 1: 有理财产品)';
COMMENT ON COLUMN customer_behavior_assets.fund_flag IS '基金标志 (0: 无基金产品, 1: 有基金产品)';
COMMENT ON COLUMN customer_behavior_assets.insurance_flag IS '保险标志 (0: 无保险产品, 1: 有保险产品)';

-- 更新customer_behavior_assets表的类别字段注释
COMMENT ON COLUMN customer_behavior_assets.asset_level IS '资产等级 (普通客户/中端客户/高端客户/私人银行)';
COMMENT ON COLUMN customer_behavior_assets.contact_result IS '联系结果 (成功/未接通/NaN，NaN表示未联系)'; 