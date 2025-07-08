import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('eda_output', exist_ok=True)

# 1. 读取数据
bank_shibor = pd.read_csv('mfd_bank_shibor.csv', encoding='utf-8')
day_share_interest = pd.read_csv('mfd_day_share_interest.csv', encoding='utf-8')
user_profile = pd.read_csv('user_profile_table.csv', encoding='utf-8')
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')

# 2. 数据量与字段类型、缺失值统计
summary = {}
for name, df in zip([
    'mfd_bank_shibor', 'mfd_day_share_interest', 'user_profile_table', 'user_balance_table'],
    [bank_shibor, day_share_interest, user_profile, user_balance]):
    summary[name] = {
        'shape': df.shape,
        'dtypes': df.dtypes.astype(str).to_dict(),
        'missing': df.isnull().sum().to_dict()
    }
pd.DataFrame(summary).to_csv('eda_output/各表字段类型与缺失统计.csv', encoding='utf-8-sig')

# 3. 主要数值型字段描述性统计
bank_shibor.describe().to_csv('eda_output/bank_shibor_描述统计.csv', encoding='utf-8-sig')
day_share_interest.describe().to_csv('eda_output/day_share_interest_描述统计.csv', encoding='utf-8-sig')
user_balance.describe().to_csv('eda_output/user_balance_描述统计.csv', encoding='utf-8-sig')

# 4. 用户画像分析
# 性别分布
plt.figure()
user_profile['sex'].value_counts().plot.pie(autopct='%.1f%%', labels=['男','女'] if 1 in user_profile['sex'].unique() else ['女','男'])
plt.title('用户性别分布')
plt.ylabel('')
plt.savefig('eda_output/用户性别分布.png')
plt.close()

# 城市分布（前10）
plt.figure(figsize=(10,5))
user_profile['city'].value_counts().head(10).plot.bar()
plt.title('用户城市分布（前10）')
plt.xlabel('城市编码')
plt.ylabel('用户数')
plt.savefig('eda_output/用户城市分布前10.png')
plt.close()

# 星座分布
plt.figure(figsize=(8,6))
user_profile['constellation'].value_counts().plot.pie(autopct='%.1f%%')
plt.title('用户星座分布')
plt.ylabel('')
plt.savefig('eda_output/用户星座分布.png')
plt.close()

# 5. 申购/赎回金额、余额、收益等分布与趋势
# 日期格式转换
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 每日申购/赎回总额趋势
daily = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum()
plt.figure(figsize=(16,6))
plt.plot(daily.index, daily['total_purchase_amt'], label='申购总额')
plt.plot(daily.index, daily['total_redeem_amt'], label='赎回总额')
plt.title('每日申购与赎回总额趋势')
plt.xlabel('日期')
plt.ylabel('金额（分）')
plt.legend()
plt.tight_layout()
plt.savefig('eda_output/每日申购赎回总额趋势.png')
plt.close()

daily[['total_purchase_amt','total_redeem_amt']].describe().to_csv('eda_output/每日申购赎回总额_描述统计.csv', encoding='utf-8-sig')

# 余额分布
plt.figure(figsize=(8,6))
user_balance['tBalance'].hist(bins=50)
plt.title('今日余额分布')
plt.xlabel('余额（分）')
plt.ylabel('用户数')
plt.savefig('eda_output/今日余额分布.png')
plt.close()

# 收益分布
plt.figure(figsize=(8,6))
user_balance['share_amt'].hist(bins=50)
plt.title('今日收益分布')
plt.xlabel('收益（分）')
plt.ylabel('用户数')
plt.savefig('eda_output/今日收益分布.png')
plt.close()

# 申购/赎回金额箱线图
plt.figure(figsize=(8,6))
sns.boxplot(data=user_balance[['total_purchase_amt','total_redeem_amt']])
plt.title('申购/赎回金额箱线图')
plt.savefig('eda_output/申购赎回金额箱线图.png')
plt.close()

# 6. 收益率与利率分析
# 日期格式转换
bank_shibor['mfd_date'] = pd.to_datetime(bank_shibor['mfd_date'], format='%Y%m%d')
day_share_interest['mfd_date'] = pd.to_datetime(day_share_interest['mfd_date'], format='%Y%m%d')

# 收益率趋势
plt.figure(figsize=(16,6))
plt.plot(day_share_interest['mfd_date'], day_share_interest['mfd_daily_yield'], label='当日万份收益')
plt.plot(day_share_interest['mfd_date'], day_share_interest['mfd_7daily_yield'], label='七日年化收益率')
plt.title('余额宝收益率趋势')
plt.xlabel('日期')
plt.ylabel('收益率')
plt.legend()
plt.tight_layout()
plt.savefig('eda_output/余额宝收益率趋势.png')
plt.close()

# 利率趋势
plt.figure(figsize=(16,6))
for col in ['Interest_O_N','Interest_1_W','Interest_2_W','Interest_1_M','Interest_3_M','Interest_6_M','Interest_9_M','Interest_1_Y']:
    plt.plot(bank_shibor['mfd_date'], bank_shibor[col], label=col)
plt.title('Shibor利率趋势')
plt.xlabel('日期')
plt.ylabel('利率（%）')
plt.legend()
plt.tight_layout()
plt.savefig('eda_output/Shibor利率趋势.png')
plt.close()

# 7. 保存部分中间结果
user_profile.to_csv('eda_output/user_profile_table.csv', index=False, encoding='utf-8-sig')
user_balance.to_csv('eda_output/user_balance_table_head10000.csv', index=False, encoding='utf-8-sig',
                    columns=user_balance.columns)

# 8. 其他分析可根据需要补充
print('EDA分析与可视化已完成，结果保存在eda_output目录。') 