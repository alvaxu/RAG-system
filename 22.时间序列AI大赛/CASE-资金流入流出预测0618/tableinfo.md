# 数据表结构说明（tableinfo.md）

---

## 1. mfd_bank_shibor.csv

| 字段名           | 类型    | 含义           |
|------------------|---------|----------------|
| mfd_date         | int     | 日期（YYYYMMDD）|
| Interest_O_N     | float   | 隔夜利率       |
| Interest_1_W     | float   | 1周利率        |
| Interest_2_W     | float   | 2周利率        |
| Interest_1_M     | float   | 1月利率        |
| Interest_3_M     | float   | 3月利率        |
| Interest_6_M     | float   | 6月利率        |
| Interest_9_M     | float   | 9月利率        |
| Interest_1_Y     | float   | 1年利率        |

---

## 2. mfd_day_share_interest.csv

| 字段名           | 类型    | 含义           |
|------------------|---------|----------------|
| mfd_date         | int     | 日期（YYYYMMDD）|
| mfd_daily_yield  | float   | 当日万份收益    |
| mfd_7daily_yield | float   | 七日年化收益率  |

---

## 3. user_profile_table.csv

| 字段名        | 类型    | 含义         |
|---------------|---------|--------------|
| user_id       | int     | 用户ID       |
| sex           | int     | 性别（0/1）  |
| city          | int     | 城市编码     |
| constellation | string  | 星座         |

---

## 4. user_balance_table.csv

| 字段名               | 类型    | 含义                     |
|----------------------|---------|--------------------------|
| user_id              | int     | 用户ID                   |
| report_date          | int     | 日期（YYYYMMDD）         |
| tBalance             | int     | 今日余额                 |
| yBalance             | int     | 昨日余额                 |
| total_purchase_amt   | int     | 今日购买总量             |
| direct_purchase_amt  | int     | 今日直接购买量           |
| purchase_bal_amt     | int     | 今日宝付宝购买量         |
| purchase_bank_amt    | int     | 今日银行卡购买量         |
| total_redeem_amt     | int     | 今日赎回总量             |
| consume_amt          | int     | 今日消费总量             |
| transfer_amt         | int     | 今日转出总量             |
| tftobal_amt          | int     | 今日转出到支付宝余额总量 |
| tftocard_amt         | int     | 今日转出到支付宝卡总量   |
| share_amt            | int     | 今日收益                 |
| category1            | float   | 今日类别1消费总额        |
| category2            | float   | 今日类别2消费总额        |
| category3            | float   | 今日类别3消费总额        |
| category4            | float   | 今日类别4消费总额        |

---

> 注：所有表均为UTF-8编码，字段类型根据前五行数据推断。 