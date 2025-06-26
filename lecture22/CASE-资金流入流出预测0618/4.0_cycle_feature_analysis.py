'''
4.0_cycle_feature_analysis.py
功能：
- 可视化分析各周期因子（weekday、month_period、is_holiday、is_workday_shift、is_next_workday）与申购/赎回的关系。
- 输出各因子分组下申购/赎回均值、样本数、标准差、最大/最小值等统计信息，便于直观理解周期因子的影响。
- 分组统计信息写入csv，图片输出到4.0_feature_output目录。
- 分析结论写入print和注释。
'''

import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib

# 设置matplotlib支持中文
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('4.0_feature_output', exist_ok=True)

# 1. 读取特征和原始数据
feature_df = pd.read_csv('4.0_feature_output/4.0_cycle_daily_features.csv', parse_dates=['ds'])
user_balance = pd.read_csv('user_balance_table.csv', encoding='utf-8')
user_balance['report_date'] = pd.to_datetime(user_balance['report_date'], format='%Y%m%d')

# 2. 聚合每日申购/赎回总额
agg = user_balance.groupby('report_date')[['total_purchase_amt','total_redeem_amt']].sum().reset_index()
agg = agg.rename(columns={'report_date': 'ds', 'total_purchase_amt': 'purchase', 'total_redeem_amt': 'redeem'})

# 3. 合并特征
df = pd.merge(feature_df, agg, on='ds', how='left')

# 4. 可视化分析各周期因子
factors = ['weekday', 'month_period', 'is_holiday', 'is_workday_shift', 'is_next_workday']
for factor in factors:
    plt.figure(figsize=(8,5))
    if df[factor].dtype == 'O':
        order = ['begin','middle','end'] if factor=='month_period' else sorted(df[factor].unique())
        df.groupby(factor)[['purchase','redeem']].mean().loc[order].plot(kind='bar', ax=plt.gca())
    else:
        df.groupby(factor)[['purchase','redeem']].mean().plot(kind='bar', ax=plt.gca())
    plt.title(f'{factor}分组下申购/赎回均值')
    plt.ylabel('金额')
    plt.xlabel(factor)
    plt.tight_layout()
    plt.savefig(f'4.0_feature_output/4.0_cycle_{factor}_mean.png')
    plt.close()
    # 统计信息
    group_stats = df.groupby(factor)[['purchase','redeem']].agg(['mean','std','min','max','count'])
    group_stats.columns = ['_'.join(col) for col in group_stats.columns]
    group_stats.to_csv(f'4.0_feature_output/4.0_cycle_{factor}_group_stats.csv', encoding='utf-8-sig')
    # 控制台打印均值和样本数
    print(f'\n[{factor}]分组下申购/赎回均值及样本数:')
    print(group_stats[['purchase_mean','redeem_mean','purchase_count']])

# 5. 分析结论（可根据实际输出补充）
print('\n分析结论建议：')
print('1. weekday: 通常周一至周五资金流动较高，周末较低（如有调休需结合is_workday_shift判断）。')
print('2. month_period: 月初/月末可能存在申购/赎回高峰。')
print('3. is_holiday: 节假日资金流动特征明显，通常申购减少、赎回增加或反之。')
print('4. is_workday_shift: 调休补班日资金流动接近普通工作日。')
print('5. is_next_workday: 节后首个工作日资金流动可能有特殊波动。')
print('具体结论请结合输出图片和分组统计csv进一步分析。') 