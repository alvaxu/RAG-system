import pandas as pd

"""
:function: 读取 user_balance_table.csv 文件的前5行数据
:param 无
:return: 前5行的DataFrame
"""
def read_first5_rows():
    # 读取前5行数据
    try:
        df = pd.read_csv('user_balance_table.csv', encoding='utf-8', nrows=5)
    except UnicodeDecodeError:
        # 如果utf-8编码出错，尝试使用gbk编码
        df = pd.read_csv('user_balance_table.csv', encoding='gbk', nrows=5)
    print(df)

if __name__ == "__main__":
    read_first5_rows() 