import pandas as pd

# 读取Excel文件
policy_data = pd.read_excel('policy_data.xlsx')
policy_test = pd.read_excel('policy_test.xlsx')

# 输出policy_data的前5行
print("policy_data.xlsx的前5行数据：")
print(policy_data.head())

# 获取数据的基本信息
data_info = {
    'policy_data_shape': policy_data.shape,
    'policy_test_shape': policy_test.shape,
    'policy_data_columns': policy_data.columns.tolist(),
    'policy_test_columns': policy_test.columns.tolist(),
    'policy_data_dtypes': policy_data.dtypes,
    'policy_test_dtypes': policy_test.dtypes
}

# 将分析结果写入markdown文件
with open('basic_analysis.md', 'w', encoding='utf-8') as f:
    f.write('# 保单数据分析报告\n\n')
    
    # 写入policy_data的前5行数据
    f.write('## policy_data.xlsx前5行数据\n')
    f.write('```\n')
    f.write(str(policy_data.head()))
    f.write('\n```\n\n')
    
    # 写入数据基本信息
    f.write('## 数据基本信息\n\n')
    f.write('### policy_data.xlsx\n')
    f.write(f'- 数据维度: {data_info["policy_data_shape"]}\n')
    f.write('- 列名:\n')
    for col in data_info['policy_data_columns']:
        f.write(f'  - {col}\n')
    f.write('\n### policy_test.xlsx\n')
    f.write(f'- 数据维度: {data_info["policy_test_shape"]}\n')
    f.write('- 列名:\n')
    for col in data_info['policy_test_columns']:
        f.write(f'  - {col}\n')
    
    # 写入数据分析建议
    f.write('\n## 数据分析建议\n\n')
    f.write('根据数据的基本信息，这些数据可以用于：\n')
    f.write('1. 保单数据分析：分析保单的基本特征和分布情况\n')
    f.write('2. 客户行为分析：研究客户的保单购买行为和偏好\n')
    f.write('3. 风险预测：基于历史数据预测保单风险\n')
    f.write('4. 客户分群：对客户进行分群，制定差异化营销策略\n')
    f.write('5. 续保预测：预测客户续保的可能性\n') 