import pandas as pd
import json

# 读取Excel文件
df = pd.read_excel('香港各区疫情数据_20250322.xlsx')

# 确保日期列是datetime类型
df['报告日期'] = pd.to_datetime(df['报告日期'])

# 计算每日统计数据
daily_stats = df.groupby('报告日期').agg({
    '新增确诊': 'sum',
    '累计确诊': 'sum'
}).reset_index()

# 计算增长率
daily_stats['增长率'] = daily_stats['新增确诊'] / daily_stats['累计确诊'].shift(1) * 100
daily_stats['增长率'] = daily_stats['增长率'].fillna(0)

# 计算各地区累计确诊
area_stats = df.groupby('地区名称').agg({
    '累计确诊': 'max'
}).reset_index()

# 准备数据
data = {
    'dates': daily_stats['报告日期'].dt.strftime('%Y-%m-%d').tolist(),
    'newCases': daily_stats['新增确诊'].tolist(),
    'totalCases': daily_stats['累计确诊'].tolist(),
    'growthRate': daily_stats['增长率'].round(2).tolist(),
    'areaData': area_stats.to_dict('records')
}

# 保存为JSON文件
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('数据已处理完成，保存为data.json') 