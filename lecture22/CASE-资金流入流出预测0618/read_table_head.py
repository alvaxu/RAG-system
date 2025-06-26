import pandas as pd

# 读取前五行数据的通用函数
"""
:function: read_head
:param file_path: 文件路径
:param n: 读取的行数，默认5
:return: DataFrame，前n行数据
"""
def read_head(file_path, n=5):
    try:
        df = pd.read_csv(file_path, encoding='utf-8', nrows=n)
        print(f'文件 {file_path} 前{n}行:')
        print(df)
        print('\n')
        return df
    except Exception as e:
        print(f'读取 {file_path} 时出错: {e}')
        return None

if __name__ == '__main__':
    # 需要读取的文件列表
    files = [
        'mfd_bank_shibor.csv',
        'mfd_day_share_interest.csv',
        'user_profile_table.csv',
        'user_balance_table.csv',
    ]
    for file in files:
        read_head(file, 5) 